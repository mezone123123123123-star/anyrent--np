import sqlite3, os
DB = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("SELECT id, username, email, verification_status FROM user WHERE username = 'rijeshdhakal' OR email = 'rijeshdhakal24@gmail.com'")
row = cur.fetchone()
if row:
    cur.execute("UPDATE user SET verification_status = 'verified' WHERE id = ?", (row[0],))
    conn.commit()
    print(f"Verified user: id={row[0]}, username={row[1]}, email={row[2]}")
else:
    print('No matching user found to verify')
conn.close()
