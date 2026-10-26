@echo off
REM Launcher untuk skrip pembuat paket instalasi (PowerShell).
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0BUAT-PAKET-INSTALL.ps1"
