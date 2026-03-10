import sqlite3

conn = sqlite3.connect("database.db")
cursor = conn.cursor()

cursor.execute("""
INSERT INTO image_hashes(hash,source,trust_level)
VALUES(
'ff12aa33bb44cc55',
'BBC News',
'trusted'
)
""")

conn.commit()
conn.close()

print("Test hash inserted")