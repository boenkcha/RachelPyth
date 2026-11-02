"""
Audit READ-ONLY (tidak mengubah data apa pun): cek seberapa banyak PASIEN,
BARANG/JASA, dan KARYAWAN yang disebut di Penjualan.csv/R_penjualan.csv
TERNYATA BELUM ADA di master (Pasien/Barang/produk_pelayanan/Karyawan) saat
ini -- sebelum migrasi_penjualantanggal dieksekusi.

Jalankan:
    AC_MYSQL_PASSWORD='password_anda' python3 diagnosa_master_hilang.py
"""
import app as _app
from app import _migr_sv, _migr_norm_nama, _load_sementara_csv


def main():
    print(f"Backend aktif: {_app.DB_BACKEND} | Database: {_app.MYSQL_CONFIG.get('database') if _app.DB_BACKEND=='mysql' else _app.DB_PATH}\n")

    hdrs_p, rows_p, err_p = _load_sementara_csv('Penjualan.csv')
    if err_p:
        print("Gagal baca Penjualan.csv:", err_p); return
    hdrs_r, rows_r, err_r = _load_sementara_csv('R_penjualan.csv')
    if err_r:
        print("Gagal baca R_penjualan.csv:", err_r); return

    # ── PASIEN ──────────────────────────────────────────────
    csv_pasien = set()
    for r in rows_p:
        d = {h.lower(): v for h, v in zip(hdrs_p, r)}
        kd = _migr_sv(d.get('kd_pasien', ''))
        if kd:
            csv_pasien.add(kd)

    db_pasien = {row['kd_pasien'] for row in _app.query("SELECT kd_pasien FROM Pasien")}
    pasien_hilang = sorted(csv_pasien - db_pasien)
    print(f"=== PASIEN ===")
    print(f"Distinct kd_pasien di Penjualan.csv : {len(csv_pasien)}")
    print(f"Sudah ada di master Pasien           : {len(csv_pasien & db_pasien)}")
    print(f"BELUM ADA di master Pasien           : {len(pasien_hilang)}")
    if pasien_hilang:
        print(f"Contoh 15 kd_pasien yang belum ada  : {pasien_hilang[:15]}")

    # ── BARANG / JASA (by nama, sesuai logika eksekusi yg sudah diperbaiki) ──
    pelayanan_by_nama = {_migr_norm_nama(row['nm_pelayanan']) for row in _app.query(
        "SELECT nm_pelayanan FROM produk_pelayanan")}
    barang_by_nama = {_migr_norm_nama(row['nm_barang']) for row in _app.query(
        "SELECT nm_barang FROM Barang")}

    csv_nama = {}
    for r in rows_r:
        d = {h.lower(): v for h, v in zip(hdrs_r, r)}
        kd_b = _migr_sv(d.get('kd_barang', ''))  # sebenarnya nama, lihat _LEGACY_LAYOUTS
        if kd_b:
            csv_nama.setdefault(_migr_norm_nama(kd_b), kd_b)

    tidak_cocok = {raw for norm, raw in csv_nama.items()
                   if norm not in pelayanan_by_nama and norm not in barang_by_nama}
    print(f"\n=== BARANG / JASA (by nama) ===")
    print(f"Distinct nama produk/jasa di R_penjualan.csv : {len(csv_nama)}")
    print(f"Cocok ke Barang/produk_pelayanan skrg         : {len(csv_nama) - len(tidak_cocok)}")
    print(f"TIDAK cocok (stok tak terpotong utk ini)      : {len(tidak_cocok)}")
    if tidak_cocok:
        print(f"Contoh 15 nama yang tidak cocok : {sorted(tidak_cocok)[:15]}")

    # ── KARYAWAN ('0'/kosong=barang, selain itu=jasa & kode staf, koma-jamak
    #    kalau >1 orang) -- dicocokkan ke Karyawan.nickname skrg, bukan kd_karyawan.
    csv_staff_codes = set()
    for r in rows_r:
        d = {h.lower(): v for h, v in zip(hdrs_r, r)}
        staff_raw = _migr_sv(d.get('kd_karyawan', ''))
        if staff_raw and staff_raw != '0':
            for c in staff_raw.split(','):
                c = c.strip()
                if c and c != '0':
                    csv_staff_codes.add(c)

    nickname_norm = {_migr_norm_nama(row['nickname']) for row in _app.query(
        "SELECT nickname FROM Karyawan WHERE nickname IS NOT NULL AND nickname != ''")}
    staff_cocok = {c for c in csv_staff_codes if _migr_norm_nama(c) in nickname_norm}
    staff_tidak_cocok = csv_staff_codes - staff_cocok
    print(f"\n=== KARYAWAN (by nickname) ===")
    print(f"Distinct kode staf (bukan '0') di CSV : {len(csv_staff_codes)}")
    print(f"Cocok ke nickname staf skrg (dapat komisi) : {len(staff_cocok)}")
    print(f"TIDAK cocok (auto-create staf baru, tanpa komisi) : {len(staff_tidak_cocok)}")
    if staff_tidak_cocok:
        print(f"Contoh 15 kode staf yang tidak cocok : {sorted(staff_tidak_cocok)[:15]}")

    print("\nSelesai. Kirim seluruh output di atas untuk diputuskan langkah selanjutnya.")


if __name__ == '__main__':
    main()
