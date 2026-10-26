import sqlite3
con = sqlite3.connect("rachel_clinic.db")
cur = con.cursor()

# 1. Hapus item dengan stok = 0
cur.execute("DELETE FROM Stok_barang WHERE kd_lokasi='INDUK' AND stok_sisa <= 0")
deleted = cur.rowcount
print(f"Dihapus (stok=0): {deleted} item")

# 2. Ubah kd_lokasi INDUK -> CBG1 untuk yang tersisa
cur.execute("UPDATE Stok_barang SET kd_lokasi='CBG1' WHERE kd_lokasi='INDUK'")
updated = cur.rowcount
print(f"Diupdate ke CBG1: {updated} item")

con.commit()

# Verifikasi
cur.execute("SELECT kd_lokasi, COUNT(*), SUM(stok_sisa) FROM Stok_barang GROUP BY kd_lokasi")
print("\nRingkasan stok:")
for r in cur.fetchall():
    print(f"  lokasi={r[0]}  jumlah_item={r[1]}  total_stok={r[2]}")

cur.execute("SELECT kd_barang, nm_barang, stok_sisa, satuan FROM Stok_barang WHERE kd_lokasi='CBG1' ORDER BY stok_sisa DESC LIMIT 10")
print("\nTop 10 stok CBG1:")
for r in cur.fetchall():
    print(f"  {r[0]:30s} {r[1]:20s} stok={r[2]} {r[3]}")

con.close()
