# 🇵🇭 Coins.ph Dynamic QR Ph Payment Gateway, Web3 Hub & Telegram Bot

Payment Gateway mandiri, POS Kasir Web resmi berstandar nasional Filipina (**QR Ph / InstaPay**), dan **Bot Telegram Otomatisasi Multi-Role** dengan generator in-slot, auto-random merchant name engine, kalkulator kurs Bitget P2P, Web3 Multi-Network Wallet Transfer (Base USDC, BSC USDT, dan BSC USDC), serta otomasi reset jaringan ADB.

---

## 🌟 Fitur Unggulan

### 1. 🤖 Telegram Bot Otomatisasi (Multi-Platform: PC & Termux)
- **Role-Based Access Control (RBAC) Multi-User (Zero-Backdoor / ID-Based)**:
  - **Super Admin**: Hak akses Super Admin ditentukan secara aman dan privat via `admin_ids` pada `core/config.json`. Bot otomatis mengenali Telegram ID pemilik secara kriptografis tanpa memerlukan password atau kode rahasia di chat.
  - **Generator Kode Akses Member**: Admin dapat membuat kode token akses berdurasi `1 Hari`, `3 Hari`, `7 Hari`, dan `30 Hari` untuk member lain via perintah `/gencode`.
  - **Pemisahan Menu Berdasarkan Role**:
    - **Admin**: Akses penuh (Buat QR Ph, Transfer Web3, Reset ADB, Status Slot, Buat Kode User, Base Setting).
    - **User/Member**: Pembuatan QR Ph, Cek Kurs/Kalkulator, Riwayat Transaksi, dan Cek Masa Aktif Akun.
    - **Guest/Expired**: Menu terkunci hingga memasukkan kode akses member yang valid dari Admin.
- **Dynamic QR Ph Generator Langsung di Chat**:
  - Pilihan Slot Akun (Slot 1 s/d Slot 4).
  - Pilihan Nominal Preset Cepat (`₱ 100`, `₱ 200`, `₱ 250`, `₱ 500`, `₱ 1,000`, `₱ 2,500`) + Opsi Input Bebas.
  - Opsi Acak Nama Toko (500M+ kombinasi nama autentik Filipina).
  - Foto barcode HD ber-badge resmi InstaPay dikirim langsung ke Telegram.
  - **Auto-Delete Barcode**: Pesan foto barcode lama otomatis dihapus dari chat begitu pembayaran lunas atau expired, digantikan konfirmasi struk pembayaran sukses.
- **Kalkulator Kurs Bitget Realtime**:
  - Menampilkan kurs live Bitget P2P PHP/USDC + profit buffer.
  - Kalkulator instan dua arah: Ketik langsung di chat, misal `500 php` atau `25 usdc`.
- **Web3 Multi-Chain Wallet Manager (Khusus Admin)**:
  - Cek saldo Base (ETH, USDC) dan BSC (BNB, USDT, USDC).
  - Transfer token Web3 langsung dari bot Telegram dengan tautan explorer (BaseScan / BscScan).
- **Background Realtime Order Watcher**:
  - Background task otomatis memantau transaksi masuk di database SQLite (`payments.db`) dan mengirim notifikasi saat pembayaran lunas.
- **Reset Multi App & Jaringan via ADB**:
  - Eksekusi atomic chained shell (Force stop, Clear cache, Airplane Mode ON/OFF, Restart Multi App).
  - Mendukung PC USB Debugging, Termux Shizuku (`rish`), Wireless ADB, dan Root (`su`).

### 2. 🇵🇭 Dynamic QR Ph Filipina (Coins.ph & InstaPay P2P)
- **Standard EMVCo & QR Ph InstaPay P2P**: Menghasilkan barcode pembayaran QR Ph resmi yang kompatibel dengan seluruh e-wallet dan mobile banking di Filipina (Coins.ph, GCash, Maya, GrabPay, BDO, BPI, UnionBank, dll.).
- **In-Slot QR Generator Controls**:
  - Tombol kontrol nominal (`₱` input + tombol **Set** dan `⚡ +0.01`) ditempatkan langsung di dalam setiap kartu slot di atas barcode.
  - Tombol `🎲 Acak Nama` di dalam slot untuk mengacak nama toko Filipina untuk semua slot secara instan.
  - **Mode Acak Nama Toko (Toggle Switch In-Slot)**:
    - **Saat ON**: Tombol petir `⚡ +0.01` otomatis meng-generate nama merchant Filipina baru dan nominal baru di semua slot akun.
    - **Saat OFF**: Tombol petir `⚡ +0.01` hanya menaikkan nominal (+₱0.01) saja di semua slot akun, nama toko tetap dipertahankan.
- **Authentic Philippine Merchant Name Generator**:
  - Menghasilkan 500.000.000+ variasi kombinasi nama toko otentik khas Filipina (Sari-Sari Store, Mini Mart, Express, Trading, dll.) dengan panjang karakter maksimal 25 huruf kapital sesuai standar EMVCo Tag 59.
- **Multi-Slot Account Management**:
  - Mendukung penambahan, penyimpanan, dan penghapusan multi-akun slot Coins.ph dengan data tersimpan rapi di `config.json`.

### 3. ⚡ Web3 Multi-Network Wallet Transfer (Web & POS)
- **Dukungan Multi-Jaringan Web3**:
  - 🔵 **Base Network**: USDC (Decimals: 6) & Gas ETH
  - 🟡 **BSC Network (BEP-20)**: USDT (Decimals: 18) & Gas BNB
  - 🟢 **BSC Network (BEP-20)**: USDC (Decimals: 18) & Gas BNB
- **Dual-Mode QR Barcode Scanner (Desktop & Mobile 100% Reliable)**:
  - Pemindaian live video stream jika browser mendukung izin kamera.
  - Tombol ambil foto kamera native HP (`capture="environment"`) & upload file gambar barcode.
  - Dukungan paste tangkapan layar barcode langsung dari clipboard (<kbd>Ctrl + V</kbd>).
  - Menggunakan engine decoder berkecepatan tinggi berbasis C++ ZXing Engine (`zxing-cpp`) di backend untuk akurasi pemindaian 100%.

---

## 📁 Struktur Direktori Bersih (Pure Engine)

```text
COINS_PAYMENT_GATEWAY/
├── run.bat                   # 🚀 [PC] 1-Klik Pintar Launcher Bot Telegram (Auto-Venv, Auto-Pip, Run)
├── START_SERVER.bat          # 🌐 [PC] Launcher Server Web POS & Dashboard (Port 5000)
├── INSTALL_REQUIREMENTS.bat  # 📦 [PC] Installer Dependensi Python
├── README.md                 # 📖 Dokumentasi Lengkap
├── .gitignore                # 🔒 Proteksi Kredensial (config.json & database aman)
│
├── core/                     # 📁 Mesin Utama
│   ├── bot.py                # 🤖 Bot Telegram RBAC, Dynamic QR Ph & Watcher
│   ├── ecosystem.config.js   # ⚙️ Konfigurasi PM2 Process Manager (Auto-Restart 24/7)
│   ├── adb_helper.py         # ⚡ Automasi ADB (PC, Shizuku, Wireless, Root)
│   ├── api_server.py         # 🌐 Flask REST API Server & Web POS Routing
│   ├── qr_engine.py          # 🇵🇭 EMVCo / QR Ph InstaPay Payload & Image Generator
│   ├── wallet_manager.py     # 💳 Web3 Multi-Network Engine (Base & BSC)
│   ├── database.py           # 🗄️ SQLite Database Engine (payments.db)
│   ├── config.json           # ⚙️ Konfigurasi Aktif (Private / Gitignored)
│   ├── config.example.json   # 📄 Template Konfigurasi Publik
│   ├── requirements.txt      # 📦 Daftar Dependensi Python
│   ├── test_system.py        # 🧪 Automated Test Suite Sistem Web
│   ├── static/               # 🎨 Aset Web Frontend (JS, CSS)
│   └── templates/            # 🖥️ Template HTML (POS, Dashboard, Checkout)
│
└── termux/                   # 📁 Script Khusus Android Termux
    ├── setup.sh              # 🎛️ Menu Interaktif 9-in-1 (Bot, PM2, Deps, Token, Web POS)
    └── run.sh                # 🚀 Launcher Server Web Termux
```

---

## 💻 Panduan Menjalankan di PC / Windows

### 1. Menjalankan Bot Telegram (1-Klik):
Cukup double-click file:
```text
run.bat
```
Script akan otomatis mengecek Python, mengaktifkan virtual environment, menginstall dependensi, dan menjalankan bot.

### 2. Menjalankan Server Web POS & Kasir:
Double-click file:
```text
START_SERVER.bat
```
Server berjalan di port 5000 dan dapat diakses di:
- POS Kasir: `http://<IP-LAN>:5000/pos`
- Dashboard Transaksi: `http://<IP-LAN>:5000/dashboard`

---

## 📱 Panduan Lengkap Android (Termux) — Dari Nol Hingga Berjalan

Panduan instalasi mandiri dari awal (*fresh install*), konfigurasi bot, hingga menjalankan bot 24/7 di perangkat Android menggunakan **Termux**.

> [!IMPORTANT]
> **Gunakan Termux Versi Resmi**:
> Unduh aplikasi Termux dari **[F-Droid](https://f-droid.org/en/packages/com.termux/)** atau **[GitHub Releases Termux](https://github.com/termux/termux-app/releases)**.  
> ⚠️ **Jangan gunakan Termux dari Google Play Store** karena repositorinya sudah usang (*deprecated*) dan tidak dapat menginstall paket.

---

### ⚡ Mode Ekspres (1 Baris Perintah Langsung Jadi)

Jika Anda ingin langsung menginstall semuanya sekaligus secara otomatis, buka **Termux** lalu salin dan tempel perintah berikut:

```bash
pkg update -y && pkg install -y git python && git clone https://github.com/Imammaulidy/coins.git && cd coins && bash setup.sh
```

---

### 📋 Tahapan Instalasi Manual Lengkap (Step-by-Step dari Awal)

Bagi Anda yang ingin menjalankan tahapan satu per satu dari awal:

#### 1. Perbarui Paket & Pasang Git serta Python:
```bash
pkg update -y && pkg upgrade -y
pkg install -y git python python-pip
```

#### 2. Clone Repositori Proyek dari GitHub:
```bash
git clone https://github.com/Imammaulidy/coins.git
```

#### 3. Masuk ke Direktori Proyek & Buka Menu Setup:
```bash
cd coins && bash setup.sh
```
*(Atau Anda juga bisa mengetik: `bash TERMUX/setup.sh`)*

---

### 🎛️ Menu Interaktif & Panduan Penggunaan (`setup.sh`)

Saat menu setup terbuka di layar Termux:

```text
=================================================================
    COINS.PH PAYMENT GATEWAY BOT - TERMUX SETUP & LAUNCHER      
=================================================================

Pilih menu yang ingin dijalankan:

  [1] Mode ADB Wifi (Wireless Debugging)
  [2] Mode ADB Shizuku (rish)
  [3] Install Dependencies (Python + Android Tools + rish)
  [4] Masukan atau Update Token Bot & Admin ID
  [5] Jalankan Bot Telegram (PM2 / Auto-Restart Background)
  [6] Lihat Log Bot Terbaru
  [7] Stop Bot (PM2 / Native)
  [8] Setup PM2 (NodeJS & PM2 Auto-Restart)
  [9] Jalankan Server Web POS (Port 5000)
  [0] Keluar
```

#### Langkah Konfigurasi Pertama Kali:
1. **Pasang Dependensi Sistem**:
   - Ketik `3` lalu tekan **Enter**. Script akan menginstall library Python yang dibutuhkan dan dependensi Android tools secara otomatis.
2. **Masukkan Token Bot Telegram & ID Admin**:
   - Ketik `4` lalu tekan **Enter**.
   - Masukkan token bot yang didapat dari `@BotFather`.
   - Masukkan Telegram User ID Anda (dapat dilihat dari `@userinfobot` atau saat ketik `/start` di bot Anda).
   - Konfigurasi akan tersimpan otomatis ke `core/config.json`.
3. **Pilih Jalur Automasi Device Android**:
   - **Pilihan `[1]` ADB Wifi**: Untuk Android 11 ke atas dengan Wireless Debugging (pairing nirkabel).
   - **Pilihan `[2]` ADB Shizuku (rish)**: Menggunakan Shizuku untuk eksekusi perintah tap/send langsung di jaringan data seluler tanpa butuh Wi-Fi.
4. **Jalankan Bot Telegram**:
   - Ketik `8` untuk menginstall PM2 Process Manager (opsional, sangat direkomendasikan agar bot otomatis restart bila terjadi error).
   - Ketik `5` untuk menjalankan Bot Telegram di background.
   - Ketik `6` untuk memantau log transaksi dan order watcher secara langsung.

---

### 🔄 Perintah Manajemen PM2 (Background 24/7)

Setelah PM2 terpasang (Menu `[8]`), Anda dapat mengontrol bot kapan saja dari luar menu setup:

```bash
# Jalankan Bot di background 24/7
pm2 start core/ecosystem.config.js

# Pantau log bot secara realtime
pm2 logs coins-bot

# Cek status proses bot
pm2 status

# Restart bot
pm2 restart coins-bot

# Hentikan bot
pm2 stop coins-bot
```

---

### 🔄 Cara Memperbarui Script ke Versi Terbaru (Git Pull)
Jika ada pembaruan fitur atau perbaikan bug di GitHub, cukup jalankan:
```bash
cd coins && git pull origin main && bash setup.sh
```

---

## 👑 Hak Akses & Keamanan RBAC (ID-Based)

1. **Super Admin**:
   - Daftarkan Telegram User ID Anda ke dalam daftar `admin_ids` pada `core/config.json`.
   - Bot otomatis mengenali Anda sebagai Super Admin secara kriptografis tanpa password atau backdoor di chat.
2. **Member / User Biasa**:
   - Minta kode akses berdurasi (1, 3, 7, atau 30 hari) ke Super Admin yang di-generate via perintah `/gencode`.
   - Ketik kode token (contoh: `COINS-3D-A1B2C3`) di chat untuk aktivasi sesi.
