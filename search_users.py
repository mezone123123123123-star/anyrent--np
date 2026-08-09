import sqlite3, os
DB = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
conn = sqlite3.connect(DB)
cur = conn.cursor()
terms = ['dhakal','rijesh','dhakalrijesh','dhakalrijesh50','dhakalrijesh50@gmail.com']
found = False
for term in terms:
    cur.execute("SELECT id, username, email, verification_status FROM user WHERE email LIKE ? OR username LIKE ?;", (f'%{term}%', f'%{term}%'))
    rows = cur.fetchall()
    if rows:
        print('Matches for', term)
        for r in rows:
            print(r)
        found = True
if not found:
    print('No similar users found for search terms')
conn.close()
