import sqlite3
from datetime import datetime

conn = sqlite3.connect('server/app/vendly.db')
cursor = conn.cursor()

now = datetime.now().isoformat()

# Check how many electronics products exist
cursor.execute('SELECT COUNT(*) FROM products WHERE category_id = 5')
print(f'Current electronics products: {cursor.fetchone()[0]}')

# Add new electronics products with INSERT (not IGNORE) to see errors
new_products = [
    ('USB-C to USB-C Cable 2m', 'ELC-010', '8905234567900', 'Fast charging USB-C cable', 12.99, 5.00, 60, 15, 5, 18.0, 1, now),
    ('Lightning Cable 1m', 'ELC-011', '8905234567901', 'Apple MFi certified cable', 14.99, 6.00, 50, 12, 5, 18.0, 1, now),
    ('USB-A to Micro USB', 'ELC-012', '8905234567902', 'Standard micro USB cable', 7.99, 3.00, 80, 20, 5, 18.0, 1, now),
    ('Fast Charger 20W', 'ELC-013', '8905234567903', 'USB-C wall charger', 19.99, 8.00, 40, 10, 5, 18.0, 1, now),
    ('Dual USB Charger', 'ELC-014', '8905234567904', '2-port USB wall adapter', 14.99, 6.00, 45, 10, 5, 18.0, 1, now),
    ('Car Charger USB-C', 'ELC-015', '8905234567905', 'Fast car charger', 16.99, 7.00, 35, 8, 5, 18.0, 1, now),
    ('Wireless Charger Pad', 'ELC-016', '8905234567906', '15W wireless charging pad', 24.99, 10.00, 30, 8, 5, 18.0, 1, now),
    ('MagSafe Charger', 'ELC-017', '8905234567907', 'Magnetic wireless charger', 34.99, 15.00, 25, 5, 5, 18.0, 1, now),
    ('Wired Earphones', 'ELC-020', '8905234567910', '3.5mm jack earphones', 9.99, 4.00, 70, 20, 5, 18.0, 1, now),
    ('Bluetooth Speaker Mini', 'ELC-021', '8905234567911', 'Portable mini speaker', 29.99, 12.00, 25, 8, 5, 18.0, 1, now),
    ('Bluetooth Speaker Large', 'ELC-022', '8905234567912', 'Party speaker with bass', 79.99, 35.00, 15, 5, 5, 18.0, 1, now),
    ('Over-Ear Headphones', 'ELC-023', '8905234567913', 'Wireless over-ear headphones', 69.99, 30.00, 20, 5, 5, 18.0, 1, now),
    ('Noise Cancelling Earbuds', 'ELC-024', '8905234567914', 'ANC true wireless earbuds', 89.99, 40.00, 18, 5, 5, 18.0, 1, now),
    ('Gaming Headset', 'ELC-025', '8905234567915', 'USB gaming headset with mic', 49.99, 20.00, 22, 6, 5, 18.0, 1, now),
    ('Aux Cable 3.5mm', 'ELC-026', '8905234567916', 'Audio auxiliary cable 1.5m', 5.99, 2.00, 100, 25, 5, 18.0, 1, now),
    ('Bluetooth Audio Receiver', 'ELC-027', '8905234567917', 'Bluetooth to aux adapter', 14.99, 6.00, 30, 8, 5, 18.0, 1, now),
    ('Keyboard Wireless', 'ELC-030', '8905234567920', 'Compact wireless keyboard', 34.99, 15.00, 20, 5, 5, 18.0, 1, now),
    ('Keyboard Mechanical', 'ELC-031', '8905234567921', 'RGB mechanical keyboard', 79.99, 35.00, 12, 4, 5, 18.0, 1, now),
    ('Mouse Pad Large', 'ELC-032', '8905234567922', 'Extended gaming mouse pad', 14.99, 5.00, 40, 10, 5, 18.0, 1, now),
    ('Mouse Pad RGB', 'ELC-033', '8905234567923', 'LED gaming mouse pad', 24.99, 10.00, 25, 6, 5, 18.0, 1, now),
    ('USB Hub 4-Port', 'ELC-034', '8905234567924', 'USB 3.0 hub', 19.99, 8.00, 35, 10, 5, 18.0, 1, now),
    ('USB Hub 7-Port', 'ELC-035', '8905234567925', 'Powered USB hub', 34.99, 15.00, 20, 5, 5, 18.0, 1, now),
    ('Webcam 1080p', 'ELC-036', '8905234567926', 'HD webcam with microphone', 44.99, 20.00, 18, 5, 5, 18.0, 1, now),
    ('Webcam 4K', 'ELC-037', '8905234567927', 'Ultra HD webcam', 89.99, 40.00, 10, 3, 5, 18.0, 1, now),
    ('Phone Case Universal', 'ELC-040', '8905234567930', 'Clear protective case', 9.99, 3.00, 80, 20, 5, 18.0, 1, now),
    ('Screen Protector Glass', 'ELC-041', '8905234567931', 'Tempered glass protector', 7.99, 2.50, 100, 30, 5, 18.0, 1, now),
    ('Phone Stand Adjustable', 'ELC-042', '8905234567932', 'Desktop phone holder', 12.99, 5.00, 45, 12, 5, 18.0, 1, now),
    ('Car Phone Mount', 'ELC-043', '8905234567933', 'Magnetic car mount', 16.99, 7.00, 35, 10, 5, 18.0, 1, now),
    ('PopSocket Grip', 'ELC-044', '8905234567934', 'Phone grip and stand', 8.99, 3.00, 60, 15, 5, 18.0, 1, now),
    ('Selfie Ring Light', 'ELC-045', '8905234567935', 'Clip-on ring light', 14.99, 6.00, 30, 8, 5, 18.0, 1, now),
    ('USB Flash Drive 32GB', 'ELC-050', '8905234567940', 'USB 3.0 flash drive', 9.99, 4.00, 50, 15, 5, 18.0, 1, now),
    ('USB Flash Drive 64GB', 'ELC-051', '8905234567941', 'USB 3.0 flash drive', 14.99, 6.00, 45, 12, 5, 18.0, 1, now),
    ('USB Flash Drive 128GB', 'ELC-052', '8905234567942', 'USB 3.0 flash drive', 24.99, 10.00, 30, 10, 5, 18.0, 1, now),
    ('MicroSD Card 32GB', 'ELC-053', '8905234567943', 'Class 10 memory card', 12.99, 5.00, 40, 10, 5, 18.0, 1, now),
    ('MicroSD Card 64GB', 'ELC-054', '8905234567944', 'Class 10 memory card', 19.99, 8.00, 35, 10, 5, 18.0, 1, now),
    ('MicroSD Card 128GB', 'ELC-055', '8905234567945', 'Class 10 memory card', 29.99, 12.00, 25, 8, 5, 18.0, 1, now),
    ('External SSD 256GB', 'ELC-056', '8905234567946', 'Portable SSD drive', 49.99, 25.00, 15, 5, 5, 18.0, 1, now),
    ('External SSD 512GB', 'ELC-057', '8905234567947', 'Portable SSD drive', 79.99, 40.00, 12, 4, 5, 18.0, 1, now),
    ('Smart Plug WiFi', 'ELC-060', '8905234567950', 'WiFi smart outlet plug', 14.99, 6.00, 40, 12, 5, 18.0, 1, now),
    ('LED Light Strip 5m', 'ELC-061', '8905234567951', 'RGB LED strip lights', 24.99, 10.00, 25, 8, 5, 18.0, 1, now),
]

added = 0
for p in new_products:
    try:
        cursor.execute('''
            INSERT INTO products 
            (name, sku, barcode, description, price, cost, quantity, min_quantity, category_id, tax_rate, is_active, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', p)
        added += 1
    except sqlite3.IntegrityError as e:
        print(f'Skipped {p[0]}: {e}')

conn.commit()
print(f'\nAdded {added} new products')

cursor.execute('SELECT COUNT(*) FROM products WHERE category_id = 5')
print(f'Total electronics products: {cursor.fetchone()[0]}')
conn.close()
