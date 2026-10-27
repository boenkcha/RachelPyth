# Setup database MySQL baru untuk AppClinic (`appclinic`)

Database MySQL lama `rachel_clinic`/user `rachel_app` **TIDAK disentuh sama sekali** —
ada sistem lain yang masih berjalan memakainya. AppClinic memakai database & user
BARU yang terpisah total, kosong (instalasi baru dari nol).

Password root MySQL **tidak pernah diketik ke saya** — perintah di bawah akan minta
password lewat prompt `mysql -p` sendiri.

## 1. Buat database & user baru (kosong)
```bash
mysql -u root -p <<'SQL'
CREATE DATABASE appclinic CHARACTER SET utf8mb4;
CREATE USER 'appclinic_app'@'localhost' IDENTIFIED BY 'GANTI_DENGAN_PASSWORD_BARU';
GRANT ALL PRIVILEGES ON appclinic.* TO 'appclinic_app'@'localhost';
FLUSH PRIVILEGES;
SQL
```
Ganti `GANTI_DENGAN_PASSWORD_BARU` dengan password pilihan Anda. Database `rachel_clinic`
dan user `rachel_app` tetap ada seperti semula, tidak diubah/dihapus — aman untuk sistem
lain yang masih memakainya.

## 2. Set env var untuk menjalankan AppClinic
Kode sekarang membaca env var prefix `AC_` (dulu `RC_`). Di tempat Anda biasa set env
var untuk menjalankan server ini (shell profile, script start, atau launchd plist),
pastikan:

| Env var | Nilai |
|---|---|
| `AC_DB_BACKEND` | `mysql` (default, boleh tidak diset) |
| `AC_MYSQL_HOST` | `localhost` (default, boleh tidak diset) |
| `AC_MYSQL_PORT` | `3306` (default, boleh tidak diset) |
| `AC_MYSQL_USER` | `appclinic_app` (default di kode, boleh tidak diset) |
| `AC_MYSQL_DB` | `appclinic` (default di kode, boleh tidak diset) |
| `AC_MYSQL_PASSWORD` | **wajib diisi** — password yang Anda buat di langkah 1 |

Kalau Anda tidak pernah set `RC_MYSQL_USER`/`RC_MYSQL_DB` secara eksplisit sebelumnya
(hanya andalkan default di kode), tidak perlu diapa-apakan — default barunya sudah
`appclinic_app`/`appclinic`. Yang **wajib** diubah hanya nama env var password, dari
`RC_MYSQL_PASSWORD` jadi `AC_MYSQL_PASSWORD`, kalau sebelumnya Anda set itu di suatu
tempat (shell profile/script/plist) untuk instance Rachel Clinic yang lama — biarkan
yang lama itu tetap ada/tidak diubah (dipakai sistem lain), cukup tambahkan env var
baru untuk instance AppClinic ini.

## 3. Jalankan server
```bash
AC_MYSQL_PASSWORD='password_baru_anda' python3 app.py
```
Saat pertama kali jalan, `init_db_mysql()` otomatis membuat semua tabel (kosong) di
database `appclinic` beserta data default (login admin: `admin`/`admin123`, master
barang/jasa contoh, pengaturan `klinik_nama='AppClinic'`, dll — sama seperti instalasi
baru Rachel Clinic dulu pertama kali).

## 4. Verifikasi
- Login ke `http://localhost:5000` (atau alamat server Anda) pakai `admin`/`admin123`.
- Cek judul & logo tampil "AppClinic".
- **Segera ganti password admin default** setelah login pertama kali.
