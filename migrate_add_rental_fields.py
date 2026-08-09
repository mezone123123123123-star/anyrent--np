import sqlite3
import os
DB = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
conn = sqlite3.connect(DB)
cur = conn.cursor()
# Check if columns exist
cur.execute("PRAGMA table_info(rental);")
cols = [r[1] for r in cur.fetchall()]
added = False
if 'deposit_amount' not in cols:
    print('Adding deposit_amount column to rental table...')
    cur.execute("ALTER TABLE rental ADD COLUMN deposit_amount INTEGER DEFAULT 0;")
    added = True
if 'admin_commission' not in cols:
    print('Adding admin_commission column to rental table...')
    cur.execute("ALTER TABLE rental ADD COLUMN admin_commission INTEGER DEFAULT 0;")
    added = True
if added:
    conn.commit()
    print('Columns added.')
else:
    print('Columns already present.')
conn.close()
