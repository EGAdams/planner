#!/usr/bin/env python3
"""
Add "Personal" as a third top-level category to the nonprofit_finance database.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import mysql.connector
from app.config import settings


def main():
    print(f"Connecting to MySQL at {settings.host}:{settings.port} as user {settings.user}")

    # Connect to the database
    conn = mysql.connector.connect(
        host=settings.host,
        port=settings.port,
        user=settings.user,
        password=settings.password,
        database=settings.database,
        autocommit=True
    )
    cursor = conn.cursor()

    try:
        # Check if Personal category already exists
        cursor.execute("SELECT id FROM categories WHERE name='Personal' AND parent_id IS NULL")
        result = cursor.fetchone()

        if result:
            print(f"✅ Personal category already exists with ID: {result[0]}")
        else:
            # Insert Personal as a top-level category (id=3)
            cursor.execute("""
                INSERT INTO categories (id, parent_id, name, kind, is_active)
                VALUES (3, NULL, 'Personal', 'EXPENSE', 1)
            """)
            print("✅ Personal category added successfully with ID: 3")

        # Verify the three top-level categories
        cursor.execute("SELECT id, name FROM categories WHERE parent_id IS NULL ORDER BY id")
        categories = cursor.fetchall()
        print("\nTop-level categories:")
        for cat_id, name in categories:
            print(f"  {cat_id}: {name}")

    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    main()
