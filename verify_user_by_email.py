import sqlite3
import os
import sys

DB = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
email = sys.argv[1] if len(sys.argv) > 1 else 'dhakalrijesh50@gmail.coml'

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute('SELECT id, username, email, verification_status FROM user WHERE email = ?', (email,))
row = cur.fetchone()
if row:
    uid = row[0]
    cur.execute("UPDATE user SET verification_status = 'verified' WHERE id = ?", (uid,))
    conn.commit()
    print(f"User {row[1]} ({row[2]}) set to verified.")
else:
    # try a common typo: remove trailing 'l'
    alt = email.rstrip('l')
    if alt != email:
        cur.execute('SELECT id, username, email, verification_status FROM user WHERE email = ?', (alt,))
        row2 = cur.fetchone()
        if row2:
            uid = row2[0]
            cur.execute("UPDATE user SET verification_status = 'verified' WHERE id = ?", (uid,))
            conn.commit()
            print(f"User {row2[1]} ({row2[2]}) set to verified (matched alt email '{alt}').")
            conn.close()
            sys.exit(0)
    print('No user found with that email.')
conn.close()
