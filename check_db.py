import sqlite3

con = sqlite3.connect("suraksha.db")

cursor = con.cursor()

cursor.execute("""
SELECT name
FROM sqlite_master
WHERE type='table';
""")

tables = cursor.fetchall()

print("Tables found:")
print(tables)

con.close()