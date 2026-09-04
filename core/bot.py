"""
Telegram Bot Coins.ph Payment Gateway & POS Automation
======================================================
Bot Telegram komprehensif untuk otomasi Coins.ph QR Ph (InstaPay), kalkulator kurs Bitget P2P,
manajemen multi-slot merchant, monitoring pembayaran realtime, Web3 multi-chain wallet (Base/BSC),
serta proteksi RBAC Multi-User berbatas waktu.

Arsitektur:
- python-telegram-bot v20+ (Async/Await)
- Persistent Menu Navigation (ReplyKeyboardMarkup sesuai Role)
- Dynamic EMVCo / QR Ph generator ber-badge InstaPay langsung di chat Telegram
- Auto-delete barcode QR saat lunas / expired
- Realtime background order status poller
- Kalkulator kurs konversi PHP <-> USDC otomatis
- Web3 Wallet multi-chain manager (Base & BSC)
- ADB reset multi-app modular engine
"""

import os
import sys
import json
import uuid
import secrets
import logging
import asyncio
import html
import re
from io import BytesIO
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple, List

# Pastikan direktori core masuk ke Python sys.path
CORE_DIR = os.path.dirname(os.path.abspath(__file__))
if CORE_DIR not in sys.path:
    sys.path.insert(0, CORE_DIR)

# Pastikan output console UTF-8 di Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove
)
from telegram.constants import ParseMode
from telegram.request import HTTPXRequest
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

from qr_engine import (
    load_config,
    save_config,
    get_account,
    generate_qrph_payload,
    generate_qr_image,
    get_random_merchant_name,
    CONFIG_PATH
)
from database import (
    init_db,
    create_order,
    get_order,
    get_recent_orders,
    mark_as_paid
)
from wallet_manager import rate_engine, wallet_manager
from adb_helper import ADBManager

# Inisialisasi Database SQLite
init_db()

# Setup Logging
logging.basicConfig(
    format="%(asctime)s - [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("CoinsTelegramBot")

# ============================================================
# GLOBAL STATE & CACHE
# ============================================================
config: Dict[str, Any] = load_config()

GLOBAL_BOT: Optional[Any] = None

# Active Invoices tracked: order_id -> {chat_id, user_id, message_id, amount_php, slot_id, created_at}
ACTIVE_INVOICES: Dict[str, Dict[str, Any]] = {}

# User Interactive States: user_id -> state string (misal: "AWAITING_CUSTOM_AMOUNT", "AWAITING_TRANSFER_ADDR", etc.)
USER_STATES: Dict[int, Dict[str, Any]] = {}

# Set of already notified order IDs to prevent duplicate notifications
NOTIFIED_PAID_ORDERS: set = set()


# ============================================================
# RBAC & SECURITY HELPERS
# ============================================================

def get_user_role_and_expiry(user_id: int) -> Tuple[str, Optional[datetime]]:
    """
    Mengembalikan (ROLE, EXPIRY_DATETIME)
    Role: 'ADMIN' | 'USER' | 'EXPIRED' | 'GUEST'
    """
    global config
    admin_ids = config.get("telegram", {}).get("admin_ids", [])
    if user_id in admin_ids:
        return "ADMIN", None

    security = config.setdefault("security", {})
    sessions = security.setdefault("user_sessions", {})
    uid_str = str(user_id)

    if uid_str in sessions:
        sess = sessions[uid_str]
        role = sess.get("role", "GUEST")
        if role == "ADMIN":
            return "ADMIN", None

        exp_str = sess.get("expires_at")
        if exp_str:
            try:
                exp_dt = datetime.fromisoformat(exp_str)
                if datetime.now() < exp_dt:
                    return "USER", exp_dt
                else:
                    return "EXPIRED", exp_dt
            except Exception:
                return "GUEST", None

    return "GUEST", None


def redeem_code(user_id: int, username: str, code_input: str) -> Tuple[bool, str, str]:
    """
    Menebus kode akses atau Master Key Admin.
    Returns: (SUCCESS, ROLE, MESSAGE)
    """
    global config
    code_input = code_input.strip()
    master_key = config.get("security", {}).get("admin_master_code", "ADMIN123")

    # 1. Cek Master Key Admin
    if code_input == master_key:
        admin_ids = config.setdefault("telegram", {}).setdefault("admin_ids", [])
        if user_id not in admin_ids:
            admin_ids.append(user_id)
        security = config.setdefault("security", {})
        security.setdefault("user_sessions", {})[str(user_id)] = {
            "role": "ADMIN",
            "username": username,
            "registered_at": datetime.now().isoformat(),
            "expires_at": None
        }
        save_config(config)
        return True, "ADMIN", "🎉 <b>AKSES SUPER ADMIN DIAKTIFKAN!</b>\nAnda sekarang memiliki hak akses penuh ke seluruh fitur sistem Coins.ph."

    # 2. Cek Kode Akses User Biasa
    security = config.setdefault("security", {})
    codes = security.setdefault("access_codes", {})

    if code_input in codes:
        c_info = codes[code_input]
        if c_info.get("used_by") and c_info.get("used_by") != user_id:
            return False, "USED", "❌ <b>Kode akses ini sudah pernah digunakan pengguna lain.</b>"

        duration = c_info.get("duration_days", 1)
        exp_dt = datetime.now() + timedelta(days=duration)

        c_info["used_by"] = user_id
        c_info["used_at"] = datetime.now().isoformat()

        security.setdefault("user_sessions", {})[str(user_id)] = {
            "role": "USER",
            "username": username,
            "code": code_input,
            "registered_at": datetime.now().isoformat(),
            "expires_at": exp_dt.isoformat()
        }
        save_config(config)
        exp_fmt = exp_dt.strftime("%d/%m/%Y %H:%M WIB")
        return True, "USER", f"🎉 <b>KODE AKSES BERHASIL DIAKTIFKAN!</b>\n\n⏰ <b>Masa Aktif:</b> {duration} Hari\n📅 <b>Berlaku Hingga:</b> <code>{exp_fmt}</code>"

    return False, "INVALID", "❌ <b>Kode akses tidak valid atau tidak terdaftar!</b>\nSilakan masukkan kode yang valid atau hubungi Admin."


def generate_user_code(duration_days: int, creator_id: int) -> str:
    """Membuat token kode akses berbatas waktu baru"""
    global config
    token = secrets.token_hex(3).upper()
    code = f"COINS-{duration_days}D-{token}"
    security = config.setdefault("security", {})
    codes = security.setdefault("access_codes", {})
    codes[code] = {
        "duration_days": duration_days,
        "created_by": creator_id,
        "created_at": datetime.now().isoformat(),
        "used_by": None,
        "used_at": None
    }
    save_config(config)
    return code


# ============================================================
# KEYBOARD MENU GENERATORS
# ============================================================

def get_role_reply_keyboard(role: str) -> ReplyKeyboardMarkup:
    """
    Keyboard Menu Navigasi Bawah Layar Berdasarkan Role:
    - ADMIN : Fitur lengkap (QR Ph, Slot, Kurs, Web3 Wallet, ADB, Kode User, Setting Base)
    - USER  : Fitur transaksi & cek kurs (QR Ph, Slot, Kurs, Riwayat, Masa Aktif)
    - GUEST : Layar terkunci
    """
    if role == "ADMIN":
        keyboard = [
            [KeyboardButton("⚡ Buat QR Ph"), KeyboardButton("📱 Status Akun Slot")],
            [KeyboardButton("📊 Kurs & Kalkulator"), KeyboardButton("💳 Saldo Web3 Wallet")],
            [KeyboardButton("💸 Kirim Token Web3"), KeyboardButton("⚡ Reset Multi App (ADB)")],
            [KeyboardButton("🔑 Buat Kode User"), KeyboardButton("⚙️ Ubah Base Nominal")],
            [KeyboardButton("📜 Riwayat Transaksi"), KeyboardButton("⚙️ Status Sistem")],
            [KeyboardButton("📖 Panduan & Bantuan")]
        ]
    elif role == "USER":
        keyboard = [
            [KeyboardButton("⚡ Buat QR Ph"), KeyboardButton("📱 Status Akun Slot")],
            [KeyboardButton("📊 Kurs & Kalkulator"), KeyboardButton("📜 Riwayat Transaksi")],
            [KeyboardButton("⏳ Masa Aktif Akun"), KeyboardButton("📖 Panduan & Bantuan")]
        ]
    else:
        keyboard = [
            [KeyboardButton("🔑 Masukkan Kode Akses"), KeyboardButton("📖 Panduan")]
        ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, is_persistent=True)


def get_slot_selection_keyboard() -> InlineKeyboardMarkup:
    """Keyboard inline untuk memilih Slot Akun Coins.ph"""
    global config
    accounts = config.get("accounts", [])
    buttons = []

    if accounts:
        row = []
        for i, acc in enumerate(accounts):
            slot_id = acc.get("id", f"slot_{i+1}")
            slot_label = f"📱 Slot {i+1} ({acc.get('name', 'Account')[:10]})"
            row.append(InlineKeyboardButton(slot_label, callback_data=f"sel_slot_{slot_id}"))
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
    else:
        buttons.append([InlineKeyboardButton("📱 Gunakan Default Slot (Slot 1)", callback_data="sel_slot_slot_1")])

    buttons.append([InlineKeyboardButton("❌ Batal", callback_data="qr_cancel")])
    return InlineKeyboardMarkup(buttons)


def get_nominal_preset_keyboard(slot_id: str) -> InlineKeyboardMarkup:
    """Keyboard inline untuk memilih nominal preset atau input manual"""
    global config
    base = config.get("bot_settings", {}).get("default_base_php", 100)

    # Preset tombol cepat
    keyboard = [
        [
            InlineKeyboardButton(f"₱ {base:,} (Base)", callback_data=f"gen_{slot_id}_{base}"),
            InlineKeyboardButton(f"₱ {base*2:,}", callback_data=f"gen_{slot_id}_{base*2}")
        ],
        [
            InlineKeyboardButton("₱ 250", callback_data=f"gen_{slot_id}_250"),
            InlineKeyboardButton("₱ 500", callback_data=f"gen_{slot_id}_500")
        ],
        [
            InlineKeyboardButton("₱ 1,000", callback_data=f"gen_{slot_id}_1000"),
            InlineKeyboardButton("₱ 2,500", callback_data=f"gen_{slot_id}_2500")
        ],
        [
            InlineKeyboardButton("✏️ Ketik Nominal Bebas", callback_data=f"gen_custom_{slot_id}"),
            InlineKeyboardButton("❌ Batal", callback_data="qr_cancel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


# ============================================================
# COMMAND HANDLERS
# ============================================================

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu Utama Bot dengan Pengecekan Sesi & Role"""
    user = update.effective_user
    if not user:
        return

    role, expiry = get_user_role_and_expiry(user.id)

    # Pengguna belum terdaftar / Guest / Masa aktif habis
    if role in ["GUEST", "EXPIRED"]:
        status_txt = "🔴 <b>Masa Aktif Selesai!</b>" if role == "EXPIRED" else "🔒 <b>Akses Bot Terkunci!</b>"
        text = (
            f"🤖 <b>COINS.PH PAYMENT GATEWAY & AUTOMATION BOT</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"Halo {html.escape(user.first_name)}! 👋\n"
            f"{status_txt}\n\n"
            f"Silakan kirimkan <b>Kode Akses</b> atau <b>Master Key Admin</b> Anda untuk membuka seluruh fitur bot:\n"
            f"<i>Ketik langsung kodenya pada chat ini.</i>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🆔 Telegram ID Anda: <code>{user.id}</code>"
        )
        USER_STATES[user.id] = {"state": "AWAITING_LOGIN_CODE"}
        reply_markup = get_role_reply_keyboard("GUEST")
        if update.callback_query:
            await update.callback_query.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        else:
            await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        return

    # Sesi Aktif (Admin / User)
    rate_info = rate_engine.get_info()
    rate_val = rate_info.get("effective_rate", 60.75)
    rate_src = rate_info.get("source", "Bitget P2P")

    acc_count = len(config.get("accounts", []))
    base_nom = config.get("bot_settings", {}).get("default_base_php", 100)

    expiry_info = (
        f"📅 <b>Berlaku Hingga:</b> <code>{expiry.strftime('%d/%m/%Y %H:%M WIB')}</code>\n"
        if expiry else "👑 <b>Akses:</b> <code>Super Admin (Permanen)</code>\n"
    )

    text = (
        f"🤖 <b>COINS.PH PAYMENT GATEWAY HUB</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 <b>Pengguna:</b> {html.escape(user.first_name)} [{role}]\n"
        f"{expiry_info}"
        f"📱 <b>Total Slot Akun:</b> <code>{acc_count}</code> Akun Aktif\n"
        f"📊 <b>Kurs Live USDC/PHP:</b> <b>₱ {rate_val:.2f}</b>\n"
        f"📡 <b>Sumber Kurs:</b> <i>{rate_src}</i>\n"
        f"🔢 <b>Nominal Base:</b> <code>₱ {base_nom:,}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"Pilih menu di keyboard bawah untuk navigasi cepat:"
    )

    reply_markup = get_role_reply_keyboard(role)
    if update.callback_query:
        await update.callback_query.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)


async def cmd_qr_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu awal pembuatan QR Ph: Pilih Slot Akun"""
    user = update.effective_user
    role, _ = get_user_role_and_expiry(user.id)
    if role not in ["ADMIN", "USER"]:
        await cmd_start(update, context)
        return

    text = (
        f"⚡ <b>PEMBUATAN QR PH INSTAPAY</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"Silakan pilih <b>Slot Akun Coins.ph</b> tujuan pembayaran di bawah ini:"
    )
    reply_markup = get_slot_selection_keyboard()

    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)


async def cmd_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cek Kurs Live Bitget PHP/USDC & Panduan Kalkulator"""
    user = update.effective_user
    role, _ = get_user_role_and_expiry(user.id)
    if role not in ["ADMIN", "USER"]:
        await cmd_start(update, context)
        return

    rate_info = rate_engine.get_info()
    client_rate = rate_info.get("effective_rate", 60.75)
    base_rate = rate_info.get("base_rate", 60.55)
    buffer = rate_info.get("buffer", 0.20)
    source = rate_info.get("source", "Bitget P2P")
    updated_ago = rate_info.get("last_updated_ago_sec", 0)

    text = (
        f"📊 <b>KURS REALTIME BITGET WALLET</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💵 <b>1 USDC =</b> <b>₱ {client_rate:.2f} PHP</b>\n"
        f"🔹 <i>Base P2P Rate:</i> ₱ {base_rate:.2f}\n"
        f"🔹 <i>Profit Buffer:</i> +₱ {buffer:.2f}\n"
        f"📡 <i>Sumber:</i> {source}\n"
        f"⏰ <i>Pembaruan Terakhir:</i> {updated}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 <b>Kalkulator Instan:</b>\n"
        f"Ketik nominal langsung di chat ini untuk konversi cepat!\n"
        f"• Contoh ke USDC: <code>500 php</code> atau <code>1500php</code>\n"
        f"• Contoh ke PHP: <code>25 usdc</code> atau <code>100usdt</code>"
    )

    if update.callback_query:
        await update.callback_query.message.reply_text(text, parse_mode=ParseMode.HTML)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_slots_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menampilkan status semua slot akun Coins.ph"""
    user = update.effective_user
    role, _ = get_user_role_and_expiry(user.id)
    if role not in ["ADMIN", "USER"]:
        await cmd_start(update, context)
        return

    global config
    accounts = config.get("accounts", [])
    if not accounts:
        text = (
            "📱 <b>STATUS SLOT AKUN COINS.PH</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "⚠️ <i>Belum ada akun terdaftar di core/config.json.</i>\n"
            "Tambahkan akun via POS Web atau konfigurasi."
        )
        await update.message.reply_text(text, parse_mode=ParseMode.HTML)
        return

    lines = ["📱 <b>STATUS SLOT AKUN COINS.PH</b>\n━━━━━━━━━━━━━━━━━━━━━"]
    for i, acc in enumerate(accounts):
        active_str = "🟢 Aktif" if acc.get("active", True) else "🔴 Non-Aktif"
        lines.append(
            f"🔹 <b>Slot {i+1}</b>: <b>{acc.get('name', 'Coins User')}</b>\n"
            f"   📞 Nomor HP: <code>{acc.get('account_id') or acc.get('phone')}</code>\n"
            f"   🏛 Bank BIC: <code>{acc.get('bank_bic', 'DCPHPHM1XXX')}</code>\n"
            f"   📌 Sub-ID: <code>{acc.get('sub_id', '99964403')}</code>\n"
            f"   🔌 Status: {active_str}\n"
        )
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def cmd_wallet_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cek Saldo Multi-Chain Web3 Wallet (Khusus Admin)"""
    user = update.effective_user
    role, _ = get_user_role_and_expiry(user.id)
    if role != "ADMIN":
        await update.message.reply_text("⛔ <b>Akses Terbatas!</b>\nMenu Web3 Wallet hanya tersedia untuk Super Admin.", parse_mode=ParseMode.HTML)
        return

    msg = await update.message.reply_text("⏳ <i>Menghubungi Blockchain RPC (Base & BSC)...</i>", parse_mode=ParseMode.HTML)

    loop = asyncio.get_running_loop()
    balances = await loop.run_in_executor(None, wallet_manager.get_all_balances)
    pub_addr = wallet_manager.get_address() or "Belum Diatur (Cek .env / wallet_manager)"

    base_b = balances.get("base", {})
    bsc_b = balances.get("bsc", {})

    text = (
        f"💳 <b>INFORMASI WEB3 WALLET</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📬 <b>Alamat Wallet:</b>\n"
        f"<code>{pub_addr}</code>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔵 <b>Base Network:</b>\n"
        f"  • ETH (Gas): <b>{base_b.get('ETH', 0.0):.5f} ETH</b>\n"
        f"  • USDC: <b>${base_b.get('USDC', 0.0):.2f} USDC</b>\n\n"
        f"🟡 <b>BNB Smart Chain (BSC):</b>\n"
        f"  • BNB (Gas): <b>{bsc_b.get('BNB', 0.0):.5f} BNB</b>\n"
        f"  • USDT: <b>${bsc_b.get('USDT', 0.0):.2f} USDT</b>\n"
        f"  • USDC: <b>${bsc_b.get('USDC', 0.0):.2f} USDC</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"<i>Gunakan tombol '💸 Kirim Token Web3' untuk transfer dana.</i>"
    )

    keyboard = [
        [InlineKeyboardButton("🔄 Refresh Saldo", callback_data="wallet_refresh")],
        [InlineKeyboardButton("💸 Kirim Token", callback_data="wallet_send_prompt")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await msg.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)


async def cmd_transfer_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Pilihan Jaringan & Token untuk Transfer Web3 (Khusus Admin)"""
    user = update.effective_user
    role, _ = get_user_role_and_expiry(user.id)
    if role != "ADMIN":
        await update.message.reply_text("⛔ <b>Akses Terbatas!</b>\nHanya Admin yang dapat mengirim token.", parse_mode=ParseMode.HTML)
        return

    text = (
        f"💸 <b>TRANSFER TOKEN WEB3</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"Pilih Jaringan & Token yang ingin Anda kirimkan:"
    )
    keyboard = [
        [
            InlineKeyboardButton("🔵 Base USDC", callback_data="tx_start_base_USDC"),
            InlineKeyboardButton("🟡 BSC USDT", callback_data="tx_start_bsc_USDT")
        ],
        [
            InlineKeyboardButton("🟡 BSC USDC", callback_data="tx_start_bsc_USDC"),
            InlineKeyboardButton("❌ Batal", callback_data="tx_cancel")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)


async def cmd_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lihat Riwayat Transaksi Terbaru dari payments.db"""
    user = update.effective_user
    role, _ = get_user_role_and_expiry(user.id)
    if role not in ["ADMIN", "USER"]:
        await cmd_start(update, context)
        return

    msg = await update.message.reply_text("⏳ <i>Mengambil riwayat transaksi...</i>", parse_mode=ParseMode.HTML)
    orders = get_recent_orders(limit=7)

    if not orders:
        await msg.edit_text("ℹ️ <i>Belum ada transaksi di sistem database.</i>", parse_mode=ParseMode.HTML)
        return

    lines = ["📜 <b>7 TRANSAKSI TERAKHIR (PAYMENTS DB)</b>\n━━━━━━━━━━━━━━━━━━━━━"]
    for o in orders:
        status_icon = "🟢" if o.get("status") == "PAID" else ("🟡" if o.get("status") == "PENDING" else "🔴")
        lines.append(
            f"{status_icon} <b>ID:</b> <code>{o.get('order_id')}</code>\n"
            f"   💰 ₱ {o.get('amount'):,.2f} | 📱 {o.get('account_id', 'slot')}\n"
            f"   🏪 {o.get('customer_name') or o.get('account_name') or 'InstaPay'}\n"
            f"   📅 {o.get('created_at')} | <b>{o.get('status')}</b>\n"
        )
    lines.append("━━━━━━━━━━━━━━━━━━━━━")
    await msg.edit_text("\n".join(lines), parse_mode=ParseMode.HTML)


async def cmd_reset_adb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset Multi App & Jaringan via ADB (Khusus Admin)"""
    user = update.effective_user
    role, _ = get_user_role_and_expiry(user.id)
    if role != "ADMIN":
        await update.message.reply_text("⛔ <b>Akses Terbatas!</b>\nFitur ADB hanya tersedia untuk Super Admin.", parse_mode=ParseMode.HTML)
        return

    status_msg = await update.message.reply_text(
        "⚡ <b>MENJALANKAN RESET MULTI APP...</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "⏳ <i>Memproses eksekusi atomic chained shell...</i>",
        parse_mode=ParseMode.HTML
    )

    res = await ADBManager.reset_multi_app()

    if res.get("success"):
        dev_id = html.escape(str(res.get("device_id", "Device")))
        mode = res.get("mode", "PC")
        mode_labels = {
            "ROOT": "📱 Termux (Root / su)",
            "SHIZUKU": "📱 Termux (Shizuku / rish)",
            "WIRELESS_ADB": "📱 Termux (Wireless ADB)",
            "PC": "💻 PC (USB Debugging)"
        }
        mode_icon = mode_labels.get(mode, f"⚙️ {mode}")

        text = (
            f"✅ <b>RESET MULTI APP BERHASIL!</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📱 <b>Backend:</b> <code>{mode_icon}</code>\n"
            f"🎯 <b>Target:</b> <code>{dev_id}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🛑 [1/5] Force stop <code>com.waxmoon.ma.gp</code>\n"
            f"🧹 [2/5] Bersihkan Cache internal & external\n"
            f"✈️ [3/5] Mode Pesawat ON (Reset IP)\n"
            f"📶 [4/5] Mode Pesawat OFF (Koneksi Baru)\n"
            f"🚀 [5/5] Membuka kembali Multi App\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"✨ <i>Cache bersih, IP baru aktif & Multi App siap digunakan!</i>"
        )
    else:
        err = html.escape(str(res.get("error", "Gagal menjalankan ADB.")))
        text = f"❌ <b>Gagal Menjalankan ADB!</b>\n━━━━━━━━━━━━━━━━━━━━━\n<b>Alasan:</b> {err}"

    await status_msg.edit_text(text, parse_mode=ParseMode.HTML)


async def cmd_generate_code_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menu Generator Kode Akses User (Khusus Admin)"""
    user = update.effective_user
    role, _ = get_user_role_and_expiry(user.id)
    if role != "ADMIN":
        await update.message.reply_text("⛔ <b>Hanya Admin yang dapat membuat kode akses.</b>", parse_mode=ParseMode.HTML)
        return

    text = (
        f"🔑 <b>GENERATOR KODE AKSES USER</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"Pilih durasi masa aktif kode yang ingin dibuat:\n"
        f"<i>User yang memasukkan kode ini akan mendapatkan akses ke bot Coins.ph sesuai durasi terpilih.</i>"
    )
    keyboard = [
        [
            InlineKeyboardButton("🎟️ 1 Hari (24 Jam)", callback_data="gen_code_1"),
            InlineKeyboardButton("🎟️ 3 Hari", callback_data="gen_code_3")
        ],
        [
            InlineKeyboardButton("🎟️ 7 Hari (1 Minggu)", callback_data="gen_code_7"),
            InlineKeyboardButton("🎟️ 30 Hari (1 Bulan)", callback_data="gen_code_30")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.callback_query:
        await update.callback_query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)


async def cmd_set_base_nominal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ubah Nominal Default Base PHP (Admin)"""
    user = update.effective_user
    role, _ = get_user_role_and_expiry(user.id)
    if role != "ADMIN":
        await update.message.reply_text("⛔ <b>Hanya Admin yang dapat mengubah base nominal.</b>", parse_mode=ParseMode.HTML)
        return

    curr_base = config.get("bot_settings", {}).get("default_base_php", 100)
    USER_STATES[user.id] = {"state": "AWAITING_BASE_NOMINAL"}

    text = (
        f"⚙️ <b>UBAH NOMINAL DEFAULT BASE PHP</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"Nominal Base saat ini: <code>₱ {curr_base:,}</code>\n\n"
        f"Ketik nominal base baru yang Anda inginkan (contoh: <code>100</code>, <code>200</code>, atau <code>500</code>):\n"
        f"<i>Tombol preset pembuatan QR Ph akan otomatis mengikuti nominal ini!</i>"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_user_expiry_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cek Masa Aktif Akun User"""
    user = update.effective_user
    role, expiry = get_user_role_and_expiry(user.id)

    if role == "ADMIN":
        text = "👑 <b>STATUS AKUN: SUPER ADMIN</b>\n━━━━━━━━━━━━━━━━━━━━━\nMasa aktif Anda: <b>Permanen (Unlimited)</b>"
    elif role == "USER" and expiry:
        exp_fmt = expiry.strftime("%d/%m/%Y %H:%M:%S WIB")
        sisa = expiry - datetime.now()
        hours, remainder = divmod(int(sisa.total_seconds()), 3600)
        minutes, _ = divmod(remainder, 60)
        days = hours // 24
        hours = hours % 24
        text = (
            f"⏳ <b>STATUS MASA AKTIF AKUN</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 <b>Pengguna:</b> {html.escape(user.first_name)}\n"
            f"🔑 <b>Role:</b> Member\n"
            f"📅 <b>Berlaku Hingga:</b> <code>{exp_fmt}</code>\n"
            f"⏰ <b>Sisa Waktu:</b> <b>{days} hari, {hours} jam, {minutes} menit</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━"
        )
    else:
        text = "🔒 <b>Akun Anda belum memiliki akses aktif.</b>"

    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_system_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cek Status Sistem & Akun (Admin)"""
    user = update.effective_user
    role, _ = get_user_role_and_expiry(user.id)
    if role != "ADMIN":
        await cmd_user_expiry_status(update, context)
        return

    sessions = config.get("security", {}).get("user_sessions", {})
    total_users = len(sessions)
    acc_count = len(config.get("accounts", []))
    rate_info = rate_engine.get_info()

    text = (
        f"⚙️ <b>STATUS SISTEM COINS.PH GATEWAY</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"👥 <b>Total Sesi Terdaftar:</b> <code>{total_users}</code> User\n"
        f"📱 <b>Total Slot Terdaftar:</b> <code>{acc_count}</code> Slot Akun\n"
        f"📊 <b>Kurs Live USDC/PHP:</b> ₱ {rate_info.get('effective_rate', 60.75):.2f}\n"
        f"📡 <b>Status Rate Engine:</b> 🟢 Standby\n"
        f"💳 <b>Web3 Wallet Engine:</b> 🟢 Terhubung (Base & BSC)\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ <i>Semua layanan pembayaran QR Ph dan database orders beroperasi normal.</i>"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Panduan Penggunaan Bot Sesuai Role"""
    user = update.effective_user
    role, _ = get_user_role_and_expiry(user.id)

    if role == "ADMIN":
        text = (
            f"📖 <b>PANDUAN LENGKAP BOT (SUPER ADMIN)</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔹 <b>⚡ Buat QR Ph</b> - Buat invoice QR code InstaPay dinamis\n"
            f"🔹 <b>📱 Status Akun Slot</b> - Cek nomor HP & identitas slot akun\n"
            f"🔹 <b>📊 Kurs & Kalkulator</b> - Cek kurs P2P Bitget & konversi instan\n"
            f"🔹 <b>💳 Saldo Web3 Wallet</b> - Pantau saldo Base (ETH/USDC) & BSC (BNB/USDT)\n"
            f"🔹 <b>💸 Kirim Token Web3</b> - Transfer token USDC / USDT ke alamat lain\n"
            f"🔹 <b>⚡ Reset Multi App</b> - Eksekusi Reset ADB (Root/Shizuku/Wireless/PC)\n"
            f"🔹 <b>🔑 Buat Kode User</b> - Generate token masa aktif member (1, 3, 7, 30 hari)\n"
            f"🔹 <b>⚙️ Ubah Base Nominal</b> - Ubah nominal default base PHP\n"
            f"🔹 <b>📜 Riwayat Transaksi</b> - Pantau transaksi database terbaru\n"
            f"🔹 <b>⚙️ Status Sistem</b> - Cek status kesehatan gateway & sesi user\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Auto-Delete Barcode aktif: Barcode lama otomatis terhapus begitu lunas/dibatalkan.</i>"
        )
    else:
        text = (
            f"📖 <b>PANDUAN PENGGUNAAN BOT (MEMBER)</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔹 <b>⚡ Buat QR Ph</b> - Buat invoice barcode pembayaran QR Ph\n"
            f"🔹 <b>📱 Status Akun Slot</b> - Cek slot akun Coins.ph aktif\n"
            f"🔹 <b>📊 Kurs & Kalkulator</b> - Cek kurs USDC/PHP dan kalkulator hitung\n"
            f"🔹 <b>📜 Riwayat Transaksi</b> - Lihat status transaksi order Anda\n"
            f"🔹 <b>⏳ Masa Aktif Akun</b> - Cek sisa durasi masa aktif akun Anda\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"<i>Tips: Anda bisa langsung mengetik angka seperti '1000 php' di chat untuk hitung kurs!</i>"
        )
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


# ============================================================
# PROCESS QR PH GENERATION & AUTO-DELETE BARCODE
# ============================================================

async def process_generate_qrph(
    chat_id: int,
    user_id: int,
    slot_id: str,
    amount_php: float,
    origin_message: Any
):
    """
    Membuat Invoice QR Ph EMVCo Resmi dengan badge InstaPay,
    menyimpan order ke database SQLite, dan mengirim foto barcode ke Telegram.
    """
    global config, GLOBAL_BOT
    if hasattr(origin_message, "reply_text"):
        status_msg = await origin_message.reply_text("⏳ <i>Memproses pembuatan QR Ph InstaPay...</i>", parse_mode=ParseMode.HTML)
    else:
        status_msg = await GLOBAL_BOT.send_message(chat_id=chat_id, text="⏳ <i>Memproses pembuatan QR Ph InstaPay...</i>", parse_mode=ParseMode.HTML)

    acc = get_account(slot_id, config)
    if not acc:
        accounts = config.get("accounts", [])
        if accounts:
            acc = accounts[0]
            slot_id = acc.get("id", "slot_1")
        else:
            acc = {
                "id": "slot_1",
                "name": "COINS MERCHANT",
                "phone": "639170000000",
                "account_id": "639170000000",
                "bank_bic": "DCPHPHM1XXX",
                "sub_id": "99964403",
                "city": "Manila"
            }

    order_id = f"CPH-{datetime.now().strftime('%y%m%d%H%M%S')}-{secrets.token_hex(2).upper()}"
    auto_rand = config.get("bot_settings", {}).get("auto_random_name", True)
    merchant_name = get_random_merchant_name() if auto_rand else acc.get("name", "JUANDELACRUZ")

    # Generate EMVCo Payload
    try:
        payload = generate_qrph_payload(
            amount=amount_php,
            order_id=order_id,
            account=acc,
            config=config,
            merchant_name=merchant_name,
            auto_random_name=False
        )
    except Exception as e:
        logger.error(f"Gagal generate QR Ph payload: {e}")
        await status_msg.edit_text(f"❌ <b>Gagal membuat barcode QR Ph!</b>\nError: {e}", parse_mode=ParseMode.HTML)
        return

    # Hitung estimasi USDC berdasarkan rate live
    rate_info = rate_engine.get_info()
    client_rate = rate_info.get("effective_rate", 60.75)
    est_usdc = rate_engine.php_to_usdc(amount_php)

    # Simpan order ke database SQLite
    create_order(
        order_id=order_id,
        amount=amount_php,
        qr_payload=payload,
        account_id=slot_id,
        account_name=merchant_name,
        customer_name=merchant_name,
        customer_phone=acc.get("account_id") or acc.get("phone"),
        note=f"Created via Telegram Bot by {user_id}",
        timeout_minutes=config.get("bot_settings", {}).get("invoice_timeout_minutes", 15)
    )

    # Render HD QR Image dengan InstaPay Badge
    loop = asyncio.get_running_loop()
    def _render_image_bytes():
        img = generate_qr_image(payload, box_size=10, border=2, with_badge=True)
        bio = BytesIO()
        img.save(bio, format="PNG")
        bio.seek(0)
        return bio.getvalue()

    qr_bytes = await loop.run_in_executor(None, _render_image_bytes)

    caption = (
        f"🏛 <b>INVOICE COINS.PH QR PH (INSTAPAY)</b>\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📱 <b>Slot Akun:</b> {slot_id.upper()} (<code>{acc.get('account_id') or acc.get('phone')}</code>)\n"
        f"🏪 <b>Merchant:</b> <b>{merchant_name}</b>\n"
        f"🏷 <b>Total Bayar:</b> <b>₱ {amount_php:,.2f} PHP</b>\n"
        f"💵 <b>Estimasi USDC:</b> <b>~{est_usdc:.2f} USDC</b> (Kurs: ₱ {client_rate:.2f})\n"
        f"📌 <b>Order ID:</b> <code>{order_id}</code>\n"
        f"⏰ <b>Batas Waktu:</b> 15 Menit\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📲 <i>Buka aplikasi Coins.ph, GCash, Maya, GrabPay, atau Mobile Banking, lalu scan barcode di atas.</i>\n\n"
        f"🔄 <i>Status pembayaran dipantau realtime otomatis.</i>"
    )

    keyboard = [
        [InlineKeyboardButton("🔄 Cek Status Bayar", callback_data=f"chk_{order_id}")],
        [
            InlineKeyboardButton("📋 Salin Payload", callback_data=f"copy_{order_id}"),
            InlineKeyboardButton("❌ Batalkan / Hapus QR", callback_data=f"cnl_{order_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await status_msg.delete()

    sent = await GLOBAL_BOT.send_photo(
        chat_id=chat_id,
        photo=qr_bytes,
        caption=caption,
        parse_mode=ParseMode.HTML,
        reply_markup=reply_markup
    )

    ACTIVE_INVOICES[order_id] = {
        "order_id": order_id,
        "chat_id": chat_id,
        "user_id": user_id,
        "message_id": sent.message_id,
        "amount_php": amount_php,
        "slot_id": slot_id,
        "merchant_name": merchant_name,
        "created_at": datetime.now()
    }

    # Jalankan background monitoring khusus untuk order ini
    asyncio.create_task(auto_poll_single_order(order_id))


async def auto_poll_single_order(order_id: str):
    """
    Background Task per Invoice:
    Memantau order di database. Begitu status berubah menjadi PAID,
    pesan foto barcode lama otomatis DIHAPUS dari chat (Auto-Delete Barcode)
    dan dikirimkan struk konfirmasi lunas.
    """
    global GLOBAL_BOT, ACTIVE_INVOICES
    poll_sec = config.get("bot_settings", {}).get("auto_check_interval_seconds", 5)
    timeout_mins = config.get("bot_settings", {}).get("invoice_timeout_minutes", 15)
    max_loops = int((timeout_mins * 60) / poll_sec)

    for _ in range(max_loops):
        await asyncio.sleep(poll_sec)

        if order_id not in ACTIVE_INVOICES:
            break

        inv = ACTIVE_INVOICES[order_id]
        order = get_order(order_id)

        if not order:
            break

        status = order.get("status", "PENDING")

        if status == "PAID":
            del ACTIVE_INVOICES[order_id]
            NOTIFIED_PAID_ORDERS.add(order_id)

            # 1. HAPUS PESAN FOTO BARCODE LAMA DARI CHAT (Auto-Delete Barcode)
            try:
                if GLOBAL_BOT and inv.get("message_id"):
                    await GLOBAL_BOT.delete_message(chat_id=inv["chat_id"], message_id=inv["message_id"])
                    logger.info(f"✅ Barcode lama order {order_id} berhasil dihapus dari chat")
            except Exception as e:
                logger.debug(f"Gagal menghapus barcode lama: {e}")

            # 2. Kirim Pesan Konfirmasi Pembayaran Sukses
            success_text = (
                f"🎉 <b>PEMBAYARAN QR PH BERHASIL DITERIMA!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"💰 <b>Nominal:</b> <b>₱ {inv['amount_php']:,.2f} PHP</b>\n"
                f"📌 <b>Order ID:</b> <code>{order_id}</code>\n"
                f"📱 <b>Slot:</b> {inv['slot_id'].upper()}\n"
                f"🏪 <b>Merchant:</b> {inv['merchant_name']}\n"
                f"⏰ <b>Waktu Bayar:</b> {order.get('paid_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"✅ <i>Dana telah masuk dan status order telah diperbarui ke sistem!</i>"
            )

            role, _ = get_user_role_and_expiry(inv["user_id"])
            try:
                if GLOBAL_BOT:
                    await GLOBAL_BOT.send_message(
                        chat_id=inv["chat_id"],
                        text=success_text,
                        parse_mode=ParseMode.HTML,
                        reply_markup=get_role_reply_keyboard(role)
                    )
            except Exception as e:
                logger.error(f"Gagal kirim notifikasi bayar: {e}")
            break

        elif status in ["CANCELLED", "EXPIRED"]:
            del ACTIVE_INVOICES[order_id]
            try:
                if GLOBAL_BOT and inv.get("message_id"):
                    await GLOBAL_BOT.delete_message(chat_id=inv["chat_id"], message_id=inv["message_id"])
            except Exception:
                pass
            break

    if order_id in ACTIVE_INVOICES:
        del ACTIVE_INVOICES[order_id]


# ============================================================
# REALTIME BACKGROUND ORDER WATCHER
# ============================================================

async def background_order_watcher():
    """
    Background Task Global:
    Memantau payments.db secara realtime. Jika ada order yang ditandai PAID
    (misal melalui POS Web, scanner kamera, atau API callback), bot akan
    mengirim notifikasi instan ke Admin dan User terkait.
    """
    global GLOBAL_BOT, NOTIFIED_PAID_ORDERS
    logger.info("🚀 Background Order Watcher aktif memantau pembayaran...")

    while True:
        try:
            await asyncio.sleep(4)
            recent_orders = get_recent_orders(limit=20)

            for order in recent_orders:
                oid = order.get("order_id")
                status = order.get("status")

                if status == "PAID" and oid not in NOTIFIED_PAID_ORDERS:
                    NOTIFIED_PAID_ORDERS.add(oid)

                    # Jika ada barcode aktif di Telegram, hapus barcode dan notifikasi sudah ditangani oleh auto_poll
                    if oid in ACTIVE_INVOICES:
                        continue

                    # Notifikasi untuk pembayaran yang terjadi di luar bot (misal Web POS)
                    admin_ids = config.get("telegram", {}).get("admin_ids", [])
                    notif_text = (
                        f"🔔 <b>PEMBAYARAN DITERIMA (WEB / GATEWAY)</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━━\n"
                        f"💰 <b>Nominal:</b> <b>₱ {order.get('amount', 0.0):,.2f} PHP</b>\n"
                        f"📌 <b>Order ID:</b> <code>{oid}</code>\n"
                        f"📱 <b>Slot:</b> {order.get('account_id', 'slot_1')}\n"
                        f"🏪 <b>Akun:</b> {order.get('account_name', 'Merchant')}\n"
                        f"💳 <b>Metode:</b> {order.get('payment_method', 'QR Ph / InstaPay')}\n"
                        f"⏰ <b>Waktu:</b> {order.get('paid_at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}\n"
                        f"━━━━━━━━━━━━━━━━━━━━━"
                    )

                    for aid in admin_ids:
                        try:
                            if GLOBAL_BOT:
                                await GLOBAL_BOT.send_message(chat_id=aid, text=notif_text, parse_mode=ParseMode.HTML)
                        except Exception as e:
                            logger.debug(f"Gagal kirim notif watcher ke admin {aid}: {e}")

        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.debug(f"Error di background_order_watcher: {e}")
            await asyncio.sleep(4)


# ============================================================
# CALLBACK QUERY HANDLER
# ============================================================

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani semua event klik tombol inline"""
    query = update.callback_query
    await query.answer()

    user = query.from_user
    role, _ = get_user_role_and_expiry(user.id)

    if role not in ["ADMIN", "USER"]:
        await query.answer("⛔ Sesi Anda belum aktif.", show_alert=True)
        return

    data = query.data

    # 1. PILIH SLOT UNTUK QR PH
    if data.startswith("sel_slot_"):
        slot_id = data.replace("sel_slot_", "")
        acc = get_account(slot_id, config)
        slot_name = acc.get("name", slot_id) if acc else slot_id

        text = (
            f"⚡ <b>PILIH NOMINAL QR PH</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📱 <b>Slot Terpilih:</b> {slot_id.upper()} ({slot_name})\n"
            f"Pilih nominal preset di bawah atau gunakan 'Ketik Nominal Bebas':"
        )
        reply_markup = get_nominal_preset_keyboard(slot_id)
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=reply_markup)
        return

    # 2. PILIH NOMINAL DARI PRESET
    elif data.startswith("gen_custom_"):
        slot_id = data.replace("gen_custom_", "")
        USER_STATES[user.id] = {"state": "AWAITING_CUSTOM_AMOUNT", "slot_id": slot_id}
        text = (
            f"✏️ <b>INPUT NOMINAL BEBAS (PHP)</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"Ketik nominal pembayaran dalam PHP (contoh: <code>150</code>, <code>500</code>, atau <code>1250</code>):"
        )
        await query.edit_message_text(text, parse_mode=ParseMode.HTML)
        return

    elif data.startswith("gen_"):
        parts = data.split("_")
        # Format: gen_{slot_id}_{amount}
        if len(parts) >= 3:
            slot_id = parts[1]
            try:
                amount_php = float(parts[2])
                await process_generate_qrph(query.message.chat_id, user.id, slot_id, amount_php, query.message)
            except ValueError:
                await query.answer("Nominal tidak valid.", show_alert=True)
        return

    # 3. CEK STATUS BAYAR ORDER
    elif data.startswith("chk_"):
        order_id = data.replace("chk_", "")
        order = get_order(order_id)
        if not order:
            await query.answer("Order tidak ditemukan di database.", show_alert=True)
            return

        status = order.get("status", "PENDING")
        if status == "PAID":
            await query.answer("✅ Pembayaran SUDAH LUNAS!", show_alert=True)
        else:
            await query.answer(f"⏳ Status: {status} (Menunggu Pembayaran)", show_alert=True)
        return

    # 4. SALIN PAYLOAD QR
    elif data.startswith("copy_"):
        order_id = data.replace("copy_", "")
        order = get_order(order_id)
        if order and order.get("qr_payload"):
            payload = order["qr_payload"]
            await query.message.reply_text(
                f"📋 <b>EMVCo Payload QR Ph:</b>\n\n<code>{payload}</code>",
                parse_mode=ParseMode.HTML
            )
        else:
            await query.answer("Payload tidak ditemukan.", show_alert=True)
        return

    # 5. BATALKAN / HAPUS QR
    elif data.startswith("cnl_"):
        order_id = data.replace("cnl_", "")
        if order_id in ACTIVE_INVOICES:
            del ACTIVE_INVOICES[order_id]
        try:
            await query.message.delete()
            await query.message.reply_text("❌ <b>Barcode QR Ph telah dibatalkan & dihapus.</b>", parse_mode=ParseMode.HTML)
        except Exception:
            pass
        return

    elif data == "qr_cancel":
        try:
            await query.message.delete()
        except Exception:
            pass
        return

    # 6. GENERATOR KODE AKSES USER (ADMIN)
    elif data.startswith("gen_code_"):
        if role != "ADMIN":
            await query.answer("⛔ Hanya Admin yang dapat membuat kode.", show_alert=True)
            return

        days_str = data.replace("gen_code_", "")
        try:
            days = int(days_str)
            code = generate_user_code(days, user.id)
            exp_date = (datetime.now() + timedelta(days=days)).strftime("%d/%m/%Y")
            res_text = (
                f"🔑 <b>KODE AKSES USER BARU BERHASIL DIBUAT!</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🎟️ <b>Kode Akses:</b>\n"
                f"<code>{code}</code>\n\n"
                f"⏰ <b>Durasi:</b> {days} Hari (Berlaku s/d {exp_date})\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📋 <i>Salin kode di atas dan kirimkan ke user. Pengguna cukup mengetikkan kode tersebut ke bot ini.</i>"
            )
            await query.edit_message_text(res_text, parse_mode=ParseMode.HTML)
        except ValueError:
            pass
        return

    # 7. WEB3 WALLET REFRESH & TRANSFER WIZARD
    elif data == "wallet_refresh":
        loop = asyncio.get_running_loop()
        balances = await loop.run_in_executor(None, wallet_manager.get_all_balances)
        pub_addr = wallet_manager.get_address() or "Belum Diatur"
        base_b = balances.get("base", {})
        bsc_b = balances.get("bsc", {})

        text = (
            f"💳 <b>INFORMASI WEB3 WALLET (UPDATED)</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📬 <b>Alamat Wallet:</b>\n"
            f"<code>{pub_addr}</code>\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"🔵 <b>Base Network:</b>\n"
            f"  • ETH (Gas): <b>{base_b.get('ETH', 0.0):.5f} ETH</b>\n"
            f"  • USDC: <b>${base_b.get('USDC', 0.0):.2f} USDC</b>\n\n"
            f"🟡 <b>BNB Smart Chain (BSC):</b>\n"
            f"  • BNB (Gas): <b>{bsc_b.get('BNB', 0.0):.5f} BNB</b>\n"
            f"  • USDT: <b>${bsc_b.get('USDT', 0.0):.2f} USDT</b>\n"
            f"  • USDC: <b>${bsc_b.get('USDC', 0.0):.2f} USDC</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━"
        )
        keyboard = [
            [InlineKeyboardButton("🔄 Refresh Saldo", callback_data="wallet_refresh")],
            [InlineKeyboardButton("💸 Kirim Token", callback_data="wallet_send_prompt")]
        ]
        await query.edit_message_text(text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data == "wallet_send_prompt":
        await cmd_transfer_prompt(update, context)
        return

    elif data.startswith("tx_start_"):
        parts = data.split("_")
        # Format: tx_start_{network}_{token}
        if len(parts) >= 4:
            net = parts[2]
            token = parts[3]
            USER_STATES[user.id] = {"state": "AWAITING_TRANSFER_ADDR", "network": net, "token": token}
            text = (
                f"💸 <b>KIRIM {token} ({net.upper()})</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"Silakan kirimkan <b>Alamat Dompet Penerima (0x...)</b>:"
            )
            await query.edit_message_text(text, parse_mode=ParseMode.HTML)
        return

    elif data == "tx_cancel":
        USER_STATES.pop(user.id, None)
        try:
            await query.message.delete()
        except Exception:
            pass
        return


# ============================================================
# TEXT MESSAGE & KEYBOARD MENU ROUTING
# ============================================================

async def handle_text_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Menangani input teks pengguna, klik tombol navigasi keyboard bawah, dan state machine"""
    user = update.effective_user
    if not user:
        return

    text = update.message.text.strip()
    user_id = user.id
    role, expiry = get_user_role_and_expiry(user_id)

    # 1. PENEBUSAN KODE AKSES / LOGIN ADMIN
    user_st = USER_STATES.get(user_id, {})
    curr_state = user_st.get("state")

    if curr_state == "AWAITING_LOGIN_CODE" or role in ["GUEST", "EXPIRED"]:
        ok, res_role, msg = redeem_code(user_id, user.first_name, text)
        if ok:
            USER_STATES.pop(user_id, None)
            new_role, _ = get_user_role_and_expiry(user_id)
            await update.message.reply_text(
                msg,
                parse_mode=ParseMode.HTML,
                reply_markup=get_role_reply_keyboard(new_role)
            )
            return
        else:
            await update.message.reply_text(
                f"{msg}\n\nSilakan coba lagi atau masukkan Master Key Admin.",
                parse_mode=ParseMode.HTML
            )
            return

    # 2. ROUTING TOMBOL KEYBOARD MENU BAWAH
    if text in ["⚡ Buat QR Ph", "Buat QR Ph", "QR Ph", "Deposit"]:
        await cmd_qr_menu(update, context)
        return
    elif text in ["📱 Status Akun Slot", "Status Akun Slot", "Status Slot"]:
        await cmd_slots_status(update, context)
        return
    elif text in ["📊 Kurs & Kalkulator", "Kurs & Kalkulator", "Kurs", "Rate"]:
        await cmd_rate(update, context)
        return
    elif text in ["💳 Saldo Web3 Wallet", "Saldo Web3 Wallet", "Wallet"]:
        await cmd_wallet_status(update, context)
        return
    elif text in ["💸 Kirim Token Web3", "Kirim Token Web3", "Kirim Token", "Transfer"]:
        await cmd_transfer_prompt(update, context)
        return
    elif text in ["⚡ Reset Multi App (ADB)", "Reset Multi App (ADB)", "Reset ADB"]:
        await cmd_reset_adb(update, context)
        return
    elif text in ["🔑 Buat Kode User", "Buat Kode User"]:
        await cmd_generate_code_menu(update, context)
        return
    elif text in ["⚙️ Ubah Base Nominal", "Ubah Base Nominal"]:
        await cmd_set_base_nominal(update, context)
        return
    elif text in ["📜 Riwayat Transaksi", "Riwayat Transaksi", "Riwayat"]:
        await cmd_history(update, context)
        return
    elif text in ["⚙️ Status Sistem", "Status Sistem", "Status"]:
        await cmd_system_status(update, context)
        return
    elif text in ["⏳ Masa Aktif Akun", "Masa Aktif Akun", "Masa Aktif"]:
        await cmd_user_expiry_status(update, context)
        return
    elif text in ["📖 Panduan & Bantuan", "Panduan", "Help", "Bantuan"]:
        await cmd_help(update, context)
        return

    # 3. INTERACTIVE STATE MACHINE
    if curr_state == "AWAITING_CUSTOM_AMOUNT":
        slot_id = user_st.get("slot_id", "slot_1")
        clean_str = text.replace("₱", "").replace("PHP", "").replace("php", "").replace(",", "").strip()
        try:
            val = float(clean_str)
            if val <= 0:
                raise ValueError()
            USER_STATES.pop(user_id, None)
            await process_generate_qrph(update.effective_chat.id, user_id, slot_id, val, update.message)
            return
        except ValueError:
            await update.message.reply_text(
                "⚠️ <b>Nominal tidak valid!</b> Masukkan angka nominal dalam PHP (contoh: <code>500</code>):",
                parse_mode=ParseMode.HTML
            )
            return

    elif curr_state == "AWAITING_BASE_NOMINAL":
        if role != "ADMIN":
            return
        clean_str = text.replace("₱", "").replace("PHP", "").replace("php", "").replace(",", "").strip()
        try:
            val = int(clean_str)
            if val <= 0:
                raise ValueError()
            USER_STATES.pop(user_id, None)
            config.setdefault("bot_settings", {})["default_base_php"] = val
            save_config(config)
            await update.message.reply_text(
                f"✅ <b>Nominal Default Base Berhasil Diubah ke ₱ {val:,} PHP!</b>\n\n"
                f"Semua tombol preset pembuatan QR Ph otomatis mengikuti nominal ini.",
                parse_mode=ParseMode.HTML,
                reply_markup=get_role_reply_keyboard(role)
            )
            return
        except ValueError:
            await update.message.reply_text(
                "⚠️ <b>Nominal tidak valid!</b> Masukkan angka (contoh: <code>150</code> atau <code>500</code>):",
                parse_mode=ParseMode.HTML
            )
            return

    elif curr_state == "AWAITING_TRANSFER_ADDR":
        if role != "ADMIN":
            return
        addr = text.strip()
        if not re.match(r"^0x[a-fA-F0-9]{40}$", addr):
            await update.message.reply_text(
                "⚠️ <b>Alamat dompet tidak valid!</b>\nFormat harus diawali <code>0x</code> dan terdiri dari 42 karakter hex. Silakan ketik ulang:",
                parse_mode=ParseMode.HTML
            )
            return
        user_st["to_address"] = addr
        user_st["state"] = "AWAITING_TRANSFER_AMOUNT"
        USER_STATES[user_id] = user_st
        await update.message.reply_text(
            f"✅ <b>Alamat Penerima Tercatat:</b>\n<code>{addr}</code>\n\n"
            f"Ketik jumlah token <b>{user_st.get('token')}</b> yang ingin dikirimkan (contoh: <code>5.5</code> atau <code>10</code>):",
            parse_mode=ParseMode.HTML
        )
        return

    elif curr_state == "AWAITING_TRANSFER_AMOUNT":
        if role != "ADMIN":
            return
        clean_amt = text.replace("$", "").replace(",", "").strip()
        try:
            amt = float(clean_amt)
            if amt <= 0:
                raise ValueError()
            net = user_st.get("network", "base")
            token = user_st.get("token", "USDC")
            to_addr = user_st.get("to_address")
            USER_STATES.pop(user_id, None)

            status_msg = await update.message.reply_text(
                f"⏳ <b>Memproses Pengiriman Blockchain...</b>\n"
                f"Jaringan: <code>{net.upper()}</code>\n"
                f"Token: <code>{token}</code>\n"
                f"Nominal: <code>{amt} {token}</code>\n"
                f"Tujuan: <code>{to_addr}</code>\n\n"
                f"<i>Mohon tunggu konfirmasi block...</i>",
                parse_mode=ParseMode.HTML
            )

            loop = asyncio.get_running_loop()
            res = await loop.run_in_executor(None, wallet_manager.send_token, net, token, to_addr, amt)

            if res.get("success"):
                tx_hash = res.get("tx_hash", "0x")
                explorer = res.get("explorer_url", "")
                link_txt = f"<a href='{explorer}'>Lihat di Explorer</a>" if explorer else f"<code>{tx_hash}</code>"
                await status_msg.edit_text(
                    f"🎉 <b>TRANSFER TOKEN BERHASIL!</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🌐 <b>Jaringan:</b> {net.upper()}\n"
                    f"🪙 <b>Token:</b> {amt} {token}\n"
                    f"📬 <b>Penerima:</b> <code>{to_addr}</code>\n"
                    f"🔗 <b>TX Hash:</b> {link_txt}\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"✅ <i>Transaksi telah disiarkan dan diverifikasi di blockchain!</i>",
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True
                )
            else:
                err = res.get("error", "Terjadi kesalahan transaksi.")
                await status_msg.edit_text(
                    f"❌ <b>Transfer Gagal!</b>\n\n<b>Alasan:</b> {html.escape(str(err))}",
                    parse_mode=ParseMode.HTML
                )
            return
        except ValueError:
            await update.message.reply_text("⚠️ <b>Nominal tidak valid!</b> Masukkan angka desimal (contoh: <code>10.5</code>):", parse_mode=ParseMode.HTML)
            return

    # 4. KALKULATOR KURS INSTAN (DETEKSI POLA OTOMATIS)
    php_match = re.match(r"^([0-9.,]+)\s*(?:php|pesos?)$", text, re.IGNORECASE)
    if php_match:
        try:
            val_php = float(php_match.group(1).replace(",", ""))
            rate_val = rate_engine.rate
            res_usdc = rate_engine.php_to_usdc(val_php)
            await update.message.reply_text(
                f"🧮 <b>KONVERSI KURS BITGET</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🇵🇭 <b>₱ {val_php:,.2f} PHP</b>\n"
                f"⬇️\n"
                f"💵 <b>${res_usdc:,.4f} USDC</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 <i>Kurs Acuan: 1 USDC = ₱ {rate_val:.2f} PHP</i>",
                parse_mode=ParseMode.HTML
            )
            return
        except Exception:
            pass

    usdc_match = re.match(r"^([0-9.,]+)\s*(?:usdc|usdt|usd|\$)$", text, re.IGNORECASE)
    if usdc_match:
        try:
            val_usdc = float(usdc_match.group(1).replace(",", ""))
            rate_val = rate_engine.rate
            res_php = rate_engine.usdc_to_php(val_usdc)
            await update.message.reply_text(
                f"🧮 <b>KONVERSI KURS BITGET</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"💵 <b>${val_usdc:,.2f} USDC</b>\n"
                f"⬇️\n"
                f"🇵🇭 <b>₱ {res_php:,.2f} PHP</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"📊 <i>Kurs Acuan: 1 USDC = ₱ {rate_val:.2f} PHP</i>",
                parse_mode=ParseMode.HTML
            )
            return
        except Exception:
            pass


# ============================================================
# ERROR HANDLER & POST INIT
# ============================================================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error("Exception while handling an update:", exc_info=context.error)


async def post_init(application: Application):
    """Jalankan background task setelah bot terhubung"""
    rate_engine.start()

    # Jalankan background order watcher
    asyncio.create_task(background_order_watcher())
    logger.info("🚀 Background Tasks (Order Watcher) telah aktif.")


# ============================================================
# MAIN ENTRYPOINT
# ============================================================

def main():
    global GLOBAL_BOT

    bot_token = config.get("telegram", {}).get("bot_token", "")
    if not bot_token or bot_token == "ISI_BOT_TOKEN_DISINI":
        print("\n" + "=" * 65)
        print(" [!] PERINGATAN: Bot Token Telegram belum diisi di core/config.json!")
        print("     Silakan isi bot_token pada core/config.json sebelum menjalankan bot.")
        print("=" * 65 + "\n")
        sys.exit(1)

    print("================================================================")
    print("  MEMULAI COINS.PH PAYMENT GATEWAY & AUTOMATION TELEGRAM BOT")
    print("================================================================")

    req = HTTPXRequest(httpx_kwargs={"verify": False})
    app = Application.builder().token(bot_token).request(req).post_init(post_init).build()
    GLOBAL_BOT = app.bot

    # Daftarkan Command Handlers
    app.add_handler(CommandHandler(["start", "menu"], cmd_start))
    app.add_handler(CommandHandler(["qr", "deposit"], cmd_qr_menu))
    app.add_handler(CommandHandler(["rate", "kurs"], cmd_rate))
    app.add_handler(CommandHandler(["slots", "akun"], cmd_slots_status))
    app.add_handler(CommandHandler(["wallet", "saldo"], cmd_wallet_status))
    app.add_handler(CommandHandler(["kirim", "transfer"], cmd_transfer_prompt))
    app.add_handler(CommandHandler("history", cmd_history))
    app.add_handler(CommandHandler("reset", cmd_reset_adb))
    app.add_handler(CommandHandler("gencode", cmd_generate_code_menu))
    app.add_handler(CommandHandler("setbase", cmd_set_base_nominal))
    app.add_handler(CommandHandler("status", cmd_system_status))
    app.add_handler(CommandHandler("help", cmd_help))

    # Daftarkan Callback Query & Message Handlers
    app.add_handler(CallbackQueryHandler(handle_callback_query))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_messages))
    app.add_error_handler(error_handler)

    print("[+] Bot aktif dan siap melayani transaksi di Telegram!")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
