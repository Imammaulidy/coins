@echo off
title Coins.ph Multi-Account QR Ph Payment Gateway Server
color 0b
cd /d "%~dp0"

echo ======================================================================
echo           COINS.PH DYNAMIC QR PH PAYMENT GATEWAY SERVER
echo ======================================================================
echo.

:: 1. Check / Setup Virtual Environment
if not exist ".venv\Scripts\python.exe" (
    echo [INFO] Virtual Environment belum ditemukan.
    echo Menjalankan instalasi requirement otomatis...
    call INSTALL_REQUIREMENTS.bat
    if errorlevel 1 goto ERROR
)

:: 2. Deteksi IP Dinamis Local LAN
for /f %%i in ('.venv\Scripts\python.exe core\get_ip.py') do set LOCAL_IP=%%i
if "%LOCAL_IP%"=="" (
    echo [ERROR] IP Local LAN tidak terdeteksi!
    goto ERROR
)

:: 3. Buka Browser Otomatis ke POS Kasir (Lewat IP:PORT Otomatis)
echo [1/2] Membuka browser ke http://%LOCAL_IP%:5000/pos ...
start http://%LOCAL_IP%:5000/pos

:: 4. Jalankan Server
echo.
echo ======================================================================
echo   SERVER BERHASIL DIJALANKAN (HOST DILAYANI HANYA LEWAT IP:PORT)!
echo   - POS Kasir (PC / HP / Device) : http://%LOCAL_IP%:5000/pos
echo   - Dashboard Riwayat Transaksi  : http://%LOCAL_IP%:5000/dashboard
echo   - REST API Endpoint            : http://%LOCAL_IP%:5000/api/payment/create
echo   - Live Rate Engine             : http://%LOCAL_IP%:5000/api/rate
echo   - Status Web3 Wallet           : http://%LOCAL_IP%:5000/api/wallet/status
echo ======================================================================
echo.
echo [INFO] Jangan tutup jendela CMD ini selama kasir digunakan!
echo.

cd core
"..\.venv\Scripts\python.exe" api_server.py
pause
exit /b 0

:ERROR
color 0c
echo [ERROR] Gagal menjalankan server!
pause
exit /b 1
