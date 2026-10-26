# Rachel Clinic — Sistem Manajemen

Migrasi dari VB6 + MS Access ke Python 3 + SQLite + HTML (single-page app).

## Cara Menjalankan

### 1. Install Python 3.8+
https://python.org/downloads

### 2. Install dependensi
```
pip install flask
```

### 3. Jalankan server
```
cd rachel_clinic
python app.py
```

### 4. Buka browser
```
http://localhost:5000
```

## Login Default
- **Username:** admin  
- **Password:** admin123

---

## Fitur Yang Tersedia

| Fitur | Status |
|---|---|
| Dashboard (omzet, statistik, chart 7 hari) | ✅ |
| Kasir / POS (input transaksi, keranjang, bayar) | ✅ |
| Antrian Pasien | ✅ |
| Master Pasien + Member | ✅ |
| Stok Barang (monitor, edit harga) | ✅ |
| Pembelian dari Supplier | ✅ |
| Laporan Penjualan (filter tanggal) | ✅ |
| Laporan Stok | ✅ |
| Point Member | ✅ |
| Multi metode bayar (Tunai, Bank, Kredit, Point) | ✅ |
| Komisi Karyawan per Tindakan | ✅ (backend) |
| Cetak Struk | 🔜 (bisa ditambah) |

---

## Struktur File

```
rachel_clinic/
├── app.py              ← Backend Flask + semua API
├── rachel_clinic.db    ← Database SQLite (auto-dibuat)
├── requirements.txt
├── README.md
└── static/
    └── index.html      ← Frontend single-page
```

## Database

SQLite otomatis dibuat saat pertama kali `python app.py` dijalankan.  
File: `rachel_clinic.db` (bisa dibuka dengan DB Browser for SQLite).

---

## Tabel Database (dari VB6 original)

| Tabel VB6 | Tabel Baru | Keterangan |
|---|---|---|
| Pasien | Pasien | Sama |
| Member | Member | Sama |
| DetailPoint | DetailPoint | Point member |
| Karyawan | Karyawan | Sama |
| stok_barang | Stok_barang | Sama |
| produk_pelayanan | produk_pelayanan | Layanan/jasa |
| R_penjualan | R_Penjualan | Detail item jual |
| Penjualan | Penjualan | Header transaksi |
| TKredit | TKredit | Bayar non-tunai |
| R_Pembelian | R_Pembelian | Detail beli |
| Pembelian | Pembelian | Header beli |
| Point_karyawan | Point_karyawan | Komisi |
| RiwayatBarang | RiwayatBarang | Log stok |
| Log | Log | Audit trail |
| Nomor | Nomor | Counter faktur |
| Antrian | Antrian | Antrian pasien |
| TKunjunganBerikut | TKunjunganBerikut | Jadwal kontrol |
