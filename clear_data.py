import sqlite3

con = sqlite3.connect("appclinic.db")
cur = con.cursor()
cur.execute("PRAGMA foreign_keys = OFF")

tables = [
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

for t in tables:
    cur.execute(f"DELETE FROM [{t}]")
    cur.execute("DELETE FROM sqlite_sequence WHERE name=?", (t,))
    print(f"  cleared: {t}")

cur.execute("PRAGMA foreign_keys = ON")
con.commit()

# verifikasi Pengguna masih utuh
cur.execute("SELECT COUNT(*) FROM Pengguna")
print(f"\nPengguna tetap: {cur.fetchone()[0]} user")
con.close()
print("Selesai.")
