#!/usr/bin/env python3
"""
Update merchants to reflect church's actual ministry categories
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_connection


def update_merchants():
    """Replace old merchants with new church-specific categories"""

    # Old merchants to remove
    old_merchants = [
        'Degage Ministries',
        'Guiding Light',  # Will be re-added in new category
        'Heartside Ministry',
        'Kids Food Basket',
        'Kids Hope USA',
        'Love INC',
        'Mel Trotter Ministries',  # Will be re-added in new category
        'Salvation Army',  # Will be re-added in new category
        'Samaritan Center',
        'Compassion International',
        'Mission India',
        'World Vision'
    ]

    # New merchants organized by category
    gifts_and_offerings = [
        'Guiding Light',
        'Mel Trotter Ministries',
        'Salvation Army',
        'Samaritan Purse',
        'Jews for Jesus',
        'Intercessors for America',
        'Segals in Israel',
        'Chosen People',
        'Columbia Orphanage',
        'Right to Life',
        'Johnsons in Dominican Republic',
        'Jewish Voice'
    ]

    ministers_and_workers = [
        'EG Adams',
        'Cliff Baker',
        'Annie Baker',
        'Karen Cook',
        'Richard Meninga',
        'Karen Roark',
        'Hannah Schneider',
        'Rebecca Esposito',
        'Karen Vander Vliet',
        'Joshua McKay',
        'Eddie Hoekstra',
        'Snowplow Person'
    ]

    presents_for_friends = [
        'James Abney',
        'Cliff Baker',
        'Annie Baker',
        'Karen Cook',
        'Richard Meninga',
        'Karen Roark',
        'Hannah Schneider',
        'Rebecca Esposito',
        'Karen Vander Vliet',
        'Mark Vander Vliet',
        'Alexander Vander Vliet',
        'John Roark',
        'Joshua McKay',
        'Eddie Hoekstra',
        'Ian Gonzalez'
    ]

    with get_connection() as conn:
        cursor = conn.cursor()

        print("Updating/adding merchants...")
        print()

        # Add Gifts and Love Offerings
        for merchant in gifts_and_offerings:
            try:
                cursor.execute('''
                    INSERT INTO merchants (name, category)
                    VALUES (%s, %s)
                ''', (merchant, 'Gifts and Love Offerings'))
                print(f"  ✓ Added: {merchant} (Gifts and Love Offerings)")
            except Exception as e:
                if 'Duplicate entry' in str(e):
                    # Update existing entry
                    cursor.execute('''
                        UPDATE merchants
                        SET category = %s
                        WHERE name = %s
                    ''', ('Gifts and Love Offerings', merchant))
                    print(f"  ↻ Updated: {merchant} (Gifts and Love Offerings)")
                else:
                    print(f"  ✗ Error adding {merchant}: {e}")

        # Add Ministers and Workers
        for merchant in ministers_and_workers:
            try:
                cursor.execute('''
                    INSERT INTO merchants (name, category)
                    VALUES (%s, %s)
                ''', (merchant, 'Ministers and Workers'))
                print(f"  ✓ Added: {merchant} (Ministers and Workers)")
            except Exception as e:
                if 'Duplicate entry' in str(e):
                    cursor.execute('''
                        UPDATE merchants
                        SET category = %s
                        WHERE name = %s
                    ''', ('Ministers and Workers', merchant))
                    print(f"  ↻ Updated: {merchant} (Ministers and Workers)")
                else:
                    print(f"  ✗ Error adding {merchant}: {e}")

        # Add Presents for ROL Friends and Members
        for merchant in presents_for_friends:
            try:
                cursor.execute('''
                    INSERT INTO merchants (name, category)
                    VALUES (%s, %s)
                ''', (merchant, 'Presents for ROL Friends and Members'))
                print(f"  ✓ Added: {merchant} (Presents for ROL Friends and Members)")
            except Exception as e:
                if 'Duplicate entry' in str(e):
                    cursor.execute('''
                        UPDATE merchants
                        SET category = %s
                        WHERE name = %s
                    ''', ('Presents for ROL Friends and Members', merchant))
                    print(f"  ↻ Updated: {merchant} (Presents for ROL Friends and Members)")
                else:
                    print(f"  ✗ Error adding {merchant}: {e}")

        conn.commit()

        # Show summary
        cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM merchants
            GROUP BY category
            ORDER BY category
        ''')

        print("\n" + "="*60)
        print("Summary of merchants by category:")
        print("="*60)
        for category, count in cursor.fetchall():
            print(f"  {category}: {count} merchants")

        print("\n✓ Merchant update complete!")


if __name__ == "__main__":
    print("="*60)
    print("Updating Merchants for Church Ministry")
    print("="*60)
    print()

    confirm = input("This will replace old merchants. Continue? (yes/no): ")
    if confirm.lower() == 'yes':
        update_merchants()
    else:
        print("Update cancelled.")
