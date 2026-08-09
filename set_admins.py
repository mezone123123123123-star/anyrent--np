import sqlite3
import os
from werkzeug.security import generate_password_hash
from datetime import datetime

DB = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
conn = sqlite3.connect(DB)
cur = conn.cursor()

def ensure_user(email, username=None, password='adminbrothers'):
    cur.execute('SELECT id, username, email, is_admin FROM user WHERE email = ?', (email,))
    row = cur.fetchone()
    if row:
        print('Found user:', row)
        return row[0]
    # create user
    if not username:
        username = email.split('@')[0]
    pw_hash = generate_password_hash(password, method='pbkdf2:sha256')
    created_at = datetime.utcnow().isoformat(sep=' ')
    cur.execute('INSERT INTO user (username, email, password_hash, full_name, verification_status, is_admin, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (username, email, pw_hash, username, 'verified', 1, created_at))
    conn.commit()
    uid = cur.lastrowid
    print('Created user id', uid)
    return uid

# Ensure target admin exists
target_email = 'dhakalrijesh50@gmail.com'
uid = ensure_user(target_email)
# Set as admin and verified
cur.execute("UPDATE user SET is_admin = 1, verification_status = 'verified' WHERE id = ?", (uid,))

# Remove admin from adminguy if exists
cur.execute("SELECT id, username, is_admin FROM user WHERE username = 'adminguy'")
row = cur.fetchone()
if row:
    cur.execute("UPDATE user SET is_admin = 0 WHERE id = ?", (row[0],))
    print('Removed admin flag from', row[1])
else:
    print('adminguy not found')

conn.commit()
print('Done. Updated admins.')
conn.close()
