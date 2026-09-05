#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
#   COINS.PH PAYMENT GATEWAY - ALL-IN-ONE TERMUX LAUNCHER & SETUP SUITE
#   Mendukung Web POS Server, Telegram Bot, & Cloudflare Tunnel (triomerak.web.id)
#   Mendukung PM2 Background 24/7, Non-Root (Wireless ADB/Shizuku) & Root
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# Buat alias lowercase termux jika berjalan di Linux case-sensitive
if [ -d "$PROJECT_ROOT/TERMUX" ] && [ ! -e "$PROJECT_ROOT/termux" ]; then
    ln -s "$PROJECT_ROOT/TERMUX" "$PROJECT_ROOT/termux" 2>/dev/null
fi

# Cegah CPU Termux masuk mode tidur di background
termux-wake-lock 2>/dev/null

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
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

banner() {
    clear
    echo -e "${CYAN}${BOLD}=================================================================${NC}"
    echo -e "${CYAN}${BOLD}    COINS.PH PAYMENT GATEWAY - TERMUX SETUP & LAUNCHER          ${NC}"
    echo -e "${CYAN}${BOLD}    Web POS Server • Bot Telegram • Cloudflare Tunnel (triomerak) ${NC}"
    echo -e "${CYAN}${BOLD}=================================================================${NC}"
    echo ""
}

show_status() {
    LOCAL_IP=$(get_local_ip)
    
    # 1. Cek Server POS
    SERVER_ON=0
    if command -v pm2 >/dev/null 2>&1 && pm2 jlist 2>/dev/null | grep -q '"name":"coins-server".*"status":"online"'; then
        SERVER_ON=1
    elif pgrep -f "api_server.py" >/dev/null 2>&1; then
        SERVER_ON=2
    fi

    # 2. Cek Telegram Bot
    BOT_ON=0
    if command -v pm2 >/dev/null 2>&1 && pm2 jlist 2>/dev/null | grep -q '"name":"coins-bot".*"status":"online"'; then
        BOT_ON=1
    elif pgrep -f "bot.py" >/dev/null 2>&1; then
        BOT_ON=2
    fi

    # 3. Cek Cloudflare Tunnel
    TUNNEL_ON=0
    if command -v pm2 >/dev/null 2>&1 && pm2 jlist 2>/dev/null | grep -q '"name":"coins-tunnel".*"status":"online"'; then
        TUNNEL_ON=1
    elif pgrep -f "cloudflared" >/dev/null 2>&1; then
        TUNNEL_ON=2
    fi

    # Tampilkan Indikator Status
    if [ $SERVER_ON -eq 1 ]; then
        echo -e "  ● SERVER WEB POS   : ${GREEN}ONLINE (PM2 24/7)${NC} -> http://${LOCAL_IP}:5000/pos"
    elif [ $SERVER_ON -eq 2 ]; then
        echo -e "  ● SERVER WEB POS   : ${GREEN}ONLINE (Native PID)${NC} -> http://${LOCAL_IP}:5000/pos"
    else
        echo -e "  ○ SERVER WEB POS   : ${RED}OFFLINE${NC}"
    fi

    if [ $BOT_ON -eq 1 ]; then
        echo -e "  ● TELEGRAM BOT     : ${GREEN}ONLINE (PM2 24/7)${NC}"
    elif [ $BOT_ON -eq 2 ]; then
        echo -e "  ● TELEGRAM BOT     : ${GREEN}ONLINE (Native PID)${NC}"
    else
        echo -e "  ○ TELEGRAM BOT     : ${RED}OFFLINE${NC}"
    fi

    if [ $TUNNEL_ON -eq 1 ]; then
        echo -e "  ● CLOUDFLARE TUNNEL: ${GREEN}ONLINE (PM2 24/7)${NC} -> https://triomerak.web.id"
    elif [ $TUNNEL_ON -eq 2 ]; then
        echo -e "  ● CLOUDFLARE TUNNEL: ${GREEN}ONLINE (Native PID)${NC} -> https://triomerak.web.id"
    else
        echo -e "  ○ CLOUDFLARE TUNNEL: ${RED}OFFLINE${NC}"
    fi

    # Status Manager
    if command -v pm2 >/dev/null 2>&1; then
        echo -e "  ★ PROCESS MANAGER  : ${CYAN}PM2 Siap (NodeJS)${NC}"
    else
        echo -e "  ★ PROCESS MANAGER  : ${YELLOW}Native Background (Install PM2 via menu [10] disarankan)${NC}"
    fi
    echo -e "${CYAN}-----------------------------------------------------------------${NC}"
}

show_menu() {
    banner
    show_status
    echo -e "${BOLD}PILIHAN EKSEKUSI & OPERASIONAL:${NC}"
    echo -e "  ${GREEN}[1]${NC} ${BOLD}JALANKAN ALL-IN-ONE (Server + Bot + Tunnel 24/7 via PM2)${NC}"
    echo -e "      ${CYAN}*Rekomendasi Utama* : 1-Klik aktifkan semua layanan di latar belakang${NC}"
    echo ""
    echo -e "  ${GREEN}[2]${NC} ${BOLD}Jalankan Server Web POS Kasir (Port 5000)${NC}"
    echo -e "      Akses POS Kasir & API Server di LAN lokal / browser"
    echo ""
    echo -e "  ${GREEN}[3]${NC} ${BOLD}Jalankan Cloudflare Tunnel (triomerak.web.id)${NC}"
    echo -e "      Hubungkan server lokal Termux ke domain publik resmi"
    echo ""
    echo -e "  ${GREEN}[4]${NC} ${BOLD}Jalankan Bot Telegram Saja (PM2 / Background)${NC}"
    echo -e "      Jalankan engine auto transfer & approval bot"
    echo ""
    echo -e "  ${CYAN}[5]${NC} ${BOLD}Lihat Log Realtime (Semua / Server / Bot / Tunnel)${NC}"
    echo -e "      Monitoring log output langsung dari Termux"
    echo ""
    echo -e "  ${RED}[6]${NC} ${BOLD}Stop Layanan (Semua / Pilihan Tertentu)${NC}"
    echo -e "      Hentikan proses yang berjalan dengan aman"
    echo ""
    echo -e "${BOLD}PENGATURAN & KONFIGURASI:${NC}"
    echo -e "  ${YELLOW}[7]${NC} ${BOLD}Pengaturan Cloudflare Tunnel (triomerak.web.id)${NC}"
    echo -e "      Input Token / Pasang cloudflared ARM64 / Login / Quick Tunnel"
    echo ""
    echo -e "  ${YELLOW}[8]${NC} ${BOLD}Masukan atau Update Token Bot & Admin ID${NC}"
    echo -e "      Input Token Bot & User ID Admin, simpan ke core/config.json"
    echo ""
    echo -e "  ${BLUE}[9]${NC} ${BOLD}Mode Automasi Android (ADB Wifi / Shizuku rish)${NC}"
    echo -e "      Pairing & Connect port ADB nirkabel / Test rish Shizuku"
    echo ""
    echo -e "  ${MAGENTA}[10]${NC} ${BOLD}Setup Lengkap Dependensi Termux${NC}"
    echo -e "       Install Python, NodeJS, PM2, build tools, & cloudflared ARM64"
    echo ""
    echo -e "  ${RED}[0]${NC} Keluar"
    echo ""
    echo -ne "Pilihan Anda [0-10]: "
}

ensure_config() {
    if [ ! -f "core/config.json" ] && [ -f "core/config.example.json" ]; then
        cp "core/config.example.json" "core/config.json"
        echo -e "${GREEN}[+] core/config.json berhasil dibuat dari template config.example.json${NC}"
    fi
}

install_cloudflared() {
    echo ""
    echo -e "${YELLOW}[*] Memeriksa instalasi binary cloudflared untuk Termux/Android...${NC}"
    CF_EXISTING=$(get_cf_bin)
    if [ -n "$CF_EXISTING" ]; then
        echo -e "${GREEN}[+] cloudflared sudah terpasang: $($CF_EXISTING --version 2>/dev/null | head -n 1)${NC}"
        return 0
    fi

    ARCH=$(uname -m)
    CF_URL=""
    case "$ARCH" in
        aarch64|arm64)
            CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
            ;;
        arm|armv7l|armhf)
            CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm"
            ;;
        x86_64|amd64)
            CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
            ;;
        *)
            CF_URL="https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
            ;;
    esac

    echo -e "${CYAN}[*] Mengunduh binary cloudflared resmi Cloudflare ($ARCH)...${NC}"
    mkdir -p "$PROJECT_ROOT/core/bin"
    TARGET_BIN="$PROJECT_ROOT/core/bin/cloudflared"
    
    curl -L --progress-bar "$CF_URL" -o "$TARGET_BIN"
    if [ -f "$TARGET_BIN" ] && [ -s "$TARGET_BIN" ]; then
        chmod +x "$TARGET_BIN"
        ln -sf "$TARGET_BIN" "$PREFIX/bin/cloudflared" 2>/dev/null
        chmod +x "$PREFIX/bin/cloudflared" 2>/dev/null
        echo -e "${GREEN}[+] cloudflared ARM64 berhasil dipasang di $TARGET_BIN & $PREFIX/bin/cloudflared!${NC}"
        "$TARGET_BIN" --version 2>/dev/null | head -n 1
        return 0
    else
        echo -e "${RED}[-] Gagal mengunduh cloudflared.${NC}"
        return 1
    fi
}

start_all_in_one() {
    echo ""
    echo -e "${CYAN}${BOLD}=================================================================${NC}"
    echo -e "${CYAN}${BOLD}     MENJALANKAN ALL-IN-ONE (SERVER + BOT + CLOUDFLARE TUNNEL)  ${NC}"
    echo -e "${CYAN}${BOLD}=================================================================${NC}"
    echo ""
    ensure_config

    CF_BIN=$(get_cf_bin)
    if [ -z "$CF_BIN" ]; then
        echo -e "${YELLOW}[!] Binary cloudflared belum terpasang. Memulai unduhan otomatis...${NC}"
        install_cloudflared
        CF_BIN=$(get_cf_bin)
    fi

    LOCAL_IP=$(get_local_ip)

    if command -v pm2 >/dev/null 2>&1; then
        echo -e "${GREEN}[*] Meluncurkan seluruh layanan via PM2 Process Manager (24/7 Auto-Restart)...${NC}"
        pm2 start core/ecosystem.config.js
        pm2 save >/dev/null 2>&1
        echo ""
        echo -e "${GREEN}${BOLD}[+] SEMUA LAYANAN BERHASIL DIAKTIFKAN DI BACKGROUND!${NC}"
        echo -e "    ● Web POS Server  : http://${LOCAL_IP}:5000/pos"
        echo -e "    ● Dashboard Admin : http://${LOCAL_IP}:5000/dashboard"
        echo -e "    ● Publik Domain   : https://triomerak.web.id/pos"
        echo -e "    ● Telegram Bot    : Aktif (Auto-Approval & P2P Monitoring)"
        echo ""
        echo -e "Gunakan menu [5] untuk melihat log realtime, atau [6] untuk menghentikan."
    else
        echo -e "${YELLOW}[!] PM2 belum diinstall. Menjalankan di Native Background (nohup)...${NC}"
        # Jalankan server
        nohup python core/api_server.py > server.log 2>&1 &
        echo $! > "$PROJECT_ROOT/.server.pid"
        # Jalankan bot
        nohup python core/bot.py > bot.log 2>&1 &
        echo $! > "$PROJECT_ROOT/.bot.pid"
        # Jalankan tunnel jika ada binary
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
    read -p "Tekan Enter untuk kembali ke menu..."
}

start_server() {
    echo ""
    echo -e "${CYAN}=== JALANKAN SERVER WEB POS KASIR (PORT 5000) ===${NC}"
    echo "  [1] Jalankan di Background 24/7 (PM2 Auto-Restart)"
    echo "  [2] Jalankan di Foreground (Tampilan Log Langsung di Layar)"
    echo "  [0] Kembali"
    echo ""
    read -p "Pilihan Anda [1/2/0]: " s_opt
    case "$s_opt" in
        1)
            if command -v pm2 >/dev/null 2>&1; then
                pm2 start core/ecosystem.config.js --only coins-server
                pm2 save >/dev/null 2>&1
                LOCAL_IP=$(get_local_ip)
                echo -e "${GREEN}[+] Server Web POS aktif via PM2 di http://${LOCAL_IP}:5000/pos${NC}"
            else
                nohup python core/api_server.py > server.log 2>&1 &
                echo $! > "$PROJECT_ROOT/.server.pid"
                echo -e "${GREEN}[+] Server aktif di background (PID: $(cat .server.pid))${NC}"
            fi
            read -p "Tekan Enter..."
            ;;
        2)
            echo ""
            LOCAL_IP=$(get_local_ip)
            echo -e "${GREEN}[*] Memulai server di foreground. Tekan CTRL+C untuk berhenti.${NC}"
            echo -e "Akses lokal: http://${LOCAL_IP}:5000/pos"
            echo ""
            cd "$PROJECT_ROOT/core"
            python api_server.py
            cd "$PROJECT_ROOT"
            ;;
        *) return ;;
    esac
}

start_tunnel() {
    echo ""
    echo -e "${CYAN}=== JALANKAN CLOUDFLARE TUNNEL (triomerak.web.id) ===${NC}"
    CF_BIN=$(get_cf_bin)
    if [ -z "$CF_BIN" ]; then
        echo -e "${YELLOW}[!] Binary cloudflared belum terpasang. Memulai unduhan otomatis...${NC}"
        install_cloudflared
        CF_BIN=$(get_cf_bin)
        if [ -z "$CF_BIN" ]; then
            echo -e "${RED}[-] Gagal memasang cloudflared. Silakan gunakan menu [7] untuk instalasi manual.${NC}"
            read -p "Tekan Enter..."
            return
        fi
    fi

    LOCAL_IP=$(get_local_ip)
    echo "  [1] Jalankan di Background 24/7 (PM2 Auto-Restart)"
    echo "  [2] Jalankan di Foreground (Tampilan Terminal Terbuka)"
    echo "  [3] Jalankan Quick Tunnel Gratis (*.trycloudflare.com)"
    echo "  [0] Kembali"
    echo ""
    read -p "Pilihan Anda [1/2/3/0]: " t_opt
    case "$t_opt" in
        1)
            if command -v pm2 >/dev/null 2>&1; then
                pm2 start core/ecosystem.config.js --only coins-tunnel
                pm2 save >/dev/null 2>&1
                echo -e "${GREEN}[+] Cloudflare Tunnel aktif via PM2 -> https://triomerak.web.id${NC}"
            else
                if [ -f "$PROJECT_ROOT/cloudflare_token.txt" ]; then
                    CF_TOKEN=$(cat "$PROJECT_ROOT/cloudflare_token.txt" | tr -d '[:space:]')
                    nohup "$CF_BIN" tunnel run --token "$CF_TOKEN" > tunnel.log 2>&1 &
                    echo $! > "$PROJECT_ROOT/.tunnel.pid"
                else
                    nohup "$CF_BIN" tunnel run --url "http://${LOCAL_IP}:5000" triomerak > tunnel.log 2>&1 &
                    echo $! > "$PROJECT_ROOT/.tunnel.pid"
                fi
                echo -e "${GREEN}[+] Tunnel aktif di background (PID: $(cat .tunnel.pid))${NC}"
            fi
            read -p "Tekan Enter..."
            ;;
        2)
            echo ""
            echo -e "${CYAN}[*] Menghubungkan tunnel triomerak.web.id di foreground...${NC}"
            echo -e "${YELLOW}[INFO] Tekan CTRL+C untuk menghentikan tunnel.${NC}"
            echo ""
            if [ -f "$PROJECT_ROOT/cloudflare_token.txt" ]; then
                CF_TOKEN=$(cat "$PROJECT_ROOT/cloudflare_token.txt" | tr -d '[:space:]')
                "$CF_BIN" tunnel run --token "$CF_TOKEN"
            elif [ -f "$HOME/.cloudflared/cert.pem" ]; then
                "$CF_BIN" tunnel run --url "http://${LOCAL_IP}:5000" triomerak
            else
                echo -e "${YELLOW}[!] Belum ada token atau sertifikat Cloudflare tersimpan.${NC}"
                echo "Silakan input token melalui Menu [7] terlebih dahulu."
                read -p "Tekan Enter..."
            fi
            ;;
        3)
            echo ""
            echo -e "${CYAN}[*] Menghubungkan ke Cloudflare Quick Tunnel (*.trycloudflare.com)...${NC}"
            echo -e "${YELLOW}[INFO] URL publik acak akan muncul di bawah. Tekan CTRL+C untuk berhenti.${NC}"
            echo ""
            "$CF_BIN" tunnel --url "http://${LOCAL_IP}:5000"
            ;;
        *) return ;;
    esac
}

start_bot() {
    echo ""
    echo -e "${CYAN}=== JALANKAN BOT TELEGRAM COINS.PH ===${NC}"
    ensure_config
    echo "  [1] Jalankan di Background 24/7 (PM2 Auto-Restart)"
    echo "  [2] Jalankan di Foreground (Lihat Output Langsung)"
    echo "  [0] Kembali"
    echo ""
    read -p "Pilihan Anda [1/2/0]: " b_opt
    case "$b_opt" in
        1)
            if command -v pm2 >/dev/null 2>&1; then
                pm2 start core/ecosystem.config.js --only coins-bot
                pm2 save >/dev/null 2>&1
                echo -e "${GREEN}[+] Bot Telegram aktif via PM2 24/7!${NC}"
            else
                nohup python core/bot.py > bot.log 2>&1 &
                echo $! > "$PROJECT_ROOT/.bot.pid"
                echo -e "${GREEN}[+] Bot aktif di background (PID: $(cat .bot.pid))${NC}"
            fi
            read -p "Tekan Enter..."
            ;;
        2)
            echo ""
            echo -e "${GREEN}[*] Memulai bot di foreground. Tekan CTRL+C untuk berhenti.${NC}"
            echo ""
            cd "$PROJECT_ROOT/core"
            python bot.py
            cd "$PROJECT_ROOT"
            ;;
        *) return ;;
    esac
}

view_logs() {
    echo ""
    echo -e "${CYAN}=== MONITORING LOG REALTIME ===${NC}"
    echo "  [1] Log Semua Layanan Bersama (PM2 logs)"
    echo "  [2] Log Server Web POS (coins-server)"
    echo "  [3] Log Bot Telegram (coins-bot)"
    echo "  [4] Log Cloudflare Tunnel (coins-tunnel)"
    echo "  [0] Kembali"
    echo ""
    read -p "Pilihan Anda [1-4/0]: " l_opt
    case "$l_opt" in
        1)
            if command -v pm2 >/dev/null 2>&1; then
                pm2 logs --lines 40
            else
                tail -n 30 server.log bot.log tunnel.log 2>/dev/null
                read -p "Tekan Enter..."
            fi
            ;;
        2)
            if command -v pm2 >/dev/null 2>&1 && pm2 jlist 2>/dev/null | grep -q '"name":"coins-server"'; then
                pm2 logs coins-server --lines 50
            elif [ -f "server.log" ]; then
                tail -n 50 server.log
                read -p "Tekan Enter..."
            else
                echo -e "${YELLOW}[!] Log server belum tersedia.${NC}"
                read -p "Tekan Enter..."
            fi
            ;;
        3)
            if command -v pm2 >/dev/null 2>&1 && pm2 jlist 2>/dev/null | grep -q '"name":"coins-bot"'; then
                pm2 logs coins-bot --lines 50
            elif [ -f "bot.log" ]; then
                tail -n 50 bot.log
                read -p "Tekan Enter..."
            else
                echo -e "${YELLOW}[!] Log bot belum tersedia.${NC}"
                read -p "Tekan Enter..."
            fi
            ;;
        4)
            if command -v pm2 >/dev/null 2>&1 && pm2 jlist 2>/dev/null | grep -q '"name":"coins-tunnel"'; then
                pm2 logs coins-tunnel --lines 50
            elif [ -f "tunnel.log" ]; then
                tail -n 50 tunnel.log
                read -p "Tekan Enter..."
            else
                echo -e "${YELLOW}[!] Log tunnel belum tersedia.${NC}"
                read -p "Tekan Enter..."
            fi
            ;;
        *) return ;;
    esac
}

stop_services() {
    echo ""
    echo -e "${YELLOW}=== PENGHENTIAN LAYANAN ===${NC}"
    echo "  [1] Hentikan SEMUA Layanan (Server + Bot + Tunnel)"
    echo "  [2] Hentikan Server Web POS Saja"
    echo "  [3] Hentikan Bot Telegram Saja"
    echo "  [4] Hentikan Cloudflare Tunnel Saja"
    echo "  [0] Kembali"
    echo ""
    read -p "Pilihan Anda [1-4/0]: " stop_opt
    case "$stop_opt" in
        1)
            if command -v pm2 >/dev/null 2>&1; then
                pm2 stop all 2>/dev/null
                pm2 save >/dev/null 2>&1
            fi
            pkill -f "api_server.py" 2>/dev/null
            pkill -f "bot.py" 2>/dev/null
            pkill -f "cloudflared" 2>/dev/null
            rm -f "$PROJECT_ROOT/.server.pid" "$PROJECT_ROOT/.bot.pid" "$PROJECT_ROOT/.tunnel.pid" 2>/dev/null
            echo -e "${GREEN}[+] Semua layanan berhasil dihentikan!${NC}"
            read -p "Tekan Enter..."
            ;;
        2)
            if command -v pm2 >/dev/null 2>&1; then
                pm2 stop coins-server 2>/dev/null
            fi
            pkill -f "api_server.py" 2>/dev/null
            rm -f "$PROJECT_ROOT/.server.pid" 2>/dev/null
            echo -e "${GREEN}[+] Server Web POS berhasil dihentikan!${NC}"
            read -p "Tekan Enter..."
            ;;
        3)
            if command -v pm2 >/dev/null 2>&1; then
                pm2 stop coins-bot 2>/dev/null
            fi
            pkill -f "bot.py" 2>/dev/null
            rm -f "$PROJECT_ROOT/.bot.pid" 2>/dev/null
            echo -e "${GREEN}[+] Bot Telegram berhasil dihentikan!${NC}"
            read -p "Tekan Enter..."
            ;;
        4)
            if command -v pm2 >/dev/null 2>&1; then
                pm2 stop coins-tunnel 2>/dev/null
            fi
            pkill -f "cloudflared" 2>/dev/null
            rm -f "$PROJECT_ROOT/.tunnel.pid" 2>/dev/null
            echo -e "${GREEN}[+] Cloudflare Tunnel berhasil dihentikan!${NC}"
            read -p "Tekan Enter..."
            ;;
        *) return ;;
    esac
}

config_cloudflare() {
    while true; do
        clear
        echo -e "${CYAN}${BOLD}=================================================================${NC}"
        echo -e "${CYAN}${BOLD}       PENGATURAN CLOUDFLARE TUNNEL (triomerak.web.id)          ${NC}"
        echo -e "${CYAN}${BOLD}=================================================================${NC}"
        echo ""
        CF_BIN=$(get_cf_bin)
        if [ -n "$CF_BIN" ]; then
            echo -e "  ● Binary cloudflared : ${GREEN}TERPASANG${NC} ($CF_BIN)"
        else
            echo -e "  ● Binary cloudflared : ${RED}BELUM TERPASANG${NC}"
        fi

        if [ -f "$PROJECT_ROOT/cloudflare_token.txt" ] && [ -s "$PROJECT_ROOT/cloudflare_token.txt" ]; then
            TOKEN_PREVIEW=$(cut -c 1-15 "$PROJECT_ROOT/cloudflare_token.txt")...
            echo -e "  ● Token Zero Trust   : ${GREEN}TERSIMPAN${NC} ($TOKEN_PREVIEW)"
        elif [ -f "$HOME/.cloudflared/cert.pem" ]; then
            echo -e "  ● Status Login       : ${GREEN}TERHUBUNG VIA CERT (cert.pem)${NC}"
        else
            echo -e "  ● Status Konfigurasi : ${YELLOW}BELUM DIKONFIGURASI${NC}"
        fi
        echo ""
        echo "Pilih opsi:"
        echo "  [1] Input / Ganti Token Cloudflare Zero Trust Manual"
        echo "  [2] Unduh / Pasang Binary cloudflared ARM64 Otomatis"
        echo "  [3] Login Cloudflare via Browser (cloudflared tunnel login)"
        echo "  [4] Uji Coba Quick Tunnel Gratis (*.trycloudflare.com)"
        echo "  [5] Hapus Token Tersimpan"
        echo "  [0] Kembali ke Menu Utama"
        echo ""
        read -p "Pilihan Anda [0-5]: " cf_opt
        case "$cf_opt" in
            1)
                echo ""
                echo -e "${CYAN}=== INPUT TOKEN CLOUDFLARE TUNNEL ===${NC}"
                echo "Salin Token dari dashboard Cloudflare Zero Trust (Tunnels)."
                echo "(Jika Anda meng-copy seluruh baris perintah 'cloudflared tunnel run --token ...',"
                echo " sistem akan otomatis mengekstrak token intinya saja)."
                echo ""
                read -p "Masukkan Token: " RAW_TOKEN
                if [ -z "$RAW_TOKEN" ]; then
                    echo -e "${RED}[-] Token tidak boleh kosong!${NC}"
                else
                    CLEAN_TOKEN=$(echo "$RAW_TOKEN" | sed -e 's/.*--token[ =]*//' -e 's/^[ \t]*//' -e 's/[ \t]*$//' -e 's/["'\'']//g')
                    echo "$CLEAN_TOKEN" > "$PROJECT_ROOT/cloudflare_token.txt"
                    echo -e "${GREEN}[+] Token berhasil disimpan ke cloudflare_token.txt!${NC}"
                fi
                read -p "Tekan Enter..."
                ;;
            2)
                install_cloudflared
                read -p "Tekan Enter..."
                ;;
            3)
                CF_BIN=$(get_cf_bin)
                if [ -z "$CF_BIN" ]; then
                    install_cloudflared
                    CF_BIN=$(get_cf_bin)
                fi
                echo ""
                echo -e "${CYAN}[*] Membuka URL otorisasi Cloudflare via browser...${NC}"
                "$CF_BIN" tunnel login
                if [ -f "$HOME/.cloudflared/cert.pem" ]; then
                    echo -e "${GREEN}[+] Login Cloudflare berhasil! cert.pem aktif.${NC}"
                    "$CF_BIN" tunnel create triomerak 2>/dev/null
                    "$CF_BIN" tunnel route dns -f triomerak triomerak.web.id 2>/dev/null
                    "$CF_BIN" tunnel route dns -f triomerak www.triomerak.web.id 2>/dev/null
                    echo -e "${GREEN}[+] Domain triomerak.web.id berhasil di-route ke tunnel!${NC}"
                fi
                read -p "Tekan Enter..."
                ;;
            4)
                CF_BIN=$(get_cf_bin)
                if [ -z "$CF_BIN" ]; then
                    install_cloudflared
                    CF_BIN=$(get_cf_bin)
                fi
                LOCAL_IP=$(get_local_ip)
                echo ""
                echo -e "${CYAN}[*] Menjalankan Quick Tunnel... Tekan CTRL+C untuk berhenti.${NC}"
                "$CF_BIN" tunnel --url "http://${LOCAL_IP}:5000"
                read -p "Tekan Enter..."
                ;;
            5)
                rm -f "$PROJECT_ROOT/cloudflare_token.txt"
                echo -e "${GREEN}[+] cloudflare_token.txt berhasil dihapus.${NC}"
                read -p "Tekan Enter..."
                ;;
            0) return ;;
            *) ;;
        esac
    done
}

update_token() {
    echo ""
    echo -e "${CYAN}=== INPUT / UPDATE TOKEN BOT & ADMIN TELEGRAM ===${NC}"
    echo "1. Dapatkan token bot dari @BotFather di Telegram."
    echo "2. Dapatkan Telegram User ID Anda dari bot (ketik /start) atau @userinfobot."
    echo ""
    read -p "Masukkan Bot Token Telegram: " NEW_TOKEN
    NEW_TOKEN=$(echo "$NEW_TOKEN" | tr -d '[:space:]')
    
    if [ -z "$NEW_TOKEN" ]; then
        echo -e "${RED}[-] Token tidak boleh kosong!${NC}"
        read -p "Tekan Enter untuk kembali..."
        return
    fi

    read -p "Masukkan Telegram User ID Admin (opsional, contoh: 1234567890): " NEW_ADMIN_ID
    NEW_ADMIN_ID=$(echo "$NEW_ADMIN_ID" | tr -d '[:space:]')

    python -c "
import json, os
cfg_file = 'core/config.json'
if not os.path.exists(cfg_file) and os.path.exists('core/config.example.json'):
    import shutil; shutil.copyfile('core/config.example.json', cfg_file)
with open(cfg_file, 'r', encoding='utf-8') as f:
    cfg = json.load(f)
cfg.setdefault('telegram', {})['bot_token'] = '$NEW_TOKEN'
admin_id_str = '$NEW_ADMIN_ID'
if admin_id_str.isdigit():
    admin_id_int = int(admin_id_str)
    admin_ids = cfg.setdefault('telegram', {}).setdefault('admin_ids', [])
    if admin_id_int not in admin_ids:
        admin_ids.append(admin_id_int)
with open(cfg_file, 'w', encoding='utf-8') as f:
    json.dump(cfg, f, indent=2)
print('Konfigurasi token & admin ID berhasil disimpan!')
"
    echo -e "${GREEN}[+] Token bot Telegram & Admin ID berhasil disimpan ke core/config.json!${NC}"
    read -p "Tekan Enter untuk kembali ke menu..."
}

adb_wifi_menu() {
    echo ""
    echo -e "${CYAN}=== MODE ADB WIFI (WIRELESS DEBUGGING) ===${NC}"
    echo "1. Aktifkan Opsi Pengembang & Wireless Debugging di Setelan HP Android."
    echo "2. Masukkan alamat IP & Port Pairing jika belum berpasangan."
    echo ""
    read -p "Ketik Port Connect Wireless Debugging (misal: 38455): " ADB_P
    if [ -n "$ADB_P" ]; then
        adb connect "localhost:$ADB_P"
        adb devices
    fi
    read -p "Tekan Enter untuk kembali..."
}

adb_shizuku_menu() {
    echo ""
    echo -e "${CYAN}=== MODE ADB SHIZUKU (RISH) ===${NC}"
    echo "Menguji koneksi Shizuku via rish (berjalan pada Data Seluler murni)..."
    export RISH_APPLICATION_ID="com.termux"
    if rish -c "id" 2>/dev/null || sh /data/data/com.termux/files/usr/bin/rish -c "id" 2>/dev/null; then
        echo -e "${GREEN}[+] Shizuku rish terhubung dengan sukses!${NC}"
    else
        echo -e "${YELLOW}[!] Gagal terhubung ke Shizuku. Pastikan aplikasi Shizuku aktif dan beri izin Termux.${NC}"
    fi
    read -p "Tekan Enter untuk kembali..."
}

install_all_deps() {
    echo ""
    echo -e "${YELLOW}${BOLD}=================================================================${NC}"
    echo -e "${YELLOW}${BOLD}       SETUP LENGKAP DEPENDENSI SISTEM TERMUX (ALL-IN-ONE)       ${NC}"
    echo -e "${YELLOW}${BOLD}=================================================================${NC}"
    echo ""
    echo -e "${CYAN}[1/5] Memperbarui repositori paket Termux...${NC}"
    pkg update -y
    
    echo ""
    echo -e "${CYAN}[2/5] Menginstall paket dasar, Python, NodeJS, build tools...${NC}"
    pkg install -y python python-pip git android-tools clang libffi openssl make curl libjpeg-turbo libpng freetype openjpeg zlib nodejs
    pkg install -y python-pillow 2>/dev/null

    echo ""
    echo -e "${CYAN}[3/5] Menginstall dependensi Python dari core/requirements.txt...${NC}"
    pip install -r core/requirements.txt --prefer-binary --no-warn-script-location

    echo ""
    echo -e "${CYAN}[4/5] Memasang PM2 Process Manager secara global via NPM...${NC}"
    npm install -g pm2

    echo ""
    echo -e "${CYAN}[5/5] Memeriksa & memasang rish helper & cloudflared ARM64...${NC}"
    RISH_BIN="$PREFIX/bin/rish"
    if [ ! -f "$RISH_BIN" ]; then
        curl -sL "https://raw.githubusercontent.com/RikkaApps/Shizuku-API/master/rish/rish" -o "$RISH_BIN" 2>/dev/null
        chmod +x "$RISH_BIN" 2>/dev/null
    fi
    install_cloudflared

    echo ""
    echo -e "${GREEN}${BOLD}[+] SEMUA DEPENDENSI TERMUX TELAH BERHASIL DIPASANG DENGAN SEMPURNA!${NC}"
    echo "Kini Anda siap menjalankan sistem All-in-One via Menu [1]."
    read -p "Tekan Enter untuk kembali ke menu..."
}

# Main Loop
while true; do
    show_menu
    read -r opt
    case "$opt" in
        1) start_all_in_one ;;
        2) start_server ;;
        3) start_tunnel ;;
        4) start_bot ;;
        5) view_logs ;;
        6) stop_services ;;
        7) config_cloudflare ;;
        8) update_token ;;
        9)
            echo ""
            echo "  [1] ADB Wifi (Wireless Debugging)"
            echo "  [2] ADB Shizuku (rish)"
            echo "  [0] Kembali"
            read -p "Pilihan: " adb_opt
            if [ "$adb_opt" = "1" ]; then
                adb_wifi_menu
            elif [ "$adb_opt" = "2" ]; then
                adb_shizuku_menu
            fi
            ;;
        10) install_all_deps ;;
        0)
            echo ""
            echo -e "${GREEN}Terima kasih telah menggunakan Coins.ph Gateway. Sampai jumpa!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Pilihan tidak valid.${NC}"
            sleep 1
            ;;
    esac
done

