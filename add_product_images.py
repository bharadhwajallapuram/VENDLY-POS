"""
Update products with image URLs
"""
import sqlite3

DB_PATH = 'server/app/vendly.db'

# Product images using free stock photos (Unsplash) and placeholder images
PRODUCT_IMAGES = {
    # Beverages
    'BEV-001': 'https://images.unsplash.com/photo-1554866585-cd94860890b7?w=400',  # Coca-Cola
    'BEV-002': 'https://images.unsplash.com/photo-1629203851122-3726ecdf080e?w=400',  # Pepsi
    'BEV-003': 'https://images.unsplash.com/photo-1621506289937-a8e4df240d0b?w=400',  # Orange Juice
    'BEV-004': 'https://images.unsplash.com/photo-1559056199-641a0ac8b55e?w=400',  # Coffee Beans
    'BEV-005': 'https://images.unsplash.com/photo-1556679343-c7306c1976bc?w=400',  # Green Tea
    
    # Snacks
    'SNK-001': 'https://images.unsplash.com/photo-1566478989037-eec170784d0b?w=400',  # Potato Chips
    'SNK-002': 'https://images.unsplash.com/photo-1606312619070-d48b4c652a52?w=400',  # Chocolate Bar
    'SNK-003': 'https://images.unsplash.com/photo-1599599810769-bcde5a160d32?w=400',  # Mixed Nuts
    'SNK-004': 'https://images.unsplash.com/photo-1558961363-fa8fdf82db35?w=400',  # Cookies
    
    # Dairy
    'DRY-001': 'https://images.unsplash.com/photo-1563636619-e9143da7973b?w=400',  # Milk
    'DRY-002': 'https://images.unsplash.com/photo-1486297678162-eb2a19b0a32d?w=400',  # Cheese
    'DRY-003': 'https://images.unsplash.com/photo-1488477181946-6428a0291777?w=400',  # Yogurt
    'DRY-004': 'https://images.unsplash.com/photo-1589985270826-4b7bb135bc9d?w=400',  # Butter
    
    # Bakery
    'BAK-001': 'https://images.unsplash.com/photo-1509440159596-0249088772ff?w=400',  # Bread
    'BAK-002': 'https://images.unsplash.com/photo-1555507036-ab1f4038808a?w=400',  # Croissants
    'BAK-003': 'https://images.unsplash.com/photo-1585535889547-1578c8ab2e5f?w=400',  # Bagels
    
    # Electronics
    'ELC-001': 'https://images.unsplash.com/photo-1583394838336-acd977736f90?w=400',  # USB Cable
    'ELC-002': 'https://images.unsplash.com/photo-1527864550417-7fd91fc51a46?w=400',  # Mouse
    'ELC-003': 'https://images.unsplash.com/photo-1609091839311-d5365f9ff1c5?w=400',  # Power Bank
    'ELC-004': 'https://images.unsplash.com/photo-1590658268037-6bf12165a8df?w=400',  # Earbuds
    
    # Groceries
    'GRC-001': 'https://images.unsplash.com/photo-1586201375761-83865001e31c?w=400',  # Rice
    'GRC-002': 'https://images.unsplash.com/photo-1551462147-ff29053bfc14?w=400',  # Pasta
    'GRC-003': 'https://images.unsplash.com/photo-1474979266404-7eaacbcd87c5?w=400',  # Olive Oil
    'GRC-004': 'https://images.unsplash.com/photo-1587049352846-4a222e784d38?w=400',  # Honey
    
    # Personal Care
    'PRC-001': 'https://images.unsplash.com/photo-1556227702-d1e4e7b5c232?w=400',  # Shampoo
    'PRC-002': 'https://images.unsplash.com/photo-1559013332-aad3e4c83c0f?w=400',  # Toothpaste
    'PRC-003': 'https://images.unsplash.com/photo-1584305574647-0cc949a2bb9f?w=400',  # Hand Soap
    
    # Frozen Foods
    'FRZ-001': 'https://images.unsplash.com/photo-1497034825429-c343d7c6a68f?w=400',  # Ice Cream
    'FRZ-002': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ae38?w=400',  # Pizza
    'FRZ-003': 'https://images.unsplash.com/photo-1597362925123-77861d3fbac7?w=400',  # Frozen Vegetables
}

def update_product_images():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 60)
    print("🖼️  Updating Product Images")
    print("=" * 60)
    
    updated = 0
    for sku, image_url in PRODUCT_IMAGES.items():
        cursor.execute("""
            UPDATE products 
            SET image_url = ? 
            WHERE sku = ?
        """, (image_url, sku))
        
        if cursor.rowcount > 0:
            print(f"   ✓ {sku}: Image added")
            updated += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Updated {updated} products with images!")
    print("\nImages are from Unsplash (free to use).")
    print("Refresh DB Browser to see the updated image_url column.")

if __name__ == "__main__":
    update_product_images()
