import sqlite3
import os
DB = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("PRAGMA table_info(message);")
cols = [r[1] for r in cur.fetchall()]
if 'image' not in cols:
    print('Adding image column to message table...')
    cur.execute("ALTER TABLE message ADD COLUMN image VARCHAR(500) DEFAULT '';")
    print('Image column added.')
else:
    print('Image column already present.')
if 'video' not in cols:
    print('Adding video column to message table...')
    cur.execute("ALTER TABLE message ADD COLUMN video VARCHAR(500) DEFAULT '';")
    print('Video column added.')
else:
    print('Video column already present.')
conn.commit()
conn.close()
