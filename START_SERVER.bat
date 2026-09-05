@echo off
title COINS.PH PAYMENT GATEWAY - ALL IN ONE (SERVER + BOT + TUNNEL)
color 0b
cd /d "%~dp0"

:: ======================================================================
:: 1. Cek / Setup Virtual Environment
:: ======================================================================
if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Virtual Environment belum ditemukan.
    echo Menjalankan instalasi requirement otomatis...
    call INSTALL_REQUIREMENTS.bat
    if errorlevel 1 goto ERROR
)

:: ======================================================================
:: 2. Deteksi IP Dinamis Local LAN
:: ======================================================================
set LOCAL_IP=
if exist ".venv\Scripts\python.exe" (
    for /f %%i in ('.venv\Scripts\python.exe core\get_ip.py') do set LOCAL_IP=%%i
)
if "%LOCAL_IP%"=="" (
    for /f "tokens=4" %%a in ('route print 0.0.0.0 ^| findstr /r "0\.0\.0\.0"') do if "%LOCAL_IP%"=="" set LOCAL_IP=%%a
)
if "%LOCAL_IP%"=="" set LOCAL_IP=192.168.1.20

:: ======================================================================
:: 3. Deteksi PM2 & Node.js
:: ======================================================================
set PM2_CMD=pm2
where pm2 >nul 2>&1
if errorlevel 1 (
    if exist "%APPDATA%\npm\pm2.cmd" (
        set PM2_CMD="%APPDATA%\npm\pm2.cmd"
    ) else if exist "C:\Program Files\nodejs\npm.cmd" (
        echo [*] Menginstall PM2 Process Manager secara global...
        call "C:\Program Files\nodejs\npm.cmd" install -g pm2 pm2-windows-startup
        set PM2_CMD="%APPDATA%\npm\pm2.cmd"
    )
)

:MENU
cls
echo ======================================================================
echo    COINS.PH PAYMENT GATEWAY - ALL IN ONE CONTROLLER (TRIO MERAK)
echo ======================================================================
echo  [*] Target IP Lokal  : http://%LOCAL_IP%:5000
echo  [*] Domain Publik    : https://triomerak.web.id
echo  [*] POS Kasir        : https://triomerak.web.id/pos
echo  [*] Engine Services  : Web Server + Bot Telegram + Cloudflare Tunnel
echo ======================================================================
echo.
echo Pilih Mode Operasi:
echo.
echo   [1] JALANKAN SEMUA DENGAN PM2 (Rekomendasi 24 Jam Saat Layar Mati)
echo   [2] LIHAT STATUS ^& MONITOR PM2 (pm2 status)
echo   [3] LIHAT LOG REALTIME SEMUA SERVICE (pm2 logs)
echo   [4] RESTART SEMUA LAYANAN (pm2 restart all)
echo   [5] STOP / MATIKAN SEMUA LAYANAN (pm2 stop all)
echo   [6] BUKA BROWSER KE POS KASIR
echo   [7] JALANKAN MANUAL (Jendela CMD Biasa Tanpa PM2)
echo   [8] KELUAR
echo.
echo ======================================================================

choice /c 12345678 /n /m "Pilihan Anda (1-8) [Default=1]: "
if errorlevel 8 exit /b 0
if errorlevel 7 goto RUN_FOREGROUND
if errorlevel 6 goto OPEN_BROWSER
if errorlevel 5 goto STOP_PM2
if errorlevel 4 goto RESTART_PM2
if errorlevel 3 goto LOGS_PM2
if errorlevel 2 goto STATUS_PM2
if errorlevel 1 goto START_PM2

goto MENU

:: ======================================================================
:: PM2 ACTIONS
:: ======================================================================

:START_PM2
cls
echo ======================================================================
echo   MENJALANKAN SEMUA SERVICE DENGAN PM2 (LATAR BELAKANG / BACKGROUND)
echo ======================================================================
echo.
echo [*] Memulai coins-server, coins-bot, dan coins-tunnel...
call %PM2_CMD% start core\ecosystem.config.js
call %PM2_CMD% save >nul 2>&1

echo.
echo ======================================================================
echo   [SUKSES] SEMUA LAYANAN BERJALAN DI BACKGROUND!
echo   - Web Server POS     : http://%LOCAL_IP%:5000/pos
echo   - Domain Publik      : https://triomerak.web.id/pos
echo   - Bot Telegram       : Aktif melayani transaksi
echo   - Cloudflare Tunnel  : Terhubung 24 jam non-stop
echo ======================================================================
echo.
echo [PENTING] Anda AMAN MENUTUP JENDELA CMD INI atau MEMATIKAN MONITOR!
echo           Semua sistem akan tetap bekerja secara mandiri di background.
echo.
start http://%LOCAL_IP%:5000/pos
pause
goto MENU

:STATUS_PM2
cls
echo ======================================================================
echo                     STATUS LAYANAN PM2 AKTIF
echo ======================================================================
echo.
call %PM2_CMD% status
echo.
pause
goto MENU

:LOGS_PM2
cls
echo ======================================================================
echo                 LOG REALTIME LAYANAN (Ctrl+C untuk keluar)
echo ======================================================================
echo.
call %PM2_CMD% logs
pause
goto MENU

:RESTART_PM2
cls
echo ======================================================================
echo                     MERESTART SEMUA LAYANAN PM2
echo ======================================================================
echo.
call %PM2_CMD% restart all
echo.
echo [+] Semua layanan berhasil direstart!
pause
goto MENU

:STOP_PM2
cls
echo ======================================================================
echo                   MENGHENTIKAN SEMUA LAYANAN PM2
echo ======================================================================
echo.
call %PM2_CMD% stop all
echo.
echo [-] Semua layanan telah dihentikan.
pause
goto MENU

:OPEN_BROWSER
start https://triomerak.web.id/pos
start http://%LOCAL_IP%:5000/pos
goto MENU

:: ======================================================================
:: MANUAL FOREGROUND MODE
:: ======================================================================

:RUN_FOREGROUND
cls
echo ======================================================================
echo          MENJALANKAN SERVER ^& BOT SECARA MANUAL (CMD WINDOWS)
echo ======================================================================
echo.
echo [*] Membuka jendela CMD untuk Bot Telegram...
start "Coins.ph - Telegram Bot" cmd /k "cd /d ""%~dp0"" && call .venv\Scripts\activate.bat && python core\bot.py"

echo [*] Membuka browser ke POS Kasir...
start http://%LOCAL_IP%:5000/pos

echo [*] Menjalankan Server Web API pada jendela ini...
echo.
cd core
"..\.venv\Scripts\python.exe" api_server.py
pause
goto MENU

:ERROR
color 0c
echo [ERROR] Terjadi kegagalan konfigurasi!
pause
exit /b 1
