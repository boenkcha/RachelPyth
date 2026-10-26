import sqlite3
con = sqlite3.connect("rachel_clinic.db")
cur = con.cursor()
cur.execute("SELECT COUNT(*) FROM Stok_barang WHERE kd_lokasi='INDUK'")
print("Total stok INDUK:", cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM Stok_barang WHERE kd_lokasi='INDUK' AND stok_sisa > 0")
print("Stok INDUK > 0 :", cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM Stok_barang WHERE kd_lokasi='INDUK' AND stok_sisa <= 0")
print("Stok INDUK = 0 :", cur.fetchone()[0])
cur.execute("SELECT kd_barang, nm_barang, stok_sisa FROM Stok_barang WHERE kd_lokasi='INDUK' AND stok_sisa > 0 LIMIT 8")
print("\nContoh stok > 0:")
for r in cur.fetchall():
    print(" ", r)
con.close()
