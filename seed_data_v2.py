"""
Seed script to populate Vendly POS database with sample data (v2 - with correct schema)
"""
import sqlite3
from datetime import datetime, timedelta
import random

DB_PATH = 'server/app/vendly.db'

def seed_database():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    print("=" * 60)
    print("🌱 Seeding Vendly POS Database (v2)")
    print("=" * 60)
    
    # ============================================
    # 1. CATEGORIES (with created_at, is_active)
    # ============================================
    print("\n📁 Adding categories...")
    categories = [
        ('Beverages', 'Hot and cold drinks', None, 1, now),
        ('Snacks', 'Quick bites and chips', None, 1, now),
        ('Dairy', 'Milk, cheese, and dairy products', None, 1, now),
        ('Bakery', 'Fresh bread and pastries', None, 1, now),
        ('Electronics', 'Gadgets and accessories', None, 1, now),
        ('Groceries', 'Daily essentials', None, 1, now),
        ('Personal Care', 'Health and hygiene products', None, 1, now),
        ('Frozen Foods', 'Ice cream and frozen items', None, 1, now),
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO categories (name, description, parent_id, is_active, created_at) 
        VALUES (?, ?, ?, ?, ?)
    """, categories)
    print(f"   ✓ Added {len(categories)} categories")
    
    # ============================================
    # 2. PRODUCTS (with created_at)
    # ============================================
    print("\n📦 Adding products...")
    products = [
        # (name, sku, barcode, description, price, cost, quantity, min_quantity, category_id, tax_rate, is_active, created_at)
        ('Coca-Cola 500ml', 'BEV-001', '8901234567890', 'Refreshing cola drink', 2.50, 1.50, 100, 20, 1, 5.0, 1, now),
        ('Pepsi 500ml', 'BEV-002', '8901234567891', 'Cola beverage', 2.50, 1.50, 80, 20, 1, 5.0, 1, now),
        ('Orange Juice 1L', 'BEV-003', '8901234567892', 'Fresh orange juice', 4.99, 3.00, 50, 10, 1, 5.0, 1, now),
        ('Coffee Beans 500g', 'BEV-004', '8901234567893', 'Premium arabica beans', 12.99, 8.00, 30, 5, 1, 5.0, 1, now),
        ('Green Tea Pack', 'BEV-005', '8901234567894', 'Organic green tea bags', 6.99, 4.00, 40, 10, 1, 5.0, 1, now),
        
        ('Potato Chips Large', 'SNK-001', '8902234567890', 'Crispy salted chips', 3.99, 2.00, 60, 15, 2, 12.0, 1, now),
        ('Chocolate Bar', 'SNK-002', '8902234567891', 'Milk chocolate 100g', 2.99, 1.50, 100, 25, 2, 12.0, 1, now),
        ('Mixed Nuts 200g', 'SNK-003', '8902234567892', 'Assorted roasted nuts', 7.99, 5.00, 35, 10, 2, 12.0, 1, now),
        ('Cookies Pack', 'SNK-004', '8902234567893', 'Butter cookies 250g', 4.49, 2.50, 45, 10, 2, 12.0, 1, now),
        
        ('Whole Milk 1L', 'DRY-001', '8903234567890', 'Fresh whole milk', 3.49, 2.00, 40, 15, 3, 0.0, 1, now),
        ('Cheddar Cheese 200g', 'DRY-002', '8903234567891', 'Aged cheddar block', 5.99, 3.50, 25, 8, 3, 0.0, 1, now),
        ('Greek Yogurt', 'DRY-003', '8903234567892', 'Plain greek yogurt 500g', 4.99, 3.00, 30, 10, 3, 0.0, 1, now),
        ('Butter 250g', 'DRY-004', '8903234567893', 'Salted butter', 4.49, 2.80, 35, 10, 3, 0.0, 1, now),
        
        ('White Bread Loaf', 'BAK-001', '8904234567890', 'Fresh sliced bread', 2.99, 1.50, 25, 10, 4, 0.0, 1, now),
        ('Croissants 4-pack', 'BAK-002', '8904234567891', 'Butter croissants', 5.99, 3.50, 20, 8, 4, 0.0, 1, now),
        ('Bagels 6-pack', 'BAK-003', '8904234567892', 'Plain bagels', 4.49, 2.50, 18, 6, 4, 0.0, 1, now),
        
        ('USB Cable Type-C', 'ELC-001', '8905234567890', 'Fast charging cable 1m', 9.99, 4.00, 50, 10, 5, 18.0, 1, now),
        ('Wireless Mouse', 'ELC-002', '8905234567891', 'Ergonomic wireless mouse', 24.99, 12.00, 20, 5, 5, 18.0, 1, now),
        ('Power Bank 10000mAh', 'ELC-003', '8905234567892', 'Portable charger', 29.99, 15.00, 15, 5, 5, 18.0, 1, now),
        ('Earbuds Bluetooth', 'ELC-004', '8905234567893', 'Wireless earbuds', 39.99, 20.00, 25, 5, 5, 18.0, 1, now),
        
        ('Rice 5kg', 'GRC-001', '8906234567890', 'Premium basmati rice', 12.99, 8.00, 40, 10, 6, 0.0, 1, now),
        ('Pasta 500g', 'GRC-002', '8906234567891', 'Italian spaghetti', 2.49, 1.20, 60, 20, 6, 0.0, 1, now),
        ('Olive Oil 500ml', 'GRC-003', '8906234567892', 'Extra virgin olive oil', 8.99, 5.50, 30, 8, 6, 0.0, 1, now),
        ('Honey 350g', 'GRC-004', '8906234567893', 'Pure natural honey', 7.49, 4.50, 25, 8, 6, 0.0, 1, now),
        
        ('Shampoo 400ml', 'PRC-001', '8907234567890', 'Anti-dandruff shampoo', 6.99, 3.50, 35, 10, 7, 18.0, 1, now),
        ('Toothpaste 150g', 'PRC-002', '8907234567891', 'Whitening toothpaste', 3.99, 2.00, 50, 15, 7, 18.0, 1, now),
        ('Hand Soap 250ml', 'PRC-003', '8907234567892', 'Antibacterial hand wash', 2.99, 1.50, 40, 12, 7, 18.0, 1, now),
        
        ('Ice Cream 1L', 'FRZ-001', '8908234567890', 'Vanilla ice cream tub', 5.99, 3.00, 20, 8, 8, 12.0, 1, now),
        ('Frozen Pizza', 'FRZ-002', '8908234567891', 'Pepperoni pizza', 7.99, 4.00, 15, 5, 8, 12.0, 1, now),
        ('Frozen Vegetables 500g', 'FRZ-003', '8908234567892', 'Mixed vegetables', 3.99, 2.00, 25, 8, 8, 12.0, 1, now),
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO products 
        (name, sku, barcode, description, price, cost, quantity, min_quantity, category_id, tax_rate, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, products)
    print(f"   ✓ Added {len(products)} products")
    
    # ============================================
    # 3. CUSTOMERS (with created_at)
    # ============================================
    print("\n👥 Adding customers...")
    customers = [
        ('John Smith', 'john.smith@email.com', '+1-555-0101', '123 Main Street, City', 'Regular customer', 150, 1, now),
        ('Sarah Johnson', 'sarah.j@email.com', '+1-555-0102', '456 Oak Avenue, Town', 'VIP member', 500, 1, now),
        ('Michael Brown', 'michael.b@email.com', '+1-555-0103', '789 Pine Road, Village', '', 75, 1, now),
        ('Emily Davis', 'emily.d@email.com', '+1-555-0104', '321 Elm Street, City', 'Prefers organic', 200, 1, now),
        ('David Wilson', 'david.w@email.com', '+1-555-0105', '654 Maple Lane, Town', '', 100, 1, now),
        ('Jennifer Taylor', 'jen.t@email.com', '+1-555-0106', '987 Cedar Court, Village', 'Bulk buyer', 350, 1, now),
        ('Robert Martinez', 'rob.m@email.com', '+1-555-0107', '147 Birch Way, City', '', 50, 1, now),
        ('Lisa Anderson', 'lisa.a@email.com', '+1-555-0108', '258 Spruce Drive, Town', 'Staff discount', 425, 1, now),
        ('James Thomas', 'james.t@email.com', '+1-555-0109', '369 Willow Path, Village', '', 80, 1, now),
        ('Amanda Garcia', 'amanda.g@email.com', '+1-555-0110', '741 Ash Boulevard, City', 'Corporate account', 600, 1, now),
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO customers 
        (name, email, phone, address, notes, loyalty_points, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, customers)
    print(f"   ✓ Added {len(customers)} customers")
    
    # ============================================
    # 4. TAX RATES (with effective_from, created_at, updated_at)
    # ============================================
    print("\n💰 Adding tax rates...")
    tax_rates = [
        # (region, tax_type, name, rate, state_code, is_active, effective_from, description, created_at, updated_at)
        ('in', 'gst', 'CGST 9%', 9.0, None, 1, now, 'Central GST for India', now, now),
        ('in', 'gst', 'SGST 9%', 9.0, None, 1, now, 'State GST for India', now, now),
        ('in', 'gst', 'IGST 18%', 18.0, None, 1, now, 'Integrated GST', now, now),
        ('in', 'gst', 'GST 5%', 5.0, None, 1, now, 'Reduced GST rate', now, now),
        ('in', 'gst', 'GST 12%', 12.0, None, 1, now, 'Standard GST rate', now, now),
        ('us', 'sales_tax', 'California Sales Tax', 7.25, 'CA', 1, now, 'CA state sales tax', now, now),
        ('us', 'sales_tax', 'New York Sales Tax', 8.0, 'NY', 1, now, 'NY state sales tax', now, now),
        ('us', 'sales_tax', 'Texas Sales Tax', 6.25, 'TX', 1, now, 'TX state sales tax', now, now),
        ('uk', 'vat', 'Standard VAT', 20.0, None, 1, now, 'UK standard VAT', now, now),
        ('uk', 'vat', 'Reduced VAT', 5.0, None, 1, now, 'UK reduced VAT', now, now),
        ('au', 'gst', 'Australian GST', 10.0, None, 1, now, 'Australian GST', now, now),
        ('ca', 'hst', 'Ontario HST', 13.0, 'ON', 1, now, 'Ontario HST', now, now),
        ('eu', 'vat', 'EU Standard VAT', 21.0, None, 1, now, 'EU standard VAT', now, now),
    ]
    
    cursor.executemany("""
        INSERT OR IGNORE INTO tax_rates 
        (region, tax_type, name, rate, state_code, is_active, effective_from, description, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, tax_rates)
    print(f"   ✓ Added {len(tax_rates)} tax rates")
    
    # Commit changes
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
    
    print("\n📊 Final record counts:")
    for table in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"   {table}: {count}")
        except:
            pass
    
    conn.close()
    print("\n🎉 Done! Refresh DB Browser to see the new data.")

if __name__ == "__main__":
    seed_database()
