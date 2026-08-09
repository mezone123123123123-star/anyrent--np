import sqlite3, os
from datetime import datetime
DB = os.path.join(os.path.dirname(__file__), 'instance', 'database.db')
conn = sqlite3.connect(DB)
cur = conn.cursor()

more = [
    {'owner_id':1,'name':'GoPro HERO 11','category':'Camera','type':'Action','price':900,'deposit':3000,'location':'Kathmandu','image':'https://images.unsplash.com/photo-1519183071298-a2962be54a88?auto=format&fit=crop&w=900&q=80','description':'Lightweight action camera for adventure shots.'},
    {'owner_id':1,'name':'DJ Mixer X100','category':'Music','type':'DJ','price':1500,'deposit':5000,'location':'Kathmandu','image':'https://images.unsplash.com/photo-1518972559570-9f3b5f79c1df?auto=format&fit=crop&w=900&q=80','description':'Professional DJ controller for events.'},
    {'owner_id':1,'name':'Electric Mountain Bike','category':'Bike','type':'Electric','price':2200,'deposit':8000,'location':'Lalitpur','image':'https://images.unsplash.com/photo-1542365887-43b8a9e45c10?auto=format&fit=crop&w=900&q=80','description':'E-bike for off-road and city rides.'},
    {'owner_id':1,'name':'4K Projector Plus','category':'Electronics','type':'Projector','price':1100,'deposit':4000,'location':'Bhaktapur','image':'https://images.unsplash.com/photo-1503602642458-232111445657?auto=format&fit=crop&w=900&q=80','description':'High-brightness 4K projector.'},
    {'owner_id':1,'name':'Portable PA Speaker','category':'Music','type':'Audio','price':700,'deposit':2500,'location':'Kathmandu','image':'https://images.unsplash.com/photo-1599388803962-0d8f7f3c8ce3?auto=format&fit=crop&w=900&q=80','description':'Battery powered PA speaker for small events.'}
]
count = 0
for it in more:
    cur.execute('INSERT INTO item (owner_id, name, category, type, description, price, deposit, location, image, rating, reviews, created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)',
                (it['owner_id'], it['name'], it['category'], it['type'], it['description'], it['price'], it['deposit'], it['location'], it['image'], 0.0, 0, datetime.utcnow().isoformat(sep=' ')))
    count += 1
conn.commit()
print(f'Inserted {count} items')
conn.close()
