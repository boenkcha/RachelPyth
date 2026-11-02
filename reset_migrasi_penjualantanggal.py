"""
Hapus HANYA batch migrasi_penjualantanggal yang sudah terlanjur masuk dengan
logika LAMA (sebelum perbaikan pencocokan-by-nama, perbaikan koneksi DB, &
perbaikan mapping kolom staf/pasien yg sebelumnya TERTUKAR) -- supaya bisa
dieksekusi ulang bersih dari awal dengan logika yang benar.

Faktur ditandai lewat kolom Penjualan.kasir = KASIR_MARKER (samakan dengan
field "Nama Kasir (default)" yang diisi saat eksekusi kemarin). Master
auto-create (Pasien/Barang/produk_pelayanan/Karyawan) ditandai lewat prefix
"⚠" di nama-nya (lihat app.py migrasi_penjualantanggal_eksekusi) -- termasuk
yg kemarin SALAH dibuat (kode pasien nyasar jadi "karyawan") krn mapping
kolom yg waktu itu masih keliru. HANYA baris dengan marker2 itu yang disentuh
-- data normal/manual TIDAK disentuh.

Backup penuh (format sama dgn menu Backup aplikasi) dibuat otomatis dulu
sebelum apa pun dihapus.

Jalankan:
    AC_MYSQL_PASSWORD='password_anda' python3 reset_migrasi_penjualantanggal.py
"""
import os
import sys
import gzip
import json
from datetime import datetime

import app as _app

KASIR_MARKER = 'migrasi'  # samakan dengan field "Nama Kasir (default)" yang dipakai saat eksekusi kemarin


def buat_backup():
    table_names = [t[0] for t in _app._MYSQL_TABLES]
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'backup_{ts}_sebelum_reset_migrasi.jsonl.gz'
    path = os.path.join(_app.BACKUP_DIR, filename)
    os.makedirs(_app.BACKUP_DIR, exist_ok=True)

    con = _app.get_db()
    total_rows, tables_done = 0, 0
    try:
        cur = con.cursor()
        meta = {'__meta__': True, 'created_at': str(datetime.now()),
                'keterangan': 'Otomatis — sebelum reset_migrasi_penjualantanggal.py dijalankan',
                'created_by': 'reset_migrasi_penjualantanggal.py', 'db_backend': _app.DB_BACKEND,
                'tables': table_names}
        with gzip.open(path, 'wt', encoding='utf-8') as gz:
            gz.write(json.dumps(meta, ensure_ascii=False) + '\n')
            for tname in table_names:
                try:
                    cur.execute(f"SELECT * FROM {tname}")
                except Exception:
                    continue
                gz.write(json.dumps({'__table__': tname}) + '\n')
                n = 0
                while True:
                    batch = cur.fetchmany(2000)
                    if not batch:
                        break
                    for row in batch:
                        gz.write(json.dumps(dict(row), ensure_ascii=False, default=str) + '\n')
                        n += 1
                gz.write(json.dumps({'__table_end__': tname, 'row_count': n}) + '\n')
                total_rows += n
                tables_done += 1
    finally:
        con.close()

    record = {
        'filename': filename, 'keterangan': 'Otomatis — sebelum reset_migrasi_penjualantanggal.py dijalankan',
        'created_by': 'reset_migrasi_penjualantanggal.py', 'created_at': str(datetime.now()),
        'size_bytes': os.path.getsize(path), 'tables_count': tables_done,
        'total_rows': total_rows, 'db_backend': _app.DB_BACKEND,
    }
    items = _app._backup_load_index()
    items.append(record)
    _app._backup_save_index(items)
    print(f"[OK] Backup dibuat: {filename} ({tables_done} tabel, {total_rows} baris) "
          f"— muncul juga di menu Backup aplikasi, bisa dipulihkan dari situ kalau perlu.")


FLAG_PASIEN = '⚠ Perlu dilengkapi%'
FLAG_BARANG = '⚠ PERLU KODE%'
FLAG_PELAYANAN = '⚠ PERLU DATA ASLI%'
FLAG_KARYAWAN = '⚠ Perlu dilengkapi%'


def hitung():
    n = {}
    n['Penjualan'] = _app.query("SELECT COUNT(*) AS n FROM Penjualan WHERE kasir=?", (KASIR_MARKER,), one=True)['n']
    n['R_Penjualan'] = _app.query("""SELECT COUNT(*) AS n FROM R_Penjualan
        WHERE no_faktur IN (SELECT no_faktur FROM Penjualan WHERE kasir=?)""", (KASIR_MARKER,), one=True)['n']
    n['RiwayatBarang'] = _app.query("SELECT COUNT(*) AS n FROM RiwayatBarang WHERE keterangan LIKE 'Migrasi susulan%'", one=True)['n']
    n['Point_karyawan'] = _app.query("""SELECT COUNT(*) AS n FROM Point_karyawan
        WHERE no_faktur IN (SELECT no_faktur FROM Penjualan WHERE kasir=?)""", (KASIR_MARKER,), one=True)['n']
    n['DetailPoint'] = _app.query("""SELECT COUNT(*) AS n FROM DetailPoint
        WHERE keterangan IN (SELECT no_faktur FROM Penjualan WHERE kasir=?)""", (KASIR_MARKER,), one=True)['n']
    n['Pasien (⚠ auto-create)'] = _app.query("SELECT COUNT(*) AS n FROM Pasien WHERE nm_pasien LIKE ?", (FLAG_PASIEN,), one=True)['n']
    n['Barang (⚠ auto-create)'] = _app.query("SELECT COUNT(*) AS n FROM Barang WHERE nm_barang LIKE ?", (FLAG_BARANG,), one=True)['n']
    n['Stok_barang (⚠ auto-create)'] = _app.query("SELECT COUNT(*) AS n FROM Stok_barang WHERE nm_barang LIKE ?", (FLAG_BARANG,), one=True)['n']
    n['produk_pelayanan (⚠ auto-create)'] = _app.query("SELECT COUNT(*) AS n FROM produk_pelayanan WHERE nm_pelayanan LIKE ?", (FLAG_PELAYANAN,), one=True)['n']
    n['Karyawan (⚠ auto-create)'] = _app.query("SELECT COUNT(*) AS n FROM Karyawan WHERE nm_karyawan LIKE ?", (FLAG_KARYAWAN,), one=True)['n']
    return n


def reset():
    con = _app.get_raw_db(timeout=120)
    cur = con.cursor()
    cur.execute("PRAGMA foreign_keys = OFF")

    cur.execute("""DELETE FROM DetailPoint
        WHERE keterangan IN (SELECT no_faktur FROM Penjualan WHERE kasir=?)""", (KASIR_MARKER,))
    cur.execute("""DELETE FROM Point_karyawan
        WHERE no_faktur IN (SELECT no_faktur FROM Penjualan WHERE kasir=?)""", (KASIR_MARKER,))
    cur.execute("DELETE FROM RiwayatBarang WHERE keterangan LIKE 'Migrasi susulan%'")
    cur.execute("""DELETE FROM R_Penjualan
        WHERE no_faktur IN (SELECT no_faktur FROM Penjualan WHERE kasir=?)""", (KASIR_MARKER,))
    cur.execute("DELETE FROM Penjualan WHERE kasir=?", (KASIR_MARKER,))

    # Master auto-create (termasuk yg kemarin salah: kode pasien nyasar jadi
    # "karyawan" krn mapping kolom staf/pasien yg waktu itu masih tertukar).
    cur.execute("DELETE FROM Pasien WHERE nm_pasien LIKE ?", (FLAG_PASIEN,))
    cur.execute("DELETE FROM Stok_barang WHERE nm_barang LIKE ?", (FLAG_BARANG,))
    cur.execute("DELETE FROM Barang WHERE nm_barang LIKE ?", (FLAG_BARANG,))
    cur.execute("DELETE FROM produk_pelayanan WHERE nm_pelayanan LIKE ?", (FLAG_PELAYANAN,))
    cur.execute("DELETE FROM Karyawan WHERE nm_karyawan LIKE ?", (FLAG_KARYAWAN,))

    cur.execute("PRAGMA foreign_keys = ON")
    con.commit()
    con.close()


def _cetak(n):
    for k, v in n.items():
        print(f"  {k:32s}: {v}")


def main():
    print(f"Backend aktif: {_app.DB_BACKEND} | Database: {_app.MYSQL_CONFIG.get('database') if _app.DB_BACKEND=='mysql' else _app.DB_PATH}")
    print(f"Marker kasir yang akan dihapus: '{KASIR_MARKER}'\n")

    n = hitung()
    print("=== Yang akan dihapus ===")
    _cetak(n)

    if n['Penjualan'] == 0 and all(v == 0 for k, v in n.items() if k != 'Penjualan'):
        print("\nTidak ada data dengan marker ini. Tidak ada yang dihapus.")
        sys.exit(0)

    jawab = input("\nLanjutkan hapus batch ini? Backup penuh dibuat dulu. (ketik 'YA' untuk lanjut): ").strip()
    if jawab != 'YA':
        print("Dibatalkan.")
        sys.exit(0)

    print("\n=== Membuat backup ===")
    buat_backup()

    print("\n=== Menghapus batch migrasi lama ===")
    reset()

    print("\n=== Verifikasi sesudah ===")
    _cetak(hitung())
    print("\nSelesai. Sekarang bisa upload ulang CSV & eksekusi lagi dari awal lewat UI migrasi_penjualantanggal.html.")


if __name__ == '__main__':
    main()
