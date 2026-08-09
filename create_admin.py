import sqlite3
import os
from werkzeug.security import generate_password_hash
from datetime import datetime

DB = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
username = 'adminguy'
email = 'admin@anyrent.local'
password = 'adminbrothers'

conn = sqlite3.connect(DB)
cur = conn.cursor()
# Check if user exists
cur.execute('SELECT id FROM user WHERE username = ? OR email = ?', (username, email))
row = cur.fetchone()
if row:
    print('Admin user already exists with id', row[0])
else:
    pw_hash = generate_password_hash(password, method='pbkdf2:sha256')
    created_at = datetime.utcnow().isoformat(sep=' ')
    cur.execute(
        'INSERT INTO user (username, email, password_hash, full_name, verification_status, is_admin, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (username, email, pw_hash, 'Administrator', 'verified', 1, created_at)
    )
    conn.commit()
    print('Created admin user', username, 'with email', email)

conn.close()
