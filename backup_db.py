"""
Backup database Rachel Clinic dengan aman (SQLite Online Backup API).
Aman dipakai walau server sedang berjalan & memakai mode WAL.

Hasil: backup\rachel_clinic_YYYYMMDD_HHMMSS.db
"""
import os
import sqlite3
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
SRC  = os.path.join(HERE, 'rachel_clinic.db')


def main():
    if not os.path.exists(SRC):
        print('[GAGAL] rachel_clinic.db tidak ditemukan.')
        return
    backup_dir = os.path.join(HERE, 'backup')
    os.makedirs(backup_dir, exist_ok=True)
    ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    dst_path = os.path.join(backup_dir, f'rachel_clinic_{ts}.db')

    src = sqlite3.connect(SRC)
    dst = sqlite3.connect(dst_path)
    try:
        with dst:
            src.backup(dst)          # konsisten walau ada WAL / sedang dipakai
    finally:
        dst.close()
        src.close()

    size_mb = os.path.getsize(dst_path) / (1024 * 1024)
    print(f'[OK] Backup tersimpan: {dst_path} ({size_mb:.1f} MB)')


if __name__ == '__main__':
    main()
