#!/data/data/com.termux/files/usr/bin/bash
# ===========================================================
#  COINS.PH PAYMENT GATEWAY - JALANKAN SERVER (TERMUX)
# ===========================================================
# Perintah: bash run.sh
# ===========================================================

echo ""
echo "============================================================"
echo "   COINS.PH PAYMENT GATEWAY - SERVER TERMUX"
echo "============================================================"
echo ""

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CORE_DIR="$SCRIPT_DIR/../core"

if [ ! -f "$CORE_DIR/api_server.py" ]; then
    echo "[ERROR] File api_server.py tidak ditemukan di: $CORE_DIR"
    echo "Pastikan Anda sudah mengekstrak ZIP dengan benar."
    exit 1
fi

# Cek Python tersedia
if ! command -v python &> /dev/null; then
    echo "[ERROR] Python belum terinstall."
    echo "Jalankan dulu: bash setup.sh"
    exit 1
fi

echo "[*] Menjalankan server dari: $CORE_DIR"
echo "[*] Kurs Bitget P2P Dynamic Engine Aktif"
LOCAL_IP=$(python -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('8.8.8.8',80)); print(s.getsockname()[0]); s.close()" 2>/dev/null || echo "IP-HP")

echo "[*] Akses server di:"
echo "    http://$LOCAL_IP:5000/pos        <-- POS / Kasir"
echo "    http://$LOCAL_IP:5000/dashboard  <-- Dashboard"
echo ""
echo "[*] Tekan CTRL+C untuk stop server."
echo "============================================================"
echo ""

cd "$CORE_DIR"
python api_server.py
