import sqlite3, os, time, glob

base = os.path.dirname(os.path.abspath(__file__))
db = os.path.join(base, 'rachel_clinic.db')
print("== DB UTAMA ==")
print("path :", db)
print("ada  :", os.path.exists(db))
if os.path.exists(db):
    st = os.stat(db)
    print("ukuran:", f"{st.st_size:,} bytes")
    print("modif :", time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.st_mtime)))

con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
def c(sql, p=()):
    try:
        return con.execute(sql, p).fetchone()[0]
    except Exception as e:
        return f"ERR {e}"

print("\n== JUMLAH BARIS TABEL INTI ==")
for t in ['Stok_barang','Barang','Penjualan','R_Penjualan','RiwayatBarang','Pasien','Karyawan','produk_pelayanan']:
    print(f"{t:18}: {c('SELECT COUNT(*) FROM '+t)}")

print("\n== Stok_barang per kd_lokasi ==")
try:
    for r in con.execute("SELECT kd_lokasi, COUNT(*) n, COALESCE(SUM(stok_sisa),0) sisa FROM Stok_barang GROUP BY kd_lokasi ORDER BY kd_lokasi"):
        print(f"  {str(r['kd_lokasi']):8} : {r['n']:>6} baris, total sisa = {r['sisa']}")
except Exception as e:
    print("  ERR", e)

print("\n== Cabang berstok (stok_sisa>0) ==")
try:
    for r in con.execute("SELECT kd_lokasi, COUNT(*) n FROM Stok_barang WHERE stok_sisa>0 AND kd_lokasi!='INDUK' GROUP BY kd_lokasi"):
        print(f"  {str(r['kd_lokasi']):8} : {r['n']} baris berstok")
except Exception as e:
    print("  ERR", e)

print("\n== Kit / request (perubahan terbaru) ==")
for t in ['Stok_Perawat','Kit_Log','Kit_Request','Kit_Request_Detail','Perawatan_Bahan']:
    print(f"{t:20}: {c('SELECT COUNT(*) FROM '+t)}")

print("\n== RiwayatBarang terbaru (10) ==")
try:
    for r in con.execute("SELECT tanggal,kd_barang,keterangan,nilai FROM RiwayatBarang ORDER BY id DESC LIMIT 10"):
        print(f"  {r['tanggal']}  {str(r['kd_barang'])[:18]:18}  {str(r['keterangan'])[:30]:30}  {r['nilai']}")
except Exception as e:
    print("  ERR", e)

con.close()

print("\n== FILE *.db DI FOLDER ==")
for f in sorted(glob.glob(os.path.join(base, '*.db'))):
    st = os.stat(f)
    print(f"  {os.path.basename(f):45} {st.st_size:>12,} B  {time.strftime('%Y-%m-%d %H:%M', time.localtime(st.st_mtime))}")
