#!/data/data/com.termux/files/usr/bin/bash
# ===========================================================
#  COINS.PH PAYMENT GATEWAY - TERMUX SETUP
#  Coins.ph Multi-Account QR Hub (Bitget USDC Auto-Increment)
# ===========================================================
# Jalankan sekali saja: bash termuxsetup.sh
# ===========================================================

set -e

echo ""
echo "============================================================"
echo "   COINS.PH PAYMENT GATEWAY - SETUP TERMUX"
echo "============================================================"
echo ""

# 1. Update dan install paket dasar Termux
echo "[1/6] Update paket Termux..."
pkg update -y && pkg upgrade -y

echo ""
echo "[2/6] Install Python & dependencies sistem..."
pkg install -y python python-pip clang libffi openssl zlib libjpeg-turbo

echo ""
echo "[3/6] Upgrade pip..."
pip install --upgrade pip

# Lokasi folder core relatif terhadap TERMUX/
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CORE_DIR="$SCRIPT_DIR/../core"

if [ ! -f "$CORE_DIR/requirements.txt" ]; then
    echo "[ERROR] requirements.txt tidak ditemukan di: $CORE_DIR"
    echo ""
    echo "Pastikan struktur folder:"
    echo "  COINS_PAYMENT_GATEWAY/"
    echo "    TERMUX/"
    echo "      termuxsetup.sh  <-- (file ini)"
    echo "      run.sh"
    echo "    core/"
    echo "      requirements.txt"
    exit 1
fi

echo ""
echo "[4/6] Install requirements dari core/requirements.txt..."
pip install -r "$CORE_DIR/requirements.txt"

echo ""
echo "[5/6] Install Pillow & zxingcpp (generate QR)..."
pip install pillow 2>/dev/null && echo "  Pillow OK" || echo "  [Warn] Pillow gagal"
pip install zxingcpp 2>/dev/null && echo "  zxingcpp OK" || echo "  [Warn] zxingcpp gagal (optional)"

echo ""
echo "[6/6] Verifikasi instalasi..."
python -c "import flask; print('  Flask OK:', flask.__version__)"
python -c "import qrcode; print('  qrcode OK:', qrcode.__version__)"
python -c "import PIL; print('  Pillow OK:', PIL.__version__)"
python -c "import sqlite3; print('  SQLite3 OK (built-in)')"

echo ""
echo "============================================================"
echo "  SETUP SELESAI!"
echo ""
echo "  Cara menjalankan server:"
echo "  $ bash run.sh"
echo ""
echo "  Lalu buka browser di HP dan akses:"
echo "  http://<IP-HP>:5000/pos"
echo "============================================================"
echo ""
