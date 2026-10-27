# ============================================================
# migrate_access.py  — Import CSV hasil export MDB ke SQLite
# Jalankan SETELAH migr_export.ps1 selesai
# ============================================================
import sqlite3, csv, os, sys, time
from datetime import datetime

MIGR_TEMP = r"d:\App Python\appclinic\migr_temp"
DB_PATH   = r"d:\App Python\appclinic\appclinic.db"
BATCH     = 2000   # INSERT batch size

# ── date parser ─────────────────────────────────────────────
def pd(s):
    s = str(s).strip()
    if not s or s in ('None',''):
        return ''
    if len(s) >= 10 and s[4] == '-':
        return s[:10]   # already YYYY-MM-DD
    for fmt in ('%d/%m/%Y %H:%M:%S','%m/%d/%Y %H:%M:%S',
                '%d/%m/%Y','%m/%d/%Y','%Y/%m/%d','%d-%m-%Y'):
        try:
            return datetime.strptime(s, fmt).strftime('%Y-%m-%d')
        except:
            pass
    return s[:10]   # fallback

def fv(s):
    """float value, 0 if blank/invalid"""
    try: return float(str(s).replace(',','.'))
    except: return 0.0

def sv(s):
    """string value, strip whitespace"""
    return str(s).strip() if s is not None else ''

# ── CSV loader ───────────────────────────────────────────────
def load_csv(fname):
    path = os.path.join(MIGR_TEMP, fname + '.csv')
    if not os.path.exists(path):
        print(f"  [SKIP] {fname}.csv tidak ada")
        return None, None
    with open(path, encoding='utf-8-sig') as f:   # utf-8-sig strips BOM
        reader = csv.reader(f, delimiter='|')
        rows = list(reader)
    if not rows:
        return [], []
    headers = [h.lower() for h in rows[0]]
    return headers, rows[1:]

def col(row_dict, *keys):
    """ambil nilai dari row_dict, coba beberapa kemungkinan nama kolom"""
    for k in keys:
        if k in row_dict:
            return row_dict[k]
    return ''

# ── progress helper ──────────────────────────────────────────
def insert_batch(cur, sql, data_gen, label):
    t0 = time.time()
    buf, total = [], 0
    for row in data_gen:
        buf.append(row)
        if len(buf) >= BATCH:
            cur.executemany(sql, buf)
            total += len(buf)
            buf = []
            print(f"    {label}: {total:,} baris...  ", end='\r')
    if buf:
        cur.executemany(sql, buf)
        total += len(buf)
    elapsed = time.time() - t0
    print(f"    {label}: {total:,} baris  ({elapsed:.1f}s)          ")
    return total

# ── MAIN ─────────────────────────────────────────────────────
def main():
    if not os.path.exists(MIGR_TEMP):
        print("ERROR: Folder migr_temp tidak ada. Jalankan dulu migr_export.ps1 !")
        sys.exit(1)

    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("PRAGMA foreign_keys = OFF")
    cur.execute("PRAGMA journal_mode = WAL")
    cur.execute("PRAGMA synchronous = NORMAL")

    print("=" * 60)
    print("  MIGRASI DATA RACHEL.MDB -> appclinic.db")
    print("=" * 60)

    # ── 1. BERSIHKAN TABEL (urutan FK-safe) ─────────────────
    print("\n[1] Menghapus data lama ...")
    truncate_order = [
        'DetailResepRacikan','ResepRacikan',
        'DetailResepDigital','ResepDigital',
        'Foto_Pasien','Antrian',
        'RekamMedik',
        'R_Penjualan','Penjualan',
        'Point_karyawan','TKunjunganBerikut','TKredit',
        'R_Pembelian','Pembelian',
        'Order_Transfer_Detail','Order_Transfer',
        'Transfer_Stok_Log',
        'Produksi',
        'Formula_Produksi_Detail','Formula_Produksi',
        'DetailPoint','Member',
        'RiwayatBarang','Tindakan','Log','Nomor',
        'Stok_barang','produk_pelayanan',
        'Suplier','Karyawan','Pasien',
    ]
    for tbl in truncate_order:
        cur.execute(f"DELETE FROM [{tbl}]")
        # reset autoincrement
        cur.execute("DELETE FROM sqlite_sequence WHERE name=?", (tbl,))
    con.commit()
    print("    Semua tabel data sudah dikosongkan.\n")

    # ── 2. PASIEN ────────────────────────────────────────────
    print("[2] Import Pasien ...")
    hdrs, rows = load_csv('PasienC')
    if rows is not None:
        def gen():
            for r in rows:
                d = dict(zip(hdrs, r))
                telp = sv(col(d,'hp')) or sv(col(d,'telepon'))
                yield (
                    sv(col(d,'kd_pasien')),
                    sv(col(d,'nm_pasien')),
                    sv(col(d,'alamat')),
                    telp,
                    pd(col(d,'t_lahir')),
                    sv(col(d,'kelamin')),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                )
        sql = "INSERT OR IGNORE INTO Pasien(kd_pasien,nm_pasien,alamat,telp,tgl_lahir,jenis_kelamin,created_at) VALUES(?,?,?,?,?,?,?)"
        insert_batch(cur, sql, gen(), 'Pasien')
        con.commit()

    # ── 3. KARYAWAN ──────────────────────────────────────────
    print("[3] Import Karyawan ...")
    hdrs, rows = load_csv('Karyawan')
    if rows is not None:
        def gen():
            for r in rows:
                d = dict(zip(hdrs, r))
                telp = sv(col(d,'hp')) or sv(col(d,'telepon'))
                yield (
                    sv(col(d,'kd_karyawan')),
                    sv(col(d,'nm_karyawan')),
                    sv(col(d,'nickname')),
                    sv(col(d,'pekerjaan')),
                    telp,
                    1,
                )
        sql = "INSERT OR IGNORE INTO Karyawan(kd_karyawan,nm_karyawan,nickname,pekerjaan,telp,aktif) VALUES(?,?,?,?,?,?)"
        insert_batch(cur, sql, gen(), 'Karyawan')
        con.commit()

    # ── 4. SUPLIER ───────────────────────────────────────────
    print("[4] Import Suplier ...")
    hdrs, rows = load_csv('Suplier')
    if rows is not None:
        def gen():
            for r in rows:
                d = dict(zip(hdrs, r))
                kd = sv(col(d,'kd_suplier','kdsuplier','kd_supplier'))
                nm = sv(col(d,'nm_suplier','nmsuplier','nm_supplier','namasuplier'))
                if not kd and not nm:
                    continue
                yield (
                    kd,
                    nm,
                    sv(col(d,'alamat')),
                    sv(col(d,'telp','telepon','hp')),
                    sv(col(d,'kontak')),
                )
        sql = "INSERT OR IGNORE INTO Suplier(kd_suplier,nm_suplier,alamat,telp,kontak) VALUES(?,?,?,?,?)"
        insert_batch(cur, sql, gen(), 'Suplier')
        con.commit()

    # ── 5. STOK BARANG ───────────────────────────────────────
    print("[5] Import Stok_barang ...")
    hdrs, rows = load_csv('Stok_barang')
    if rows is not None:
        def gen():
            for r in rows:
                d = dict(zip(hdrs, r))
                kd = sv(col(d,'kd_barang'))
                if not kd:
                    continue
                yield (
                    kd,
                    sv(col(d,'nm_barang')),
                    fv(col(d,'harga_beli')),
                    fv(col(d,'harga_beli_awal')),
                    fv(col(d,'stok_awal')),
                    fv(col(d,'stok_sisa')),
                    fv(col(d,'stok_gudang')),
                    fv(col(d,'stok_min')),
                    fv(col(d,'harga')),
                    fv(col(d,'disc')),
                    sv(col(d,'satuan')),
                    sv(col(d,'exp')),
                    fv(col(d,'discmem')),
                    fv(col(d,'disclain')),
                    'INDUK',
                )
        sql = """INSERT INTO Stok_barang
            (kd_barang,nm_barang,harga_beli,harga_beli_awal,stok_awal,stok_sisa,
             stok_gudang,stok_min,harga,disc,satuan,exp,DiscMem,DiscLain,kd_lokasi)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
        insert_batch(cur, sql, gen(), 'Stok_barang')
        con.commit()

    # ── 6. PRODUK PELAYANAN ──────────────────────────────────
    print("[6] Import produk_pelayanan ...")
    hdrs, rows = load_csv('Produk_pelayanan')
    if rows is not None:
        def gen():
            for r in rows:
                d = dict(zip(hdrs, r))
                yield (
                    sv(col(d,'kd_pelayanan')),
                    sv(col(d,'nm_pelayanan')),
                    fv(col(d,'harga')),
                    fv(col(d,'komisi3','komisi_dokter')),    # Komisi3 = dokter
                    fv(col(d,'komisi2','komisi_supervisor')),# Komisi2 = supervisor
                    fv(col(d,'komisi','komisi_perawat')),    # Komisi  = perawat
                )
        sql = "INSERT OR IGNORE INTO produk_pelayanan(kd_pelayanan,nm_pelayanan,harga,komisi_dokter,komisi_supervisor,komisi_perawat) VALUES(?,?,?,?,?,?)"
        insert_batch(cur, sql, gen(), 'produk_pelayanan')
        con.commit()

    # ── 7. PEMBELIAN (header) ────────────────────────────────
    print("[7] Import Pembelian ...")
    hdrs, rows = load_csv('Pembelian')
    if rows is not None:
        def gen():
            for r in rows:
                d = dict(zip(hdrs, r))
                yield (
                    sv(col(d,'no_faktur')),
                    pd(col(d,'tanggal')),
                    fv(col(d,'total_harga')),
                    sv(col(d,'sistem_bayar')),
                    int(fv(col(d,'lunas'))),
                    sv(col(d,'tempo')),
                    sv(col(d,'nm_suplier')),
                    'INDUK',
                )
        sql = "INSERT OR IGNORE INTO Pembelian(no_faktur,tanggal,total_harga,sistem_bayar,lunas,tempo,nm_suplier,kd_lokasi) VALUES(?,?,?,?,?,?,?,?)"
        insert_batch(cur, sql, gen(), 'Pembelian')
        con.commit()

    # ── 8. R_PEMBELIAN (detail) ──────────────────────────────
    print("[8] Import R_Pembelian ...")
    hdrs, rows = load_csv('R_pembelian')
    if rows is not None:
        def gen():
            for r in rows:
                d = dict(zip(hdrs, r))
                yield (
                    sv(col(d,'no_faktur')),
                    pd(col(d,'tanggal')),
                    sv(col(d,'kd_suplier','kd_supplier')),
                    sv(col(d,'nm_suplier','nm_supplier')),
                    sv(col(d,'sistem_bayar')),
                    sv(col(d,'kd_barang')),
                    sv(col(d,'nm_barang')),
                    fv(col(d,'disc')),
                    fv(col(d,'harga_beli_kotor')),
                    fv(col(d,'harga_beli_bersih')),
                    fv(col(d,'sub_total')),
                    fv(col(d,'ppn')),
                    sv(col(d,'tempo')),
                    fv(col(d,'qty')),
                    fv(col(d,'harga_asli')),
                    sv(col(d,'satuan')),
                    sv(col(d,'exp')),
                )
        sql = """INSERT INTO R_Pembelian
            (no_faktur,tanggal,kd_suplier,nm_suplier,sistem_bayar,kd_barang,nm_barang,
             disc,harga_beli_kotor,harga_beli_bersih,sub_total,ppn,tempo,qty,harga_asli,satuan,exp)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
        insert_batch(cur, sql, gen(), 'R_Pembelian')
        con.commit()

    # ── 9. PENJUALAN (header) — 181K rows ────────────────────
    print("[9] Import Penjualan ...")
    hdrs, rows = load_csv('Penjualan18')
    if rows is not None:
        def gen():
            for r in rows:
                d = dict(zip(hdrs, r))
                yield (
                    sv(col(d,'no_faktur')),
                    pd(col(d,'tanggal')),
                    fv(col(d,'total_harga')),
                    fv(col(d,'hpp')),
                    sv(col(d,'dokter')),
                    sv(col(d,'kd_pasien')),
                    sv(col(d,'dokter')),   # kasir (pakai dokter sbg fallback)
                    'tunai',
                    'done',
                    0, 0,
                    'CBG1',
                )
        sql = """INSERT OR IGNORE INTO Penjualan
            (no_faktur,tanggal,total_harga,hpp,dokter,kd_pasien,kasir,
             metode_bayar,status,disc_trx,disc_trx_nilai,kd_lokasi)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)"""
        insert_batch(cur, sql, gen(), 'Penjualan')
        con.commit()

    # ── 10. R_PENJUALAN (detail) — 466K rows ─────────────────
    print("[10] Import R_Penjualan ...")
    hdrs, rows = load_csv('R_penjualan18')
    if rows is not None:
        def gen():
            for r in rows:
                d = dict(zip(hdrs, r))
                yield (
                    sv(col(d,'no_faktur')),
                    pd(col(d,'tanggal')),
                    sv(col(d,'kd_barang')),
                    sv(col(d,'nm_barang')),
                    fv(col(d,'harga')),
                    fv(col(d,'harga_asli')),
                    fv(col(d,'qty')),
                    fv(col(d,'disc')),
                    fv(col(d,'sub_total')),
                    fv(col(d,'total_harbeli')),
                    sv(col(d,'kd_karyawan')),
                    sv(col(d,'cashier')),
                    sv(col(d,'exp')),
                    'barang',
                    '',
                )
        sql = """INSERT INTO R_Penjualan
            (no_faktur,tanggal,kd_barang,nm_barang,harga,harga_asli,qty,disc,
             sub_total,total_harbeli,kd_karyawan,cashier,exp,jenis,racikan_ref)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"""
        insert_batch(cur, sql, gen(), 'R_Penjualan')
        con.commit()

    # ── 11. REKAM MEDIK (dari Hasil_pasien) — 839K rows ──────
    print("[11] Import RekamMedik (dari Hasil_pasien) ...")
    hdrs, rows = load_csv('Hasil_pasien')
    if rows is not None:
        rm_counter = [0]
        def gen():
            for r in rows:
                d = dict(zip(hdrs, r))
                tindakan = sv(col(d,'perawatan'))
                if not tindakan:
                    continue
                rm_counter[0] += 1
                no_rm = 'RM' + str(rm_counter[0]).zfill(7)
                yield (
                    no_rm,
                    sv(col(d,'kd_pasien')),
                    pd(col(d,'tanggal')),
                    '',          # nm_dokter
                    'done',
                    '',          # S_keluhan
                    '',          # O_jenis_kulit
                    '',          # O_kondisi_kulit
                    tindakan,    # A_diagnosa (pakai tindakan juga)
                    tindakan,    # P_tindakan
                    '',          # P_catatan
                    '',          # no_faktur
                )
        sql = """INSERT INTO RekamMedik
            (no_rm,kd_pasien,tanggal,nm_dokter,status,S_keluhan,O_jenis_kulit,
             O_kondisi_kulit,A_diagnosa,P_tindakan,P_catatan,no_faktur)
            VALUES(?,?,?,?,?,?,?,?,?,?,?,?)"""
        insert_batch(cur, sql, gen(), 'RekamMedik')
        con.commit()

    # ── 12. POINT KARYAWAN ───────────────────────────────────
    print("[12] Import Point_karyawan ...")
    hdrs, rows = load_csv('Point_karyawan')
    if rows is not None:
        def gen():
            for r in rows:
                d = dict(zip(hdrs, r))
                yield (
                    sv(col(d,'no_faktur')),
                    pd(col(d,'tanggal')),
                    sv(col(d,'kd_pasien')),
                    sv(col(d,'kd_pelayanan')),
                    sv(col(d,'nm_pelayanan')),
                    fv(col(d,'komisi')),
                    sv(col(d,'kd_karyawan')),
                )
        sql = "INSERT INTO Point_karyawan(no_faktur,tanggal,kd_pasien,kd_pelayanan,nm_pelayanan,komisi,kd_karyawan) VALUES(?,?,?,?,?,?,?)"
        insert_batch(cur, sql, gen(), 'Point_karyawan')
        con.commit()

    # ── 13. RIWAYAT BARANG ───────────────────────────────────
    print("[13] Import RiwayatBarang ...")
    hdrs, rows = load_csv('RiwayatBarang')
    if rows is not None:
        def gen():
            for r in rows:
                d = dict(zip(hdrs, r))
                yield (
                    pd(col(d,'tanggal')),
                    sv(col(d,'kd_barang')),
                    sv(col(d,'exp')),
                    sv(col(d,'keterangan')),
                    fv(col(d,'nilai')),
                    fv(col(d,'saldoe')),
                    fv(col(d,'saldog')),
                )
        sql = "INSERT INTO RiwayatBarang(tanggal,kd_barang,exp,keterangan,nilai,saldo_e,saldo_g) VALUES(?,?,?,?,?,?,?)"
        insert_batch(cur, sql, gen(), 'RiwayatBarang')
        con.commit()

    # ── 14. TINDAKAN ─────────────────────────────────────────
    print("[14] Import Tindakan ...")
    hdrs, rows = load_csv('Tindakan')
    if rows is not None:
        def gen():
            for r in rows:
                d = dict(zip(hdrs, r))
                yield (
                    pd(col(d,'tanggal')),
                    sv(col(d,'kd_pelayanan')),
                    fv(col(d,'banyaknya')),
                )
        sql = "INSERT INTO Tindakan(tanggal,kd_pelayanan,banyaknya) VALUES(?,?,?)"
        insert_batch(cur, sql, gen(), 'Tindakan')
        con.commit()

    # ── 15. LOG ──────────────────────────────────────────────
    print("[15] Import Log ...")
    hdrs, rows = load_csv('Log')
    if rows is not None:
        def gen():
            for r in rows:
                d = dict(zip(hdrs, r))
                yield (
                    pd(col(d,'tanggal')),
                    sv(col(d,'keterangan')),
                    fv(col(d,'qty')),
                    sv(col(d,'kasir')),
                    sv(col(d,'event')),
                )
        sql = "INSERT INTO Log(tanggal,keterangan,qty,kasir,event) VALUES(?,?,?,?,?)"
        insert_batch(cur, sql, gen(), 'Log')
        con.commit()

    # ── 16. NOMOR ────────────────────────────────────────────
    print("[16] Import Nomor ...")
    hdrs, rows = load_csv('Nomor')
    if rows is not None:
        def gen():
            for r in rows:
                d = dict(zip(hdrs, r))
                yield (
                    pd(col(d,'tanggal')),
                    int(fv(col(d,'nota_jual'))),
                    int(fv(col(d,'nota_piutang'))),
                    int(fv(col(d,'nota_resep'))),
                )
        sql = "INSERT OR IGNORE INTO Nomor(tanggal,nota_jual,nota_piutang,nota_resep) VALUES(?,?,?,?)"
        insert_batch(cur, sql, gen(), 'Nomor')
        con.commit()

    # ── 17. T KREDIT ─────────────────────────────────────────
    print("[17] Import TKredit ...")
    hdrs, rows = load_csv('TKredit')
    if rows is not None:
        def gen():
            for r in rows:
                d = dict(zip(hdrs, r))
                yield (
                    sv(col(d,'nota')),
                    sv(col(d,'konsumen')),
                    fv(col(d,'total')),
                    sv(col(d,'bank')),
                    sv(col(d,'kasir')),
                    pd(col(d,'tanggal')),
                )
        sql = "INSERT INTO TKredit(nota,konsumen,total,bank,kasir,tanggal) VALUES(?,?,?,?,?,?)"
        insert_batch(cur, sql, gen(), 'TKredit')
        con.commit()

    # ── 18. T KUNJUNGAN BERIKUT ──────────────────────────────
    print("[18] Import TKunjunganBerikut ...")
    hdrs, rows = load_csv('TKunjunganBerikut')
    if rows is not None:
        def gen():
            for r in rows:
                d = dict(zip(hdrs, r))
                yield (
                    sv(col(d,'no_faktur')),
                    pd(col(d,'next_tanggal')),
                    sv(col(d,'kd_pasien')),
                )
        sql = "INSERT INTO TKunjunganBerikut(no_faktur,next_tanggal,kd_pasien) VALUES(?,?,?)"
        insert_batch(cur, sql, gen(), 'TKunjunganBerikut')
        con.commit()

    # ── SELESAI ───────────────────────────────────────────────
    cur.execute("PRAGMA foreign_keys = ON")
    con.commit()
    con.close()

    print("\n" + "=" * 60)
    print("  MIGRASI SELESAI!")
    print("=" * 60)
    print("\nCek row count:")
    con2 = sqlite3.connect(DB_PATH)
    cur2 = con2.cursor()
    for tbl in ['Pasien','Karyawan','Suplier','Stok_barang','produk_pelayanan',
                'Penjualan','R_Penjualan','RekamMedik','Point_karyawan',
                'RiwayatBarang','Tindakan','Log','TKredit','Pembelian','R_Pembelian']:
        cur2.execute(f"SELECT COUNT(*) FROM [{tbl}]")
        cnt = cur2.fetchone()[0]
        print(f"  {tbl:30s}: {cnt:,}")
    con2.close()

if __name__ == '__main__':
    main()
