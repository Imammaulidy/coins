import os
import time
import uuid
import threading
from io import BytesIO
from datetime import datetime
from flask import Flask, request, jsonify, render_template, redirect, send_file, url_for
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
from wallet_manager import rate_engine, wallet_manager

TEMPLATES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app = Flask(__name__, template_folder=TEMPLATES_DIR, static_folder=STATIC_DIR)
app.config["TEMPLATES_AUTO_RELOAD"] = True

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
# PAGE ROUTES
# ============================================================

@app.route("/")
def index():
    return redirect("/pos")


@app.route("/pos")
def pos_page():
    config = load_config()
    return render_template("pos.html", config=config)


@app.route("/dashboard")
def dashboard_page():
    config = load_config()
    orders = get_recent_orders(100)
    total_revenue = sum(o["amount"] for o in orders if o["status"] == "PAID")
    total_paid = sum(1 for o in orders if o["status"] == "PAID")
    total_pending = sum(1 for o in orders if o["status"] == "PENDING")
    return render_template(
        "dashboard.html",
        orders=orders,
        total_revenue=total_revenue,
        total_paid=total_paid,
        total_pending=total_pending,
        config=config
    )


@app.route("/api/orders", methods=["GET"])
def api_get_orders():
    limit = int(request.args.get("limit", 100))
    account_id = request.args.get("account_id")
    orders = get_recent_orders(limit=limit, account_id=account_id)
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
    """Set manual base_rate and buffer dynamically."""
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
    """Connect wallet using Private Key or Seed Phrase."""
    data = request.get_json(silent=True) or {}
    method = data.get("method", "private_key")  # "private_key" | "phrase"
    credential = (data.get("credential") or data.get("secret") or "").strip()

    if not credential:
        return jsonify({"success": False, "message": "Credential (PK / Phrase) tidak boleh kosong."}), 400

    if method == "phrase":
        result = wallet_manager.connect_phrase(credential)
    else:
        result = wallet_manager.connect_private_key(credential)

    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code


@app.route("/api/wallet/disconnect", methods=["POST"])
def api_wallet_disconnect():
    wallet_manager.disconnect()
    return jsonify({"success": True, "message": "Wallet berhasil diputus."})


@app.route("/api/wallet/status", methods=["GET"])
def api_wallet_status():
    """Get current wallet connection status and multi-network balances."""
    if wallet_manager.is_connected:
        bal = wallet_manager.get_balance()
        return jsonify({
            "success": True,
            "connected": True,
            "address": wallet_manager.address,
            "address_short": f"{wallet_manager.address[:6]}...{wallet_manager.address[-4:]}" if wallet_manager.address else None,
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
    """Get balances across Base (USDC, ETH) and BSC (USDT, USDC, BNB)."""
    network = request.args.get("network")
    if not wallet_manager.is_connected:
        return jsonify({"success": False, "message": "Wallet belum terkoneksi."}), 200
    result = wallet_manager.get_balance(network=network)
    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code


@app.route("/api/wallet/send", methods=["POST"])
def api_wallet_send():
    """
    Send Token on Base (USDC) or BSC (USDT/USDC).
    Body: {
        "to": "0x...",
        "amount": 1.17,
        "network": "base" | "bsc",
        "token": "USDC" | "USDT",
        "php_amount": 70.11
    }
    """
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

    result = wallet_manager.send_token(to_address=to_address, amount=amount, network=network, token=token)
    status_code = 200 if result.get("success") else 400
    return jsonify(result), status_code


# ============================================================
# ACCOUNT MANAGEMENT
# ============================================================

@app.route("/api/accounts", methods=["GET"])
def api_get_accounts():
    config = load_config()
    return jsonify({"success": True, "accounts": config.get("accounts", [])})


@app.route("/api/accounts", methods=["POST"])
@app.route("/api/account/add", methods=["POST"])
def api_add_account():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    phone = data.get("phone") or data.get("account_id")
    city = data.get("city", "Manila")
    display_name = data.get("display_name") or name
    slot_id = data.get("slot_id") or data.get("id")

    if not name or not phone:
        return jsonify({"success": False, "message": "Nama dan nomor HP wajib diisi."}), 400

    new_acc = add_or_update_account(
        name=name, phone=phone, city=city,
        display_name=display_name, slot_id=slot_id
    )
    return jsonify({"success": True, "account": new_acc, "message": "Akun berhasil disimpan."})


@app.route("/api/accounts/<slot_id>", methods=["DELETE"])
@app.route("/api/account/<slot_id>", methods=["DELETE"])
def api_delete_account(slot_id):
    ok = delete_account(slot_id)
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
    account = get_account(account_id, config)
    if not account:
        return jsonify({"success": False, "message": "Belum ada akun Coins.ph yang terdaftar."}), 400

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
        timeout_minutes=timeout_mins, currency="PHP"
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
    account = get_account(account_id, config)
    merchant_name = request.args.get("merchant_name")
    auto_random_name = request.args.get("random_name") in ["1", "true", "yes"]

    if not account and not order_id:
        return "Belum ada akun terdaftar", 400

    if order_id:
        order = get_order(order_id)
        payload = order["qr_payload"] if order else generate_qrph_payload(
            amount=amount, order_id=order_id, account=account, config=config,
            merchant_name=merchant_name, auto_random_name=auto_random_name
        )
    else:
        payload = generate_qrph_payload(
            amount=amount, account=account, config=config,
            merchant_name=merchant_name, auto_random_name=auto_random_name
        )

    img = generate_qr_image(payload)
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return send_file(buf, mimetype="image/png")


@app.route("/api/qr/raw", methods=["GET"])
def api_qr_raw():
    config = load_config()
    account = get_account(request.args.get("account_id"), config)
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


@app.route("/api/matrix", methods=["GET"])
def api_matrix():
    config = load_config()
    try:
        amount = float(request.args.get("amount", "70"))
    except ValueError:
        amount = 70.0
    merchant_name = request.args.get("merchant_name")
    auto_random_name = request.args.get("random_name") in ["1", "true", "yes"]
    results = []
    for acc in config.get("accounts", []):
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
    return jsonify({"success": True, "amount": amount, "slots": results})


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
