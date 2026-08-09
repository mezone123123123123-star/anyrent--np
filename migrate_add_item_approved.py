import sqlite3
import os
DB = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
conn = sqlite3.connect(DB)
cur = conn.cursor()
# Check if column is_approved exists
cur.execute("PRAGMA table_info(item);")
cols = [r[1] for r in cur.fetchall()]
if 'is_approved' not in cols:
    print('Adding is_approved column to item table...')
    cur.execute("ALTER TABLE item ADD COLUMN is_approved INTEGER DEFAULT 1;")
    conn.commit()
    print('Column added.')
else:
    print('is_approved column already exists.')
conn.close()
