import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

# create users table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT,
password TEXT
)
""")

# create image hash table
cursor.execute("""
CREATE TABLE IF NOT EXISTS image_hashes(
id INTEGER PRIMARY KEY AUTOINCREMENT,
hash TEXT,
source TEXT,
trust_level TEXT
)
""")

conn.commit()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print("Tables in database:", cursor.fetchall())

conn.close()