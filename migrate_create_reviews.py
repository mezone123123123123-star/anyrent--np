import sqlite3
import os
DB = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
conn = sqlite3.connect(DB)
cur = conn.cursor()
# Create reviews table if not exists
cur.execute("CREATE TABLE IF NOT EXISTS review (id INTEGER PRIMARY KEY, item_id INTEGER NOT NULL, user_id INTEGER NOT NULL, rating INTEGER NOT NULL, comment TEXT, created_at DATETIME);")
conn.commit()
# Ensure there is no existing FK constraints necessary for this simple migration
print('review table ensured')
conn.close()
