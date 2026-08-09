import sqlite3
import os
DB = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
conn = sqlite3.connect(DB)
cur = conn.cursor()
# Check if column phash exists
cur.execute("PRAGMA table_info(age_template);")
cols = [r[1] for r in cur.fetchall()]
if 'phash' not in cols:
    print('Adding phash column to age_template table...')
    cur.execute("ALTER TABLE age_template ADD COLUMN phash VARCHAR(64);")
    conn.commit()
    print('Column added.')
else:
    print('phash column already exists.')
conn.close()
