import sqlite3, os
from datetime import datetime
DB = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
conn = sqlite3.connect(DB)
cur = conn.cursor()
# Find rentals with admin_commission > 0 that are approved/completed
cur.execute("SELECT id, admin_commission, created_at FROM rental WHERE (admin_commission IS NOT NULL AND admin_commission > 0) AND status IN ('approved','completed')")
rows = cur.fetchall()
inserted = 0
for rid, amt, created in rows:
    # check if commission_record exists
    cur.execute('SELECT id FROM commission_record WHERE rental_id = ?', (rid,))
    if cur.fetchone():
        continue
    created_at = created if created else datetime.utcnow().isoformat(sep=' ')
    cur.execute('INSERT INTO commission_record (rental_id, amount, created_at) VALUES (?,?,?)', (rid, amt, created_at))
    inserted += 1
conn.commit()
print(f'Inserted {inserted} commission records')
conn.close()
