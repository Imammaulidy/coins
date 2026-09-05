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
if exist "%USERPROFILE%\.cloudflared\cert.pem" (
    echo [*] Status Otorisasi     : [TERHUBUNG RESMI DENGAN triomerak.web.id]
) else if exist "cloudflare_token.txt" (
    echo [*] Status Token         : [TERSIMPAN DI cloudflare_token.txt]
) else (
    echo [*] Status Otorisasi     : [BELUM DIKONFIGURASI]
)
echo ======================================================================
echo.
echo Pilih menu yang ingin dijalankan:
echo.
echo   [1] Jalankan Tunnel triomerak.web.id (1-Klik Langsung Aktif)
echo   [2] Buka Browser ke https://triomerak.web.id/pos
echo   [3] Otorisasi Ulang via Browser (cloudflared login)
echo   [4] Input / Ganti Token Zero Trust Manual
echo   [5] Jalankan Quick Tunnel Gratis (*.trycloudflare.com)
echo   [6] Keluar
echo.

choice /c 123456 /n /m "Pilihan Anda (1-6) [Default=1]: "
if errorlevel 6 exit /b 0
if errorlevel 5 goto RUN_QUICK
if errorlevel 4 goto INPUT_TOKEN
if errorlevel 3 goto AUTO_LOGIN
if errorlevel 2 goto OPEN_BROWSER
if errorlevel 1 goto RUN_TUNNEL

goto MENU

:RUN_TUNNEL
cls
echo ======================================================================
echo       MENJALANKAN TUNNEL DOMAIN CLOUDFLARE: triomerak.web.id
echo ======================================================================
echo.
echo [*] Target Lokal  : %TARGET_LOCAL_URL%
echo [*] Domain Publik : https://triomerak.web.id
echo [*] Menghubungkan tunnel ke Cloudflare Edge Network...
echo.
echo ======================================================================
echo [INFO] JANGAN TUTUP JENDELA INI AGAR WEBSITE TETAP ONLINE!
echo ======================================================================
echo.

:: Prioritaskan tunnel bernama yang sudah terotorisasi
if exist "%USERPROFILE%\.cloudflared\cert.pem" (
    "%CF_BIN%" tunnel run --url %TARGET_LOCAL_URL% triomerak
    goto TUNNEL_END
)

:: Jika menggunakan token manual
if exist "cloudflare_token.txt" (
    set /p CF_TOKEN=<"cloudflare_token.txt"
    if not "%CF_TOKEN%"=="" (
        "%CF_BIN%" tunnel run --token %CF_TOKEN%
        goto TUNNEL_END
    )
)

echo [!] Tunnel belum diotorisasi. Membuka login browser otomatis...
pause
goto AUTO_LOGIN

:TUNNEL_END
echo.
echo [-] Tunnel berhenti.
pause
goto MENU

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
"%CF_BIN%" tunnel route dns -f triomerak www.triomerak.web.id
echo [+] Domain triomerak.web.id berhasil di-route ke tunnel!
echo.
pause
goto RUN_TUNNEL

:INPUT_TOKEN
cls
echo ======================================================================
echo                 INPUT / GANTI CLOUDFLARE TUNNEL TOKEN
echo ======================================================================
echo.
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

echo %CLEAN_TOKEN%> "cloudflare_token.txt"
echo.
echo [+] Token berhasil disimpan ke cloudflare_token.txt!
echo.
pause
goto RUN_TUNNEL

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
