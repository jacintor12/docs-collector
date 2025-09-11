import sys
import os
import sqlite3

db_path = os.path.join(os.path.dirname(__file__), '..', 'document_hub.db')
db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'document_hub.db'))
print('Checking database file:', db_path)
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print('Tables:', tables)
conn.close()
