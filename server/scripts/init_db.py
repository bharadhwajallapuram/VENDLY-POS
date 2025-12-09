#!/usr/bin/env python
"""
Vendly POS - Database Initialization Script
============================================
This script automatically creates the database and all tables.

Usage:
    python scripts/init_db.py

Options:
    --drop    Drop existing tables before creating (CAUTION: destroys data!)
"""

import os
import sys

# Add the server directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import OperationalError, ProgrammingError

from app.core.config import settings
from app.db.models import Base


def get_database_name(url: str) -> str:
    """Extract database name from URL"""
    if "sqlite" in url:
        return url.split("/")[-1]
    # For MySQL/PostgreSQL: mysql+pymysql://user:pass@host:port/dbname
    return url.split("/")[-1].split("?")[0]


def get_base_url(url: str) -> str:
    """Get database URL without the database name (for MySQL/PostgreSQL)"""
    if "sqlite" in url:
        return url
    parts = url.rsplit("/", 1)
    return parts[0]


def create_mysql_database(url: str, db_name: str):
    """Create MySQL database if it doesn't exist"""
    base_url = get_base_url(url)
    engine = create_engine(base_url)

    with engine.connect() as conn:
        conn.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        )
        conn.commit()
        print(f"[OK] Database '{db_name}' created or already exists")

    engine.dispose()


def create_tables(drop_existing: bool = False):
    """Create all database tables"""
    db_url = settings.DATABASE_URL
    db_name = get_database_name(db_url)

    print(f"\n{'='*50}")
    print("Vendly POS - Database Initialization")
    print(f"{'='*50}\n")
    print(f"Database URL: {db_url.split('@')[-1] if '@' in db_url else db_url}")
    print(f"Database Name: {db_name}")
    print()

    # For MySQL, create the database first
    if "mysql" in db_url:
        try:
            create_mysql_database(db_url, db_name)
        except Exception as e:
            print(f"[ERROR] Error creating database: {e}")
            print("\nMake sure MySQL is running and credentials are correct.")
            sys.exit(1)

    # Create engine for the actual database
    engine = create_engine(db_url, echo=False)

    try:
        # Test connection
        with engine.connect() as conn:
            if "mysql" in db_url:
                result = conn.execute(text("SELECT VERSION()"))
                version = result.scalar()
                print(f"[OK] Connected to MySQL {version}")
            elif "sqlite" in db_url:
                print(f"[OK] Connected to SQLite")
            elif "postgresql" in db_url:
                result = conn.execute(text("SELECT version()"))
                version = result.scalar()
                print(f"[OK] Connected to {version.split(',')[0]}")
    except OperationalError as e:
        print(f"[ERROR] Connection failed: {e}")
        sys.exit(1)

    # Drop tables if requested
    if drop_existing:
        print("\n[WARNING] Dropping existing tables...")
        Base.metadata.drop_all(bind=engine)
        print("[OK] Tables dropped")

    # Create tables
    print("\n📦 Creating tables...")
    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] Tables created successfully!")
    except Exception as e:
        print(f"[ERROR] Error creating tables: {e}")
        sys.exit(1)

    # List created tables
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"\n📋 Tables in database ({len(tables)}):")
    for table in sorted(tables):
        print(f"   - {table}")

    engine.dispose()
    print(f"\n{'='*50}")
    print("[OK] Database initialization complete!")
    print(f"{'='*50}\n")


def create_admin_user():
    """Create a default admin user"""
    from sqlalchemy.orm import Session

    from app.core.security import hash_password
    from app.db.models import User

    engine = create_engine(settings.DATABASE_URL)

    with Session(engine) as session:
        # Check if admin exists
        existing = session.query(User).filter(User.email == "admin@vendly.com").first()
        if existing:
            print("[INFO] Admin user already exists")
            return

        # Create admin user
        admin = User(
            email="admin@vendly.com",
            password_hash=hash_password("admin123"),
            full_name="System Admin",
            is_active=True,
            role="admin",
        )
        session.add(admin)
        session.commit()
        print("[OK] Admin user created: admin@vendly.com / admin123")

    engine.dispose()


if __name__ == "__main__":
    drop_flag = "--drop" in sys.argv

    if drop_flag:
        confirm = input("⚠️  This will DELETE all data. Type 'yes' to confirm: ")
        if confirm.lower() != "yes":
            print("Aborted.")
            sys.exit(0)

    create_tables(drop_existing=drop_flag)

    # Ask to create admin user
    create_admin = input("\nCreate default admin user? (y/n): ")
    if create_admin.lower() == "y":
        create_admin_user()
