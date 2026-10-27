# Panduan Instalasi AppClinic — Server (MySQL)

Panduan memasang aplikasi AppClinic sebagai **server** di sebuah komputer,
lalu diakses oleh komputer kasir lain lewat jaringan (LAN/WiFi).

> **Update penting:** aplikasi ini sekarang berjalan di atas **MySQL** (bukan
> lagi SQLite sebagai default). Backend bisa dikembalikan ke SQLite kapan saja
> lewat env var `AC_DB_BACKEND=sqlite` (lihat bagian K), tapi panduan di bawah
> ini untuk jalur **MySQL** yang dipakai server produksi saat ini.

---

## A. Konsep Singkat

- **1 komputer jadi SERVER** (menjalankan MySQL + aplikasi Flask).
- Komputer kasir lain cukup pakai **browser** (Chrome/Edge) membuka alamat server.
  Tidak perlu instalasi apa pun di komputer kasir.
- Untuk cabang **beda gedung**, pasang server sendiri di tiap gedung
  (database berdiri sendiri-sendiri). Bedakan **Kode Awalan Faktur** tiap cabang
  lewat menu **⚙️ Pengaturan** agar nomor faktur unik. Kiriman stok antar-gedung
  bisa lewat menu **📥 Terima Kiriman Stok**.

```
        [ KOMPUTER SERVER ]  <-- MySQL Server + aplikasi Flask (app.py)
                 |  jaringan (kabel LAN / WiFi)
     ------------+------------
     |           |           |
 [ Kasir 1 ] [ Kasir 2 ] [ Supervisor ]   <-- cukup browser
```

---

## B. Spesifikasi Minimum Komputer Server

- Windows 10/11, macOS, atau Linux
- RAM 4 GB (8 GB lebih nyaman kalau banyak kasir sekaligus)
- **Python 3.10 atau lebih baru**
- **MySQL Server 8.0 atau lebih baru**
- Disarankan **IP statis** (lihat bagian G) agar alamat server tidak berubah

---

## C. Langkah Instalasi (di komputer SERVER)

### 1. Pasang Python
- Unduh dari https://www.python.org/downloads
- Saat instalasi **WAJIB centang "Add Python to PATH"**.

### 2. Pasang MySQL Server
- Unduh MySQL Community Server: https://dev.mysql.com/downloads/mysql/
- Saat instalasi, catat **password root** yang dibuat.
- Pastikan service MySQL berjalan (`mysqld`/"MySQL80" di Windows Services).

### 3. Buat database & user aplikasi
Buka **MySQL Command Line Client** (atau `mysql -u root -p` di terminal), lalu jalankan:
```sql
CREATE DATABASE appclinic CHARACTER SET utf8mb4;
CREATE USER 'appclinic_app'@'localhost' IDENTIFIED BY 'GANTI_PASSWORD_ANDA';
GRANT ALL PRIVILEGES ON appclinic.* TO 'appclinic_app'@'localhost';
FLUSH PRIVILEGES;
```
> Ganti `GANTI_PASSWORD_ANDA` dengan password pilihan Anda sendiri. Aplikasi
> **TIDAK punya password default** (lihat `MYSQL_CONFIG` di awal `app.py`) —
> wajib set env var `AC_MYSQL_PASSWORD` dengan nilai yang SAMA PERSIS saat
> menjalankan server (lihat bagian K), kalau tidak server tidak akan mau jalan.

### 4. Salin folder aplikasi
- Salin seluruh folder aplikasi (`app.py`, `static/`, `requirements.txt`, dst.)
  ke komputer server, misalnya ke `C:\AppClinic` (Windows) atau
  `~/AppClinic` (macOS/Linux).

### 5. Pasang dependensi Python
Buka terminal/Command Prompt di folder aplikasi, lalu:
```
python3 -m venv .venv
```
Aktifkan virtual environment:
- Windows: `.venv\Scripts\activate`
- macOS/Linux: `source .venv/bin/activate`

Lalu pasang semua dependensi:
```
pip install -r requirements.txt
```

### 6. Jalankan server
```
python3 app.py
```
Saat pertama kali dijalankan, aplikasi **otomatis membuat semua tabel** di
database `appclinic` yang sudah dibuat di langkah 3 (tidak perlu import
SQL manual). Akan muncul alamat seperti:
```
Komputer ini   : http://localhost:5000
Komputer lain  : http://192.168.1.10:5000
```
**Biarkan jendela terminal ini tetap terbuka** selama jam operasional.
Menutup jendela = mematikan server. (Untuk menjalankan di background lewat
service/launchd/systemd, tanyakan saat butuh — di luar cakupan panduan ini.)

> Catatan: angka `192.168.1.10` adalah contoh — pakai angka yang muncul di
> komputer Anda (lihat bagian G).

---

## D. Cara Komputer Kasir Terhubung

1. Pastikan komputer kasir berada di **jaringan yang sama** dengan server.
2. Buka browser (Chrome/Edge).
3. Ketik alamat server, contoh: `http://192.168.1.10:5000`
4. Login. Untuk akses cepat, bisa di-bookmark / dibuat shortcut di desktop.

Untuk **HP** (foto pasien, komisi perawat/beautician, Serah-Terima Kunci):
buka `http://192.168.1.10:5000/mobile` pada browser HP (HP harus terhubung
WiFi yang sama). Bisa juga lewat tombol QR "📱 Akses Mobile" di halaman Kasir/POS.

---

## E. (Opsional) Server Otomatis Jalan Saat Windows Nyala

1. Buat file `jalankan_server.bat` isinya:
   ```bat
   cd /d C:\AppClinic
   call .venv\Scripts\activate
   python app.py
   pause
   ```
2. Tekan `Win + R`, ketik `shell:startup`, Enter.
3. Buat **shortcut** dari `jalankan_server.bat` ke folder Startup tersebut.

---

## F. Agar Alamat Server Tidak Berubah (IP Statis)

Kalau IP server berubah-ubah, komputer kasir bisa kehilangan koneksi.
Solusi: set IP statis di komputer server.

1. `Win + R` → `ncpa.cpl` → Enter.
2. Klik kanan koneksi aktif (Ethernet/WiFi) → **Properties**.
3. Pilih **Internet Protocol Version 4 (TCP/IPv4)** → **Properties**.
4. Pilih **Use the following IP address**, isi mis.:
   - IP address : `192.168.1.10`
   - Subnet mask: `255.255.255.0`
   - Gateway    : `192.168.1.1` (sesuaikan dengan router)
   - DNS        : `192.168.1.1` atau `8.8.8.8`
5. Simpan. Mulai kini server selalu di `http://192.168.1.10:5000`.

> Sesuaikan angka dengan jaringan Anda. Tanyakan admin jaringan bila ragu.

---

## G. Database & Backup

- Semua data disimpan di **MySQL** (database `appclinic`), bukan lagi 1 file.
- **Backup rutin** (WAJIB, disarankan tiap akhir hari) via `mysqldump`:
  ```
  mysqldump -u appclinic_app -p appclinic > backup_2026-09-11.sql
  ```
  Simpan hasilnya ke flashdisk/cloud, jangan cuma di komputer server.
- **Pulihkan backup** (di komputer baru/setelah masalah):
  ```
  mysql -u appclinic_app -p appclinic < backup_2026-09-11.sql
  ```
- Foto pasien tersimpan terpisah sebagai file di folder `static/uploads/` —
  salin folder ini juga saat memindahkan/mem-backup ke komputer lain.

---

## H. Pengaturan Nomor Faktur (multi-kasir / multi-cabang)

Buka menu **⚙️ Pengaturan** (login admin):

- **Kode Awalan Faktur (cabang)** — beda untuk tiap cabang/gedung berdatabase
  terpisah, agar nomor faktur unik secara global.
- **Kode Kasir/Terminal (komputer ini)** — beda untuk tiap komputer kasir dalam
  satu gedung (DB sama), agar nomor **tidak tabrakan / saling menimpa**.

Contoh: cabang "RC", dua kasir A & B →
`RCA120926001`, `RCB120926001`, ... (kode awalan + kode kasir digabung di depan,
lalu tanggal, lalu nomor urut 3 digit — urutan masing-masing terminal berdiri sendiri).

---

## I. Identitas Klinik & Logo Faktur

Di menu **⚙️ Pengaturan**: isi nama klinik, alamat, telepon, kota, dan **upload logo**.
Semuanya langsung tampil pada hasil cetak faktur.

---

## J. Login Default

| Username | Password | Peran |
|----------|----------|-------|
| admin    | admin123 | Admin penuh |

> Segera ganti/atur akun lewat menu **Manajemen Pengguna** setelah instalasi.

---

## K. Variabel Lingkungan (opsional, utk pengaturan lanjutan)

Set sebelum menjalankan `python3 app.py` (di terminal yang sama):

| Variabel | Default | Kegunaan |
|---|---|---|
| `AC_DB_BACKEND` | `mysql` | Ganti ke `sqlite` utk pakai file lokal `appclinic.db` (zero-config, tanpa install MySQL) |
| `AC_MYSQL_HOST` | `localhost` | Alamat server MySQL (kalau MySQL di komputer lain) |
| `AC_MYSQL_PORT` | `3306` | Port MySQL |
| `AC_MYSQL_USER` | `appclinic_app` | Username MySQL |
| `AC_MYSQL_PASSWORD` | *(wajib diisi, tanpa default)* | Password MySQL — harus sama dgn yg dibuat di langkah 3 |
| `AC_MYSQL_DB` | `appclinic` | Nama database |

Contoh (macOS/Linux), pakai password custom:
```
AC_MYSQL_PASSWORD='password_baru_anda' python3 app.py
```

---

## L. Mengatasi Masalah

| Masalah | Solusi |
|---------|--------|
| `RuntimeError: AC_DB_BACKEND=mysql tapi module 'pymysql' belum terinstall` | Jalankan `pip install -r requirements.txt` di dalam virtual environment yang aktif. |
| Server tidak bisa konek ke MySQL (`Can't connect to MySQL server`) | Pastikan service MySQL sedang berjalan; cek `AC_MYSQL_HOST`/port; pastikan user & password di langkah C.3 sudah benar. |
| Komputer kasir tidak bisa buka alamat server | Pastikan 1 jaringan; buka port 5000 di Firewall Windows/macOS; cek IP server dengan `ipconfig` (Windows) / `ifconfig` (macOS). |
| "python bukan perintah dikenali" | Python belum ter-PATH. Install ulang Python, centang **Add Python to PATH**. |
| Port 5000 dipakai aplikasi lain | Tutup aplikasi tsb, atau ubah baris `port=5000` di akhir `app.py`. |
| IP server berubah-ubah | Set **IP statis** (bagian F). |
| Server lambat saat banyak kasir sekaligus | Server bawaan Flask (`app.run`) cukup utk beberapa kasir; utk lebih stabil di jaringan (bukan localhost), pertimbangkan `waitress` (sudah ada di `requirements.txt`, tanyakan admin sistem/AI utk diaktifkan). |

---

## M. Menghentikan Server

Tutup jendela terminal server, atau tekan `CTRL + C` di dalamnya.

---

*AppClinic — Sistem Manajemen Klinik. Dokumen ini untuk instalasi server MySQL di komputer baru.*
