# -*- coding: utf-8 -*-
import sqlite3, os, sys
sys.stdout.reconfigure(encoding='utf-8')
base = os.path.dirname(os.path.abspath(__file__))

for name in ['appclinic.db', 'appclinicWH.db']:
    f = os.path.join(base, name)
    if not os.path.exists(f): continue
    print("="*64)
    print(name)
    con = sqlite3.connect(f"file:{f}?mode=ro", uri=True)
    def q(sql):
        try: return list(con.execute(sql))
        except Exception as e: return [("ERR", str(e))]
    print("  Penjualan tanggal MIN/MAX:", q("SELECT MIN(tanggal), MAX(tanggal) FROM Penjualan")[0])
    print("  Penjualan per kd_lokasi:")
    for r in q("SELECT COALESCE(kd_lokasi,'(null)'), COUNT(*) FROM Penjualan GROUP BY kd_lokasi ORDER BY 2 DESC"):
        print(f"      {str(r[0]):8}: {r[1]}")
    print("  5 transaksi terakhir (tanggal,no_faktur,kd_lokasi,total):")
    for r in q("SELECT tanggal,no_faktur,kd_lokasi,total_harga FROM Penjualan ORDER BY tanggal DESC, rowid DESC LIMIT 5"):
        print("      ", tuple(r))
    print("  Transaksi 2026 (tahun ini):", q("SELECT COUNT(*) FROM Penjualan WHERE tanggal>='2026-01-01'")[0][0])
    con.close()
