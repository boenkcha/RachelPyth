@echo off
title AppClinic Server
color 0A
cd /d "%~dp0"

REM Pakai virtual environment bila ada (hasil INSTALL.bat)
if exist ".venv\Scripts\activate.bat" (
  call ".venv\Scripts\activate.bat"
) else (
  echo [info] .venv belum ada. Jalankan INSTALL.bat dulu untuk hasil terbaik.
)

REM Muat konfigurasi database (AC_DB_BACKEND / AC_MYSQL_*) hasil INSTALL.bat
if exist "appclinic.env.bat" (
  call "appclinic.env.bat"
) else (
  echo [info] appclinic.env.bat belum ada. Jalankan INSTALL.bat dulu untuk setup database.
)

python run_server.py

echo.
echo  Server berhenti.
pause
