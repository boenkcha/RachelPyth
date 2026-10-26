# Membuat paket instalasi server Rachel Clinic yang bersih.
# Hasil: folder + zip di Desktop, berisi hanya file yang diperlukan
# (tanpa .venv, cache, skrip dev, atau database — kecuali Anda memilih menyertakannya).

$ErrorActionPreference = 'Stop'
$src  = $PSScriptRoot
$dest = Join-Path ([Environment]::GetFolderPath('Desktop')) 'RachelClinic-Server'

Write-Host '============================================================'
Write-Host '  MEMBUAT PAKET INSTALASI RACHEL CLINIC - SERVER'
Write-Host '============================================================'

if (Test-Path $dest) {
    $ans = Read-Host "Folder '$dest' sudah ada. Hapus & buat ulang? (y/n)"
    if ($ans -eq 'y') { Remove-Item $dest -Recurse -Force }
    else { Write-Host 'Dibatalkan.'; exit }
}
New-Item -ItemType Directory -Path $dest -Force | Out-Null

# --- File inti aplikasi & installer ---
$files = @(
    'app.py','run_server.py','backup_db.py','requirements.txt',
    'INSTALL.bat','jalankan_server.bat','BACKUP-DATABASE.bat',
    'PANDUAN-SERVER.md','README.md','Barang.csv'
)
foreach ($f in $files) {
    $p = Join-Path $src $f
    if (Test-Path $p) { Copy-Item $p -Destination $dest }
    else { Write-Host "  (lewati, tidak ada: $f)" -ForegroundColor DarkYellow }
}

# --- Folder static (html + logo), TANPA isi uploads ---
$staticSrc = Join-Path $src  'static'
$staticDst = Join-Path $dest 'static'
New-Item -ItemType Directory -Path $staticDst -Force | Out-Null
Get-ChildItem $staticSrc -File | Copy-Item -Destination $staticDst
New-Item -ItemType Directory -Path (Join-Path $staticDst 'uploads\foto_pasien') -Force | Out-Null

# --- Sertakan database & foto saat ini? ---
$inc = Read-Host 'Sertakan database & foto saat ini untuk PINDAH DATA? (y = pindah data / n = cabang baru kosong)'
if ($inc -eq 'y') {
    $db = Join-Path $src 'rachel_clinic.db'
    if (Test-Path $db) {
        Copy-Item $db -Destination $dest
        Write-Host '  + rachel_clinic.db disertakan' -ForegroundColor Yellow
    }
    $up = Join-Path $staticSrc 'uploads'
    if (Test-Path $up) {
        Copy-Item $up -Destination $staticDst -Recurse -Force
        Write-Host '  + foto pasien (static\uploads) disertakan' -ForegroundColor Yellow
    }
} else {
    Write-Host '  Paket dibuat TANPA database (server cabang baru = DB kosong otomatis).' -ForegroundColor Yellow
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
