# ============================================================
# migr_export.ps1  — Export RACHEL.mdb ke CSV (jalankan pakai 32-bit PowerShell)
# ============================================================
param([string]$outDir = "d:\App Python\rachel_clinic\migr_temp")

$mdb = "d:\App Python\rachel_clinic\data rachel\RACHEL.mdb"

if (-not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir | Out-Null }

$conn = New-Object -ComObject ADODB.Connection
$conn.Open("Provider=Microsoft.ACE.OLEDB.12.0;Data Source='$mdb';")

# Helper: export satu tabel ke CSV
function ExportTable($tbl, $sql) {
    $outFile = "$outDir\$tbl.csv"
    Write-Host "  Exporting $tbl ..."
    $rs = $conn.Execute($sql)
    $lines = New-Object System.Collections.Generic.List[string]
    # Header
    $hdrs = @()
    for ($i=0; $i -lt $rs.Fields.Count; $i++) { $hdrs += $rs.Fields($i).Name }
    $lines.Add(($hdrs -join "|"))
    # Rows
    $rowCount = 0
    while (-not $rs.EOF) {
        $vals = @()
        foreach ($h in $hdrs) {
            $v = $rs.Fields($h).Value
            if ($null -eq $v -or $v -is [System.DBNull]) { $vals += "" }
            else {
                $s = "$v".Replace("|","//").Replace("`n"," ").Replace("`r"," ")
                $vals += $s
            }
        }
        $lines.Add(($vals -join "|"))
        $rs.MoveNext()
        $rowCount++
        if ($rowCount % 50000 -eq 0) { Write-Host "    ... $rowCount baris" }
    }
    [System.IO.File]::WriteAllLines($outFile, $lines, [System.Text.Encoding]::UTF8)
    Write-Host "    Selesai: $rowCount baris -> $outFile"
}

Write-Host "=== MULAI EXPORT ==="

ExportTable "PasienC"        "SELECT Kd_pasien,Nm_pasien,Alamat,Telepon,HP,Kelamin,T_lahir FROM PasienC"
ExportTable "Karyawan"       "SELECT Kd_karyawan,Nm_karyawan,Nickname,Pekerjaan,Telepon,HP FROM Karyawan"
ExportTable "Suplier"        "SELECT * FROM Suplier" 2>$null
ExportTable "Stok_barang"    "SELECT Kd_barang,Nm_barang,Stok_min,Stok_sisa,Stok_awal,Harga_beli,Harga_beli_awal,Harga,Disc,Satuan,exp,DiscMem,DiscLain,Stok_gudang FROM Stok_barang"
ExportTable "Produk_pelayanan" "SELECT Kd_pelayanan,Nm_pelayanan,Harga,Komisi,Komisi2,Komisi3 FROM Produk_pelayanan"
ExportTable "Penjualan18"    "SELECT No_faktur,Tanggal,Total_harga,HPP,dokter,kd_pasien FROM Penjualan18"
ExportTable "R_penjualan18"  "SELECT No_faktur,Kd_karyawan,Tanggal,Kd_barang,Nm_barang,Qty,Harga,Disc,Sub_total,Kd_pasien,Cashier,Harga_asli,Total_harBeli,exp FROM R_penjualan18"
ExportTable "Hasil_pasien"   "SELECT Kd_pasien,Tanggal,Perawatan,Tarif FROM Hasil_pasien WHERE Perawatan IS NOT NULL AND Perawatan <> ''"
ExportTable "Point_karyawan" "SELECT No_faktur,Tanggal,Kd_pasien,Kd_pelayanan,Nm_Pelayanan,Komisi,Kd_karyawan FROM Point_karyawan"
ExportTable "RiwayatBarang"  "SELECT Tanggal,Kd_barang,Exp,Keterangan,Nilai,SaldoE,SaldoG FROM RiwayatBarangBackup"
ExportTable "Tindakan"       "SELECT Tanggal,Kd_pelayanan,Banyaknya FROM Tindakan"
ExportTable "Log"            "SELECT Tanggal,Keterangan,Qty,Kasir,Event FROM Log"
ExportTable "Nomor"          "SELECT Tanggal,Nota_jual,Nota_piutang,Nota_resep FROM Nomor"
ExportTable "TKredit"        "SELECT Nota,Konsumen,Total,Bank,Kasir,Tanggal FROM Tkredit"
ExportTable "TKunjunganBerikut" "SELECT No_faktur,Next_tanggal,Kd_pasien FROM TKunjunganBerikut"
ExportTable "R_pembelian"    "SELECT No_faktur,Tanggal,Sistem_bayar,Tempo,Kd_barang,Nm_barang,Qty,Harga_beli_kotor,Sub_total,Kd_Suplier,Nm_suplier,Harga_beli_bersih,Disc,PPN,Harga_asli,satuan,exp FROM R_pembelian"
ExportTable "Pembelian"      "SELECT No_faktur,Tanggal,Total_harga,Sistem_bayar,Lunas,Nm_suplier,Tempo FROM Pembelian"

$conn.Close()
Write-Host ""
Write-Host "=== EXPORT SELESAI. File ada di: $outDir ==="
