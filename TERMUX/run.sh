#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
#   COINS.PH PAYMENT GATEWAY - SMART QUICK LAUNCHER (TERMUX / ANDROID)
#   Jalankan: bash run.sh [--all | --server | --tunnel | --bot | --stop | --menu]
# ==============================================================================

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

get_local_ip() {
    python -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('8.8.8.8',80)); print(s.getsockname()[0]); s.close()" 2>/dev/null || echo "127.0.0.1"
}

get_cf_bin() {
    if command -v cloudflared >/dev/null 2>&1; then
        echo "cloudflared"
    elif [ -x "$PREFIX/bin/cloudflared" ]; then
        echo "$PREFIX/bin/cloudflared"
    elif [ -x "$PROJECT_ROOT/core/bin/cloudflared" ]; then
        echo "$PROJECT_ROOT/core/bin/cloudflared"
    else
        echo ""
    fi
}

start_all() {
    echo ""
    echo -e "${CYAN}${BOLD}=================================================================${NC}"
    echo -e "${CYAN}${BOLD}    MEMULAI ALL-IN-ONE (SERVER + BOT + CLOUDFLARE TUNNEL)       ${NC}"
    echo -e "${CYAN}${BOLD}=================================================================${NC}"
    echo ""
    LOCAL_IP=$(get_local_ip)
    
    if command -v pm2 >/dev/null 2>&1; then
        echo -e "${GREEN}[*] Menjalankan via PM2 Process Manager (Background 24/7)...${NC}"
        pm2 start core/ecosystem.config.js
        pm2 save >/dev/null 2>&1
        echo ""
        echo -e "${GREEN}${BOLD}[+] SEMUA LAYANAN AKTIF BERJALAN DI LATAR BELAKANG!${NC}"
        echo -e "    ● Web POS Server  : http://${LOCAL_IP}:5000/pos"
        echo -e "    ● Publik Domain   : https://triomerak.web.id/pos"
        echo -e "    ● Dashboard Admin : http://${LOCAL_IP}:5000/dashboard"
        echo -e "    ● Telegram Bot    : Aktif (Auto-Approval P2P)"
        echo ""
        echo -e "Cek log via: ${CYAN}pm2 logs${NC} atau ${CYAN}bash TERMUX/setup.sh${NC}"
    else
        echo -e "${YELLOW}[*] PM2 tidak terdeteksi. Menjalankan di Native Background...${NC}"
        nohup python core/api_server.py > server.log 2>&1 &
        echo $! > "$PROJECT_ROOT/.server.pid"
        nohup python core/bot.py > bot.log 2>&1 &
        echo $! > "$PROJECT_ROOT/.bot.pid"
        CF_BIN=$(get_cf_bin)
        if [ -n "$CF_BIN" ]; then
            if [ -f "$PROJECT_ROOT/cloudflare_token.txt" ]; then
                CF_TOKEN=$(cat "$PROJECT_ROOT/cloudflare_token.txt" | tr -d '[:space:]')
                nohup "$CF_BIN" tunnel run --token "$CF_TOKEN" > tunnel.log 2>&1 &
                echo $! > "$PROJECT_ROOT/.tunnel.pid"
            else
                nohup "$CF_BIN" tunnel run --url "http://${LOCAL_IP}:5000" triomerak > tunnel.log 2>&1 &
                echo $! > "$PROJECT_ROOT/.tunnel.pid"
            fi
        fi
        echo -e "${GREEN}[+] Server, Bot, & Tunnel aktif di latar belakang (Native PID)!${NC}"
    fi
    echo ""
}

start_server_fg() {
    LOCAL_IP=$(get_local_ip)
    echo ""
    echo -e "${CYAN}[*] Menjalankan Web POS Server (Port 5000) di foreground...${NC}"
    echo -e "    Akses: http://${LOCAL_IP}:5000/pos"
    echo -e "    Tekan CTRL+C untuk berhenti."
    echo ""
    cd "$PROJECT_ROOT/core"
    python api_server.py
}

start_tunnel_fg() {
    CF_BIN=$(get_cf_bin)
    if [ -z "$CF_BIN" ]; then
        echo -e "${RED}[-] cloudflared belum terpasang. Jalankan: bash TERMUX/setup.sh (Menu [7] atau [10])${NC}"
        exit 1
    fi
    LOCAL_IP=$(get_local_ip)
    echo ""
    echo -e "${CYAN}[*] Menjalankan Cloudflare Tunnel ke triomerak.web.id...${NC}"
    echo -e "    Tekan CTRL+C untuk berhenti."
    echo ""
    if [ -f "$PROJECT_ROOT/cloudflare_token.txt" ]; then
        CF_TOKEN=$(cat "$PROJECT_ROOT/cloudflare_token.txt" | tr -d '[:space:]')
        "$CF_BIN" tunnel run --token "$CF_TOKEN"
    elif [ -f "$HOME/.cloudflared/cert.pem" ]; then
        "$CF_BIN" tunnel run --url "http://${LOCAL_IP}:5000" triomerak
    else
        echo -e "${YELLOW}[!] Belum ada token tersimpan. Menjalankan quick tunnel...${NC}"
        "$CF_BIN" tunnel --url "http://${LOCAL_IP}:5000"
    fi
}

stop_all() {
    echo ""
    echo -e "${YELLOW}[*] Menghentikan seluruh layanan...${NC}"
    if command -v pm2 >/dev/null 2>&1; then
        pm2 stop all 2>/dev/null
        pm2 save >/dev/null 2>&1
    fi
    pkill -f "api_server.py" 2>/dev/null
    pkill -f "bot.py" 2>/dev/null
    pkill -f "cloudflared" 2>/dev/null
    rm -f "$PROJECT_ROOT/.server.pid" "$PROJECT_ROOT/.bot.pid" "$PROJECT_ROOT/.tunnel.pid" 2>/dev/null
    echo -e "${GREEN}[+] Seluruh layanan berhasil dihentikan!${NC}"
    echo ""
}

# Cek argumen CLI
case "$1" in
    --all)
        start_all
        exit 0
        ;;
    --server)
        start_server_fg
        exit 0
        ;;
    --tunnel)
        start_tunnel_fg
        exit 0
        ;;
    --bot)
        cd "$PROJECT_ROOT/core" && python bot.py
        exit 0
        ;;
    --stop)
        stop_all
        exit 0
        ;;
    --menu)
        bash "$SCRIPT_DIR/setup.sh"
        exit 0
        ;;
esac

# Tampilan Menu Cepat Interaktif
clear
echo -e "${CYAN}${BOLD}=================================================================${NC}"
echo -e "${CYAN}${BOLD}     COINS.PH PAYMENT GATEWAY - SMART QUICK LAUNCHER (TERMUX)   ${NC}"
echo -e "${CYAN}${BOLD}=================================================================${NC}"
echo ""
echo -e "  ${GREEN}[1]${NC} ${BOLD}Jalankan ALL-IN-ONE (Server + Bot + Tunnel 24/7 PM2)${NC} [Default]"
echo -e "  ${GREEN}[2]${NC} Jalankan Web Server Saja (Port 5000 Foreground)"
echo -e "  ${GREEN}[3]${NC} Jalankan Cloudflare Tunnel Saja (triomerak.web.id Foreground)"
echo -e "  ${RED}[4]${NC} Stop Semua Layanan Aktif"
echo -e "  ${YELLOW}[5]${NC} Buka Menu Setup & Konfigurasi Lengkap (setup.sh)"
echo -e "  ${RED}[0]${NC} Batal / Keluar"
echo ""
read -p "Pilihan Anda [1-5/0, Default: 1]: " choice
choice=${choice:-1}

case "$choice" in
    1) start_all ;;
    2) start_server_fg ;;
    3) start_tunnel_fg ;;
    4) stop_all ;;
    5) bash "$SCRIPT_DIR/setup.sh" ;;
    0) echo "Keluar." ;;
    *) echo "Pilihan tidak valid." ;;
esac
