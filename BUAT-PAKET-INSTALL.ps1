# Membuat paket instalasi server AppClinic yang bersih.
# Hasil: folder + zip di Desktop, berisi hanya file yang diperlukan
# (tanpa .venv, cache, skrip dev, config/password lokal, atau database —
# kecuali Anda memilih menyertakan database SQLite untuk pindah data).

$ErrorActionPreference = 'Stop'
$src  = $PSScriptRoot
$dest = Join-Path ([Environment]::GetFolderPath('Desktop')) 'AppClinic-Server'

Write-Host '============================================================'
Write-Host '  MEMBUAT PAKET INSTALASI APPCLINIC - SERVER'
Write-Host '============================================================'

if (Test-Path $dest) {
    $ans = Read-Host "Folder '$dest' sudah ada. Hapus & buat ulang? (y/n)"
    if ($ans -eq 'y') { Remove-Item $dest -Recurse -Force }
    else { Write-Host 'Dibatalkan.'; exit }
}
New-Item -ItemType Directory -Path $dest -Force | Out-Null

# --- File inti aplikasi & installer ---
# (appclinic.env.bat SENGAJA tidak ada di daftar ini — itu file config+password
# lokal milik 1 instalasi, dibuat sendiri oleh INSTALL.bat di server tujuan,
# bukan sesuatu yang boleh ikut disalin/dibagikan dari sini.)
$files = @(
    'app.py','run_server.py','backup_db.py','requirements.txt',
    'INSTALL.bat','jalankan_server.bat','BACKUP-DATABASE.bat',
    'PANDUAN-SERVER.md','README.md'
)
foreach ($f in $files) {
    $p = Join-Path $src $f
    if (Test-Path $p) { Copy-Item $p -Destination $dest }
    else { Write-Host "  (lewati, tidak ada: $f)" -ForegroundColor DarkYellow }
}

# --- Folder static (html, logo, font, dst — SEMUA kecuali uploads & mockups) ---
$staticSrc = Join-Path $src  'static'
$staticDst = Join-Path $dest 'static'
New-Item -ItemType Directory -Path $staticDst -Force | Out-Null
Get-ChildItem $staticSrc -Force | Where-Object {
    $_.Name -ne 'uploads' -and $_.Name -ne 'mockups'
} | ForEach-Object {
    Copy-Item $_.FullName -Destination $staticDst -Recurse -Force
}
New-Item -ItemType Directory -Path (Join-Path $staticDst 'uploads\foto_pasien') -Force | Out-Null

# --- Sertakan database SQLite & foto saat ini? (hanya relevan kalau instance
#     sumber ini memakai backend SQLite, bukan MySQL) ---
$inc = Read-Host 'Sertakan database SQLite & foto saat ini untuk PINDAH DATA? (y = pindah data / n = cabang baru kosong)'
if ($inc -eq 'y') {
    $db = Join-Path $src 'appclinic.db'
    if (Test-Path $db) {
        Copy-Item $db -Destination $dest
        Write-Host '  + appclinic.db disertakan' -ForegroundColor Yellow
    } else {
        Write-Host '  ! appclinic.db tidak ditemukan di sini — kalau sumber data Anda' -ForegroundColor Yellow
        Write-Host '    memakai MySQL, pindah data dilakukan lewat mysqldump/import' -ForegroundColor Yellow
        Write-Host '    (lihat PANDUAN-SERVER.md bagian G), bukan lewat paket zip ini.' -ForegroundColor Yellow
    }
    $up = Join-Path $staticSrc 'uploads'
    if (Test-Path $up) {
        Copy-Item $up -Destination $staticDst -Recurse -Force
        Write-Host '  + foto pasien (static\uploads) disertakan' -ForegroundColor Yellow
    }
} else {
    Write-Host '  Paket dibuat TANPA database (server/cabang baru = DB kosong otomatis).' -ForegroundColor Yellow
}

# --- Zip ---
$zip = "$dest.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path $dest -DestinationPath $zip

Write-Host ''
Write-Host '============================================================' -ForegroundColor Green
Write-Host '  SELESAI' -ForegroundColor Green
Write-Host "  Folder : $dest"
Write-Host "  Zip    : $zip"
Write-Host '============================================================'
Write-Host '  Salin folder/zip ini ke komputer server,'
Write-Host '  lalu jalankan INSTALL.bat (klik kanan - Run as administrator).'
Read-Host 'Tekan Enter untuk menutup'
