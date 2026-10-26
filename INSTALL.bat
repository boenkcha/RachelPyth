@echo off
title Instalasi Rachel Clinic Server
color 0A
cd /d "%~dp0"

echo ============================================================
echo    INSTALASI RACHEL CLINIC - SERVER
echo ============================================================
echo.

REM --- Cek hak Administrator (untuk aturan firewall) ---
net session >nul 2>&1
if errorlevel 1 (
  echo [PERINGATAN] Tidak dijalankan sebagai Administrator.
  echo              Aturan firewall mungkin gagal dibuat sehingga
  echo              komputer lain TIDAK bisa terhubung.
  echo              Disarankan: klik kanan INSTALL.bat - Run as administrator.
  echo.
  pause
)

REM --- 1. Cek Python ---
python --version >nul 2>&1
if errorlevel 1 (
  echo [GAGAL] Python belum terpasang di komputer ini.
  echo.
  echo  Silakan install Python 3.8+ dari: https://www.python.org/downloads
  echo  PENTING: saat instalasi centang "Add Python to PATH".
  echo  Setelah Python terpasang, jalankan INSTALL.bat lagi.
  echo.
  pause
  exit /b 1
)
echo [OK] Python ditemukan:
python --version
echo.

REM --- 2. Buat virtual environment ---
if not exist ".venv\Scripts\python.exe" (
  echo Membuat lingkungan Python lokal (.venv) ...
  python -m venv .venv
  if errorlevel 1 (
    echo [GAGAL] Tidak bisa membuat .venv
    pause
    exit /b 1
  )
)

REM --- 3. Pasang dependensi ---
echo.
echo Memasang dependensi (flask, pillow, waitress) ...
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo [GAGAL] Pemasangan dependensi gagal. Periksa koneksi internet lalu ulangi.
  pause
  exit /b 1
)

REM --- 4. Buka port 5000 di Windows Firewall (idempotent) ---
echo.
echo Membuka port 5000 di Windows Firewall ...
netsh advfirewall firewall delete rule name="Rachel Clinic Server" >nul 2>&1
netsh advfirewall firewall add rule name="Rachel Clinic Server" dir=in action=allow protocol=TCP localport=5000 >nul 2>&1

echo.
echo ============================================================
echo    INSTALASI SELESAI
echo.
echo    Jalankan server dengan klik dua kali: jalankan_server.bat
echo    Lalu komputer kasir buka alamat http://(IP-server):5000
echo ============================================================
pause
