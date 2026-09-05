@echo off
title COINS.PH GATEWAY - CLOUDFLARE TUNNEL (triomerak.web.id)
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
echo                  Target Domain: triomerak.web.id
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
echo   [1] Jalankan Tunnel Domain (via Token Zero Trust)
echo   [2] Input / Ganti Cloudflare Tunnel Token
echo   [3] Login Otomatis via Browser (cloudflared login)
echo   [4] Jalankan Quick Tunnel Gratis (*.trycloudflare.com)
echo   [5] Panduan Cara Setup Domain triomerak.web.id di Cloudflare
echo   [6] Buka Browser ke triomerak.web.id
echo   [7] Keluar
echo.

choice /c 1234567 /n /m "Pilihan Anda (1-7): "
if errorlevel 7 exit /b 0
if errorlevel 6 goto OPEN_BROWSER
if errorlevel 5 goto GUIDE
if errorlevel 4 goto RUN_QUICK
if errorlevel 3 goto AUTO_LOGIN
if errorlevel 2 goto INPUT_TOKEN
if errorlevel 1 goto RUN_TOKEN

goto MENU

:RUN_TOKEN
cls
echo ======================================================================
echo       MENJALANKAN TUNNEL DOMAIN CLOUDFLARE: triomerak.web.id
echo ======================================================================
echo.

if not exist "cloudflare_token.txt" (
    echo [!] Token Cloudflare belum ditemukan.
    pause
    goto INPUT_TOKEN
)

set /p CF_TOKEN=<"cloudflare_token.txt"
if "%CF_TOKEN%"=="" (
    echo [!] File cloudflare_token.txt kosong.
    pause
    goto INPUT_TOKEN
)

echo [*] Target Lokal : %TARGET_LOCAL_URL%
echo [*] Domain Publik: https://triomerak.web.id
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
echo CATATAN PENTING:
echo Token yang dibutuhkan adalah ZERO TRUST TUNNEL TOKEN (diawali "eyJh...").
echo BUKAN Account API Token (yang diawali "cfat_...").
echo.
echo Cara Mendapatkan Tunnel Token dari Cloudflare Zero Trust:
echo 1. Buka: https://one.dash.cloudflare.com/
echo 2. Masuk ke: Networks -^> Tunnels -^> Add a tunnel (atau Create a tunnel)
echo 3. Pilih tipe 'Cloudflare Tunnel', beri nama (misal: triomerak)
echo 4. Pilih 'Windows' dan salin TOKEN panjang (yang diawali "eyJh...")
echo.
echo ======================================================================
set /p USER_TOKEN="Masukkan Token Zero Trust Anda: "
if "%USER_TOKEN%"=="" (
    echo [-] Token tidak boleh kosong!
    pause
    goto MENU
)

REM Bersihkan token jika user mem-paste seluruh baris perintah
set CLEAN_TOKEN=%USER_TOKEN:cloudflared.exe tunnel run --token =%
set CLEAN_TOKEN=%CLEAN_TOKEN:cloudflared tunnel run --token =%
set CLEAN_TOKEN=%CLEAN_TOKEN:--token =%
set CLEAN_TOKEN=%CLEAN_TOKEN:"=%
set CLEAN_TOKEN=%CLEAN_TOKEN: =%

REM Deteksi jika user salah memasukkan API Token cfat_
echo %CLEAN_TOKEN% | findstr /i "^cfat_" >nul
if not errorlevel 1 (
    echo.
    color 0C
    echo [!] PERINGATAN: Token yang Anda masukkan diawali 'cfat_'.
    echo     Ini adalah Cloudflare API Token (untuk REST API),
    echo     BUKAN Cloudflare Zero Trust Tunnel Token!
    echo.
    echo     Tunnel Token yang benar biasanya sangat panjang dan diawali 'eyJh...'.
    echo     Dapatkan di: https://one.dash.cloudflare.com/ (Networks -^> Tunnels).
    echo.
    pause
    color 0B
    goto MENU
)

echo %CLEAN_TOKEN%> "cloudflare_token.txt"
echo.
echo [+] Token berhasil disimpan ke cloudflare_token.txt!
echo.
pause
goto RUN_TOKEN

:AUTO_LOGIN
cls
echo ======================================================================
echo               LOGIN OTOMATIS CLOUDFLARE VIA BROWSER
echo ======================================================================
echo.
echo [*] Membuka browser untuk otorisasi domain triomerak.web.id...
echo [*] Silakan klik domain 'triomerak.web.id' lalu klik 'Authorize' di browser.
echo.
"%CF_BIN%" tunnel login
if errorlevel 1 (
    echo.
    echo [-] Otorisasi browser dibatalkan atau gagal.
    pause
    goto MENU
)
echo.
echo [+] Otorisasi browser berhasil!
echo [*] Menyiapkan tunnel 'triomerak'...
"%CF_BIN%" tunnel create triomerak >nul 2>&1
"%CF_BIN%" tunnel route dns -f triomerak triomerak.web.id
echo [+] Domain triomerak.web.id berhasil di-route ke tunnel!
echo.
echo [*] Menjalankan tunnel ke target: %TARGET_LOCAL_URL% ...
echo [INFO] Jangan tutup jendela ini agar website tetap online!
echo.
"%CF_BIN%" tunnel run --url %TARGET_LOCAL_URL% triomerak
echo.
echo [-] Tunnel berhenti.
pause
goto MENU

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
start https://triomerak.web.id/pos
goto MENU

:GUIDE
cls
echo ======================================================================
echo       PANDUAN SETUP DOMAIN triomerak.web.id DI CLOUDFLARE ZERO TRUST
echo ======================================================================
echo.
echo 1. Pastikan domain triomerak.web.id sudah aktif di akun Cloudflare Anda.
echo.
echo 2. Buka Cloudflare Zero Trust:
echo    https://one.dash.cloudflare.com/
echo.
echo 3. Masuk ke menu:
echo    Networks -^> Tunnels -^> Klik "Create a tunnel" (atau "Add a tunnel")
echo.
echo 4. Beri nama tunnel, contoh: triomerak, lalu klik "Save tunnel".
echo.
echo 5. Pada tab "Install and run a connector":
echo    - Pilih "Windows".
echo    - Salin TOKEN panjang di belakang "--token" (diawali "eyJh...").
echo    - Masukkan token tersebut ke menu [2] di script ini.
echo.
echo 6. Klik "Next" ke tab "Public Hostname Page":
echo    - Subdomain : (kosongkan jika ingin langsung triomerak.web.id, atau isi misal pay)
echo    - Domain    : triomerak.web.id
echo    - Path      : (kosongkan)
echo    - Type      : HTTP
echo    - URL       : %LOCAL_IP%:5000
echo.
echo 7. Klik "Save tunnel".
echo.
echo Selesai! Setelah itu jalankan menu [1] pada script ini.
echo Website kasir Anda akan langsung online di https://triomerak.web.id
echo ======================================================================
echo.
pause
goto MENU
