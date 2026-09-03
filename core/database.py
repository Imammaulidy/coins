import sqlite3
import os
import json
import time
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import requests

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "payments.db")

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                account_id TEXT DEFAULT 'slot_1',
                account_name TEXT,
                amount REAL NOT NULL,
                currency TEXT DEFAULT 'PHP',
                customer_name TEXT,
                customer_phone TEXT,
                note TEXT,
                qr_payload TEXT NOT NULL,
                status TEXT DEFAULT 'PENDING',
                callback_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP,
                paid_at TIMESTAMP,
                payment_method TEXT,
                payer_info TEXT
            )
        """)
        # Safe migration if table exists without account_id
        try:
            conn.execute("ALTER TABLE orders ADD COLUMN account_id TEXT DEFAULT 'slot_1'")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE orders ADD COLUMN account_name TEXT")
        except Exception:
            pass

        conn.execute("CREATE INDEX IF NOT EXISTS idx_order_id ON orders(order_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_status_amount ON orders(status, amount)")
    conn.close()

def create_order(
    order_id: str,
    amount: float,
    qr_payload: str,
    account_id: str = "slot_1",
    account_name: Optional[str] = None,
    customer_name: Optional[str] = None,
    customer_phone: Optional[str] = None,
    note: Optional[str] = None,
    callback_url: Optional[str] = None,
    timeout_minutes: int = 15,
    currency: str = "PHP"
) -> Dict[str, Any]:
    now = datetime.now()
    expires_at = now + timedelta(minutes=timeout_minutes)
    
    conn = get_connection()
    with conn:
        conn.execute("""
            INSERT INTO orders (
                order_id, account_id, account_name, amount, currency, customer_name, customer_phone,
                note, qr_payload, status, callback_url, created_at, expires_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'PENDING', ?, ?, ?)
        """, (
            order_id,
            account_id,
            account_name or "",
            float(amount),
            currency,
            customer_name or "",
            customer_phone or "",
            note or "",
            qr_payload,
            callback_url or "",
            now.strftime("%Y-%m-%d %H:%M:%S"),
            expires_at.strftime("%Y-%m-%d %H:%M:%S")
        ))
    conn.close()
    return get_order(order_id)

def get_order(order_id: str) -> Optional[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE order_id = ?", (order_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def get_recent_orders(limit: int = 50, account_id: Optional[str] = None) -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    if account_id:
        cursor.execute("SELECT * FROM orders WHERE account_id = ? ORDER BY id DESC LIMIT ?", (account_id, limit))
    else:
        cursor.execute("SELECT * FROM orders ORDER BY id DESC LIMIT ?", (limit,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def mark_as_paid(
    order_id: str,
    payment_method: str = "Coins.ph QR Ph / InstaPay",
    payer_info: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_connection()
    with conn:
        conn.execute("""
            UPDATE orders 
            SET status = 'PAID', paid_at = ?, payment_method = ?, payer_info = ?
            WHERE order_id = ? AND status != 'PAID'
        """, (now, payment_method, payer_info or "", order_id))
    conn.close()
    
    order = get_order(order_id)
    if order and order.get("callback_url"):
        trigger_webhook_async(order)
    return order

def trigger_webhook_async(order: Dict[str, Any]):
    url = order.get("callback_url")
    if not url:
        return
    
    payload = {
        "event": "payment.success",
        "order_id": order["order_id"],
        "account_id": order.get("account_id", "slot_1"),
        "account_name": order.get("account_name", ""),
        "amount": order["amount"],
        "currency": order["currency"],
        "status": order["status"],
        "paid_at": order["paid_at"],
        "customer_name": order["customer_name"],
        "note": order["note"],
        "payer_info": order["payer_info"]
    }
    
    import threading
    def _send():
        try:
            requests.post(url, json=payload, timeout=5)
        except Exception as e:
            print(f"[Webhook Error] Failed to send webhook to {url}: {e}")
            
    threading.Thread(target=_send, daemon=True).start()
