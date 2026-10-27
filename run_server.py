"""
Launcher SERVER AppClinic (produksi).

- Memakai waitress (server WSGI tangguh) bila tersedia.
- Fallback ke server bawaan Flask bila waitress belum terpasang.
- Otomatis mendeteksi alamat IP LAN supaya komputer kasir lain mudah terhubung.

Jalankan lewat: jalankan_server.bat  (atau: python run_server.py)
"""
import os
import socket
from app import app, init_db

PORT = 5000


def get_lan_ip():
    """Ambil IP LAN komputer ini (yang dipakai komputer lain untuk terhubung)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Tidak benar-benar mengirim data — hanya memilih interface keluar.
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def main():
    init_db()
    ip = get_lan_ip()
    backend = os.environ.get('AC_DB_BACKEND', 'mysql').strip().lower()
    bar = '=' * 58
    print(bar)
    print('   APPCLINIC  --  SERVER')
    print(f'   Database       : {backend.upper()}')
    print(bar)
    print(f'   Komputer ini   : http://localhost:{PORT}')
    print(f'   Komputer lain  : http://{ip}:{PORT}')
    print('   (komputer kasir/cabang buka alamat di atas pada browser)')
    print(bar)
    print('   Biarkan jendela ini TERBUKA selama jam operasional.')
    print('   Tutup jendela / tekan CTRL+C untuk menghentikan server.')
    print(bar)

    try:
        from waitress import serve
        serve(app, host='0.0.0.0', port=PORT, threads=12)
    except ImportError:
        print('[info] waitress belum terpasang -> memakai server bawaan Flask.')
        print('       (jalankan INSTALL.bat agar performa lebih baik)')
        app.run(host='0.0.0.0', port=PORT, threaded=True, debug=False)


if __name__ == '__main__':
    main()
