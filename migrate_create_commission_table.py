import sqlite3
import os
DB = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
conn = sqlite3.connect(DB)
cur = conn.cursor()
# Create commission_record table if not exists
cur.execute("""
CREATE TABLE IF NOT EXISTS commission_record (
    id INTEGER PRIMARY KEY,
    rental_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    created_at DATETIME
);
""")
conn.commit()
print('commission_record table ensured')
conn.close()
