@echo off
title Rachel Clinic Server
color 0A
cd /d "%~dp0"

REM Pakai virtual environment bila ada (hasil INSTALL.bat)
if exist ".venv\Scripts\activate.bat" (
  call ".venv\Scripts\activate.bat"
) else (
  echo [info] .venv belum ada. Jalankan INSTALL.bat dulu untuk hasil terbaik.
)

python run_server.py

echo.
echo  Server berhenti.
pause
