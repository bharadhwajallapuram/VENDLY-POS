from app.db.models import Product
from app.db.session import SessionLocal, engine

products = [
    {
        "name": "Apple",
        "sku": "APL001",
        "price": 1.0,
        "quantity": 100,
        "min_quantity": 10,
        "tax_rate": 0.05,
        "is_active": True,
    },
    {
        "name": "Banana",
        "sku": "BAN001",
        "price": 0.5,
        "quantity": 150,
        "min_quantity": 15,
        "tax_rate": 0.05,
        "is_active": True,
    },
    {
        "name": "Orange Juice",
        "sku": "OJ001",
        "price": 2.5,
        "quantity": 50,
        "min_quantity": 5,
        "tax_rate": 0.12,
        "is_active": True,
    },
]

with SessionLocal() as session:
    for prod in products:
        if not session.query(Product).filter_by(sku=prod["sku"]).first():
            session.add(Product(**prod))
    session.commit()
    print("Demo products inserted.")
