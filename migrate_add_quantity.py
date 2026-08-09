import sqlite3
import os
DB = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("PRAGMA table_info(item);")
cols = [r[1] for r in cur.fetchall()]
if 'quantity' not in cols:
    print('Adding quantity column to item table...')
    cur.execute("ALTER TABLE item ADD COLUMN quantity INTEGER DEFAULT 1;")
    print('Setting quantity = 1 for all existing items...')
    cur.execute("UPDATE item SET quantity = 1 WHERE quantity IS NULL;")
    conn.commit()
    print('Quantity column added and backfilled.')
else:
    cur.execute("UPDATE item SET quantity = 1 WHERE quantity IS NULL;")
    conn.commit()
    print('Quantity column already present; backfilled missing values to 1.')
conn.close()
