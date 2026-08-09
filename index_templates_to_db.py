"""Compute phashes for AgeTemplate image files and store them in the existing SQLite DB.
Updates rows in the age_template table matching image_filename.
"""
import os
import sqlite3
from PIL import Image
import imagehash

BASE_DIR = os.path.dirname(__file__)
UPLOAD_DIR = os.path.join(BASE_DIR, 'templates', 'static', 'uploads')
DB = os.path.join(BASE_DIR, 'instance', 'database.db')

conn = sqlite3.connect(DB)
cur = conn.cursor()

cur.execute("SELECT id, image_filename FROM age_template WHERE phash IS NULL OR phash = '';")
rows = cur.fetchall()
if not rows:
    print('No templates without phash found.')
else:
    print(f'Found {len(rows)} templates without phash. Computing...')
for rid, fname in rows:
    path = os.path.join(UPLOAD_DIR, fname)
    if not os.path.exists(path):
        print(f'File not found for {fname}, skipping.')
        continue
    try:
        ph = imagehash.phash(Image.open(path))
    except Exception as e:
        print(f'Failed to compute phash for {fname}: {e}')
        continue
    ph_hex = str(ph)
    cur.execute('UPDATE age_template SET phash = ? WHERE id = ?;', (ph_hex, rid))
    print(f'Updated {fname} -> phash {ph_hex}')

conn.commit()
conn.close()
print('Done.')
