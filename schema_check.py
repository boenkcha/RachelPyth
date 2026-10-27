import sqlite3
con = sqlite3.connect('appclinic.db')
cur = con.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
for t in tables:
    cur.execute("PRAGMA table_info([%s])" % t)
    cols = [r[1] for r in cur.fetchall()]
    cur.execute("SELECT COUNT(*) FROM [%s]" % t)
    cnt = cur.fetchone()[0]
    print("%s (%d rows): %s" % (t, cnt, ", ".join(cols)))
con.close()
