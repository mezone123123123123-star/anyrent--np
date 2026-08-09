import sqlite3
import os
DB = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("PRAGMA table_info(item);")
cols = [r[1] for r in cur.fetchall()]
if 'video' not in cols:
    print('Adding video column to item table...')
    cur.execute("ALTER TABLE item ADD COLUMN video VARCHAR(500) DEFAULT '';")
    conn.commit()
    print('Video column added.')
else:
    print('Video column already present.')
conn.close()
