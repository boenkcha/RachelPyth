import sqlite3
con = sqlite3.connect('rachel_clinic.db')
con.row_factory = sqlite3.Row
cur = con.cursor()

kd = 'P008'
print("=== PASIEN ===")
p = cur.execute("SELECT * FROM Pasien WHERE kd_pasien=?", (kd,)).fetchone()
print(dict(p) if p else "TIDAK ADA")

print("\n=== PENJUALAN (semua transaksi) ===")
pj = cur.execute("SELECT no_faktur, tanggal, total_harga, status, kd_pasien FROM Penjualan WHERE kd_pasien=? ORDER BY tanggal DESC", (kd,)).fetchall()
for r in pj:
    print(dict(r))
print(f"Total transaksi: {len(pj)}")

print("\n=== REKAM MEDIK ===")
rm = cur.execute("SELECT id, no_rm, tanggal, nm_dokter, no_faktur, A_diagnosa FROM RekamMedik WHERE kd_pasien=? ORDER BY tanggal DESC", (kd,)).fetchall()
for r in rm:
    print(dict(r))
print(f"Total RM: {len(rm)}")

print("\n=== TRANSAKSI TANPA RM (orphan) ===")
orphan = cur.execute("""
    SELECT p.no_faktur, p.tanggal, p.total_harga, p.status
    FROM Penjualan p
    WHERE p.kd_pasien=?
      AND NOT EXISTS (
          SELECT 1 FROM RekamMedik rm WHERE rm.no_faktur = p.no_faktur
      )
    ORDER BY p.tanggal DESC
""", (kd,)).fetchall()
for r in orphan:
    print(dict(r))
print(f"Transaksi tanpa RM: {len(orphan)}")

print("\n=== RM TANPA FAKTUR ===")
no_fak = cur.execute("SELECT id, no_rm, tanggal, A_diagnosa FROM RekamMedik WHERE kd_pasien=? AND (no_faktur='' OR no_faktur IS NULL)", (kd,)).fetchall()
for r in no_fak:
    print(dict(r))

con.close()
