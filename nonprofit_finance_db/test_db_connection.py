#!/usr/bin/env python3
"""
Test database connection using the credentials from .env file
"""
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.db import query_all, query_one

def test_connection():
    """Test that we can connect to the database and query data"""
    print("Testing database connection...")

    try:
        # Test basic connection
        result = query_one("SELECT DATABASE() as db_name")
        print(f"✓ Connected to database: {result['db_name']}")

        # Test transactions table
        transactions = query_all("SELECT COUNT(*) as count FROM transactions", ())
        print(f"✓ Found {transactions[0]['count']} transactions in database")

        # Test categories table
        categories = query_all("SELECT COUNT(*) as count FROM categories WHERE is_active = 1", ())
        print(f"✓ Found {categories[0]['count']} active categories in database")

        # Test sample transaction
        sample = query_one("SELECT id, transaction_date, description, amount FROM transactions LIMIT 1", ())
        if sample:
            print(f"✓ Sample transaction: ID={sample['id']}, Date={sample['transaction_date']}, Description={sample['description']}, Amount={sample['amount']}")

        print("\n✅ All database tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
