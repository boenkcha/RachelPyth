@echo off
REM ============================================================
REM  Rachel Clinic -- Build Server jadi file .exe (PyInstaller)
REM  Jalankan file ini DI KOMPUTER WINDOWS (bukan di Mac).
REM  Python 3.10+ harus sudah terpasang & tercentang "Add to PATH".
REM ============================================================
cd /d "%~dp0"

echo [1/4] Membuat virtual environment build...
python -m venv .venv_build
call .venv_build\Scripts\activate

echo [2/4] Memasang dependensi aplikasi + PyInstaller...
pip install -r requirements.txt pyinstaller

echo [3/4] Compile app.py + run_server.py menjadi .exe...
pyinstaller --onedir --name RachelClinicServer --noconfirm --console ^
  --hidden-import=pymysql ^
  --hidden-import=waitress ^
  --collect-all PIL ^
  --collect-all openpyxl ^
  run_server.py

echo [4/4] Menyalin folder static/ (wajib ada di sebelah .exe)...
xcopy /E /I /Y static dist\RachelClinicServer\static
if exist Barang.csv copy /Y Barang.csv dist\RachelClinicServer\ >nul

echo.
echo ============================================================
echo  SELESAI. Hasil ada di:  dist\RachelClinicServer\
echo  Pindahkan SELURUH folder itu ke server tujuan,
echo  lalu jalankan RachelClinicServer.exe di dalamnya.
echo ============================================================
pause
