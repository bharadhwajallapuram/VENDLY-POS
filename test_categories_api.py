#!/usr/bin/env python3
"""Test the categories API"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'server'))

from app.db.session import get_db
from app.db.models.product import Category

# Test directly against the database
def main():
    db = next(get_db())
    categories = db.query(Category).all()
    print(f"\n=== Categories in Database ({len(categories)}) ===")
    for cat in categories:
        print(f"  {cat.id}: {cat.name}")
        if hasattr(cat, 'products'):
            products = cat.products
            print(f"      -> {len(products)} products")
    db.close()

if __name__ == "__main__":
    main()
