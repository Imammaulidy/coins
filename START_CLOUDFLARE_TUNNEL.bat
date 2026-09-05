@echo off
title COINS.PH GATEWAY - CLOUDFLARE TUNNEL (highcards.my.id)
color 0B
cd /d "%~dp0"

:: 1. Deteksi IP Dinamis Local LAN
set LOCAL_IP=
if exist ".venv\Scripts\python.exe" (
    for /f %%i in ('.venv\Scripts\python.exe core\get_ip.py') do set LOCAL_IP=%%i
)
if "%LOCAL_IP%"=="" (
    for /f "tokens=4" %%a in ('route print 0.0.0.0 ^| findstr /r "0\.0\.0\.0"') do if "%LOCAL_IP%"=="" set LOCAL_IP=%%a
)
if "%LOCAL_IP%"=="" set LOCAL_IP=192.168.1.20

set TARGET_LOCAL_URL=http://%LOCAL_IP%:5000

:: 2. Deteksi cloudflared.exe
set CF_BIN=cloudflared.exe
if not exist "%CF_BIN%" (
    where cloudflared >nul 2>&1
    if not errorlevel 1 (
        set CF_BIN=cloudflared
    ) else (
        echo ======================================================================
        echo       COINS.PH PAYMENT GATEWAY - CLOUDFLARE TUNNEL LAUNCHER
        echo ======================================================================
        echo [*] Mengunduh cloudflared.exe resmi dari Cloudflare GitHub...
        powershell -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; (New-Object System.Net.WebClient).DownloadFile('https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe', 'cloudflared.exe')"
        if not exist "cloudflared.exe" (
            color 0C
            echo [-] Gagal mengunduh cloudflared.exe secara otomatis!
            echo     Silakan unduh manual dan letakkan cloudflared.exe di folder ini.
            pause
            exit /b 1
        )
        echo [+] cloudflared.exe berhasil diunduh dan siap digunakan.
    )
)

:MENU
cls
echo ======================================================================
echo       COINS.PH PAYMENT GATEWAY - CLOUDFLARE TUNNEL LAUNCHER
echo                  Target Domain: highcards.my.id
echo ======================================================================
echo [*] Target Server Lokal  : %TARGET_LOCAL_URL%
if exist "cloudflare_token.txt" (
    echo [*] Status Token         : [TERSIMPAN DI cloudflare_token.txt]
) else (
    echo [*] Status Token         : [BELUM DIKONFIGURASI]
)
echo ======================================================================
echo.
echo Pilih menu yang ingin dijalankan:
echo.
echo   [1] Jalankan Tunnel Domain (highcards.my.id)
echo   [2] Input / Ganti Cloudflare Tunnel Token
echo   [3] Jalankan Quick Tunnel Gratis (*.trycloudflare.com)
echo   [4] Panduan Cara Setup Domain highcards.my.id di Cloudflare
echo   [5] Buka Browser ke highcards.my.id
echo   [6] Keluar
echo.

choice /c 123456 /n /m "Pilihan Anda (1-6): "
if errorlevel 6 exit /b 0
if errorlevel 5 goto OPEN_BROWSER
if errorlevel 4 goto GUIDE
if errorlevel 3 goto RUN_QUICK
if errorlevel 2 goto INPUT_TOKEN
if errorlevel 1 goto RUN_TOKEN

goto MENU

:RUN_TOKEN
cls
echo ======================================================================
echo       MENJALANKAN TUNNEL DOMAIN CLOUDFLARE: highcards.my.id
echo ======================================================================
echo.

if not exist "cloudflare_token.txt" (
    echo [!] Token Cloudflare belum ditemukan.
    goto INPUT_TOKEN
)

set /p CF_TOKEN=<"cloudflare_token.txt"
if "%CF_TOKEN%"=="" (
    echo [!] File cloudflare_token.txt kosong.
    goto INPUT_TOKEN
)

echo [*] Target Lokal : %TARGET_LOCAL_URL%
echo [*] Domain Publik: https://highcards.my.id
echo [*] Menghubungkan tunnel ke Cloudflare Edge Network...
echo.
echo [INFO] Jangan tutup jendela ini agar website tetap online!
echo.
"%CF_BIN%" tunnel run --token %CF_TOKEN%
echo.
echo [-] Tunnel berhenti.
pause
goto MENU

:INPUT_TOKEN
cls
echo ======================================================================
echo                 INPUT / GANTI CLOUDFLARE TUNNEL TOKEN
echo ======================================================================
echo.
echo Dapatkan Token dari Cloudflare Zero Trust:
echo 1. Buka: https://one.dash.cloudflare.com/
echo 2. Masuk ke: Networks -^> Tunnels -^> Add a tunnel
echo 3. Pilih tipe 'Cloudflare Tunnel' lalu pilih 'Windows'
echo 4. Salin TOKEN panjang di belakang perintah:
echo    "cloudflared.exe tunnel run --token [TOKEN_ANDA]"
echo.
echo ======================================================================
set /p USER_TOKEN="Paste Token Cloudflare Anda di sini: "
if "%USER_TOKEN%"=="" (
    echo [-] Token tidak boleh kosong!
    pause
    goto MENU
)

:: Bersihkan token jika user mem-paste seluruh baris perintah
set CLEAN_TOKEN=%USER_TOKEN:cloudflared.exe tunnel run --token =%
set CLEAN_TOKEN=%CLEAN_TOKEN:cloudflared tunnel run --token =%
set CLEAN_TOKEN=%CLEAN_TOKEN:--token =%
set CLEAN_TOKEN=%CLEAN_TOKEN:"=%
set CLEAN_TOKEN=%CLEAN_TOKEN: =%

echo %CLEAN_TOKEN%> "cloudflare_token.txt"
echo.
echo [+] Token berhasil disimpan ke cloudflare_token.txt!
echo.
pause
goto RUN_TOKEN

:RUN_QUICK
cls
echo ======================================================================
echo               MENJALANKAN QUICK TUNNEL (*.trycloudflare.com)
echo ======================================================================
echo.
echo [*] Menghubungkan ke Cloudflare Quick Tunnel...
echo [*] Target Lokal: %TARGET_LOCAL_URL%
echo.
echo [INFO] URL publik acak akan muncul di log bawah ini.
echo.
"%CF_BIN%" tunnel --url %TARGET_LOCAL_URL%
echo.
echo [-] Quick Tunnel berhenti.
pause
goto MENU

:OPEN_BROWSER
start https://highcards.my.id/pos
goto MENU

:GUIDE
cls
echo ======================================================================
echo       PANDUAN SETUP DOMAIN highcards.my.id DI CLOUDFLARE ZERO TRUST
echo ======================================================================
echo.
echo 1. Pastikan domain highcards.my.id sudah aktif di akun Cloudflare Anda.
echo.
echo 2. Buka Cloudflare Zero Trust:
echo    https://one.dash.cloudflare.com/
echo.
echo 3. Masuk ke menu:
echo    Networks -^> Tunnels -^> Klik "Create a tunnel" (atau "Add a tunnel")
echo.
echo 4. Beri nama tunnel, contoh: coins-gateway, lalu klik "Save tunnel".
echo.
echo 5. Pada tab "Install and run a connector":
echo    - Pilih "Windows".
echo    - Salin TOKEN yang ada di box instalasi.
echo    - Masukkan token tersebut ke menu [2] di script ini.
echo.
echo 6. Klik "Next" ke tab "Public Hostname Page":
echo    - Subdomain : (kosongkan jika ingin langsung highcards.my.id, atau isi misal pay)
echo    - Domain    : highcards.my.id
echo    - Path      : (kosongkan)
echo    - Type      : HTTP
echo    - URL       : %LOCAL_IP%:5000
echo.
echo 7. Klik "Save tunnel".
echo.
echo Selesai! Setelah itu jalankan menu [1] pada script ini.
echo Website kasir Anda akan langsung online di https://highcards.my.id
echo ======================================================================
echo.
pause
goto MENU
