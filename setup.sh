#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================
#   COINS.PH PAYMENT GATEWAY BOT - ROOT LAUNCHER FOR TERMUX
# ==============================================================
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SCRIPT_DIR/TERMUX/setup.sh" ]; then
    exec bash "$SCRIPT_DIR/TERMUX/setup.sh" "$@"
elif [ -f "$SCRIPT_DIR/termux/setup.sh" ]; then
    exec bash "$SCRIPT_DIR/termux/setup.sh" "$@"
else
    echo "[-] Error: File setup.sh tidak ditemukan di folder TERMUX!"
    exit 1
fi
