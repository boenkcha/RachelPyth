"""
Audit READ-ONLY (tidak mengubah data apa pun) untuk cek sejauh mana
migrasi_penjualantanggal kemarin benar-benar selesai di tiap tabel
(Penjualan, R_Penjualan, RiwayatBarang, Point_karyawan, DetailPoint).

Faktur hasil migrasi ditandai lewat kolom kasir = KASIR_MARKER di bawah
(sesuaikan kalau nama kasir default yang dipakai saat eksekusi beda).

Jalankan (sama seperti menjalankan app.py, perlu password MySQL yang sama):
    AC_MYSQL_PASSWORD='password_anda' python3 diagnosa_migrasi_penjualantanggal.py
"""
import app as _app

KASIR_MARKER = 'migrasi'  # ganti sesuai yang diisi di field "Nama Kasir (default)" saat eksekusi


def main():
    print(f"Backend aktif: {_app.DB_BACKEND} | Database: {_app.MYSQL_CONFIG.get('database') if _app.DB_BACKEND=='mysql' else _app.DB_PATH}")
    print(f"Marker kasir yang dicari: '{KASIR_MARKER}'\n")

    total_penjualan = _app.query("SELECT COUNT(*) AS n FROM Penjualan WHERE kasir=?", (KASIR_MARKER,), one=True)['n']
    print(f"1. Penjualan (kasir='{KASIR_MARKER}')        : {total_penjualan}")

    total_r = _app.query("""SELECT COUNT(*) AS n FROM R_Penjualan
        WHERE no_faktur IN (SELECT no_faktur FROM Penjualan WHERE kasir=?)""", (KASIR_MARKER,), one=True)['n']
    print(f"2. R_Penjualan (baris detail)              : {total_r}")

    faktur_dgn_detail = _app.query("""SELECT COUNT(DISTINCT no_faktur) AS n FROM R_Penjualan
        WHERE no_faktur IN (SELECT no_faktur FROM Penjualan WHERE kasir=?)""", (KASIR_MARKER,), one=True)['n']
    print(f"   -> faktur yang PUNYA minimal 1 baris detail : {faktur_dgn_detail} / {total_penjualan}")

    faktur_tanpa_detail = total_penjualan - faktur_dgn_detail
    print(f"   -> faktur TANPA detail sama sekali          : {faktur_tanpa_detail}")

    riwayat = _app.query("SELECT COUNT(*) AS n FROM RiwayatBarang WHERE keterangan LIKE 'Migrasi susulan%'", one=True)['n']
    print(f"3. RiwayatBarang (kartu stok tercatat)     : {riwayat}")

    komisi = _app.query("""SELECT COUNT(*) AS n FROM Point_karyawan
        WHERE no_faktur IN (SELECT no_faktur FROM Penjualan WHERE kasir=?)""", (KASIR_MARKER,), one=True)['n']
    print(f"4. Point_karyawan (komisi staf)            : {komisi}")

    poin = _app.query("""SELECT COUNT(*) AS n FROM DetailPoint
        WHERE keterangan IN (SELECT no_faktur FROM Penjualan WHERE kasir=?)""", (KASIR_MARKER,), one=True)['n']
    print(f"5. DetailPoint (poin pasien)               : {poin}")

    # Contoh 5 faktur yang Penjualan-nya ada tapi R_Penjualan-nya kosong (kalau ada)
    contoh = _app.query("""SELECT no_faktur, tanggal, total_harga FROM Penjualan
        WHERE kasir=? AND no_faktur NOT IN (SELECT no_faktur FROM R_Penjualan)
        ORDER BY no_faktur LIMIT 5""", (KASIR_MARKER,))
    if contoh:
        print("\nContoh faktur yang Penjualan ADA tapi R_Penjualan KOSONG:")
        for r in contoh:
            print(f"   {r['no_faktur']} | {r['tanggal']} | Rp{r['total_harga']}")

    print("\nSelesai. Kirim seluruh output di atas untuk didiagnosis lebih lanjut.")


if __name__ == '__main__':
    main()
