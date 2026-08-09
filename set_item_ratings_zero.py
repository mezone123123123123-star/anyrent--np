import sqlite3, os
DB = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("UPDATE item SET rating = 0.0 WHERE rating IS NULL OR rating != 0.0;")
cur.execute("UPDATE item SET reviews = 0 WHERE reviews IS NULL OR reviews != 0;")
conn.commit()
print('All item ratings set to 0 and reviews to 0.')
conn.close()
