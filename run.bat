@echo off
title COINS.PH PAYMENT GATEWAY - TELEGRAM BOT
color 0B

echo ========================================================
echo        COINS.PH PAYMENT GATEWAY - TELEGRAM BOT
echo ========================================================
echo.

cd /d "%~dp0"

:: 1. Cek Apakah Python Terinstall
python --version >nul 2>&1
if errorlevel 1 (
    color 0C
    echo [-] Python tidak terdeteksi di sistem!
    echo     Silakan install Python 3.10+ dan centang "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

:: 2. Deteksi Virtual Environment
if exist ".venv\Scripts\activate.bat" (
    echo [+] Mengaktifkan Virtual Environment .venv...
    call .venv\Scripts\activate.bat
    goto RUN_BOT
)

:: Jika belum ada venv sama sekali, buat baru
color 0E
echo [*] Menyiapkan Virtual Environment (.venv)...
python -m venv .venv
if errorlevel 1 (
    color 0C
    echo [-] Gagal membuat virtual environment!
    pause
    exit /b 1
)
echo [+] Virtual environment berhasil dibuat.

echo [*] Menginstall dependensi dari core\requirements.txt...
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
pip install -r core\requirements.txt
if exist "core\requirements-desktop.txt" (
    pip install -r core\requirements-desktop.txt
)
if errorlevel 1 (
    color 0C
    echo [-] Gagal menginstall dependensi! Periksa koneksi internet Anda.
    pause
    exit /b 1
)
echo [+] Semua dependensi berhasil terinstall!
color 0B
echo.

:RUN_BOT
:: 3. Cek Konfigurasi
if not exist "core\config.json" (
    if exist "..\core\config.json" (
        copy "..\core\config.json" "core\config.json" >nul
        echo [+] Konfigurasi disinkronkan dari folder utama.
    ) else if exist "core\config.example.json" (
        copy "core\config.example.json" "core\config.json" >nul
        echo [!] config.json baru dibuat dari template.
        echo     Silakan isi bot_token di core\config.json sebelum menjalankan bot.
        echo.
    )
)

:: 4. Jalankan Bot
echo [*] Menjalankan Bot Telegram Coins.ph...
echo.
python core\bot.py

echo.
echo ========================================================
echo [-] Bot berhenti.
echo ========================================================
pause
