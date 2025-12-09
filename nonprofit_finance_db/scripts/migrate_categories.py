#!/usr/bin/env python3
"""
Migration script to reorganize expense categories structure
This will:
1. Clear all category_id references from transactions (set to NULL)
2. Delete all existing categories
3. Insert new category structure based on Church/Housing organization
"""
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import execute, query_all

# New category structure
CATEGORIES = [
    {"id": 1, "name": "Church", "parent_id": None},
    {"id": 2, "name": "Housing", "parent_id": None},

    # ---------- CHURCH ----------
    {"id": 100, "name": "Facility Payment", "parent_id": 1},

    {"id": 110, "name": "Facility Upkeep", "parent_id": 1},
    {"id": 111, "name": "Trash", "parent_id": 110},
    {"id": 112, "name": "Furnishings", "parent_id": 110},
    {"id": 113, "name": "Tools", "parent_id": 110},
    {"id": 114, "name": "Cleaning", "parent_id": 110},
    {"id": 115, "name": "Other", "parent_id": 110},

    {"id": 120, "name": "Utilities", "parent_id": 1},
    {"id": 121, "name": "Church Gas Bill", "parent_id": 120},
    {"id": 122, "name": "Church Water Bill", "parent_id": 120},
    {"id": 123, "name": "Church Electric Bill", "parent_id": 120},
    {"id": 124, "name": "Church Phone/Internet Bill", "parent_id": 120},
    {"id": 125, "name": "Other", "parent_id": 120},

    {"id": 130, "name": "Food & Supplies", "parent_id": 1},
    {"id": 131, "name": "Family Fare", "parent_id": 130},
    {"id": 132, "name": "Meijer", "parent_id": 130},
    {"id": 133, "name": "Restaurants (members/guests)", "parent_id": 130},
    {"id": 135, "name": "Gordon Food", "parent_id": 130},
    {"id": 134, "name": "Other", "parent_id": 130},

    {"id": 140, "name": "Office", "parent_id": 1},
    {"id": 141, "name": "Supplies", "parent_id": 140},
    {"id": 142, "name": "Apple", "parent_id": 140},
    {"id": 143, "name": "Amazon", "parent_id": 140},
    {"id": 144, "name": "Postage", "parent_id": 140},
    {"id": 145, "name": "Furnishings", "parent_id": 140},
    {"id": 146, "name": "Other", "parent_id": 140},

    {"id": 150, "name": "Education / Music / TV", "parent_id": 1},
    {"id": 151, "name": "CDs", "parent_id": 150},
    {"id": 152, "name": "DVDs", "parent_id": 150},
    {"id": 153, "name": "Books", "parent_id": 150},
    {"id": 154, "name": "Amazon", "parent_id": 150},
    {"id": 155, "name": "Other", "parent_id": 150},

    {"id": 160, "name": "Travel & Transportation", "parent_id": 1},
    {"id": 161, "name": "Fuel", "parent_id": 160},
    {"id": 162, "name": "RJ gas", "parent_id": 161},
    {"id": 163, "name": "RM gas", "parent_id": 161},
    {"id": 164, "name": "Vehicle Maintenance", "parent_id": 160},
    {"id": 165, "name": "RJ wash/oil", "parent_id": 164},
    {"id": 166, "name": "RM wash/oil", "parent_id": 164},
    {"id": 167, "name": "Car repair (RJ)", "parent_id": 164},
    {"id": 168, "name": "Car repair (RM)", "parent_id": 164},
    {"id": 169, "name": "Vehicle Ownership", "parent_id": 160},
    {"id": 170, "name": "Car payment (general)", "parent_id": 169},
    {"id": 171, "name": "RJ Car Payment", "parent_id": 169},
    {"id": 172, "name": "RM Car Payment", "parent_id": 169},
    {"id": 173, "name": "License Tags", "parent_id": 169},
    {"id": 174, "name": "RJ", "parent_id": 173},
    {"id": 175, "name": "RM", "parent_id": 173},
    {"id": 176, "name": "Other", "parent_id": 173},
    {"id": 177, "name": "Trips", "parent_id": 160},
    {"id": 178, "name": "Airfare", "parent_id": 177},
    {"id": 179, "name": "Tolls", "parent_id": 177},
    {"id": 180, "name": "AAA", "parent_id": 177},
    {"id": 181, "name": "Hotels", "parent_id": 177},
    {"id": 182, "name": "Ministry-related travel", "parent_id": 177},
    {"id": 183, "name": "Other", "parent_id": 160},

    {"id": 190, "name": "Gifts & Love Offerings", "parent_id": 1},
    {"id": 191, "name": "EG Adams (work for River of Life)", "parent_id": 190},
    {"id": 192, "name": "Individuals", "parent_id": 190},
    {"id": 193, "name": "C Baker", "parent_id": 192},
    {"id": 194, "name": "A Baker", "parent_id": 192},
    {"id": 195, "name": "K Cook", "parent_id": 192},
    {"id": 196, "name": "R Menninga", "parent_id": 192},
    {"id": 197, "name": "J Menninga", "parent_id": 192},
    {"id": 198, "name": "K Roark", "parent_id": 192},
    {"id": 199, "name": "H Schneider", "parent_id": 192},
    {"id": 200, "name": "R Exposito", "parent_id": 192},
    {"id": 201, "name": "K Vander Vliet", "parent_id": 192},
    {"id": 202, "name": "J McKay", "parent_id": 192},
    {"id": 203, "name": "Sound (R Slawson)", "parent_id": 192},
    {"id": 204, "name": "Guest Speakers", "parent_id": 192},
    {"id": 205, "name": "Special occasions (name/occasion)", "parent_id": 192},
    {"id": 210, "name": "Ministries & Organizations", "parent_id": 190},
    {"id": 211, "name": "Chosen People", "parent_id": 210},
    {"id": 212, "name": "Columbia Orphanage", "parent_id": 210},
    {"id": 213, "name": "Segals in Israel", "parent_id": 210},
    {"id": 214, "name": "Intercessors for America", "parent_id": 210},
    {"id": 215, "name": "Samaritans Purse", "parent_id": 210},
    {"id": 216, "name": "Mel Trotter", "parent_id": 210},
    {"id": 217, "name": "Guiding Light", "parent_id": 210},
    {"id": 218, "name": "Right to Life", "parent_id": 210},
    {"id": 219, "name": "Johnsons in Dominican Republic", "parent_id": 210},
    {"id": 220, "name": "Jews for Jesus", "parent_id": 210},
    {"id": 221, "name": "Jewish Voice", "parent_id": 210},
    {"id": 222, "name": "Salvation Army", "parent_id": 210},
    {"id": 223, "name": "Other", "parent_id": 210},

    {"id": 230, "name": "Insurance", "parent_id": 1},
    {"id": 231, "name": "Building", "parent_id": 230},
    {"id": 232, "name": "Boiler", "parent_id": 230},
    {"id": 233, "name": "Vehicles", "parent_id": 230},

    {"id": 240, "name": "Staff & Benefits", "parent_id": 1},
    {"id": 241, "name": "Senior Pastors", "parent_id": 240},
    {"id": 242, "name": "RJ — Priority Health (medical expenses)", "parent_id": 241},
    {"id": 243, "name": "RM — Priority Health (medical expenses)", "parent_id": 241},

    {"id": 250, "name": "Misc.", "parent_id": 1},

    # ---------- HOUSING ----------
    {"id": 300, "name": "Housing Payment", "parent_id": 2},
    {"id": 301, "name": "House Payment", "parent_id": 300},

    {"id": 310, "name": "Utilities", "parent_id": 2},
    {"id": 311, "name": "Housing Gas Bill", "parent_id": 310},
    {"id": 312, "name": "Housing Water Bill", "parent_id": 310},
    {"id": 313, "name": "Housing Trash Bill", "parent_id": 310},
    {"id": 314, "name": "Housing Electric Bill", "parent_id": 310},

    {"id": 320, "name": "Taxes & Insurance", "parent_id": 2},
    {"id": 321, "name": "House Taxes", "parent_id": 320},
    {"id": 322, "name": "House Insurance", "parent_id": 320},

    {"id": 330, "name": "Services", "parent_id": 2},
    {"id": 331, "name": "Service Professor", "parent_id": 330},

    {"id": 340, "name": "Upkeep", "parent_id": 2},
    {"id": 341, "name": "Décor / Furnishings", "parent_id": 340},
    {"id": 342, "name": "Tools", "parent_id": 340},
    {"id": 343, "name": "Repair", "parent_id": 340},
    {"id": 344, "name": "Outdoor & Lawn Care", "parent_id": 340},
    {"id": 345, "name": "Other", "parent_id": 340},

    {"id": 350, "name": "Misc.", "parent_id": 2},
]


def main():
    import mysql.connector
    from app.config import settings

    print("🔄 Starting category migration...")

    # Use direct MySQL connection for better control
    cnx = mysql.connector.connect(
        host=settings.host,
        port=settings.port,
        user=settings.user,
        password=settings.password,
        database='nonprofit_finance',
        autocommit=False  # Use transactions
    )
    cursor = cnx.cursor()

    try:
        # Step 1: Clear all category references from transactions
        print("\n1️⃣ Clearing category references from transactions...")
        cursor.execute("UPDATE transactions SET category_id = NULL")
        cnx.commit()
        print("   ✅ All transaction category references cleared")

        # Step 2: Drop unique constraint on (name, kind) if it exists
        print("\n2️⃣ Checking unique constraint on category names...")
        cursor.execute("""
            SELECT COUNT(*)
            FROM information_schema.statistics
            WHERE table_schema = 'nonprofit_finance'
            AND table_name = 'categories'
            AND index_name = 'uq_categories_name_kind'
        """)
        constraint_exists = cursor.fetchone()[0] > 0

        if constraint_exists:
            cursor.execute("ALTER TABLE categories DROP INDEX uq_categories_name_kind")
            cnx.commit()
            print("   ✅ Unique constraint removed (allowing hierarchical duplicates)")
        else:
            print("   ℹ️  Unique constraint already removed")

        # Step 3: Delete all existing categories (disable FK checks)
        print("\n3️⃣ Removing old categories...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("DELETE FROM categories")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        cnx.commit()
        print("   ✅ Old categories deleted")

        # Step 4: Insert new categories with explicit IDs
        print("\n4️⃣ Inserting new category structure...")

        for cat in CATEGORIES:
            cursor.execute(
                """INSERT INTO categories (id, name, kind, parent_id, is_active)
                   VALUES (%s, %s, 'EXPENSE', %s, 1)""",
                (cat['id'], cat['name'], cat['parent_id'])
            )

        cnx.commit()
        print(f"   ✅ Inserted {len(CATEGORIES)} categories")

        # Verify the structure
        print("\n5️⃣ Verifying new structure...")
        cursor.execute("SELECT * FROM categories WHERE parent_id IS NULL")
        top_level = cursor.fetchall()
        print(f"   Top-level categories: {len(top_level)}")

        cursor.execute("SELECT COUNT(*) as count FROM categories")
        result = cursor.fetchone()
        print(f"   Total categories: {result[0]}")

        print("\n✅ Category migration complete!")
        print("\n⚠️  Note: All transactions now need to be re-categorized using the new structure.")

    except Exception as e:
        cnx.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        cursor.close()
        cnx.close()


if __name__ == "__main__":
    main()
