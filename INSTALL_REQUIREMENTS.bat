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
echo [2/2] Sedang menginstall modul requirement...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r core\requirements.txt
if exist "core\requirements-desktop.txt" (
    .venv\Scripts\python.exe -m pip install -r core\requirements-desktop.txt
)
if errorlevel 1 goto ERROR_PIP

:: 3. Cek / Install Node.js PM2 Process Manager
echo.
echo [3/3] Memeriksa PM2 Process Manager (Background 24/7)...
where pm2 >nul 2>&1
if errorlevel 1 (
    where npm >nul 2>&1
    if not errorlevel 1 (
        echo [*] Menginstall PM2 dan pm2-windows-startup via npm...
        call npm install -g pm2 pm2-windows-startup
        call pm2-startup install >nul 2>&1
    ) else if exist "C:\Program Files\nodejs\npm.cmd" (
        echo [*] Menginstall PM2 dan pm2-windows-startup...
        call "C:\Program Files\nodejs\npm.cmd" install -g pm2 pm2-windows-startup
        call "%APPDATA%\npm\pm2-startup.cmd" install >nul 2>&1
    )
) else (
    echo [OK] PM2 sudah terpasang dan siap digunakan.
)

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
