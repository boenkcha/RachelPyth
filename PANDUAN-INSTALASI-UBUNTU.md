# Panduan Instalasi AppClinic di Ubuntu Server (dikerjakan dari Mac)

Panduan lengkap memasang AppClinic di komputer **Ubuntu Server**, dikerjakan
dari **Mac Anda** lewat SSH — mulai dari mengirim file aplikasi, memasang
semua dependensi, sampai aplikasi jalan otomatis & bisa diakses kasir lewat
browser.

> **Kalau server Ubuntu-nya beda kota/jaringan dari Mac Anda**, sambungkan
> dulu lewat Tailscale sesuai `SETUP-SERVER-UBUNTU.md` — setelah itu Anda
> punya alamat IP (`100.x.x.x`) dan akses SSH ke server dari Mac manapun.
> Panduan di bawah ini mengasumsikan Anda **sudah bisa** `ssh user@ip_server`.

---

## A. Ringkasan Alur

```
[ MAC ANDA ]                         [ UBUNTU SERVER ]
  rsync file aplikasi  ───SSH───▶      folder aplikasi
  perintah instalasi    ───SSH───▶      Python + MySQL + systemd service
                                        │
                                        ▼
                               AppClinic jalan otomatis
                               di http://ip_server:5000
                                        ▲
                    [ Kasir 1 ] [ Kasir 2 ] [ Supervisor ]  — cukup browser
```

Variabel yang dipakai berulang di bawah — sesuaikan dengan milik Anda:

| Placeholder | Contoh | Keterangan |
|---|---|---|
| `USER_UBUNTU` | `ubuntu` | Username login SSH di server |
| `IP_SERVER` | `100.64.12.5` atau `192.168.1.20` | Alamat server (Tailscale atau LAN) |
| `PASSWORD_MYSQL` | *(buat sendiri, acak & kuat)* | Password user database `appclinic_app` |

---

## B. Kirim File Aplikasi dari Mac ke Ubuntu

Di **Mac**, buka Terminal, masuk ke folder proyek:

```bash
cd "/Users/sisadmin_python/Documents/App Python/Lauda SysApy"
```

### Buat folder tujuan di server (sekali saja)

```bash
ssh USER_UBUNTU@IP_SERVER "mkdir -p ~/appclinic"
```

### Kirim file lewat `rsync` (disarankan — hanya mengirim yang perlu, dan di
pengiriman berikutnya cuma mengirim yang **berubah**, jauh lebih cepat)

```bash
rsync -avz --progress \
  --exclude 'appclinic.db' \
  --exclude '__pycache__' \
  --exclude '.git' \
  --exclude 'backup/' \
  --exclude 'backup_histori/' \
  --exclude 'sementara/' \
  --exclude 'sementara copy/' \
  --exclude 'migr_temp/' \
  --exclude '.venv' \
  --exclude '*.db' \
  ./ USER_UBUNTU@IP_SERVER:~/appclinic/
```

> **Kenapa `appclinic.db` dikecualikan?** Panduan ini memasang backend
> **MySQL** di server (lihat bagian D) — database akan dibuat baru & kosong
> di sana, bukan menyalin file SQLite 261 MB dari Mac. Kalau Anda justru
> ingin server Ubuntu memakai SQLITE (bukan MySQL), hapus baris
> `--exclude 'appclinic.db'` dan `--exclude '*.db'`, lalu lewati bagian D–E
> di bawah (langsung set `AC_DB_BACKEND=sqlite`, lihat bagian H).
>
> **Kenapa ada perubahan belum di-commit ke git?** Kalau `git status` di Mac
> Anda masih menunjukkan banyak file `M`/`??` (belum di-commit), `rsync`
> langsung dari folder kerja ini sudah otomatis membawa semua perubahan
> tersebut — tidak perlu commit dulu. Kalau nanti semua sudah rapi ter-commit
> & di-push ke GitHub, cara mengirim ke server berikutnya bisa diganti
> `git clone`/`git pull` langsung di server (lebih ringkas untuk update rutin
> — lihat bagian K).

Setelah selesai, masuk ke server untuk lanjut:

```bash
ssh USER_UBUNTU@IP_SERVER
cd ~/appclinic
```

(Semua langkah **C–I** di bawah dikerjakan **di dalam sesi SSH ini**, bukan di Mac.)

---

## C. Pasang Python, MySQL & Paket Pendukung Ubuntu

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-pip \
  mysql-server libmysqlclient-dev build-essential \
  libjpeg-dev zlib1g-dev
```

- `python3-venv`/`python3-pip` — Python & virtual environment.
- `mysql-server` — database MySQL (berjalan sebagai service Ubuntu otomatis).
- `build-essential`, `libjpeg-dev`, `zlib1g-dev` — dibutuhkan saat memasang
  `pillow` (dipakai untuk memproses foto pasien).

Pastikan MySQL otomatis menyala & aktif:

```bash
sudo systemctl enable --now mysql
sudo systemctl status mysql --no-pager
```

> (Opsional tapi disarankan) Amankan instalasi MySQL baru:
> ```bash
> sudo mysql_secure_installation
> ```
> Ikuti prompt-nya — boleh pilih default untuk semua pertanyaan kalau tidak yakin.

---

## D. Buat Database & User MySQL untuk AppClinic

```bash
sudo mysql -u root <<'SQL'
CREATE DATABASE appclinic CHARACTER SET utf8mb4;
CREATE USER 'appclinic_app'@'localhost' IDENTIFIED BY 'PASSWORD_MYSQL';
GRANT ALL PRIVILEGES ON appclinic.* TO 'appclinic_app'@'localhost';
FLUSH PRIVILEGES;
SQL
```

> Ganti `PASSWORD_MYSQL` dengan password kuat pilihan Anda **sebelum**
> menjalankan perintah di atas. Catat password ini baik-baik — akan dipakai
> lagi di bagian F & G. Password ini **tidak pernah ditulis ke dalam file
> apa pun di folder aplikasi/repo** — hanya disimpan di 1 file konfigurasi
> server (bagian F) yang berada **di luar** folder aplikasi.

---

## E. Pasang Dependensi Python (virtual environment)

Masih di `~/appclinic` (lewat SSH):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Tandai berhasil kalau tidak ada error merah di akhir `pip install`. Virtual
environment ini (`.venv`) hanya perlu dibuat **sekali** — untuk sesi SSH
berikutnya, cukup `source .venv/bin/activate` lagi sebelum menjalankan `python3`.

---

## F. Simpan Konfigurasi (Password MySQL) di Luar Folder Aplikasi

Buat 1 file konfigurasi khusus di `/etc/` — **bukan** di dalam folder
`~/appclinic` (supaya tidak pernah ikut ter-rsync balik ke Mac atau ikut ke
git):

```bash
sudo tee /etc/appclinic.env > /dev/null <<'EOF'
AC_DB_BACKEND=mysql
AC_MYSQL_HOST=localhost
AC_MYSQL_PORT=3306
AC_MYSQL_USER=appclinic_app
AC_MYSQL_PASSWORD=PASSWORD_MYSQL
AC_MYSQL_DB=appclinic
EOF
sudo chmod 600 /etc/appclinic.env
```

> Ganti `PASSWORD_MYSQL` di file ini dengan password **yang sama persis**
> dengan yang dibuat di bagian D. `chmod 600` membuat file ini hanya bisa
> dibaca oleh root/pemilik — aman dari user lain di server yang sama.

---

## G. Uji Jalan Manual (sebelum dijadikan service permanen)

Masih di `~/appclinic`, dengan `.venv` aktif:

```bash
set -a; source /etc/appclinic.env; set +a
python3 run_server.py
```

Akan muncul:
```
====================================================
   APPCLINIC  --  SERVER
   Database       : MYSQL
====================================================
   Komputer ini   : http://localhost:5000
   Komputer lain  : http://IP_SERVER:5000
====================================================
```

Saat **pertama kali** jalan, aplikasi otomatis membuat semua tabel (kosong) di
database `appclinic` — tidak perlu import SQL manual.

**Dari Mac** (atau kasir lain di jaringan/Tailscale yang sama), buka browser:
`http://IP_SERVER:5000` → login `admin` / `admin123` → cek halaman tampil
normal (judul/logo "AppClinic"). Kalau berhasil, tekan `CTRL+C` di sesi SSH
untuk menghentikan sesi uji ini — lanjut ke bagian H supaya server jalan
**otomatis & permanen** (tidak tergantung sesi SSH tetap terbuka).

---

## H. Jadikan Service Permanen (systemd) — Auto-Start & Auto-Restart

Ini perbedaan penting dibanding Windows: di Ubuntu, server **tidak perlu**
jendela terminal tetap terbuka. Pakai `systemd` supaya AppClinic otomatis
jalan saat server dinyalakan, dan otomatis bangun lagi kalau sempat crash.

```bash
sudo tee /etc/systemd/system/appclinic.service > /dev/null <<EOF
[Unit]
Description=AppClinic Server
After=network.target mysql.service

[Service]
Type=simple
User=USER_UBUNTU
WorkingDirectory=/home/USER_UBUNTU/appclinic
EnvironmentFile=/etc/appclinic.env
ExecStart=/home/USER_UBUNTU/appclinic/.venv/bin/python3 /home/USER_UBUNTU/appclinic/run_server.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF
```

> Ganti **semua** `USER_UBUNTU` di atas dengan username SSH Anda yang
> sebenarnya, dan sesuaikan path `/home/USER_UBUNTU/appclinic` kalau Anda
> menaruh folder di lokasi lain.

Aktifkan:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now appclinic
sudo systemctl status appclinic --no-pager
```

Status harus `active (running)` berwarna hijau. Mulai sekarang AppClinic
otomatis jalan setiap server Ubuntu menyala — tidak perlu login/SSH manual
lagi setelah ini.

**Melihat log** (kalau butuh cek error):
```bash
journalctl -u appclinic -f
```
(`-f` = ikuti log baru secara live; `Ctrl+C` untuk keluar dari tampilan log.)

---

## I. Buka Akses dari Jaringan (Firewall)

```bash
sudo ufw allow 5000/tcp
sudo ufw status
```

Kalau `ufw` belum aktif sama sekali dan Anda ingin mengaktifkannya (opsional,
tingkatkan keamanan server):
```bash
sudo ufw allow OpenSSH
sudo ufw enable
```
(`allow OpenSSH` **wajib** dijalankan dulu sebelum `enable`, supaya Anda tidak
terkunci dari akses SSH sendiri.)

> **Lebih aman (opsional):** kalau server ini hanya diakses lewat Tailscale
> (bukan jaringan kantor/LAN terbuka), batasi port 5000 **hanya** untuk
> interface Tailscale, bukan untuk semua jaringan:
> ```bash
> sudo ufw allow in on tailscale0 to any port 5000
> sudo ufw delete allow 5000/tcp
> ```

---

## J. Verifikasi Akhir dari Komputer Kasir

1. Pastikan komputer kasir 1 jaringan dengan server (LAN/WiFi kantor), atau
   sama-sama tersambung Tailscale.
2. Buka browser → `http://IP_SERVER:5000`.
3. Login `admin` / `admin123` → **segera ganti password** lewat menu
   **Manajemen Pengguna**.
4. Untuk HP (foto pasien/komisi), buka `http://IP_SERVER:5000/mobile`.

---

## K. Memperbarui Aplikasi di Kemudian Hari

Setiap kali ada perubahan kode (fitur baru/perbaikan bug) yang perlu dipasang
ke server:

```bash
# Dari Mac:
cd "/Users/sisadmin_python/Documents/App Python/Lauda SysApy"
rsync -avz --progress \
  --exclude 'appclinic.db' --exclude '__pycache__' --exclude '.git' \
  --exclude 'backup/' --exclude 'backup_histori/' --exclude '.venv' \
  ./ USER_UBUNTU@IP_SERVER:~/appclinic/

# Lalu restart service di server:
ssh USER_UBUNTU@IP_SERVER "sudo systemctl restart appclinic"
```

Kalau perubahan menyentuh `requirements.txt` (ada library baru), tambahkan
langkah ini sebelum restart:
```bash
ssh USER_UBUNTU@IP_SERVER "cd ~/appclinic && source .venv/bin/activate && pip install -r requirements.txt"
```

---

## L. Backup Rutin (MySQL) — Otomatis Tiap Hari lewat Cron

Di server (SSH), buat skrip backup:

```bash
mkdir -p ~/appclinic-backup
sudo tee /usr/local/bin/backup-appclinic.sh > /dev/null <<'EOF'
#!/bin/bash
set -a; source /etc/appclinic.env; set +a
TS=$(date +%Y-%m-%d_%H%M)
mysqldump -u appclinic_app -p"$AC_MYSQL_PASSWORD" appclinic \
  > "$HOME/appclinic-backup/appclinic_${TS}.sql"
find "$HOME/appclinic-backup" -name '*.sql' -mtime +30 -delete
EOF
sudo chmod +x /usr/local/bin/backup-appclinic.sh
```

Jadwalkan tiap hari jam 23:30 lewat cron:
```bash
crontab -e
```
Tambahkan baris:
```
30 23 * * * /usr/local/bin/backup-appclinic.sh
```

> Skrip di atas otomatis menghapus backup yang lebih tua dari 30 hari supaya
> disk tidak penuh. **Sesekali salin folder `~/appclinic-backup/` ke tempat
> lain** (laptop/cloud) — backup yang hanya ada di 1 komputer yang sama tetap
> berisiko kalau komputer itu rusak/dicuri.
>
> Foto pasien tersimpan terpisah di `~/appclinic/static/uploads/` — folder
> ini juga sebaiknya ikut dicadangkan berkala (mis. `rsync` ke Mac/komputer
> lain), tidak tercakup oleh `mysqldump`.

---

## M. Mengatasi Masalah

| Masalah | Solusi |
|---|---|
| `systemctl status appclinic` menunjukkan `failed` | Jalankan `journalctl -u appclinic -f` lalu coba `sudo systemctl restart appclinic`, baca pesan error yang muncul. |
| `Can't connect to MySQL server` | `sudo systemctl status mysql` — pastikan `active (running)`. Cek `AC_MYSQL_PASSWORD` di `/etc/appclinic.env` sama persis dengan yang dibuat di bagian D. |
| `RuntimeError: AC_MYSQL_PASSWORD wajib diset` | Service tidak menemukan `/etc/appclinic.env` — cek baris `EnvironmentFile=` di unit file (bagian H) path-nya benar, lalu `sudo systemctl daemon-reload && sudo systemctl restart appclinic`. |
| Komputer kasir tidak bisa buka `http://IP_SERVER:5000` | Cek `sudo ufw status` (port 5000 harus `ALLOW`); pastikan 1 jaringan/Tailscale yang sama; cek service jalan dengan `sudo systemctl status appclinic`. |
| Port 5000 sudah dipakai aplikasi lain | `sudo ss -tulpn \| grep 5000` untuk lihat proses yang memakainya, atau ubah `PORT = 5000` di `run_server.py` lalu restart service. |
| Habis `rsync` tapi perubahan tidak tampak | Pastikan service di-restart (`sudo systemctl restart appclinic`) — `rsync` hanya menyalin file, tidak otomatis me-reload aplikasi yang sedang berjalan. |
| Mau pindah balik ke SQLite di server ini | Ubah `AC_DB_BACKEND=sqlite` di `/etc/appclinic.env`, hapus baris `AC_MYSQL_*` (tidak wajib tapi rapi), lalu `sudo systemctl restart appclinic`. File `appclinic.db` otomatis dibuat di `~/appclinic/`. |

---

## N. Menghentikan / Menjeda Service

```bash
sudo systemctl stop appclinic      # hentikan sekarang
sudo systemctl disable appclinic   # jangan auto-start lagi saat boot
```
Untuk menyalakan lagi: `sudo systemctl enable --now appclinic`.

---

*AppClinic — Sistem Manajemen Klinik. Dokumen ini untuk instalasi di Ubuntu
Server, dikerjakan dari Mac lewat SSH. Untuk cara menyambung ke server yang
beda lokasi/kota, lihat `SETUP-SERVER-UBUNTU.md`. Untuk instalasi di Windows,
lihat `PANDUAN-SERVER.md`.*
