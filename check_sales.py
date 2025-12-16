import sqlite3

conn = sqlite3.connect(r'c:\Users\bhara\Vendly-fastapi-Js\server\app\vendly.db')
cursor = conn.cursor()

# Check all sales
print("=== All Sales ===")
cursor.execute("SELECT id, status, total, created_at FROM sales ORDER BY created_at DESC")
rows = cursor.fetchall()
for r in rows:
    print(f'ID: {r[0]}, Status: {r[1]}, Total: {r[2]}, Date: {r[3]}')

print("\n=== Sales filtered by date (2025-12-09 to 2025-12-16) ===")
cursor.execute("""
    SELECT id, status, total, created_at 
    FROM sales 
    WHERE status = 'completed' 
    AND created_at >= '2025-12-09' 
    AND created_at <= '2025-12-16'
""")
rows = cursor.fetchall()
for r in rows:
    print(f'ID: {r[0]}, Status: {r[1]}, Total: {r[2]}, Date: {r[3]}')

print("\n=== Sales filtered with end date + time ===")
cursor.execute("""
    SELECT id, status, total, created_at 
    FROM sales 
    WHERE status = 'completed' 
    AND created_at >= '2025-12-09' 
    AND created_at <= '2025-12-16 23:59:59'
""")
rows = cursor.fetchall()
for r in rows:
    print(f'ID: {r[0]}, Status: {r[1]}, Total: {r[2]}, Date: {r[3]}')

conn.close()
