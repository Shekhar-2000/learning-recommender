import sqlite3
import json

c = sqlite3.connect('db.sqlite3')
cur = c.cursor()
cols = [r[1] for r in cur.execute('PRAGMA table_info("learning_system_customuser")').fetchall()]
rows = cur.execute('SELECT * FROM learning_system_customuser LIMIT 10').fetchall()
print(json.dumps({'columns': cols, 'rows': rows}, indent=2))
