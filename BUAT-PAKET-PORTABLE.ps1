# ============================================================
#  MEMBUAT PAKET PORTABLE RACHEL CLINIC
#  Hasil: folder + zip di Desktop berisi Python mini + aplikasi.
#  Komputer tujuan TIDAK perlu install Python -> tinggal copy & klik JALANKAN.bat
#
#  Mode:
#    .\BUAT-PAKET-PORTABLE.ps1            -> rebuild penuh (unduh Python embeddable)
#    .\BUAT-PAKET-PORTABLE.ps1 -QuickCode -> hanya perbarui kode app ke paket yg sudah ada
#                                            (cepat; tidak unduh ulang Python)
# ============================================================
param([switch]$QuickCode)

$ErrorActionPreference = 'Stop'
$src     = $PSScriptRoot
$dest    = Join-Path ([Environment]::GetFolderPath('Desktop')) 'RachelClinic-Portable'
$pyDir   = Join-Path $dest 'python'
$pyExe   = Join-Path $pyDir 'python.exe'
$PYVER   = '3.12.7'           # versi Python embeddable yang stabil + ada semua wheel

function Copy-AppCode {
    # File inti aplikasi (Barang.csv = sumber seed master Barang di first-run DB kosong)
    foreach ($f in @('app.py','run_server.py','backup_db.py','requirements.txt','Barang.csv','PANDUAN-SERVER.md')) {
        $p = Join-Path $src $f
        if (Test-Path $p) { Copy-Item $p -Destination $dest -Force }
    }
    # static: hanya file di root (html + logo), siapkan folder uploads kosong
    $staticDst = Join-Path $dest 'static'
    New-Item -ItemType Directory -Path $staticDst -Force | Out-Null
    Get-ChildItem (Join-Path $src 'static') -File | Copy-Item -Destination $staticDst -Force
    New-Item -ItemType Directory -Path (Join-Path $staticDst 'uploads\foto_pasien') -Force | Out-Null
}

# ---------- MODE CEPAT: hanya perbarui kode ----------
if ($QuickCode) {
    if (-not (Test-Path $pyExe)) {
        Write-Host "[GAGAL] Paket belum ada. Jalankan tanpa -QuickCode dulu." -ForegroundColor Red
        exit 1
    }
    Write-Host "Memperbarui kode aplikasi ke paket yang sudah ada ..."
    Copy-AppCode
    Write-Host "[OK] Kode diperbarui. (Python & library tidak diubah.)" -ForegroundColor Green
    exit 0
}

# ---------- MODE PENUH ----------
Write-Host '============================================================'
Write-Host '  MEMBUAT PAKET PORTABLE RACHEL CLINIC (rebuild penuh)'
Write-Host '============================================================'

if (Test-Path $dest) {
    $ans = Read-Host "Folder '$dest' sudah ada. Hapus & buat ulang? (y/n)"
    if ($ans -eq 'y') { Remove-Item $dest -Recurse -Force } else { Write-Host 'Dibatalkan.'; exit }
}
New-Item -ItemType Directory -Path $pyDir -Force | Out-Null

# 1) Unduh Python embeddable + get-pip
$tmp = Join-Path $env:TEMP 'rc_portable_tmp'
New-Item -ItemType Directory -Path $tmp -Force | Out-Null
$embedZip = Join-Path $tmp "python-$PYVER-embed.zip"
$getpip   = Join-Path $tmp 'get-pip.py'
if (-not (Test-Path $embedZip)) {
    Write-Host "Mengunduh Python $PYVER embeddable ..."
    Invoke-WebRequest -Uri "https://www.python.org/ftp/python/$PYVER/python-$PYVER-embed-amd64.zip" -OutFile $embedZip -UseBasicParsing
}
if (-not (Test-Path $getpip)) {
    Write-Host 'Mengunduh get-pip.py ...'
    Invoke-WebRequest -Uri 'https://bootstrap.pypa.io/get-pip.py' -OutFile $getpip -UseBasicParsing
}
Expand-Archive -Path $embedZip -DestinationPath $pyDir -Force

# 2) Aktifkan site + tambahkan folder app (..) ke path embeddable
$pth = Get-ChildItem $pyDir -Filter '*._pth' | Select-Object -First 1
@"
$($pth.BaseName).zip
.
..
Lib\site-packages

import site
"@ | Set-Content -Path $pth.FullName -Encoding ascii

# 3) Pasang pip + dependensi
Write-Host 'Memasang pip ...'
& $pyExe $getpip --no-warn-script-location
Write-Host 'Memasang flask, pillow, waitress ...'
& $pyExe -m pip install --no-warn-script-location flask pillow waitress

# 4) Salin kode aplikasi
Copy-AppCode

# 5) Tulis launcher + panduan
$jalankan = @"
@echo off
title Rachel Clinic Server (Portable)
color 0A
cd /d "%~dp0"
python\python.exe run_server.py
echo.
echo  Server berhenti.
pause
"@
$backup = @"
@echo off
title Backup Database Rachel Clinic
color 0B
cd /d "%~dp0"
python\python.exe backup_db.py
echo.
pause
"@
$firewall = @"
@echo off
title Buka Port 5000
color 0E
cd /d "%~dp0"
net session >nul 2>&1
if errorlevel 1 (
  echo [PERLU ADMIN] Klik kanan file ini - Run as administrator.
  pause
  exit /b 1
)
netsh advfirewall firewall delete rule name="Rachel Clinic Server" >nul 2>&1
netsh advfirewall firewall add rule name="Rachel Clinic Server" dir=in action=allow protocol=TCP localport=5000
echo Port 5000 dibuka. Komputer lain kini bisa terhubung.
pause
"@
Set-Content (Join-Path $dest 'JALANKAN.bat')      $jalankan -Encoding ascii
Set-Content (Join-Path $dest 'BACKUP-DATA.bat')   $backup   -Encoding ascii
Set-Content (Join-Path $dest 'BUKA-FIREWALL.bat') $firewall -Encoding ascii
# CARA-PAKAI.txt dipertahankan bila sudah ada; kalau belum, beri catatan singkat
if (-not (Test-Path (Join-Path $dest 'CARA-PAKAI.txt'))) {
    Set-Content (Join-Path $dest 'CARA-PAKAI.txt') "Klik dua kali JALANKAN.bat untuk menghidupkan server. Login awal: admin / admin123. Lihat PANDUAN-SERVER.md untuk jaringan." -Encoding utf8
}

# 6) Zip
$zip = "$dest.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
Write-Host 'Membuat ZIP ...'
Compress-Archive -Path $dest -DestinationPath $zip -CompressionLevel Optimal

Write-Host ''
Write-Host '============================================================' -ForegroundColor Green
Write-Host '  SELESAI' -ForegroundColor Green
Write-Host "  Folder : $dest"
Write-Host "  Zip    : $zip"
Write-Host '  Salin folder/zip ke komputer tujuan, klik JALANKAN.bat.'
Write-Host '============================================================'
