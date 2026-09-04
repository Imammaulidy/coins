# 🇵🇭 Coins.ph Dynamic QR Ph Payment Gateway, Web3 Hub & Telegram Bot

Payment Gateway mandiri, POS Kasir Web resmi berstandar nasional Filipina (**QR Ph / InstaPay**), dan **Bot Telegram Otomatisasi Multi-Role** dengan generator in-slot, auto-random merchant name engine, kalkulator kurs Bitget P2P, Web3 Multi-Network Wallet Transfer (Base USDC, BSC USDT, dan BSC USDC), serta otomasi reset jaringan ADB.

---

## 🌟 Fitur Unggulan

### 1. 🤖 Telegram Bot Otomatisasi (Multi-Platform: PC & Termux)
- **Role-Based Access Control (RBAC) Multi-User**:
  - **Super Admin Master Key**: Ketik kode master admin (default: `ADMIN123` atau sesuai settingan `core/config.json`) di chat untuk langsung mengklaim akses Super Admin Permanen.
  - **Generator Kode Akses Member**: Admin dapat membuat kode akses pengguna dengan masa berlaku `1 Hari`, `3 Hari`, `7 Hari`, dan `30 Hari`.
  - **Pemisahan Menu Berdasarkan Role**:
    - **Admin**: Akses penuh (Buat QR Ph, Transfer Web3, Reset ADB, Status Slot, Buat Kode User, Base Setting).
    - **User/Member**: Pembuatan QR Ph, Cek Kurs/Kalkulator, Riwayat Transaksi, dan Cek Masa Aktif Akun.
    - **Guest/Expired**: Menu terkunci hingga memasukkan kode akses yang valid.
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

## 📱 Panduan Lengkap Android (Termux) — Siap Salin & Tempel

Jalankan perintah berikut di aplikasi **Termux**:

### 1. Masuk ke Folder Proyek & Buka Menu Setup:
```bash
cd coins && bash termux/setup.sh
```

### 2. Menu Interaktif `termux/setup.sh`:
```text
=================================================================
    COINS.PH PAYMENT GATEWAY BOT - TERMUX SETUP & LAUNCHER      
=================================================================

Pilih menu yang ingin dijalankan:

  [1] Mode ADB Wifi (Wireless Debugging)
  [2] Mode ADB Shizuku (rish)
  [3] Install Dependencies (Python + Android Tools + rish)
  [4] Masukan atau Update Token Bot Tele
  [5] Jalankan Bot Telegram (PM2 / Auto-Restart Background)
  [6] Lihat Log Bot Terbaru
  [7] Stop Bot (PM2 / Native)
  [8] Setup PM2 (NodeJS & PM2 Auto-Restart)
  [9] Jalankan Server Web POS (Port 5000)
  [0] Keluar
```

### 3. Menjalankan Bot dengan PM2 (Auto-Restart 24/7):
```bash
# Jalankan Bot di background 24/7
pm2 start core/ecosystem.config.js

# Cek Log bot realtime
pm2 logs coins-bot

# Cek status bot
pm2 status

# Restart bot
pm2 restart coins-bot

# Hentikan bot
pm2 stop coins-bot
```

---

## 👑 Hak Akses & Keamanan RBAC

1. **Super Admin**:
   - Ketik kode rahasia master (default: `ADMIN123` atau ubah sesuai keinginan di `core/config.json`) di chat Telegram.
   - Status akun otomatis ditingkatkan menjadi **Super Admin Permanen**.
2. **Member / User Biasa**:
   - Minta kode akses berdurasi (1, 3, 7, atau 30 hari) ke Super Admin.
   - Ketik kode (contoh: `COINS-3D-A1B2C3`) di chat untuk aktivasi sesi.
