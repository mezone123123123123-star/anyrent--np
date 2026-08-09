import sqlite3
import os

DB = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute('''
CREATE TABLE IF NOT EXISTS listing_change (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id INTEGER NOT NULL,
    proposer_id INTEGER NOT NULL,
    new_data TEXT NOT NULL,
    prev_is_approved INTEGER DEFAULT 1,
    status TEXT DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
''')
conn.commit()
conn.close()
print('ListingChange table ensured')
