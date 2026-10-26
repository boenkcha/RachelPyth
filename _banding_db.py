# -*- coding: utf-8 -*-
import sqlite3, os, time, glob, sys
sys.stdout.reconfigure(encoding='utf-8')

base = os.path.dirname(os.path.abspath(__file__))
for f in sorted(glob.glob(os.path.join(base, '*.db'))):
    name = os.path.basename(f)
    st = os.stat(f)
    print("="*70)
    print(f"{name}   {st.st_size:,} B   {time.strftime('%Y-%m-%d %H:%M', time.localtime(st.st_mtime))}")
    try:
        con = sqlite3.connect(f"file:{f}?mode=ro", uri=True)
        def one(sql):
            try: return con.execute(sql).fetchone()[0]
            except Exception as e: return f"ERR({e})"
        print(f"  Stok_barang total : {one('SELECT COUNT(*) FROM Stok_barang')}")
        try:
            rows = list(con.execute("SELECT COALESCE(kd_lokasi,'(null)') l, COUNT(*) n, COALESCE(SUM(stok_sisa),0) s FROM Stok_barang GROUP BY kd_lokasi ORDER BY 1"))
            for r in rows:
                print(f"      lokasi {str(r[0]):8}: {r[1]:>6} baris  sisa={r[2]}")
        except Exception as e:
            print("      (no kd_lokasi)", e)
        print(f"  RiwayatBarang     : {one('SELECT COUNT(*) FROM RiwayatBarang')}")
        print(f"  Penjualan         : {one('SELECT COUNT(*) FROM Penjualan')}")
        print(f"  Pasien            : {one('SELECT COUNT(*) FROM Pasien')}")
        con.close()
    except Exception as e:
        print("  TIDAK BISA DIBUKA:", e)
