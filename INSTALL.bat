@echo off
title Instalasi AppClinic Server
color 0A
cd /d "%~dp0"

echo ============================================================
echo    INSTALASI APPCLINIC - SERVER
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
  echo  Silakan install Python 3.10+ dari: https://www.python.org/downloads
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
if exist ".venv\Scripts\python.exe" goto SKIP_VENV
echo Membuat lingkungan Python lokal (.venv) ...
python -m venv .venv
if errorlevel 1 goto VENV_GAGAL
goto SKIP_VENV

:VENV_GAGAL
echo [GAGAL] Tidak bisa membuat .venv
pause
exit /b 1

:SKIP_VENV

REM --- 3. Pasang dependensi ---
echo.
echo Memasang dependensi (flask, pillow, waitress, pymysql, openpyxl) ...
call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo [GAGAL] Pemasangan dependensi gagal. Periksa koneksi internet lalu ulangi.
  pause
  exit /b 1
)

REM --- 4. Setup database (dilewati kalau sudah pernah disetup sebelumnya) ---
if exist "appclinic.env.bat" (
  echo.
  echo [OK] Konfigurasi database sudah ada ^(appclinic.env.bat^) - setup database dilewati.
  echo      Hapus file appclinic.env.bat lalu jalankan INSTALL.bat lagi kalau mau setup ulang.
  goto FIREWALL
)

echo.
echo ============================================================
echo   PILIH DATABASE
echo ============================================================
echo   [1] MySQL   - disarankan, lebih stabil untuk banyak kasir sekaligus.
echo                 Perlu MySQL Server sudah/akan terpasang di komputer ini.
echo   [2] SQLite  - lebih sederhana, 1 file, cocok klinik kecil/1-2 kasir.
echo                 Tidak perlu instalasi tambahan apa pun.
echo.
set /p DBPILIH="Pilih 1 atau 2 lalu Enter: "

if "%DBPILIH%"=="2" goto SETUP_SQLITE
if "%DBPILIH%"=="1" goto SETUP_MYSQL
echo Pilihan tidak dikenali, memakai MySQL ^(disarankan^).
goto SETUP_MYSQL

:SETUP_SQLITE
echo.
echo Memakai SQLite - tidak ada langkah tambahan.
(
  echo @echo off
  echo set AC_DB_BACKEND=sqlite
) > appclinic.env.bat
echo [OK] appclinic.env.bat dibuat ^(mode SQLite^).
goto FIREWALL

:SETUP_MYSQL
echo.
mysql --version >nul 2>&1
if errorlevel 1 (
  echo [GAGAL] Perintah "mysql" tidak ditemukan di komputer ini.
  echo.
  echo  Silakan install MySQL Community Server dulu dari:
  echo  https://dev.mysql.com/downloads/mysql/
  echo  Saat instalasi, centang opsi agar MySQL ditambahkan ke PATH.
  echo  Catat password akun "root" yang Anda buat saat instalasi MySQL.
  echo  Setelah MySQL terpasang, jalankan INSTALL.bat ini lagi.
  echo.
  pause
  exit /b 1
)
echo [OK] MySQL ditemukan:
mysql --version
echo.

echo Membuat password khusus untuk akun aplikasi AppClinic ...
set APPPW=
for /f "delims=" %%P in ('powershell -NoProfile -Command "-join ((48..57)+(65..90)+(97..122)|Get-Random -Count 24|ForEach-Object {[char]$_})"') do set APPPW=%%P
if "%APPPW%"=="" (
  echo [GAGAL] Tidak bisa membuat password acak otomatis ^(PowerShell gagal dijalankan^).
  pause
  exit /b 1
)

echo Membuat database "appclinic" dan akun "appclinic_app" ...
echo ^(Anda akan diminta password akun "root" MySQL - diminta langsung oleh
echo  MySQL, TIDAK tersimpan di mana pun, hanya dipakai sekali di sini.^)
echo.
(
  echo CREATE DATABASE IF NOT EXISTS appclinic CHARACTER SET utf8mb4;
  echo CREATE USER IF NOT EXISTS 'appclinic_app'@'localhost' IDENTIFIED BY '%APPPW%';
  echo ALTER USER 'appclinic_app'@'localhost' IDENTIFIED BY '%APPPW%';
  echo GRANT ALL PRIVILEGES ON appclinic.* TO 'appclinic_app'@'localhost';
  echo FLUSH PRIVILEGES;
) > "%TEMP%\appclinic_setup.sql"
mysql -u root -p < "%TEMP%\appclinic_setup.sql"
if errorlevel 1 (
  echo.
  echo [GAGAL] Setup database MySQL gagal ^(password root salah, atau service
  echo         MySQL belum jalan^). Cek lalu jalankan INSTALL.bat ini lagi.
  del "%TEMP%\appclinic_setup.sql" >nul 2>&1
  pause
  exit /b 1
)
del "%TEMP%\appclinic_setup.sql" >nul 2>&1

(
  echo @echo off
  echo set AC_DB_BACKEND=mysql
  echo set AC_MYSQL_HOST=localhost
  echo set AC_MYSQL_PORT=3306
  echo set AC_MYSQL_USER=appclinic_app
  echo set AC_MYSQL_DB=appclinic
  echo set AC_MYSQL_PASSWORD=%APPPW%
) > appclinic.env.bat
echo [OK] Database "appclinic" + akun "appclinic_app" siap, password tersimpan
echo      di appclinic.env.bat ^(dipakai otomatis oleh jalankan_server.bat^).
set APPPW=

:FIREWALL
REM --- 5. Buka port 5000 di Windows Firewall (idempotent) ---
echo.
echo Membuka port 5000 di Windows Firewall ...
netsh advfirewall firewall delete rule name="AppClinic Server" >nul 2>&1
netsh advfirewall firewall add rule name="AppClinic Server" dir=in action=allow protocol=TCP localport=5000 >nul 2>&1

echo.
echo ============================================================
echo    INSTALASI SELESAI
echo.
echo    Jalankan server dengan klik dua kali: jalankan_server.bat
echo    Lalu komputer kasir buka alamat http://(IP-server-ini):5000
echo    Login awal: admin / admin123 - segera ganti setelah login pertama.
echo ============================================================
pause
