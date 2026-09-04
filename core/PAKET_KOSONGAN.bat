@echo off
title BUAT PAKET KOSONGAN - Coins.ph Gateway
color 0b
cd /d "%~dp0.."

:: Detect Python executable
set "PYEXE=python"
if exist ".venv\Scripts\python.exe" (
    set "PYEXE=.venv\Scripts\python.exe"
)

%PYEXE% --version >nul 2>&1
if errorlevel 1 goto NO_PYTHON

%PYEXE% core\package_clean.py
if errorlevel 1 goto ERROR_PACK

echo.
echo ======================================================================
echo   [BERHASIL] File ZIP paket kosongan murni sudah siap!
echo.
echo   Langkah Penggunaan di PC Baru:
echo   1. Salin file ZIP ke komputer baru ^& ekstrak.
echo   2. Jalankan 'INSTALL_REQUIREMENTS.bat' sekali saja.
echo   3. Buka 'START_SERVER.bat' untuk menjalankan kasir.
echo   4. Buka kasir POS dan klik 'Tambah Slot Akun' untuk memasukkan akun.
echo ======================================================================
echo.
pause
exit /b 0

:NO_PYTHON
color 0c
echo [ERROR] Python tidak ditemukan! Pastikan sudah install Python.
pause
exit /b 1

:ERROR_PACK
color 0c
echo [ERROR] Gagal membuat paket ZIP!
pause
exit /b 1
