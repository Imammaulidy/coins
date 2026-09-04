@echo off
title Install Modul dan Requirement - Coins.ph Gateway
color 0a
cd /d "%~dp0"

echo ======================================================================
echo           INSTALL REQUIREMENT / DEPENDENCIES COINS.PH GATEWAY
echo ======================================================================
echo.

:: 1. Cek Python
python --version >nul 2>&1
if errorlevel 1 goto NO_PYTHON

echo [OK] Python terdeteksi:
python --version
echo.

:: 2. Buat / Cek Virtual Environment
if not exist ".venv\Scripts\python.exe" goto CREATE_VENV
echo [OK] Virtual Environment .venv sudah tersedia.
goto INSTALL_PACKAGES

:CREATE_VENV
echo [1/2] Sedang membuat Virtual Environment .venv...
python -m venv .venv
if errorlevel 1 goto ERROR_VENV
echo [OK] Virtual Environment berhasil dibuat.
goto INSTALL_PACKAGES

:INSTALL_PACKAGES
echo.
echo [2/2] Sedang menginstall modul dari core\requirements.txt...
echo       Modul: flask, qrcode, pillow, requests, zxing-cpp, web3, eth-account
echo.
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\pip.exe install -r core\requirements.txt
if errorlevel 1 goto ERROR_PIP

echo.
echo ======================================================================
echo   [BERHASIL] SEMUA REQUIREMENT TELAH SELESAI DIINSTALL!
echo ======================================================================
echo.
echo Sekarang Anda dapat menjalankan server dengan klik:
echo   - START_SERVER.bat
echo.
echo ======================================================================
pause
exit /b 0

:NO_PYTHON
color 0c
echo [ERROR] Python tidak ditemukan di sistem ini!
echo Silakan install Python 3.10+ terlebih dahulu dari:
echo https://www.python.org/downloads/
echo.
echo PENTING: Saat install, pastikan centang 'Add python.exe to PATH'
echo.
pause
exit /b 1

:ERROR_VENV
color 0c
echo [ERROR] Gagal membuat virtual environment .venv!
pause
exit /b 1

:ERROR_PIP
color 0c
echo [ERROR] Gagal menginstall modul dari core\requirements.txt!
pause
exit /b 1
