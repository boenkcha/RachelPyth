"""
Migrasi data dari appclinic.db (SQLite) ke MySQL (appclinic).

Jalankan SATU KALI setelah:
1. Server pernah dijalankan minimal sekali dgn AC_DB_BACKEND=mysql
   (supaya init_db_mysql() sudah membuat semua tabel), ATAU jalankan
   langsung: python3 -c "import app; app.init_db_mysql()"
2. Kredensial MySQL (appclinic_app/appclinic) sudah benar di app.py
   (MYSQL_CONFIG) atau lewat env var AC_MYSQL_*.

Script ini AMAN dijalankan berkali-kali — tiap tabel di-TRUNCATE dulu
sebelum diisi ulang dari SQLite (jadi selalu jadi salinan persis data
SQLite saat ini, bukan digabung/duplikat).

Jalankan: python3 migrate_to_mysql.py
"""
import sqlite3
import sys
import time

import app as _app   # reuse DB_PATH & MYSQL_CONFIG dari app.py (single source of truth)
import pymysql

BATCH_SIZE = 2000

# Urutan tidak penting krn FOREIGN_KEY_CHECKS dimatikan selama migrasi.
TABLES = [name for name, _ddl in _app._MYSQL_TABLES]


def _sqlite_connect():
    con = sqlite3.connect(_app.DB_PATH)
    con.row_factory = None   # plain tuple, lebih cepat utk bulk read
    return con


def _mysql_connect():
    return pymysql.connect(**_app.MYSQL_CONFIG)


def _get_numeric_cols(mconn, table):
    """Kolom bertipe angka di MySQL — dipakai utk sanitasi '' -> NULL (SQLite
    longgar-tipe: kolom INTEGER/REAL bisa saja berisi string kosong '')."""
    mcur = mconn.cursor()
    mcur.execute("""
        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s
          AND DATA_TYPE IN ('int','bigint','double','float','decimal')
    """, (_app.MYSQL_CONFIG['database'], table))
    return {r[0] for r in mcur.fetchall()}


def migrate_table(sconn, mconn, table):
    scur = sconn.cursor()
    scur.execute(f'SELECT * FROM "{table}"')
    cols = [d[0] for d in scur.description]
    numeric_idx = {i for i, c in enumerate(cols) if c in _get_numeric_cols(mconn, table)}
    col_list = ",".join(f"`{c}`" for c in cols)
    placeholders = ",".join(["%s"] * len(cols))
    insert_sql = f"INSERT INTO `{table}` ({col_list}) VALUES ({placeholders})"

    mcur = mconn.cursor()
    mcur.execute("SET FOREIGN_KEY_CHECKS=0")
    mcur.execute(f"TRUNCATE TABLE `{table}`")

    total = 0
    t0 = time.time()
    while True:
        rows = scur.fetchmany(BATCH_SIZE)
        if not rows:
            break
        if numeric_idx:
            # SQLite longgar-tipe: kolom angka bisa kebagian '' — MySQL tolak.
            rows = [
                tuple(None if (i in numeric_idx and v == '') else v
                      for i, v in enumerate(row))
                for row in rows
            ]
        mcur.executemany(insert_sql, rows)
        total += len(rows)
    mconn.commit()
    dt = time.time() - t0
    print(f"  {table}: {total} baris ({dt:.1f}s)")
    return total


def main():
    print("=" * 60)
    print("Migrasi data SQLite -> MySQL (appclinic)")
    print("=" * 60)
    if _app.DB_BACKEND != 'mysql':
        print("[peringatan] AC_DB_BACKEND bukan 'mysql' saat ini, tapi migrasi")
        print("             tetap jalan ke MySQL_CONFIG yang terkonfigurasi.")

    sconn = _sqlite_connect()
    mconn = _mysql_connect()

    summary = []
    try:
        for table in TABLES:
            try:
                n = migrate_table(sconn, mconn, table)
                summary.append((table, n, None))
            except Exception as e:
                mconn.rollback()
                summary.append((table, None, str(e)))
                print(f"  {table}: GAGAL -> {e}")
    finally:
        mcur = mconn.cursor()
        mcur.execute("SET FOREIGN_KEY_CHECKS=1")
        mconn.commit()
        sconn.close()
        mconn.close()

    print("\n" + "=" * 60)
    print("Ringkasan verifikasi (baris tersalin per tabel):")
    print("=" * 60)
    ok = True
    for table, n, err in summary:
        if err:
            print(f"  [GAGAL] {table}: {err}")
            ok = False
        else:
            print(f"  [OK] {table}: {n}")
    print("=" * 60)
    if ok:
        print("Migrasi selesai tanpa error.")
    else:
        print("Migrasi selesai DENGAN beberapa error - cek tabel di atas.")
        sys.exit(1)


if __name__ == '__main__':
    main()
