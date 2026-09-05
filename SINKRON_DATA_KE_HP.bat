@echo off
title SINKRONISASI DATA COINS.PH (PC -> TERMUX ANDROID)
color 0b
echo =================================================================
echo   SINKRONISASI DATA COINS.PH GATEWAY (PC KE HP TERMUX)
echo =================================================================
echo.
echo Memeriksa koneksi ADB ke HP Android...
adb devices
echo.

where adb >nul 2>nul
if %errorlevel% neq 0 (
    echo [!] Binary ADB tidak ditemukan di PATH.
    pause
    exit /b 1
)

echo Mengirim data database, user, dan kode akses ke HP...
adb shell mkdir -p /sdcard/Download/coins_sync
adb push core\users.json /sdcard/Download/coins_sync/
adb push core\access_codes.json /sdcard/Download/coins_sync/
adb push core\payments.db /sdcard/Download/coins_sync/
adb push core\config.json /sdcard/Download/coins_sync/

echo.
echo =================================================================
echo [+] DATA BERHASIL DIKIRIM KE HP DI: /sdcard/Download/coins_sync/
echo =================================================================
echo.
echo Silakan buka TERMUX di HP dan jalankan perintah:
echo.
echo   cp /sdcard/Download/coins_sync/* ~/coins/core/ ^&^& pm2 restart all
echo.
echo Atau buka menu: bash TERMUX/setup.sh lalu pilih [11] Pulihkan Data.
echo =================================================================
pause
