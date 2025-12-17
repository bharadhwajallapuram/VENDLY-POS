"""
Seed script to populate Vendly POS database with sample data
"""
import sqlite3
import hashlib
import secrets
from datetime import datetime, timedelta
import random

DB_PATH = 'server/app/vendly.db'

def hash_password(password: str) -> str:
    """Simple password hash for demo purposes"""
    return hashlib.sha256(password.encode()).hexdigest()

def seed_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("🌱 Seeding Vendly POS Database")
    print("=" * 60)
    
    # ============================================
    # 1. CATEGORIES
    # ============================================
    print("\n📁 Adding categories...")
    categories = [
        ('Beverages', 'Hot and cold drinks'),
        ('Snacks', 'Quick bites and chips'),
        ('Dairy', 'Milk, cheese, and dairy products'),
        ('Bakery', 'Fresh bread and pastries'),
        ('Electronics', 'Gadgets and accessories'),
        ('Groceries', 'Daily essentials'),
        ('Personal Care', 'Health and hygiene products'),
        ('Frozen Foods', 'Ice cream and frozen items'),
    ]
    
    cursor.executemany(
        "INSERT OR IGNORE INTO categories (name, description) VALUES (?, ?)",
        categories
    )
    print(f"   ✓ Added {len(categories)} categories")
    
    # ============================================
    # 2. PRODUCTS
    # ============================================
    print("\n📦 Adding products...")
    products = [
        # (name, sku, barcode, description, price, cost, quantity, min_quantity, category_id, tax_rate, is_active)
        ('Coca-Cola 500ml', 'BEV-001', '8901234567890', 'Refreshing cola drink', 2.50, 1.50, 100, 20, 1, 5.0, 1),
        ('Pepsi 500ml', 'BEV-002', '8901234567891', 'Cola beverage', 2.50, 1.50, 80, 20, 1, 5.0, 1),
        ('Orange Juice 1L', 'BEV-003', '8901234567892', 'Fresh orange juice', 4.99, 3.00, 50, 10, 1, 5.0, 1),
        ('Coffee Beans 500g', 'BEV-004', '8901234567893', 'Premium arabica beans', 12.99, 8.00, 30, 5, 1, 5.0, 1),
        ('Green Tea Pack', 'BEV-005', '8901234567894', 'Organic green tea bags', 6.99, 4.00, 40, 10, 1, 5.0, 1),
        
        ('Potato Chips Large', 'SNK-001', '8902234567890', 'Crispy salted chips', 3.99, 2.00, 60, 15, 2, 12.0, 1),
        ('Chocolate Bar', 'SNK-002', '8902234567891', 'Milk chocolate 100g', 2.99, 1.50, 100, 25, 2, 12.0, 1),
        ('Mixed Nuts 200g', 'SNK-003', '8902234567892', 'Assorted roasted nuts', 7.99, 5.00, 35, 10, 2, 12.0, 1),
        ('Cookies Pack', 'SNK-004', '8902234567893', 'Butter cookies 250g', 4.49, 2.50, 45, 10, 2, 12.0, 1),
        
        ('Whole Milk 1L', 'DRY-001', '8903234567890', 'Fresh whole milk', 3.49, 2.00, 40, 15, 3, 0.0, 1),
        ('Cheddar Cheese 200g', 'DRY-002', '8903234567891', 'Aged cheddar block', 5.99, 3.50, 25, 8, 3, 0.0, 1),
        ('Greek Yogurt', 'DRY-003', '8903234567892', 'Plain greek yogurt 500g', 4.99, 3.00, 30, 10, 3, 0.0, 1),
        ('Butter 250g', 'DRY-004', '8903234567893', 'Salted butter', 4.49, 2.80, 35, 10, 3, 0.0, 1),
        
        ('White Bread Loaf', 'BAK-001', '8904234567890', 'Fresh sliced bread', 2.99, 1.50, 25, 10, 4, 0.0, 1),
        ('Croissants 4-pack', 'BAK-002', '8904234567891', 'Butter croissants', 5.99, 3.50, 20, 8, 4, 0.0, 1),
        ('Bagels 6-pack', 'BAK-003', '8904234567892', 'Plain bagels', 4.49, 2.50, 18, 6, 4, 0.0, 1),
        
        ('USB Cable Type-C', 'ELC-001', '8905234567890', 'Fast charging cable 1m', 9.99, 4.00, 50, 10, 5, 18.0, 1),
        ('Wireless Mouse', 'ELC-002', '8905234567891', 'Ergonomic wireless mouse', 24.99, 12.00, 20, 5, 5, 18.0, 1),
        ('Power Bank 10000mAh', 'ELC-003', '8905234567892', 'Portable charger', 29.99, 15.00, 15, 5, 5, 18.0, 1),
        ('Earbuds Bluetooth', 'ELC-004', '8905234567893', 'Wireless earbuds', 39.99, 20.00, 25, 5, 5, 18.0, 1),
        
        ('Rice 5kg', 'GRC-001', '8906234567890', 'Premium basmati rice', 12.99, 8.00, 40, 10, 6, 0.0, 1),
        ('Pasta 500g', 'GRC-002', '8906234567891', 'Italian spaghetti', 2.49, 1.20, 60, 20, 6, 0.0, 1),
        ('Olive Oil 500ml', 'GRC-003', '8906234567892', 'Extra virgin olive oil', 8.99, 5.50, 30, 8, 6, 0.0, 1),
        ('Honey 350g', 'GRC-004', '8906234567893', 'Pure natural honey', 7.49, 4.50, 25, 8, 6, 0.0, 1),
        
        ('Shampoo 400ml', 'PRC-001', '8907234567890', 'Anti-dandruff shampoo', 6.99, 3.50, 35, 10, 7, 18.0, 1),
        ('Toothpaste 150g', 'PRC-002', '8907234567891', 'Whitening toothpaste', 3.99, 2.00, 50, 15, 7, 18.0, 1),
        ('Hand Soap 250ml', 'PRC-003', '8907234567892', 'Antibacterial hand wash', 2.99, 1.50, 40, 12, 7, 18.0, 1),
        
        ('Ice Cream 1L', 'FRZ-001', '8908234567890', 'Vanilla ice cream tub', 5.99, 3.00, 20, 8, 8, 12.0, 1),
        ('Frozen Pizza', 'FRZ-002', '8908234567891', 'Pepperoni pizza', 7.99, 4.00, 15, 5, 8, 12.0, 1),
        ('Frozen Vegetables 500g', 'FRZ-003', '8908234567892', 'Mixed vegetables', 3.99, 2.00, 25, 8, 8, 12.0, 1),
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO products 
        (name, sku, barcode, description, price, cost, quantity, min_quantity, category_id, tax_rate, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, products)
    print(f"   ✓ Added {len(products)} products")
    
    # ============================================
    # 3. CUSTOMERS
    # ============================================
    print("\n👥 Adding customers...")
    customers = [
        ('John Smith', 'john.smith@email.com', '+1-555-0101', '123 Main Street, City', 'Regular customer', 150, 1),
        ('Sarah Johnson', 'sarah.j@email.com', '+1-555-0102', '456 Oak Avenue, Town', 'VIP member', 500, 1),
        ('Michael Brown', 'michael.b@email.com', '+1-555-0103', '789 Pine Road, Village', '', 75, 1),
        ('Emily Davis', 'emily.d@email.com', '+1-555-0104', '321 Elm Street, City', 'Prefers organic', 200, 1),
        ('David Wilson', 'david.w@email.com', '+1-555-0105', '654 Maple Lane, Town', '', 100, 1),
        ('Jennifer Taylor', 'jen.t@email.com', '+1-555-0106', '987 Cedar Court, Village', 'Bulk buyer', 350, 1),
        ('Robert Martinez', 'rob.m@email.com', '+1-555-0107', '147 Birch Way, City', '', 50, 1),
        ('Lisa Anderson', 'lisa.a@email.com', '+1-555-0108', '258 Spruce Drive, Town', 'Staff discount', 425, 1),
        ('James Thomas', 'james.t@email.com', '+1-555-0109', '369 Willow Path, Village', '', 80, 1),
        ('Amanda Garcia', 'amanda.g@email.com', '+1-555-0110', '741 Ash Boulevard, City', 'Corporate account', 600, 1),
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO customers 
        (name, email, phone, address, notes, loyalty_points, is_active)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, customers)
    print(f"   ✓ Added {len(customers)} customers")
    
    # ============================================
    # 4. TAX RATES
    # ============================================
    print("\n💰 Adding tax rates...")
    tax_rates = [
        # (region, tax_type, name, rate, state_code, is_active)
        ('in', 'gst', 'CGST 9%', 9.0, None, 1),
        ('in', 'gst', 'SGST 9%', 9.0, None, 1),
        ('in', 'gst', 'IGST 18%', 18.0, None, 1),
        ('in', 'gst', 'GST 5%', 5.0, None, 1),
        ('in', 'gst', 'GST 12%', 12.0, None, 1),
        ('us', 'sales_tax', 'California Sales Tax', 7.25, 'CA', 1),
        ('us', 'sales_tax', 'New York Sales Tax', 8.0, 'NY', 1),
        ('us', 'sales_tax', 'Texas Sales Tax', 6.25, 'TX', 1),
        ('uk', 'vat', 'Standard VAT', 20.0, None, 1),
        ('uk', 'vat', 'Reduced VAT', 5.0, None, 1),
        ('au', 'gst', 'Australian GST', 10.0, None, 1),
        ('ca', 'hst', 'Ontario HST', 13.0, 'ON', 1),
        ('eu', 'vat', 'EU Standard VAT', 21.0, None, 1),
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO tax_rates 
        (region, tax_type, name, rate, state_code, is_active)
        VALUES (?, ?, ?, ?, ?, ?)
    """, tax_rates)
    print(f"   ✓ Added {len(tax_rates)} tax rates")
    
    # ============================================
    # 5. SAMPLE SALES (Last 30 days)
    # ============================================
    print("\n🛒 Adding sample sales...")
    
    # Get product IDs
    cursor.execute("SELECT id, price, tax_rate FROM products")
    products_db = cursor.fetchall()
    
    if products_db:
        sales_count = 0
        for days_ago in range(30, 0, -1):
            # 2-5 sales per day
            num_sales = random.randint(2, 5)
            for _ in range(num_sales):
                sale_date = datetime.now() - timedelta(days=days_ago, hours=random.randint(8, 20))
                
                # Random 1-4 items per sale
                num_items = random.randint(1, 4)
                selected_products = random.sample(products_db, min(num_items, len(products_db)))
                
                subtotal = 0
                tax_total = 0
                items_data = []
                
                for prod_id, price, tax_rate in selected_products:
                    qty = random.randint(1, 3)
                    item_subtotal = price * qty
                    item_tax = item_subtotal * (tax_rate / 100)
                    subtotal += item_subtotal
                    tax_total += item_tax
                    items_data.append((prod_id, qty, price, item_tax, item_subtotal))
                
                total = subtotal + tax_total
                payment_method = random.choice(['cash', 'card', 'upi'])
                
                # Insert sale
                cursor.execute("""
                    INSERT INTO sales (user_id, customer_id, subtotal, tax, discount, total, 
                                      payment_method, status, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (1, random.choice([None, 1, 2, 3, 4, 5]), 
                      round(subtotal, 2), round(tax_total, 2), 0, round(total, 2),
                      payment_method, 'completed', sale_date.isoformat()))
                
                sale_id = cursor.lastrowid
                
                # Insert sale items
                for prod_id, qty, price, item_tax, item_subtotal in items_data:
                    cursor.execute("""
                        INSERT INTO sale_items (sale_id, product_id, quantity, unit_price, discount, tax, subtotal)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (sale_id, prod_id, qty, price, 0, round(item_tax, 2), round(item_subtotal, 2)))
                
                sales_count += 1
        
        print(f"   ✓ Added {sales_count} sales with items")
    
    # ============================================
    # 6. COUPONS
    # ============================================
    print("\n🎟️ Adding coupons...")
    now = datetime.now().isoformat()
    coupons = [
        # (code, type, value, max_off, min_order, active, expires_at, usage_count, stackable, created_at)
        ('WELCOME10', 'percentage', 10.0, 50.0, 0, 1, (datetime.now() + timedelta(days=90)).isoformat(), 0, 0, now),
        ('FLAT50', 'fixed', 50.0, 50.0, 200.0, 1, (datetime.now() + timedelta(days=60)).isoformat(), 0, 0, now),
        ('SUMMER20', 'percentage', 20.0, 100.0, 50.0, 1, (datetime.now() + timedelta(days=30)).isoformat(), 0, 0, now),
        ('VIP25', 'percentage', 25.0, 150.0, 100.0, 1, (datetime.now() + timedelta(days=120)).isoformat(), 0, 1, now),
        ('FREESHIP', 'fixed', 15.0, 15.0, 0, 1, (datetime.now() + timedelta(days=45)).isoformat(), 0, 1, now),
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO coupons 
        (code, type, value, max_off, min_order, active, expires_at, usage_count, stackable, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, coupons)
    print(f"   ✓ Added {len(coupons)} coupons")
    
    # ============================================
    # 7. SETTINGS
    # ============================================
    print("\n⚙️ Adding settings...")
    settings = [
        ('store_name', 'Vendly Store', 'Store display name'),
        ('store_address', '123 Commerce Street, Business City', 'Store address'),
        ('store_phone', '+1-555-VENDLY', 'Store contact number'),
        ('store_email', 'contact@vendly.com', 'Store email'),
        ('currency', 'USD', 'Default currency'),
        ('tax_enabled', 'true', 'Enable tax calculation'),
        ('receipt_footer', 'Thank you for shopping with us!', 'Receipt footer message'),
        ('low_stock_threshold', '10', 'Low stock alert threshold'),
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO settings (key, value, description)
        VALUES (?, ?, ?)
    """, settings)
    print(f"   ✓ Added {len(settings)} settings")
    
    # ============================================
    # 8. INVENTORY MOVEMENTS
    # ============================================
    print("\n📊 Adding inventory movements...")
    
    cursor.execute("SELECT id FROM products LIMIT 10")
    prod_ids = [row[0] for row in cursor.fetchall()]
    
    movements = []
    for prod_id in prod_ids:
        # Initial stock (product_id, quantity_change, movement_type, reference_id, notes, user_id, created_at)
        movements.append((prod_id, random.randint(50, 100), 'purchase', None, f'Initial stock for product {prod_id}', 1,
                         (datetime.now() - timedelta(days=35)).isoformat()))
        # Restock
        movements.append((prod_id, random.randint(20, 50), 'purchase', None, 'Restocking', 1,
                         (datetime.now() - timedelta(days=15)).isoformat()))
    
    cursor.executemany("""
        INSERT INTO inventory_movements (product_id, quantity_change, movement_type, reference_id, notes, user_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, movements)
    print(f"   ✓ Added {len(movements)} inventory movements")
    
    # Commit all changes
    conn.commit()
    
    # ============================================
    # SUMMARY
    # ============================================
    print("\n" + "=" * 60)
    print("✅ Database seeding complete!")
    print("=" * 60)
    
    # Show counts
    tables = ['categories', 'products', 'customers', 'sales', 'sale_items', 
              'coupons', 'tax_rates', 'settings', 'inventory_movements']
    
    print("\n📊 Record counts:")
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f"   {table}: {count}")
    
    conn.close()
    print("\n🎉 Done! Refresh DB Browser to see the new data.")

if __name__ == "__main__":
    seed_database()
