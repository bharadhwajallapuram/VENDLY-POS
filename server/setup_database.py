#!/usr/bin/env python3
# ===========================================
# Vendly POS - Migration & Setup Helper
# Initialize demand forecasting tables
# ===========================================

"""
Helper script to set up demand forecasting tables.
Useful for development and testing environments.
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.models import Base
from app.db.session import engine


def create_tables():
    """Create all database tables"""
    print("\n🗄️  Creating database tables...")

    try:
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        return False


def drop_tables():
    """Drop all database tables (careful!)"""
    print("\n⚠️  WARNING: This will drop ALL tables!")
    confirm = input("Are you sure? Type 'yes' to confirm: ")

    if confirm.lower() != "yes":
        print("❌ Cancelled")
        return False

    try:
        Base.metadata.drop_all(bind=engine)
        print("✅ All tables dropped successfully!")
        return True
    except Exception as e:
        print(f"❌ Error dropping tables: {e}")
        return False


def list_tables():
    """List all database tables"""
    print("\n📋 Database Tables:")
    print("-" * 50)

    try:
        inspector = __import__("sqlalchemy").inspect(engine)
        tables = inspector.get_table_names()

        if not tables:
            print("  No tables found")
            return

        for table in sorted(tables):
            columns = inspector.get_columns(table)
            col_count = len(columns)
            print(f"  ✓ {table:<30} ({col_count} columns)")

            for col in columns[:3]:  # Show first 3 columns
                nullable = "null" if col["nullable"] else "not null"
                print(f"    - {col['name']:<25} {col['type']} {nullable}")

            if col_count > 3:
                print(f"    ... and {col_count - 3} more columns")
            print()

        print(f"Total tables: {len(tables)}")
    except Exception as e:
        print(f"❌ Error listing tables: {e}")


def verify_forecast_tables():
    """Verify demand forecasting tables exist"""
    print("\n✅ Verifying Demand Forecasting Tables...")
    print("-" * 50)

    required_tables = [
        "demand_history",
        "demand_forecasts",
        "forecast_details",
        "forecast_metrics",
    ]

    try:
        inspector = __import__("sqlalchemy").inspect(engine)
        existing_tables = inspector.get_table_names()

        all_exist = True
        for table in required_tables:
            exists = table in existing_tables
            status = "✓" if exists else "✗"
            print(f"  {status} {table}")
            if not exists:
                all_exist = False

        print()
        if all_exist:
            print("✅ All required tables exist!")
            return True
        else:
            print("❌ Some tables are missing. Run: python setup_database.py")
            return False
    except Exception as e:
        print(f"❌ Error verifying tables: {e}")
        return False


def show_usage():
    """Show usage information"""
    print(
        """
╔════════════════════════════════════════════════════════════════╗
║     Vendly POS - Database Setup Helper                        ║
║     Demand Forecasting Module                                  ║
╚════════════════════════════════════════════════════════════════╝

USAGE:
    python setup_database.py [command]

COMMANDS:
    create      Create all database tables
    drop        Drop all database tables (WARNING: destructive!)
    list        List all existing tables
    verify      Verify forecasting tables exist
    help        Show this help message

EXAMPLES:
    python setup_database.py create    # Create tables
    python setup_database.py verify    # Check if tables exist
    python setup_database.py list      # Show all tables

QUICK START:
    1. Create tables:
       python setup_database.py create
    
    2. Verify creation:
       python setup_database.py verify
    
    3. Run examples:
       python demand_forecast_examples.py

"""
    )


def main():
    """Main entry point"""
    command = sys.argv[1].lower() if len(sys.argv) > 1 else "help"

    if command == "create":
        success = create_tables()
        if success:
            print("\n" + "=" * 50)
            print("Next steps:")
            print("  1. Run examples: python demand_forecast_examples.py")
            print("  2. Check docs: ai_ml/DEMAND_FORECASTING.md")
            print("=" * 50 + "\n")
        sys.exit(0 if success else 1)

    elif command == "drop":
        success = drop_tables()
        sys.exit(0 if success else 1)

    elif command == "list":
        list_tables()
        sys.exit(0)

    elif command == "verify":
        success = verify_forecast_tables()
        sys.exit(0 if success else 1)

    elif command == "help":
        show_usage()
        sys.exit(0)

    else:
        print(f"Unknown command: {command}")
        show_usage()
        sys.exit(1)


if __name__ == "__main__":
    main()
