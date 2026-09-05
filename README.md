# 🇵🇭 Coins.ph Dynamic QR Ph Payment Gateway, Web3 Hub & Telegram Bot

Payment Gateway mandiri, POS Kasir Web resmi berstandar nasional Filipina (**QR Ph / InstaPay**), dan **Bot Telegram Otomatisasi Multi-Role** dengan generator in-slot, auto-random merchant name engine, kalkulator kurs Bitget P2P, Web3 Multi-Network Wallet Transfer (Base USDC, BSC USDT, dan BSC USDC), Cloudflare Tunnel (`triomerak.web.id`), serta arsitektur **All-in-One PM2 Process Manager** yang aktif 24 jam non-stop bahkan saat monitor/layar mati.

---

## 🌟 Fitur Unggulan

### 1. 🚀 All-in-One Controller & PM2 24/7 Background Engine
- **Satu Launcher Terpadu (`START_SERVER.bat`)**:
  - Mengendalikan seluruh ekosistem aplikasi dalam satu kontroler interaktif:
    1. **Web Server POS & REST API** (`coins-server`)
    2. **Bot Telegram Notifikasi & Watcher** (`coins-bot`)
    3. **Cloudflare Tunnel Domain Publik** (`coins-tunnel`)
- **Aktif 24 Jam Non-Stop Saat Layar / Monitor Mati**:
  - Ditenagai **PM2 Process Manager** dan daemon background Windows.
  - Anda bebas menutup jendela terminal CMD atau mematikan monitor untuk hemat daya; seluruh server, bot, dan tunnel tetap aktif melayani transaksi 24 jam non-stop.
- **Auto-Restart & Crash Resilience**:
  - Jika terjadi gangguan koneksi internet sementara atau kendala tak terduga, PM2 otomatis me-restart proses secara cerdas (*zero-downtime auto restart*).
- **Menu Kontrol Interaktif**:
  - Jalankan background PM2, cek status realtime (`pm2 status`), streaming log langsung (`pm2 logs`), restart semua layanan, hingga mode fallback manual.

### 2. 🌐 Domain Publik & Cloudflare Tunnel (`triomerak.web.id`)
- **Akses Publik Berkecepatan Tinggi & Aman**:
  - Terhubung langsung ke Cloudflare Edge Network via Cloudflare Tunnel (`quic` protocol).
  - Akses POS Kasir publik: `https://triomerak.web.id/pos`
  - Akses Halaman Checkout / Invoice: `https://triomerak.web.id/pay/<order_id>`
- **Otomatisasi Port & IP Dinamis**:
  - Sistem otomatis mendeteksi IP LAN lokal aktif (`core/get_ip.py`) dan me-routing tunnel ke target lokal `http://<LOCAL_IP>:5000`.

### 3. 🛡️ Keamanan Multi-User & Forensic Session Isolation (Trio Merak)
- **Isolasi Sesi Anti-Bentrok**:
  - Multi-user berbasis cookie aman (`SESSION_COOKIE_HTTPONLY = True`, `SameSite = Lax`).
  - Tidak ada kebocoran data atau tumpang tindih data (*variable crosstalk*) antar sesi pengguna concurrent.
- **Pemisahan Slot Akun Merchant Per-Pengguna**:
  - Setiap pengguna memiliki slot merchant masing-masing di `users.json`.
  - Endpoint `/api/accounts`, `/api/matrix`, dan `/api/qr/image` terkunci murni pada slot milik user yang login.
- **Privasi Riwayat Order & Omzet**:
  - Pengguna hanya melihat transaksi milik tokonya sendiri di POS dan `/api/orders`. Super Admin tetap memiliki visibilitas global.
- **Proteksi UI & Engine Status**:
  - Tampilan teknis internal ("STATUS JARINGAN ENGINE", Host IP, Web3 RPC) dan modal "⚙️ Atur Kurs" tersembunyi total dari pengguna biasa, khusus untuk mode Admin.
  - Endpoint `/api/rate/set` memproteksi modifikasi kurs dengan `HTTP 403 Forbidden` bagi non-admin.
- **Pembersihan RAM Web3 (Anti-Bocor Memory)**:
  - Private key dan phrase Web3 langsung diputus dan dihapus dari memory server (`_user_wallets.pop()`) seketika pengguna menekan tombol **Logout**.

### 4. 🤖 Telegram Bot Otomatisasi (Multi-Platform: PC & Termux)
- **Role-Based Access Control (RBAC) ID-Based**:
  - Super Admin ditentukan aman via `admin_ids` pada `core/config.json`.
  - Generator token akses berdurasi (1 Hari, 3 Hari, 7 Hari, 30 Hari) via perintah `/gencode`.
- **Dynamic QR Ph Generator Langsung di Chat**:
  - Pilihan Slot Akun Coins.ph, nominal cepat (`⚡ Base`, `⚡ +0.01`, `✏️ Set Nominal`), acak nama toko otomatis, dan kirim foto barcode HD ber-badge resmi InstaPay.
  - Auto-delete barcode lama setelah pembayaran lunas atau expired.
- **Kalkulator Kurs Bitget Realtime**:
  - Kurs live Bitget P2P PHP/USDC + profit buffer dua arah instan.
- **Background Realtime Order Watcher**:
  - Background task otomatis memantau database SQLite (`payments.db`) dan mengirim notifikasi saat pembayaran lunas.
- **Reset Jaringan & Multi-App via ADB**:
  - Eksekusi atomic chained shell (Force stop, Clear cache, Airplane Mode ON/OFF, Restart Multi App).
  - Mendukung PC USB Debugging, Termux Shizuku (`rish`), Wireless ADB, dan Root (`su`).

### 5. 🇵🇭 Dynamic QR Ph Filipina (Coins.ph & InstaPay P2P)
- **Standard EMVCo & QR Ph InstaPay P2P**: Kompatibel dengan seluruh bank dan e-wallet di Filipina (Coins.ph, GCash, Maya, GrabPay, BDO, BPI, UnionBank, dll.).
- **In-Slot QR Generator Controls**: Kontrol nominal dan tombol toggle acak nama toko langsung di dalam kartu slot kasir.
- **Authentic Philippine Merchant Name Generator**: 500.000.000+ kombinasi nama toko otentik khas Filipina (Sari-Sari Store, Mini Mart, Express, Trading) sesuai standar EMVCo Tag 59.

### 6. ⚡ Web3 Multi-Network Wallet Transfer (Web & POS)
- **Multi-Jaringan Web3**: Base Network (USDC, ETH Gas) & BSC Network (USDT, USDC, BNB Gas).
- **Dual-Mode QR Barcode Scanner**: Kamera video stream, tombol foto kamera native HP (`capture="environment"`), upload file, dan paste clipboard (<kbd>Ctrl + V</kbd>) dengan backend C++ ZXing Engine (`zxing-cpp`).

---

## 📁 Struktur Direktori Bersih (Pure Engine)

```text
COINS_PAYMENT_GATEWAY/
├── START_SERVER.bat             # 🚀 All-in-One Controller (Web Server + Bot Telegram + PM2 24/7)
├── START_CLOUDFLARE_TUNNEL.bat  # 🌐 Dedicated Cloudflare Tunnel Launcher (triomerak.web.id)
├── INSTALL_REQUIREMENTS.bat     # 📦 Installer Dependensi Lengkap (Python + Node.js PM2)
├── README.md                    # 📖 Dokumentasi Lengkap Repositori
├── .gitignore                   # 🔒 Proteksi Kredensial & File Sensitif
│
├── core/                        # 📁 Mesin Utama & Modul Backend
│   ├── api_server.py            # 🌐 Flask REST API Server & Web POS Kasir
│   ├── bot.py                   # 🤖 Bot Telegram RBAC, Dynamic QR Ph & Watcher
│   ├── ecosystem.config.js      # ⚙️ Konfigurasi Multi-Proses PM2 (Server, Bot, Tunnel)
│   ├── qr_engine.py             # 🇵🇭 EMVCo / QR Ph InstaPay Payload & Image Generator
│   ├── wallet_manager.py        # 💳 Web3 Multi-Network Engine (Base & BSC)
│   ├── database.py              # 🗄️ SQLite Database Engine (payments.db)
│   ├── adb_helper.py            # ⚡ Automasi ADB (PC, Shizuku, Wireless, Root)
│   ├── get_ip.py                # 🔍 Detektor IP Dinamis Local LAN
│   ├── bin/                     # 🛠️ Binary Tools Internal
│   │   └── cloudflared.exe      # 🌐 Binary Resmi Cloudflare Tunnel (Windows x64)
│   ├── config.json              # ⚙️ Konfigurasi Privat Aktif (Gitignored)
│   ├── config.example.json      # 📄 Template Konfigurasi Publik
│   ├── users.json               # 👥 Database Profil Pengguna Multi-User (Gitignored)
│   ├── requirements.txt         # 📦 Daftar Dependensi Python
│   ├── test_system.py           # 🧪 Automated Test Suite Regresi Sistem Web
│   ├── static/                  # 🎨 Aset Web Frontend (JS, CSS)
│   └── templates/               # 🖥️ Template HTML (POS Kasir, Dashboard, Checkout)
│
├── docs/                        # 📚 Dokumentasi Proyek
│   └── README.md                # 📄 Salinan Dokumentasi
│
└── TERMUX/                      # 📁 Script Khusus Android Termux
    ├── run.sh                   # 🌐 Launcher POS Server Termux
    └── setup.sh                 # 🎛️ Menu Interaktif 10-in-1 (Bot, PM2, ADB Wifi/Shizuku, Deps, Token, POS)
```

---

## 💻 Panduan Menjalankan di PC / Windows

### 1. Menjalankan Semua Layanan Sekaligus (All-in-One 24 Jam):
Cukup double-click file:
```text
START_SERVER.bat
```
Pilih opsi **`[1]`** (atau tekan **Enter**).

Sistem akan otomatis:
1. Memulai **Web Server POS** (`coins-server`).
2. Memulai **Bot Telegram** (`coins-bot`).
3. Memulai **Cloudflare Tunnel** (`coins-tunnel`).
4. Menyimpan status proses ke daemon PM2 (`pm2 save`).
5. Membuka browser ke POS Kasir (`http://<IP-LAN>:5000/pos` dan `https://triomerak.web.id/pos`).

> [!TIP]
> **Aman Ditutup Kapan Saja**: Setelah memilih opsi `[1]`, Anda bebas menutup jendela CMD dan mematikan layar monitor. Sistem akan terus bekerja di background 24 jam non-stop.

### 2. Mengelola Layanan PM2 via Menu `START_SERVER.bat`:
- **`[2] Status & Monitor PM2`**: Melihat penggunaan memori RAM, CPU, dan status online setiap proses.
- **`[3] Log Realtime`**: Menampilkan log transaksi dan aktivitas sistem secara langsung (`pm2 logs`).
- **`[4] Restart Semua`**: Merestart server, bot, dan tunnel dalam 1 klik.
- **`[5] Stop Semua`**: Menghentikan seluruh proses di background.

---

## 📱 Panduan Lengkap Android (Termux)

Panduan instalasi mandiri dari awal (*fresh install*), konfigurasi bot, hingga menjalankan bot 24/7 di perangkat Android menggunakan **Termux**.

> [!IMPORTANT]
> **Gunakan Termux Versi Resmi**:
> Unduh aplikasi Termux dari **[F-Droid](https://f-droid.org/en/packages/com.termux/)** atau **[GitHub Releases Termux](https://github.com/termux/termux-app/releases)**.  
> ⚠️ **Jangan gunakan Termux dari Google Play Store** karena repositorinya sudah usang (*deprecated*).

### ⚡ Mode Ekspres (1 Baris Perintah Langsung Jadi):
```bash
pkg update -y && pkg install -y git python && git clone https://github.com/Imammaulidy/coins.git && cd coins && bash TERMUX/setup.sh
```

### 🎛️ Menu Interaktif Termux (`TERMUX/setup.sh`):
1. **Pilihan `[3]`**: Install Dependencies (Python + Android Tools + rish).
2. **Pilihan `[4]`**: Masukkan Token Bot Telegram & Admin ID.
3. **Pilihan `[8]`**: Setup PM2 (NodeJS & PM2 Auto-Restart di Termux).
4. **Pilihan `[5]`**: Jalankan Bot Telegram di background 24/7.
5. **Pilihan `[9]`**: Jalankan Web POS Kasir (Port 5000).

---

## 👑 Hak Akses & Keamanan RBAC (ID-Based)

1. **Super Admin**:
   - Daftarkan Telegram User ID Anda ke dalam daftar `admin_ids` pada `core/config.json`.
   - Bot otomatis mengenali Anda sebagai Super Admin secara kriptografis tanpa password atau backdoor di chat.
2. **Member / User Biasa**:
   - Minta kode akses berdurasi (1, 3, 7, atau 30 hari) ke Super Admin yang di-generate via perintah `/gencode`.
   - Ketik kode token (contoh: `COINS-3D-A1B2C3`) di chat untuk aktivasi sesi.
