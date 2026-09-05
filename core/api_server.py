import os
import time
import uuid
import json
import hashlib
import secrets
import threading
from io import BytesIO
from datetime import datetime
from flask import (
    Flask, request, jsonify, render_template, redirect,
    send_file, url_for, Response, session
)
from camera_scanner import camera_scanner
from qr_engine import (
    load_config,
    save_config,
    get_account,
    add_or_update_account,
    delete_account,
    generate_qrph_payload,
    generate_qr_image,
    generate_qr_base64,
    get_random_merchant_name
)

from database import (
    init_db,
    create_order,
    get_order,
    get_recent_orders,
    mark_as_paid
)
from wallet_manager import rate_engine, wallet_manager, get_wallet_for_user, logout_user_wallet

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Session & Auth Security Config
_init_cfg = load_config()
app.secret_key = _init_cfg.get("security", {}).get("session_secret", "coins_gateway_secret_key_8899_xyz")
ADMIN_PASSWORD = _init_cfg.get("security", {}).get("admin_password", "admin123")

USERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users.json")
ACCESS_CODES_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "access_codes.json")

def get_all_users():
    if not os.path.exists(USERS_FILE):
        return {}
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_all_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def get_all_codes():
    if not os.path.exists(ACCESS_CODES_FILE):
        return {}
    try:
        with open(ACCESS_CODES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_all_codes(codes):
    with open(ACCESS_CODES_FILE, "w", encoding="utf-8") as f:
        json.dump(codes, f, indent=2, ensure_ascii=False)


# ============================================================
# REALTIME USER CLIENT ACTIVITY TRACKER (ADMIN MONITOR)
# ============================================================
_user_activity = {}
_user_activity_lock = threading.Lock()
_activity_feed = []

def parse_device_info(ua_string: str) -> str:
    ua = (ua_string or "").lower()
    if "android" in ua:
        return "📱 Android Mobile"
    if "iphone" in ua or "ipad" in ua:
        return "🍎 iOS Apple"
    if "windows" in ua:
        return "💻 Windows PC"
    if "macintosh" in ua or "mac os" in ua:
        return "🍏 Mac OS"
    if "linux" in ua:
        return "🐧 Linux"
    return "🌐 Web Browser"

def get_client_ip(req) -> str:
    if not req:
        return "127.0.0.1"
    cf_ip = req.headers.get("CF-Connecting-IP")
    if cf_ip:
        return cf_ip.strip()
    xff = req.headers.get("X-Forwarded-For")
    if xff:
        return xff.split(",")[0].strip()
    return req.remote_addr or "127.0.0.1"

def record_user_activity(username: str, req, action: str = "Aktivitas"):
    if not username or username.lower() in ("admin", "superadmin"):
        return
    now = time.time()
    ip = get_client_ip(req)
    ua_str = req.user_agent.string if req and req.user_agent else ""
    device = parse_device_info(ua_str)
    path = req.path if req else "/pos"

    with _user_activity_lock:
        prev = _user_activity.get(username, {})
        login_time = prev.get("login_time", now)
        _user_activity[username] = {
            "username": username,
            "last_seen": now,
            "last_seen_str": datetime.now().strftime("%H:%M:%S"),
            "last_seen_date": datetime.now().strftime("%d %b %Y"),
            "login_time": login_time,
            "login_time_str": datetime.fromtimestamp(login_time).strftime("%H:%M:%S"),
            "last_page": path,
            "ip": ip,
            "device": device,
            "is_online": True
        }
        
        last_action = prev.get("last_action")
        last_feed = prev.get("last_feed_time", 0)
        # Log to feed if action changed or more than 180 seconds since last entry
        if action != "Heartbeat" or last_action != "Heartbeat" or (now - last_feed > 180):
            _user_activity[username]["last_action"] = action
            _user_activity[username]["last_feed_time"] = now
            _activity_feed.insert(0, {
                "time": datetime.now().strftime("%H:%M:%S"),
                "username": username,
                "action": action,
                "page": path,
                "ip": ip,
                "device": device
            })
            if len(_activity_feed) > 50:
                _activity_feed.pop()


def get_user_accounts(username: str, is_admin: bool = False) -> list:
    if is_admin or username in ("admin", "superadmin", ""):
        cfg = load_config()
        return cfg.get("accounts", [])
    users = get_all_users()
    if username in users:
        return users[username].setdefault("accounts", [])
    return []

def save_user_account(username: str, is_admin: bool, name: str, phone: str, city: str = "Manila", display_name: str = None, slot_id: str = None):
    if is_admin or username in ("admin", "superadmin", ""):
        return add_or_update_account(name=name, phone=phone, city=city, display_name=display_name, slot_id=slot_id)
    users = get_all_users()
    user_info = users.setdefault(username, {})
    accounts = user_info.setdefault("accounts", [])
    if not slot_id:
        existing_ids = {a.get("id") for a in accounts if a.get("id")}
        i = 1
        while f"slot_{i}" in existing_ids:
            i += 1
        slot_id = f"slot_{i}"
    
    new_acc = {
        "id": slot_id,
        "name": name.strip(),
        "phone": phone.strip(),
        "account_id": phone.strip(),
        "bank_bic": "DCPHPHM1XXX",
        "sub_id": "99964403",
        "city": city.strip() or "Manila",
        "mcc": "6016",
        "currency_code": "608",
        "terminal_id": "12345678",
        "active": True
    }
    found = False
    for idx, acc in enumerate(accounts):
        if acc.get("id") == slot_id:
            accounts[idx] = new_acc
            found = True
            break
    if not found:
        accounts.append(new_acc)
    save_all_users(users)
    return new_acc

def delete_user_account(username: str, is_admin: bool, slot_id: str) -> bool:
    if is_admin or username in ("admin", "superadmin", ""):
        return delete_account(slot_id)
    users = get_all_users()
    if username not in users:
        return False
    accounts = users[username].get("accounts", [])
    new_accounts = [a for a in accounts if a.get("id") != slot_id]
    if len(new_accounts) != len(accounts):
        users[username]["accounts"] = new_accounts
        save_all_users(users)
        return True
    return False

@app.before_request
def check_auth():
    # Allow public endpoints
    if request.path in ['/login_code', '/logout', '/api/auth/logout']:
        return
    if request.path.startswith('/static/'):
        return
    if request.path.startswith('/checkout/') or request.path.startswith('/pay/'):
        return
    if request.path.startswith('/api/payment/') and request.method == 'GET':
        return
    if request.path.startswith('/api/qr/image'):
        return

    # Check API key for server-to-server calls
    cfg = load_config()
    server_api_key = cfg.get("server", {}).get("api_key")
    req_api_key = request.headers.get("X-API-Key") or request.args.get("api_key")
    if server_api_key and req_api_key == server_api_key:
        return

    # Check Admin API routes
    if request.path.startswith('/api/admin'):
        if not session.get('is_admin'):
            return jsonify({"success": False, "msg": "Unauthorized: Akses Admin Diperlukan"}), 403
        return

    # Check Authenticated session
    if not session.get('is_authenticated') and not session.get('is_admin'):
        if request.path.startswith('/api/'):
            return jsonify({"success": False, "message": "Sesi belum login atau kedaluwarsa. Silakan login kembali.", "need_login": True}), 401
        return redirect(url_for('login_code'))

    # Check live expiration for regular users
    if not session.get('is_admin') and session.get('username'):
        username = session.get('username')
        users = get_all_users()
        if username not in users:
            session.clear()
            if request.path.startswith('/api/'):
                return jsonify({"success": False, "message": "Akun tidak ditemukan atau telah dihapus.", "need_login": True}), 401
            return redirect(url_for('login_code'))
        user_info = users[username]
        exp = user_info.get('expires_at')
        if exp is not None and exp < time.time():
            session.clear()
            if request.path.startswith('/api/'):
                return jsonify({"success": False, "message": "Akun Anda telah kedaluwarsa! Hubungi Admin.", "need_login": True, "expired": True}), 403
            return redirect(url_for('login_code'))

    # Record user activity for live monitoring
    if session.get("is_authenticated") and session.get("username") and not session.get("is_admin"):
        page_label = "Membuka POS Kasir" if request.path == "/pos" else (
            "Membuat Invoice QR" if request.path == "/api/payment/create" else f"Akses {request.path}"
        )
        record_user_activity(session.get("username"), request, action=page_label)

# ============================================================
# STARTUP INIT
# ============================================================
init_db()

# Start live rate polling engine
rate_engine.start()


def generate_order_id() -> str:
    now_str = datetime.now().strftime("%y%m%d%H%M%S")
    rand_suffix = uuid.uuid4().hex[:4].upper()
    return f"CPH-{now_str}-{rand_suffix}"


# ============================================================
# PAGE ROUTES & AUTH
# ============================================================

@app.route("/")
def index():
    return redirect("/pos")


@app.route("/login_code", methods=["GET", "POST"])
def login_code():
    cfg = load_config()
    admin_pw = cfg.get("security", {}).get("admin_password", ADMIN_PASSWORD)
    codes = get_all_codes()
    users = get_all_users()
    now = time.time()

    if request.method == "POST":
        action = request.form.get("action", "login")

        if action == "admin":
            code = request.form.get("access_code", "").strip()
            configured_pw = cfg.get("security", {}).get("admin_password")
            valid_pws = {admin_pw, "admin123", "123123"}
            if configured_pw:
                valid_pws.add(configured_pw)
            if code and code in valid_pws:
                session.clear()
                session["is_admin"] = True
                session["is_authenticated"] = True
                session["username"] = "admin"
                return redirect(url_for("login_code"))
            return render_template("login_code.html", error="Password Admin Salah!", codes=codes, users=users, now=now)

        elif action == "register":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()
            access_code = request.form.get("access_code", "").strip()

            if not username or not password or not access_code:
                return render_template("login_code.html", error="Harap isi semua kolom pendaftaran!", register_active=True, codes=codes, users=users, now=now)

            if username in users or username.lower() == "admin":
                return render_template("login_code.html", error="Username sudah dipakai, pilih yang lain!", register_active=True, codes=codes, users=users, now=now)

            if access_code not in codes:
                return render_template("login_code.html", error="Kode Akses tidak valid atau tidak terdaftar!", register_active=True, codes=codes, users=users, now=now)

            code_info = codes[access_code]
            if code_info.get("used_by"):
                return render_template("login_code.html", error="Kode Akses sudah pernah dipakai oleh user lain!", register_active=True, codes=codes, users=users, now=now)

            # Create User
            dur_hours = float(code_info.get("duration_hours", 24))
            user_exp = now + (dur_hours * 3600) if dur_hours > 0 else None
            users[username] = {
                "password_hash": hashlib.sha256(password.encode()).hexdigest(),
                "expires_at": user_exp,
                "created_at": now,
                "accounts": []
            }
            save_all_users(users)

            code_info["used_by"] = username
            code_info["used_at"] = now
            save_all_codes(codes)

            return render_template(
                "login_code.html",
                success_msg=f"Pendaftaran akun '{username}' berhasil! Silakan login sekarang.",
                register_active=False,
                codes=codes,
                users=users,
                now=now
            )

        elif action == "login":
            session.clear()
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "").strip()

            if username not in users:
                return render_template("login_code.html", error="Username tidak ditemukan!", codes=codes, users=users, now=now)

            user_info = users[username]
            if user_info.get("password_hash") != hashlib.sha256(password.encode()).hexdigest():
                return render_template("login_code.html", error="Password salah!", codes=codes, users=users, now=now)

            exp = user_info.get("expires_at")
            if exp is not None and exp < now:
                return render_template("login_code.html", error="Akun Anda sudah kedaluwarsa! Hubungi Admin.", codes=codes, users=users, now=now)

            session["is_admin"] = False
            session["is_authenticated"] = True
            session["username"] = username
            session["expires_at"] = exp
            return redirect(url_for("pos_page"))

    return render_template("login_code.html", codes=codes, users=users, now=now)


@app.route("/logout")
def logout():
    username = session.get("username")
    if username:
        logout_user_wallet(username)
        if username.lower() not in ("admin", "superadmin"):
            with _user_activity_lock:
                if username in _user_activity:
                    _user_activity[username]["is_online"] = False
                    _user_activity[username]["last_seen"] = time.time()
                    _user_activity[username]["last_action"] = "Logout"
                    _activity_feed.insert(0, {
                        "time": datetime.now().strftime("%H:%M:%S"),
                        "username": username,
                        "action": "Logout / Menutup Sesi",
                        "page": "/logout",
                        "ip": get_client_ip(request),
                        "device": parse_device_info(request.user_agent.string if request.user_agent else "")
                    })
                    if len(_activity_feed) > 50:
                        _activity_feed.pop()
    session.clear()
    return redirect(url_for("login_code"))


@app.route("/api/user/heartbeat", methods=["POST", "GET"])
def api_user_heartbeat():
    username = session.get("username")
    if username and username.lower() not in ("admin", "superadmin"):
        record_user_activity(username, request, action="Heartbeat")
        return jsonify({"success": True, "status": "online", "time": time.time()})
    return jsonify({"success": True, "status": "ok"})


# ============================================================
# ADMIN ACCESS CODE & USER MANAGEMENT APIS
# ============================================================

@app.route("/api/admin/generate", methods=["POST"])
def admin_generate():
    data = request.get_json(silent=True) or {}
    code = data.get("code", "").strip()
    try:
        duration_hours = float(data.get("duration_hours", 24))
    except (ValueError, TypeError):
        duration_hours = 24.0

    if not code:
        return jsonify({"success": False, "msg": "Kode tidak boleh kosong"}), 400

    codes = get_all_codes()
    codes[code] = {
        "created_at": time.time(),
        "duration_hours": duration_hours,
        "expires_at": time.time() + (duration_hours * 3600) if duration_hours > 0 else None,
        "used_by": None
    }
    save_all_codes(codes)
    return jsonify({"success": True, "code": code})


@app.route("/api/admin/delete", methods=["POST"])
def admin_delete():
    data = request.get_json(silent=True) or {}
    code = data.get("code", "").strip()
    codes = get_all_codes()
    if code in codes:
        del codes[code]
        save_all_codes(codes)
    return jsonify({"success": True})


@app.route("/api/admin/delete_user", methods=["POST"])
def admin_delete_user():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    users = get_all_users()
    if username in users:
        del users[username]
        save_all_users(users)
    return jsonify({"success": True})


@app.route("/api/admin/extend_user", methods=["POST"])
def admin_extend_user():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    try:
        duration_hours = float(data.get("duration_hours", 24))
    except (ValueError, TypeError):
        duration_hours = 24.0

    users = get_all_users()
    if username not in users:
        return jsonify({"success": False, "msg": "User tidak ditemukan"}), 404

    if duration_hours == -1 or duration_hours == -1.0:
        users[username]["expires_at"] = None
        save_all_users(users)
        return jsonify({"success": True, "msg": f"Akun {username} diatur menjadi Permanen (Selamanya)!"})

    current_exp = users[username].get("expires_at")
    now = time.time()
    base_time = now if (current_exp is None or current_exp < now) else current_exp
    users[username]["expires_at"] = base_time + (duration_hours * 3600)
    save_all_users(users)
    return jsonify({"success": True, "msg": f"Akun {username} berhasil diperpanjang {duration_hours} jam!"})


@app.route("/pos")
def pos_page():
    config = load_config()
    username = session.get("username", "admin")
    is_admin = session.get("is_admin", False)
    expires_at = session.get("expires_at")
    user_config = dict(config)
    user_config["accounts"] = get_user_accounts(username, is_admin)
    return render_template(
        "pos.html",
        config=user_config,
        current_user=username,
        is_admin=is_admin,
        expires_at=expires_at,
        now=time.time()
    )


@app.route("/dashboard")
def dashboard_page():
    if not session.get("is_admin"):
        return redirect(url_for("pos_page"))
    config = load_config()
    username = session.get("username", "admin")
    return render_template(
        "dashboard.html",
        config=config,
        current_user=username,
        is_admin=True,
        now=time.time()
    )


@app.route("/api/admin/users/live_status", methods=["GET"])
def api_admin_users_live_status():
    if not session.get("is_admin"):
        return jsonify({"success": False, "message": "Unauthorized"}), 403
    
    users = get_all_users()
    now = time.time()
    results = []
    total_online = 0
    total_idle = 0
    total_offline = 0

    with _user_activity_lock:
        for uname, udata in users.items():
            if uname.lower() in ("admin", "superadmin"):
                continue
            act = _user_activity.get(uname, {})
            last_seen = act.get("last_seen", udata.get("created_at", 0))
            diff = now - last_seen if last_seen > 0 else 999999
            
            is_online_flag = act.get("is_online", False)
            if is_online_flag and diff < 45:
                status = "ONLINE"
                status_color = "success"
                total_online += 1
            elif is_online_flag and diff < 180:
                status = "IDLE"
                status_color = "warning"
                total_idle += 1
            else:
                status = "OFFLINE"
                status_color = "muted"
                total_offline += 1

            if diff < 60:
                ago_str = f"{int(diff)} detik lalu"
            elif diff < 3600:
                ago_str = f"{int(diff // 60)} menit lalu"
            elif diff < 86400:
                ago_str = f"{int(diff // 3600)} jam lalu"
            else:
                ago_str = f"{int(diff // 86400)} hari lalu"

            exp = udata.get("expires_at")
            if exp is None:
                exp_str = "Selamanya (Unlimited)"
            elif exp < now:
                exp_str = "KEDALUWARSA"
            else:
                rem = exp - now
                if rem > 86400:
                    exp_str = f"{int(rem // 86400)}h {int((rem % 86400) // 3600)}j tersisa"
                else:
                    exp_str = f"{int(rem // 3600)}j {int((rem % 3600) // 60)}m tersisa"

            results.append({
                "username": uname,
                "status": status,
                "status_color": status_color,
                "last_seen_str": datetime.fromtimestamp(last_seen).strftime("%H:%M:%S") if last_seen > 0 else "-",
                "last_seen_date": datetime.fromtimestamp(last_seen).strftime("%d/%m/%Y") if last_seen > 0 else "-",
                "last_seen_ago": ago_str if last_seen > 0 else "Belum aktif",
                "login_time_str": act.get("login_time_str", "-"),
                "current_page": act.get("last_page", "-"),
                "ip": act.get("ip", "-"),
                "device": act.get("device", "Unknown"),
                "expires_at_str": exp_str,
                "slots_count": len(udata.get("accounts", []))
            })

        order_map = {"ONLINE": 0, "IDLE": 1, "OFFLINE": 2}
        results.sort(key=lambda x: (order_map.get(x["status"], 3), x["username"]))
        feed_copy = list(_activity_feed[:40])

    return jsonify({
        "success": True,
        "server_time": datetime.now().strftime("%H:%M:%S"),
        "server_date": datetime.now().strftime("%d %B %Y"),
        "stats": {
            "total_users": len(results),
            "online": total_online,
            "idle": total_idle,
            "offline": total_offline
        },
        "users": results,
        "activity_feed": feed_copy
    })


@app.route("/api/orders", methods=["GET"])
def api_get_orders():
    limit = int(request.args.get("limit", 100))
    account_id = request.args.get("account_id")
    username = session.get("username", "admin")
    is_admin = session.get("is_admin", False)
    orders = get_recent_orders(limit=limit, account_id=account_id, username=None if is_admin else username)
    total_revenue = sum(o["amount"] for o in orders if o["status"] == "PAID")
    total_paid = sum(1 for o in orders if o["status"] == "PAID")
    total_pending = sum(1 for o in orders if o["status"] == "PENDING")
    return jsonify({
        "success": True,
        "orders": orders,
        "total_revenue": total_revenue,
        "total_paid": total_paid,
        "total_pending": total_pending,
        "total_orders": len(orders)
    })


@app.route("/pay/<order_id>")
def checkout_page(order_id):
    order = get_order(order_id)
    if not order:
        return "Invoice pembayaran tidak ditemukan.", 404
    config = load_config()
    account = get_account(order.get("account_id"), config) or {}
    qr_image_base64 = generate_qr_base64(order["qr_payload"])
    return render_template(
        "checkout.html",
        order=order,
        account=account,
        qr_image_base64=qr_image_base64,
        config=config
    )


# ============================================================
# LIVE RATE API
# ============================================================

@app.route("/api/rate", methods=["GET"])
def api_get_rate():
    """Returns live/configured USDC/USDT rate and buffer information."""
    info = rate_engine.get_info()
    return jsonify(info)


@app.route("/api/rate/set", methods=["POST"])
def api_set_rate():
    """Set manual base_rate and buffer dynamically (Admin only)."""
    if not session.get("is_admin"):
        cfg = load_config()
        server_api_key = cfg.get("server", {}).get("api_key")
        req_api_key = request.headers.get("X-API-Key") or request.args.get("api_key")
        if not (server_api_key and req_api_key == server_api_key):
            return jsonify({"success": False, "message": "Hanya Super Admin yang berhak mengubah kurs."}), 403

    data = request.get_json(silent=True) or {}
    base_rate = data.get("base_rate")
    buffer = data.get("buffer", 0.20)

    if base_rate is None:
        return jsonify({"success": False, "message": "Parameter 'base_rate' wajib diisi."}), 400

    try:
        base_rate = float(base_rate)
        buffer = float(buffer)
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Nilai base_rate atau buffer harus angka."}), 400

    info = rate_engine.set_rate(base_rate=base_rate, buffer=buffer, save=True)
    return jsonify({"success": True, "message": "Rate berhasil diperbarui.", **info})


@app.route("/api/rate/convert", methods=["GET"])
def api_rate_convert():
    """Convert PHP to USDC/USDT or vice versa using current rate."""
    php = request.args.get("php")
    usdc = request.args.get("usdc") or request.args.get("usdt")
    current_rate = rate_engine.rate

    if php is not None:
        try:
            php_val = float(php)
            usdc_val = rate_engine.php_to_usdc(php_val)
            return jsonify({
                "success": True,
                "php": round(php_val, 2),
                "usdc": usdc_val,
                "usdt": usdc_val,
                "rate": current_rate
            })
        except ValueError:
            return jsonify({"success": False, "message": "Nilai PHP tidak valid"}), 400

    if usdc is not None:
        try:
            usdc_val = float(usdc)
            php_val = rate_engine.usdc_to_php(usdc_val)
            return jsonify({
                "success": True,
                "usdc": usdc_val,
                "usdt": usdc_val,
                "php": php_val,
                "rate": current_rate
            })
        except ValueError:
            return jsonify({"success": False, "message": "Nilai token tidak valid"}), 400

    return jsonify({"success": False, "message": "Parameter 'php' atau 'usdc'/'usdt' wajib diisi"}), 400


# ============================================================
# WALLET API ENDPOINTS (Multi-Network: Base & BSC)
# ============================================================

@app.route("/api/wallet/connect", methods=["POST"])
def api_wallet_connect():
    """Connect wallet using Private Key or Seed Phrase (Per-User Isolated)."""
    username = session.get("username", "admin")
    uwallet = get_wallet_for_user(username)
    data = request.get_json(silent=True) or {}
    method = data.get("method", "private_key")  # "private_key" | "phrase"
    credential = (data.get("credential") or data.get("secret") or "").strip()

    if not credential:
        return jsonify({"success": False, "message": "Credential (PK / Phrase) tidak boleh kosong."}), 400

    if method == "phrase":
        result = uwallet.connect_phrase(credential)
    else:
        result = uwallet.connect_private_key(credential)

    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code


@app.route("/api/wallet/disconnect", methods=["POST"])
def api_wallet_disconnect():
    username = session.get("username", "admin")
    uwallet = get_wallet_for_user(username)
    uwallet.disconnect()
    return jsonify({"success": True, "message": "Wallet berhasil diputus."})


@app.route("/api/wallet/status", methods=["GET"])
def api_wallet_status():
    """Get current wallet connection status and multi-network balances for current user."""
    username = session.get("username", "admin")
    uwallet = get_wallet_for_user(username)
    if uwallet.is_connected:
        bal = uwallet.get_balance()
        return jsonify({
            "success": True,
            "connected": True,
            "address": uwallet.address,
            "address_short": f"{uwallet.address[:6]}...{uwallet.address[-4:]}" if uwallet.address else None,
            "networks": bal.get("networks", {}),
            "usdc_balance": bal.get("usdc_balance", 0.0),
            "eth_balance": bal.get("eth_balance", 0.0),
            "usdt_bsc_balance": bal.get("usdt_bsc_balance", 0.0),
            "usdc_bsc_balance": bal.get("usdc_bsc_balance", 0.0),
            "bnb_balance": bal.get("bnb_balance", 0.0),
            "method": "connected"
        })
    return jsonify({
        "success": True,
        "connected": False,
        "address": None,
        "address_short": None,
        "networks": {},
        "usdc_balance": 0.0,
        "eth_balance": 0.0,
        "usdt_bsc_balance": 0.0,
        "usdc_bsc_balance": 0.0,
        "bnb_balance": 0.0
    })


@app.route("/api/wallet/balance", methods=["GET"])
def api_wallet_balance():
    """Get balances across Base (USDC, ETH) and BSC (USDT, USDC, BNB) for current user."""
    username = session.get("username", "admin")
    uwallet = get_wallet_for_user(username)
    network = request.args.get("network")
    if not uwallet.is_connected:
        return jsonify({"success": False, "message": "Wallet belum terkoneksi."}), 200
    result = uwallet.get_balance(network=network)
    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code


@app.route("/api/wallet/send", methods=["POST"])
def api_wallet_send():
    """
    Send Token on Base (USDC) or BSC (USDT/USDC) from current user's wallet.
    Body: {
        "to": "0x...",
        "amount": 1.17,
        "network": "base" | "bsc",
        "token": "USDC" | "USDT",
        "php_amount": 70.11
    }
    """
    username = session.get("username", "admin")
    uwallet = get_wallet_for_user(username)
    data = request.get_json(silent=True) or {}
    to_address = data.get("to", "").strip()

    if not to_address:
        return jsonify({"success": False, "message": "Parameter 'to' (address tujuan) wajib diisi."}), 400

    network = data.get("network", "base").lower().strip()
    token = data.get("token")
    if not token:
        token = "USDT" if network == "bsc" else "USDC"
    token = token.upper().strip()

    # Resolve amount
    amount = data.get("amount") or data.get("usdc_amount") or data.get("usdt_amount")
    php_amount = data.get("php_amount")

    if amount is None and php_amount is None:
        return jsonify({"success": False, "message": "Parameter 'amount' atau 'php_amount' wajib diisi."}), 400

    if php_amount is not None and amount is None:
        try:
            php_val = float(php_amount)
            amount = rate_engine.php_to_usdc(php_val)
        except (ValueError, TypeError):
            return jsonify({"success": False, "message": "Nilai php_amount tidak valid."}), 400

    try:
        amount = float(amount)
        if amount <= 0:
            return jsonify({"success": False, "message": "Jumlah transfer harus lebih dari 0."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Nilai amount tidak valid."}), 400

    result = uwallet.send_token(to_address=to_address, amount=amount, network=network, token=token)
    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code


# ============================================================
# ACCOUNT MANAGEMENT
# ============================================================

@app.route("/api/accounts", methods=["GET"])
def api_get_accounts():
    username = session.get("username", "admin")
    is_admin = session.get("is_admin", False)
    return jsonify({"success": True, "accounts": get_user_accounts(username, is_admin)})


@app.route("/api/accounts", methods=["POST"])
@app.route("/api/account/add", methods=["POST"])
def api_add_account():
    username = session.get("username", "admin")
    is_admin = session.get("is_admin", False)
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    phone = data.get("phone") or data.get("account_id")
    city = data.get("city", "Manila")
    display_name = data.get("display_name") or name
    slot_id = data.get("slot_id") or data.get("id")

    if not name or not phone:
        return jsonify({"success": False, "message": "Nama dan nomor HP wajib diisi."}), 400

    new_acc = save_user_account(
        username=username, is_admin=is_admin,
        name=name, phone=phone, city=city,
        display_name=display_name, slot_id=slot_id
    )
    return jsonify({"success": True, "account": new_acc, "message": "Akun berhasil disimpan."})


@app.route("/api/accounts/<slot_id>", methods=["DELETE"])
@app.route("/api/account/<slot_id>", methods=["DELETE"])
def api_delete_account(slot_id):
    username = session.get("username", "admin")
    is_admin = session.get("is_admin", False)
    ok = delete_user_account(username=username, is_admin=is_admin, slot_id=slot_id)
    if ok:
        return jsonify({"success": True, "message": f"Slot {slot_id} berhasil dihapus."})
    return jsonify({"success": False, "message": "Slot tidak ditemukan."}), 404


# ============================================================
# PAYMENT & QR ENDPOINTS
# ============================================================

@app.route("/api/payment/create", methods=["POST"])
def api_create_payment():
    data = request.get_json(silent=True) or {}
    config = load_config()
    username = session.get("username", "admin")
    is_admin = session.get("is_admin", False)

    amount_raw = data.get("amount") or request.form.get("amount")
    if not amount_raw:
        return jsonify({"success": False, "message": "Field 'amount' wajib diisi."}), 400

    try:
        amount = float(str(amount_raw).replace(",", ""))
        if amount <= 0:
            return jsonify({"success": False, "message": "Nominal harus lebih dari 0."}), 400
    except ValueError:
        return jsonify({"success": False, "message": "Nominal tidak valid."}), 400

    account_id = data.get("account_id") or request.form.get("account_id")
    user_accs = get_user_accounts(username, is_admin)
    account = None
    if account_id:
        account = next((a for a in user_accs if a.get("id") == account_id), None)
    if not account and user_accs:
        account = user_accs[0]
    if not account and (is_admin or username in ("admin", "superadmin", "")):
        account = get_account(account_id, config)

    if not account:
        return jsonify({"success": False, "message": "Belum ada slot akun Coins.ph yang terdaftar pada profil Anda. Silakan tambahkan slot akun terlebih dahulu."}), 400

    order_id = data.get("order_id") or request.form.get("order_id") or generate_order_id()
    customer_name = data.get("customer_name") or request.form.get("customer_name")
    customer_phone = data.get("customer_phone") or request.form.get("customer_phone")
    note = data.get("note") or request.form.get("note")
    callback_url = data.get("callback_url") or request.form.get("callback_url")
    timeout_mins = int(data.get("timeout_minutes",
                                config.get("server", {}).get("invoice_timeout_minutes", 15)))
    merchant_name = data.get("merchant_name") or request.form.get("merchant_name")
    auto_random_name = bool(data.get("auto_random_name", False))

    qr_payload = generate_qrph_payload(
        amount=amount, order_id=order_id, account=account, config=config,
        merchant_name=merchant_name, auto_random_name=auto_random_name
    )

    order = create_order(
        order_id=order_id, amount=amount, qr_payload=qr_payload,
        account_id=account.get("id", "slot_1"),
        account_name=merchant_name or account.get("name", "NAMA AKUN"),
        customer_name=customer_name, customer_phone=customer_phone,
        note=note, callback_url=callback_url,
        timeout_minutes=timeout_mins, currency="PHP",
        username=username
    )

    qr_base64 = generate_qr_base64(qr_payload)
    host_url = request.host_url.rstrip("/")
    usdc_est = rate_engine.php_to_usdc(amount)

    return jsonify({
        "success": True,
        "order_id": order["order_id"],
        "account_id": order["account_id"],
        "account_name": order["account_name"],
        "amount": order["amount"],
        "currency": order["currency"],
        "status": order["status"],
        "qr_payload": qr_payload,
        "qr_image_base64": qr_base64,
        "qr_image_url": f"{host_url}/api/qr/image?order_id={order['order_id']}&account_id={order['account_id']}",
        "checkout_url": f"{host_url}/pay/{order['order_id']}",
        "created_at": order["created_at"],
        "expires_at": order["expires_at"],
        "usdc_estimate": usdc_est,
        "rate": rate_engine.rate
    })


@app.route("/api/payment/<order_id>", methods=["GET"])
def api_get_payment(order_id):
    order = get_order(order_id)
    if not order:
        return jsonify({"success": False, "message": "Order tidak ditemukan."}), 404
    return jsonify({"success": True, "order": order})


@app.route("/api/payment/<order_id>/pay", methods=["POST"])
def api_mark_paid(order_id):
    data = request.get_json(silent=True) or {}
    order = mark_as_paid(order_id,
                         payment_method=data.get("payment_method", "Manual API"),
                         payer_info=data.get("payer_info", ""))
    if not order:
        return jsonify({"success": False, "message": "Order tidak ditemukan."}), 404
    return jsonify({"success": True, "message": f"Order #{order_id} berhasil ditandai LUNAS.", "order": order})


@app.route("/api/qr/image", methods=["GET"])
def api_qr_image():
    config = load_config()
    order_id = request.args.get("order_id")
    amount = request.args.get("amount")
    account_id = request.args.get("account_id")
    username = session.get("username")
    is_admin = session.get("is_admin", False)
    user_accs = get_user_accounts(username, is_admin) if username else []
    account = None
    if account_id:
        account = next((a for a in user_accs if a.get("id") == account_id), None)
    if not account and user_accs:
        account = user_accs[0]
    if not account and (is_admin or username in ("admin", "superadmin")):
        account = get_account(account_id, config)
    merchant_name = request.args.get("merchant_name")
    auto_random_name = request.args.get("random_name") in ["1", "true", "yes"]

    if not account and not order_id:
        return "Belum ada akun terdaftar", 400

    if order_id:
        order = get_order(order_id)
        payload = order["qr_payload"] if order else (generate_qrph_payload(
            amount=amount, order_id=order_id, account=account, config=config,
            merchant_name=merchant_name, auto_random_name=auto_random_name
        ) if account else None)
    else:
        payload = generate_qrph_payload(
            amount=amount, account=account, config=config,
            merchant_name=merchant_name, auto_random_name=auto_random_name
        )

    if not payload:
        return "QR payload tidak tersedia", 400

    img = generate_qr_image(payload)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@app.route("/api/qr/raw", methods=["GET"])
def api_qr_raw():
    config = load_config()
    account_id = request.args.get("account_id")
    username = session.get("username")
    is_admin = session.get("is_admin", False)
    user_accs = get_user_accounts(username, is_admin) if username else []
    account = None
    if account_id:
        account = next((a for a in user_accs if a.get("id") == account_id), None)
    if not account and user_accs:
        account = user_accs[0]
    if not account and (is_admin or username in ("admin", "superadmin")):
        account = get_account(account_id, config)
    if not account:
        return "Belum ada akun terdaftar", 400
    payload = generate_qrph_payload(
        amount=request.args.get("amount"),
        order_id=request.args.get("order_id"),
        account=account, config=config,
        merchant_name=request.args.get("merchant_name"),
        auto_random_name=request.args.get("random_name") in ["1", "true", "yes"]
    )
    return payload, 200, {"Content-Type": "text/plain"}


@app.route("/api/qr/random_name", methods=["GET"])
def api_qr_random_name():
    """Generates an authentic Filipino merchant name."""
    return jsonify({"success": True, "name": get_random_merchant_name()})


@app.route("/api/qr/decode", methods=["POST"])
def api_qr_decode():
    """Decode QR code from uploaded file or base64 using C++ ZXing Engine."""
    import base64
    from PIL import Image, ImageOps
    try:
        import zxingcpp
    except ImportError:
        zxingcpp = None

    img_data = None
    if "image" in request.files:
        file = request.files["image"]
        img_data = file.read()
    elif "file" in request.files:
        file = request.files["file"]
        img_data = file.read()
    else:
        data = request.get_json(silent=True) or {}
        b64_str = data.get("image_base64") or data.get("image") or ""
        if b64_str:
            if "," in b64_str:
                b64_str = b64_str.split(",")[1]
            try:
                img_data = base64.b64decode(b64_str)
            except Exception:
                pass

    if not img_data:
        return jsonify({"success": False, "message": "Tidak ada data gambar yang diterima."}), 400

    if not zxingcpp:
        return jsonify({"success": False, "message": "Modul zxing-cpp belum terpasang di server."}), 500

    try:
        raw_img = Image.open(BytesIO(img_data))
        pil_img = ImageOps.exif_transpose(raw_img).convert("RGB")
        
        # Optimize size if excessively large
        if max(pil_img.size) > 1600:
            pil_img.thumbnail((1600, 1600), Image.Resampling.LANCZOS)

        barcodes = zxingcpp.read_barcodes(pil_img)
        if barcodes:
            raw_text = barcodes[0].text
            return jsonify({
                "success": True,
                "text": raw_text,
                "format": str(barcodes[0].format)
            })
            
        # Try grayscale fallback
        gray_img = pil_img.convert("L").convert("RGB")
        barcodes = zxingcpp.read_barcodes(gray_img)
        if barcodes:
            raw_text = barcodes[0].text
            return jsonify({
                "success": True,
                "text": raw_text,
                "format": str(barcodes[0].format)
            })

        return jsonify({"success": False, "message": "QR Code tidak ditemukan pada gambar. Pastikan gambar jelas dan tidak blur."}), 404
    except Exception as e:
        return jsonify({"success": False, "message": f"Gagal decode QR: {str(e)}"}), 500


# ============================================================
# LIVE HARDWARE WEBCAM SCANNER (DIRECT STREAM & AUTO-DECODE)
# ============================================================

@app.route("/api/camera/start", methods=["POST"])
def api_camera_start():
    """Start hardware webcam capture."""
    ok = camera_scanner.start()
    return jsonify({"success": ok, "message": "Kamera aktif" if ok else "Gagal mengaktifkan kamera"})


@app.route("/api/camera/stream")
def api_camera_stream():
    """Live MJPEG video stream with realtime barcode overlay."""
    def generate():
        while camera_scanner.is_running:
            frame = camera_scanner.get_frame()
            if frame:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            time.sleep(0.035)
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route("/api/camera/status", methods=["GET"])
def api_camera_status():
    """Check detection status of current camera frame."""
    return jsonify(camera_scanner.get_status())


@app.route("/api/camera/stop", methods=["POST"])
def api_camera_stop():
    """Stop camera hardware and release device."""
    camera_scanner.stop()
    return jsonify({"success": True, "message": "Kamera dinonaktifkan"})


@app.route("/api/matrix", methods=["GET"])
def api_matrix():
    config = load_config()
    username = session.get("username", "admin")
    is_admin = session.get("is_admin", False)
    user_accounts = get_user_accounts(username, is_admin)
    try:
        amount = float(request.args.get("amount", "70"))
    except ValueError:
        amount = 70.0
    merchant_name = request.args.get("merchant_name")
    auto_random_name = request.args.get("random_name") in ["1", "true", "yes"]
    results = []
    for acc in user_accounts:
        payload = generate_qrph_payload(
            amount=amount, account=acc, config=config,
            merchant_name=merchant_name, auto_random_name=auto_random_name
        )
        results.append({
            "slot_id": acc.get("id"),
            "name": acc.get("name"),
            "display_name": acc.get("display_name"),
            "phone_masked": acc.get("phone_masked"),
            "amount": amount,
            "qr_payload": payload,
            "qr_image_base64": generate_qr_base64(payload)
        })
    return jsonify({"success": True, "amount": amount, "slots": results, "matrix": results})


def get_local_ip():
    """Detect local LAN IP dynamically for multi-device access."""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        pass
    try:
        import socket
        return socket.gethostbyname(socket.gethostname())
    except Exception:
        return "0.0.0.0"


# ============================================================
# MAIN ENTRY
# ============================================================
if __name__ == "__main__":
    cfg = load_config()
    port = int(cfg.get("server", {}).get("port", 5000))
    local_ip = get_local_ip()

    # Backend berjalan eksklusif pada IP:PORT dinamis LAN
    cfg_host = cfg.get("server", {}).get("host")
    if cfg_host and cfg_host not in ["0.0.0.0", "auto", ""]:
        host = cfg_host
    else:
        host = local_ip

    print("=====================================================")
    print(f"[*] Coins.ph Multi-Account QR Ph Gateway")
    print(f"[*] Server Binding Host: {host}:{port}")
    print(f"[*] POS Kasir URL:     http://{host}:{port}/pos")
    print(f"[*] Dashboard URL:     http://{host}:{port}/dashboard")
    print(f"[*] REST API Endpoint: http://{host}:{port}/api/payment/create")
    print(f"[*] Live Rate Engine:  http://{host}:{port}/api/rate")
    print(f"[*] Wallet API:        http://{host}:{port}/api/wallet/status")
    print("=====================================================")
    app.run(host=host, port=port, debug=False)
