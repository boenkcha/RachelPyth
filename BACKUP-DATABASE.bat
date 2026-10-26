@echo off
title Backup Database Rachel Clinic
color 0E
cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
  call ".venv\Scripts\activate.bat"
)

echo Membuat backup database ...
python backup_db.py
echo.
echo Backup tersimpan di folder: backup\
pause
