import sqlite3, os
from werkzeug.security import generate_password_hash
from datetime import datetime

DB = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
conn = sqlite3.connect(DB)
cur = conn.cursor()

# create test user
email = 'testuser@example.com'
username = 'testuser'
password = 'testpass'
cur.execute('SELECT id FROM user WHERE email = ?', (email,))
if not cur.fetchone():
    pw_hash = generate_password_hash(password, method='pbkdf2:sha256')
    cur.execute('INSERT INTO user (username, email, password_hash, full_name, verification_status, is_admin, created_at) VALUES (?,?,?,?,?,?,?)',
                (username, email, pw_hash, 'Test User', 'unverified', 0, datetime.utcnow().isoformat(sep=' ')))
    print('Created test user', email)
else:
    print('Test user already exists')

# ensure admins
admins = ['dhakalrijesh50@gmail.com', 'admin@anyrent.local']
for a in admins:
    cur.execute('SELECT id FROM user WHERE email = ?', (a,))
    row = cur.fetchone()
    if row:
        cur.execute('UPDATE user SET is_admin = 1, verification_status = "verified" WHERE id = ?', (row[0],))
        print('Set admin for', a)
    else:
        # create admin user if missing
        uname = a.split('@')[0]
        pw_hash = generate_password_hash('adminbrothers', method='pbkdf2:sha256')
        cur.execute('INSERT INTO user (username, email, password_hash, full_name, verification_status, is_admin, created_at) VALUES (?,?,?,?,?,?,?)',
                    (uname, a, pw_hash, 'Administrator', 'verified', 1, datetime.utcnow().isoformat(sep=' ')))
        print('Created admin user', a)

conn.commit()
conn.close()
