import sqlite3

conn = sqlite3.connect('server/app/vendly.db')
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

print("=" * 50)
print("Tables in vendly.db:")
print("=" * 50)
for t in tables:
    print(f"  - {t[0]}")

# Count records in key tables
print("\n" + "=" * 50)
print("Record counts:")
print("=" * 50)
for table in ['users', 'products', 'sales', 'customers']:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"  {table}: {count} records")
    except:
        pass

conn.close()
