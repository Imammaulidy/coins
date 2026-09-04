@echo off
title COINS.PH PAYMENT GATEWAY & AUTOMATION BOT
color 0B

echo ========================================================
echo        COINS.PH PAYMENT GATEWAY & AUTOMATION BOT
echo ========================================================
echo.

cd /d "%~dp0"

:: 1. Cek Apakah Python Terinstall
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [-] Python tidak terdeteksi di sistem!
    echo     Silakan install Python 3.10+ dan centang "Add Python to PATH".
    echo.
    pause
    exit /b 1
)

:: 2. Cek & Aktifkan Virtual Environment
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
) else if exist "coins\.venv\Scripts\activate.bat" (
    call coins\.venv\Scripts\activate.bat
) else (
    color 0E
    echo [*] Menyiapkan Virtual Environment (.venv)...
    python -m venv .venv
    if %errorlevel% neq 0 (
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
    if %errorlevel% neq 0 (
        color 0C
        echo [-] Gagal menginstall dependensi! Periksa koneksi internet Anda.
        pause
        exit /b 1
    )
    echo [+] Semua dependensi berhasil terinstall!
    color 0B
    echo.
)

:: 4. Cek Konfigurasi
if not exist "core\config.json" (
    if exist "core\config.example.json" (
        copy "core\config.example.json" "core\config.json" >nul
        echo [!] config.json baru dibuat dari template.
        echo     Silakan isi bot_token di core\config.json sebelum menjalankan bot.
        echo.
    )
)

:: 5. Jalankan Bot
echo [*] Menjalankan Bot Telegram Coins.ph...
python core\bot.py

if %errorlevel% neq 0 (
    echo.
    echo [-] Bot berhenti. Periksa konfigurasi di core\config.json atau log error di atas.
    echo.
    pause
)
