# 🇵🇭 Coins.ph Dynamic QR Ph Payment Gateway & Web3 Multi-Network Hub

Payment Gateway mandiri dan POS Kasir Web resmi berstandar nasional Filipina (**QR Ph / InstaPay**) dengan kontrol generator in-slot, auto-random merchant name engine, dan integrasi Web3 Multi-Network Wallet Transfer (Base USDC, BSC USDT, dan BSC USDC).

---

## 🚀 Fitur Unggulan

### 1. 🇵🇭 Dynamic QR Ph Filipina (Coins.ph & InstaPay P2P)
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

### 2. ⚡ Web3 Multi-Network Wallet Transfer
- **Dukungan Multi-Jaringan Web3**:
  - 🔵 **Base Network**: USDC (Decimals: 6) & Gas ETH
  - 🟡 **BSC Network (BEP-20)**: USDT (Decimals: 18) & Gas BNB
  - 🟢 **BSC Network (BEP-20)**: USDC (Decimals: 18) & Gas BNB
- **Dual-Mode QR Barcode Scanner (Desktop & Mobile 100% Reliable)**:
  - Pemindaian live video stream jika browser mendukung izin kamera.
  - Tombol ambil foto kamera native HP (`capture="environment"`) & upload file gambar barcode.
  - Dukungan paste tangkapan layar barcode langsung dari clipboard (<kbd>Ctrl + V</kbd>).
  - Menggunakan engine decoder berkecepatan tinggi berbasis C++ ZXing Engine (`zxing-cpp`) di backend untuk akurasi pemindaian 100% bahkan pada foto barcode beresolusi tinggi, miring, atau berorientasi vertikal/horizontal.
  - Auto-close scanner panel, audio beep sound, dan visual flash highlight begitu address penerima terdeteksi.
- **Kalkulator Estimasi Konversi Crypto Otomatis**:
  - Terintegrasi langsung dengan Kurs Dinamis Bitget Wallet (`1 USDC ≈ 60.75 PHP`).
  - Menampilkan estimasi jumlah transfer USDC/USDT di setiap kartu slot secara live.

### 3. 🛡️ Pure Dynamic IP:Port LAN Binding
- Server berjalan secara murni pada IP lokal dinamis (`http://<IP-LAN>:5000`), bebas dari ketergantungan `localhost` atau port tidak resmi.
- Dapat diakses langsung secara multi-device dari PC kasir, laptop operator, tablet, maupun smartphone Android/iOS di jaringan WiFi / LAN yang sama.

---

## 📁 Struktur Direktori Bersih (Pure Engine)

```text
COINS_PAYMENT_GATEWAY/
├── core/
│   ├── api_server.py         # Flask REST API Server & Web3 Routing
│   ├── qr_engine.py          # EMVCo / QR Ph InstaPay Payload Generator
│   ├── wallet_manager.py     # Web3 Multi-Network Engine (Base & BSC)
│   ├── database.py           # SQLite Database Engine
│   ├── get_ip.py             # Pure Dynamic LAN IP Detector
│   ├── config.json           # Konfigurasi Akun & Server
│   ├── requirements.txt      # Daftar Dependensi Python
│   ├── test_system.py        # Automated Unit Test Suite
│   ├── static/
│   │   └── jsqr.js           # Client-side QR Decoder Library
│   └── templates/
│       ├── pos.html          # Web POS Kasir & Web3 Wallet Hub
│       ├── dashboard.html    # Dashboard Riwayat Transaksi
│       └── checkout.html     # Halaman Invoice Checkout Pelanggan
├── TERMUX/
│   ├── run.sh                # Launcher Server Termux Android
│   └── termuxsetup.sh        # Installer Otomatis Termux Android
├── START_SERVER.bat          # Launcher Server Windows
├── INSTALL_REQUIREMENTS.bat  # Installer Dependensi Windows
├── cara menggunakan.txt     # Panduan Penggunaan Lengkap
└── README.md                 # Dokumentasi Repositori
```

---

## 💻 Panduan Instalasi & Menjalankan

### A. Di PC / Laptop (Windows)
1. **Install Python**: Pastikan Python 3.11 atau lebih baru telah terinstall dengan opsi *"Add Python to PATH"* dicentang.
2. **Install Dependensi**:
   Double-click file `INSTALL_REQUIREMENTS.bat`.
3. **Jalankan Server**:
   Double-click file `START_SERVER.bat`. Server akan mendeteksi IP lokal otomatis dan membuka browser ke `http://<IP-LAN>:5000/pos`.

### B. Di Android (Termux)
1. Buka aplikasi Termux lalu salin folder proyek.
2. Masuk ke folder TERMUX dan jalankan installer:
   ```bash
   cd TERMUX
   bash termuxsetup.sh
   ```
3. Jalankan server:
   ```bash
   bash run.sh
   ```
4. Buka browser ponsel dan akses `http://<IP-HP>:5000/pos`.

---

## 🧪 Pengujian Sistem & Unit Test

Jalankan pengujian unit test bawaan untuk memastikan seluruh komponen berfungsi normal:
```bash
python -m unittest core/test_system.py
```

---

## 📄 Lisensi
Hak Cipta (c) 2026 - Dikembangkan untuk sistem operasional kasir mandiri Coins.ph & Web3 Payment Hub.
