# Remote ke Ubuntu Server di kota lain (lewat internet biasa)

Server Ubuntu sudah jadi, cuma beda kota dari Anda. Solusinya: **Tailscale** —
bikin jaringan privat lewat internet antara PC Anda (Mac) dan server, tanpa
perlu setting router/IP publik/domain.

**Syarat sekali saja:** harus ada yang bisa pegang server itu **satu kali** —
entah Anda sendiri kalau pernah ke lokasinya, orang di lokasi (staf/teknisi)
yang Anda pandu lewat telepon, atau installer Ubuntu-nya kasih opsi "jalankan
skrip saat setup". Setelah langkah #1 di bawah ini selesai sekali, **seterusnya
semua bisa dari Mac Anda, dari kota manapun.**

---

## 1. Di server (sekali saja, oleh siapa pun yang pegang fisik/akses awal)

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```
Perintah kedua menampilkan link — buka link itu di browser manapun, login
pakai akun Google (atau buat akun Tailscale baru), server akan muncul di
dashboard Tailscale.

---

## 2. Di Mac Anda

Download & install **Tailscale** dari https://tailscale.com/download/mac,
login pakai akun yang **sama persis** dengan yang dipakai di langkah 1.

---

## 3. Remote dari Mac

Buka app Tailscale di Mac → lihat nama/IP server di daftar device
(contoh: `100.x.x.x`). Lalu:

**Lewat terminal (SSH):**
```bash
ssh nama_user_ubuntu@100.x.x.x
```

**Lewat tampilan visual (kalau mau klik-klik, bukan ketik perintah):**
1. Di server, jalankan sekali (via SSH di atas):
   ```bash
   sudo apt install -y xfce4 xfce4-goodies xrdp
   sudo systemctl enable --now xrdp
   echo xfce4-session > ~/.xsession
   sudo adduser xrdp ssl-cert && sudo systemctl restart xrdp
   sudo ufw allow 3389/tcp
   ```
2. Di Mac, install app gratis **Microsoft Remote Desktop** (Mac App Store) →
   Add PC → isi `100.x.x.x` → connect pakai username/password Ubuntu.

Selesai — ini bisa diulang kapan pun dari kota manapun, selama Mac & server
sama-sama nyala Tailscale dan tersambung internet.

---

*Aplikasi (install Python/MySQL/AppClinic di server-nya) lihat
`PANDUAN-INSTALASI-UBUNTU.md`, dikerjakan dari dalam sesi remote (SSH/Remote
Desktop) di atas.*
