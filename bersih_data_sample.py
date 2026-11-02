"""
Bersih-bersih data sample/testing di database AppClinic, SISAKAN HANYA:
  - Pengguna     (seluruh akun login)
  - Karyawan     (HANYA yang pekerjaan='Dokter' — staf lain/sample dihapus)
  - Pasien       (seluruh data pasien)
  - Lokasi, Pengaturan, produk_pelayanan, Suplier, Induk_Pemilik
    (tabel konfigurasi aplikasi, bukan "data", dipertahankan juga)

Semua tabel lain (Penjualan, R_Penjualan, Barang, Stok_barang, RekamMedik,
ResepRacikan, Point_karyawan, dll — 41 tabel) DIKOSONGKAN TOTAL.

AMAN: backup penuh (format sama persis dgn menu Backup di aplikasi, bisa
dipulihkan lewat menu itu juga) dibuat otomatis ke folder backup/ SEBELUM
apa pun dihapus.

Jalankan (sama seperti menjalankan app.py, perlu password MySQL yang sama):
    AC_MYSQL_PASSWORD='password_anda' python3 bersih_data_sample.py
"""
import os
import sys
import gzip
import json
from datetime import datetime

import app as _app  # noqa: E402  (import app.py sbg modul — reuse DB_BACKEND/MYSQL_CONFIG/koneksi yg sama persis)

KEEP_TABLES = {
    'Pengguna', 'Pasien', 'Lokasi', 'Pengaturan',
    'produk_pelayanan', 'Suplier', 'Induk_Pemilik',
    'Karyawan',   # ditangani khusus (filter role) di bawah, bukan dipertahankan utuh
}


def buat_backup():
    table_names = [t[0] for t in _app._MYSQL_TABLES]
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'backup_{ts}_sebelum_bersih.jsonl.gz'
    path = os.path.join(_app.BACKUP_DIR, filename)
    os.makedirs(_app.BACKUP_DIR, exist_ok=True)

    con = _app.get_db()
    total_rows, tables_done = 0, 0
    try:
        cur = con.cursor()
        meta = {'__meta__': True, 'created_at': str(datetime.now()),
                'keterangan': 'Otomatis — sebelum bersih_data_sample.py dijalankan',
                'created_by': 'bersih_data_sample.py', 'db_backend': _app.DB_BACKEND,
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
        'filename': filename, 'keterangan': 'Otomatis — sebelum bersih_data_sample.py dijalankan',
        'created_by': 'bersih_data_sample.py', 'created_at': str(datetime.now()),
        'size_bytes': os.path.getsize(path), 'tables_count': tables_done,
        'total_rows': total_rows, 'db_backend': _app.DB_BACKEND,
    }
    items = _app._backup_load_index()
    items.append(record)
    _app._backup_save_index(items)
    print(f"[OK] Backup dibuat: {filename} ({tables_done} tabel, {total_rows} baris) "
          f"— muncul juga di menu Backup aplikasi, bisa dipulihkan dari situ kalau perlu.")
    return path


def hitung_sebelum():
    table_names = [t[0] for t in _app._MYSQL_TABLES]
    counts = {}
    for tname in table_names:
        try:
            row = _app.query(f"SELECT COUNT(*) AS n FROM {tname}", one=True)
            counts[tname] = row['n'] if row else 0
        except Exception:
            counts[tname] = None
    return counts


def bersihkan():
    table_names = [t[0] for t in _app._MYSQL_TABLES]
    wipe_tables = [t for t in table_names if t not in KEEP_TABLES]

    con = _app.get_raw_db(timeout=60)
    cur = con.cursor()
    cur.execute("PRAGMA foreign_keys = OFF")

    print(f"\nMengosongkan {len(wipe_tables)} tabel...")
    for t in wipe_tables:
        try:
            cur.execute(f"DELETE FROM {t}")
            print(f"  [hapus] {t}")
        except Exception as e:
            print(f"  [lewati] {t} — {e}")
    con.commit()

    # Karyawan: pertahankan HANYA role Dokter
    try:
        cur.execute("DELETE FROM Karyawan WHERE pekerjaan != 'Dokter'")
        print("  [filter] Karyawan — hanya role 'Dokter' dipertahankan")
    except Exception as e:
        print(f"  [gagal] filter Karyawan — {e}")
    con.commit()

    cur.execute("PRAGMA foreign_keys = ON")
    con.commit()
    con.close()


def main():
    print(f"Backend aktif: {_app.DB_BACKEND} | Database: {_app.MYSQL_CONFIG.get('database') if _app.DB_BACKEND=='mysql' else _app.DB_PATH}")
    print("\n=== Jumlah baris SEBELUM ===")
    before = hitung_sebelum()
    for t, n in before.items():
        print(f"  {t}: {n}")

    print(f"\nTabel yang DIPERTAHANKAN: {', '.join(sorted(KEEP_TABLES - {'Karyawan'}))}, Karyawan (hanya role Dokter)")
    jawab = input("\nLanjutkan? File backup akan dibuat dulu sebelum menghapus apa pun. (ketik 'YA' untuk lanjut): ").strip()
    if jawab != 'YA':
        print("Dibatalkan.")
        sys.exit(0)

    print("\n=== Membuat backup ===")
    buat_backup()

    print("\n=== Membersihkan data ===")
    bersihkan()

    print("\n=== Jumlah baris SESUDAH ===")
    after = hitung_sebelum()
    for t, n in after.items():
        print(f"  {t}: {n}")

    print("\nSelesai.")


if __name__ == '__main__':
    main()
