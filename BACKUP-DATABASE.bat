@echo off
title Backup Database AppClinic
color 0E
cd /d "%~dp0"

if exist ".venv\Scripts\activate.bat" (
  call ".venv\Scripts\activate.bat"
)
if exist "appclinic.env.bat" (
  call "appclinic.env.bat"
)

if /i "%AC_DB_BACKEND%"=="mysql" goto BACKUP_MYSQL

echo Membuat backup database SQLite ...
python backup_db.py
goto END

:BACKUP_MYSQL
mysqldump --version >nul 2>&1
if errorlevel 1 (
  echo [GAGAL] Perintah "mysqldump" tidak ditemukan - pastikan folder bin MySQL
  echo         ada di PATH ^(biasanya sama dengan folder perintah "mysql"^).
  pause
  exit /b 1
)
if not exist "backup" mkdir "backup"

set TSTAMP=
for /f "delims=" %%T in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set TSTAMP=%%T
if "%TSTAMP%"=="" (
  echo [GAGAL] Tidak bisa membuat nama file backup ^(PowerShell gagal dijalankan^).
  pause
  exit /b 1
)

echo Membuat backup database MySQL "%AC_MYSQL_DB%" ...
mysqldump -u %AC_MYSQL_USER% -p%AC_MYSQL_PASSWORD% -h %AC_MYSQL_HOST% -P %AC_MYSQL_PORT% %AC_MYSQL_DB% > "backup\appclinic_%TSTAMP%.sql"
if errorlevel 1 (
  echo [GAGAL] Backup MySQL gagal. Cek kredensial/koneksi di appclinic.env.bat,
  echo         dan pastikan service MySQL sedang berjalan.
  pause
  exit /b 1
)
echo [OK] Backup tersimpan: backup\appclinic_%TSTAMP%.sql
goto END

:END
echo.
echo Backup tersimpan di folder: backup\
pause
