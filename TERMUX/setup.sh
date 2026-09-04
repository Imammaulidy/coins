#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================
#   COINS.PH BOT - INTERACTIVE SETUP & LAUNCHER (TERMUX / ANDROID)
#   Mendukung Non-Root (Wireless ADB / Shizuku) & Root (su)
# ==============================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Cegah CPU Termux masuk mode tidur di background
termux-wake-lock 2>/dev/null

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

banner() {
    clear
    echo -e "${CYAN}${BOLD}=================================================================${NC}"
    echo -e "${CYAN}${BOLD}    COINS.PH PAYMENT GATEWAY BOT - TERMUX SETUP & LAUNCHER      ${NC}"
    echo -e "${CYAN}${BOLD}=================================================================${NC}"
    echo ""
}

show_menu() {
    banner
    # Tampilkan status bot (PM2 atau Native PID)
    PM2_ACTIVE=0
    if command -v pm2 >/dev/null 2>&1; then
        if pm2 jlist 2>/dev/null | grep -q '"name":"coins-bot".*"status":"online"'; then
            PM2_ACTIVE=1
        fi
    fi

    if [ $PM2_ACTIVE -eq 1 ]; then
        echo -e "  ${GREEN}● BOT AKTIF (PM2 Auto-Restart: Online)${NC} — gunakan [6] untuk lihat log"
    elif [ -f "$PROJECT_ROOT/.bot.pid" ]; then
        SAVED_PID=$(cat "$PROJECT_ROOT/.bot.pid")
        if kill -0 "$SAVED_PID" 2>/dev/null; then
            echo -e "  ${GREEN}● BOT AKTIF (Native PID: $SAVED_PID)${NC} — gunakan [6] untuk lihat log"
        else
            echo -e "  ${RED}○ BOT TIDAK AKTIF${NC}"
        fi
    else
        echo -e "  ${RED}○ BOT TIDAK AKTIF${NC}"
    fi
    echo ""
    echo -e "${BOLD}Pilih menu yang ingin dijalankan:${NC}"
    echo ""
    echo -e "  ${GREEN}[1]${NC} ${BOLD}Mode ADB Wifi (Wireless Debugging)${NC}"
    echo -e "      Pairing & Connect port ADB nirkabel Android 11+ (Non-Root)"
    echo ""
    echo -e "  ${GREEN}[2]${NC} ${BOLD}Mode ADB Shizuku${NC}"
    echo -e "      Setup & Test rish Shizuku (Data Seluler murni tanpa Hotspot)"
    echo ""
    echo -e "  ${GREEN}[3]${NC} ${BOLD}Install Dependencies (Python + Android Tools + rish)${NC}"
    echo -e "      Install paket python, clang, adb, requirements.txt, & rish"
    echo ""
    echo -e "  ${GREEN}[4]${NC} ${BOLD}Masukan atau Update Token Bot Tele${NC}"
    echo -e "      Input Bot Token & simpan otomatis ke core/config.json"
    echo ""
    echo -e "  ${GREEN}[5]${NC} ${BOLD}Jalankan Bot Telegram (PM2 / Auto-Restart Background)${NC}"
    echo -e "      Jalankan bot via PM2 Process Manager atau Native Background"
    echo ""
    echo -e "  ${CYAN}[6]${NC} ${BOLD}Lihat Log Bot Terbaru${NC}"
    echo -e "      Tampilkan 50 baris terakhir dari pm2 logs / bot.log"
    echo ""
    echo -e "  ${RED}[7]${NC} Stop Bot (PM2 / Native)"
    echo ""
    echo -e "  ${CYAN}[8]${NC} ${BOLD}Setup PM2 (NodeJS & PM2 Auto-Restart)${NC}"
    echo -e "      Install PM2 untuk Termux agar bot selalu aktif 24/7 otomatis"
    echo ""
    echo -e "  ${YELLOW}[9]${NC} ${BOLD}Jalankan Server Web POS (Port 5000)${NC}"
    echo -e "      Jalankan API & Web POS Kasir Coins.ph di Termux"
    echo ""
    echo -e "  ${RED}[0]${NC} Keluar"
    echo ""
    echo -ne "Pilihan Anda [0-9]: "
}

install_deps() {
    echo ""
    echo -e "${YELLOW}[*] Memulai instalasi dependensi sistem Termux...${NC}"
    echo ""
    pkg update -y
    pkg install -y python python-pip git android-tools clang libffi openssl make curl libjpeg-turbo libpng freetype openjpeg zlib
    pkg install -y python-pillow 2>/dev/null
    
    echo ""
    echo -e "${YELLOW}[*] Menginstall dependensi Python dari core/requirements.txt...${NC}"
    pip install -r core/requirements.txt --prefer-binary

    echo ""
    echo -e "${YELLOW}[*] Memeriksa & memasang rish Shizuku helper...${NC}"
    RISH_BIN="$PREFIX/bin/rish"
    if [ ! -f "$RISH_BIN" ]; then
        curl -sL "https://raw.githubusercontent.com/RikkaApps/Shizuku-API/master/rish/rish" -o "$RISH_BIN" 2>/dev/null
        chmod +x "$RISH_BIN" 2>/dev/null
    fi

    echo ""
    echo -e "${GREEN}[+] Semua dependensi berhasil dipasang!${NC}"
    read -p "Tekan Enter untuk kembali ke menu..."
}

update_token() {
    echo ""
    echo -e "${CYAN}=== INPUT / UPDATE TOKEN BOT TELEGRAM ===${NC}"
    echo "Dapatkan token dari @BotFather di Telegram."
    echo ""
    read -p "Masukkan Bot Token: " NEW_TOKEN
    NEW_TOKEN=$(echo "$NEW_TOKEN" | tr -d '[:space:]')
    
    if [ -z "$NEW_TOKEN" ]; then
        echo -e "${RED}[-] Token tidak boleh kosong!${NC}"
        read -p "Tekan Enter untuk kembali..."
        return
    fi

    python -c "
import json, os
cfg_file = 'core/config.json'
if not os.path.exists(cfg_file) and os.path.exists('core/config.example.json'):
    import shutil; shutil.copyfile('core/config.example.json', cfg_file)
with open(cfg_file, 'r', encoding='utf-8') as f:
    cfg = json.load(f)
cfg.setdefault('telegram', {})['bot_token'] = '$NEW_TOKEN'
with open(cfg_file, 'w', encoding='utf-8') as f:
    json.dump(cfg, f, indent=2)
print('Token berhasil disimpan ke core/config.json')
"
    echo -e "${GREEN}[+] Token bot Telegram berhasil diperbarui!${NC}"
    read -p "Tekan Enter untuk kembali ke menu..."
}

start_bot() {
    echo ""
    echo -e "${YELLOW}[*] Menyiapkan peluncuran bot Telegram Coins.ph...${NC}"

    # Pastikan config.json ada
    if [ ! -f "core/config.json" ]; then
        if [ -f "core/config.example.json" ]; then
            cp "core/config.example.json" "core/config.json"
        fi
    fi

    # Cek PM2
    if command -v pm2 >/dev/null 2>&1; then
        echo -e "${GREEN}[*] Menjalankan bot via PM2 (Background 24/7)...${NC}"
        pm2 start ecosystem.config.js
        pm2 save >/dev/null 2>&1
        echo -e "${GREEN}[+] Bot Coins.ph aktif via PM2!${NC}"
    else
        echo -e "${YELLOW}[!] PM2 tidak terdeteksi. Menjalankan di Native Background...${NC}"
        nohup python core/bot.py > bot.log 2>&1 &
        echo $! > "$PROJECT_ROOT/.bot.pid"
        echo -e "${GREEN}[+] Bot aktif di background (PID: $(cat .bot.pid))${NC}"
        echo "Gunakan menu [6] untuk melihat log bot."
    fi
    read -p "Tekan Enter untuk kembali ke menu..."
}

view_logs() {
    echo ""
    echo -e "${CYAN}=== 50 BARIS TERAKHIR LOG BOT ===${NC}"
    echo ""
    if command -v pm2 >/dev/null 2>&1 && pm2 jlist 2>/dev/null | grep -q '"name":"coins-bot"'; then
        pm2 logs coins-bot --lines 50 --nostream
    elif [ -f "bot.log" ]; then
        tail -n 50 bot.log
    else
        echo -e "${YELLOW}[!] Belum ada file log yang dibuat.${NC}"
    fi
    echo ""
    read -p "Tekan Enter untuk kembali ke menu..."
}

stop_bot() {
    echo ""
    echo -e "${YELLOW}[*] Menghentikan bot...${NC}"
    if command -v pm2 >/dev/null 2>&1; then
        pm2 stop coins-bot 2>/dev/null
    fi
    if [ -f "$PROJECT_ROOT/.bot.pid" ]; then
        kill $(cat "$PROJECT_ROOT/.bot.pid") 2>/dev/null
        rm -f "$PROJECT_ROOT/.bot.pid"
    fi
    pkill -f "python core/bot.py" 2>/dev/null
    echo -e "${GREEN}[+] Bot berhasil dihentikan!${NC}"
    read -p "Tekan Enter untuk kembali ke menu..."
}

setup_pm2() {
    echo ""
    echo -e "${YELLOW}[*] Menginstall NodeJS & PM2 untuk Termux...${NC}"
    pkg update -y
    pkg install -y nodejs
    npm install -g pm2
    echo -e "${GREEN}[+] PM2 berhasil diinstall! Bot dapat dijalankan 24/7 tanpa henti.${NC}"
    read -p "Tekan Enter untuk kembali ke menu..."
}

start_web_pos() {
    echo ""
    echo -e "${CYAN}[*] Menjalankan Server Web POS Coins.ph (Port 5000)...${NC}"
    LOCAL_IP=$(python -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('8.8.8.8',80)); print(s.getsockname()[0]); s.close()" 2>/dev/null || echo "IP-HP")
    echo "Akses di browser: http://$LOCAL_IP:5000/pos"
    echo "Tekan CTRL+C untuk berhenti."
    cd "$PROJECT_ROOT/core"
    python api_server.py
}

# Main Loop
while true; do
    show_menu
    read -r opt
    case "$opt" in
        1)
            echo ""
            echo "Ketik port Wireless Debugging Android Anda (misal: 38455):"
            read -p "Port ADB: " ADB_P
            adb connect "localhost:$ADB_P"
            adb devices
            read -p "Tekan Enter..."
            ;;
        2)
            echo ""
            echo "Menguji koneksi Shizuku (rish)..."
            export RISH_APPLICATION_ID="com.termux"
            rish -c "id" 2>/dev/null || sh /data/data/com.termux/files/usr/bin/rish -c "id"
            read -p "Tekan Enter..."
            ;;
        3) install_deps ;;
        4) update_token ;;
        5) start_bot ;;
        6) view_logs ;;
        7) stop_bot ;;
        8) setup_pm2 ;;
        9) start_web_pos ;;
        0)
            echo -e "${GREEN}Sampai jumpa!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Pilihan tidak valid.${NC}"
            sleep 1
            ;;
    esac
done
