#!/usr/bin/env python3
"""
Manual Receipt Entry Tool

A simple command-line interface for manually entering receipt data
and saving it to the database.

Usage:
    python receipt_scanning_tools/manual_entry.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.db import get_connection

console = None  # Will be initialized in main()


def print_header():
    """Print application header"""
    os.system('clear')
    print("\n" * 4)
    print("  ============================")
    print("  === Receipt Manual Entry ===")
    print("  ============================\n")


def get_merchants() -> List[Tuple[int, str, str]]:
    """Fetch merchants from database"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, category
                FROM merchants
                ORDER BY name
            """)
            return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching merchants: {e}")
        return []


def display_merchants_menu(merchants: List[Tuple[int, str, str]]) -> Optional[Tuple[int, str]]:
    """Display merchants in a smart menu format, grouped by category"""
    os.system('clear')
    print("\n" * 2)
    print("  =======================")
    print("  === Select Merchant ===")
    print("  =======================\n")

    # Group merchants by category
    from collections import defaultdict
    grouped = defaultdict(list)
    for merchant_id, name, category in merchants:
        cat = category or "Other"
        grouped[cat].append((merchant_id, name))

    # Display merchants grouped by category
    index = 1
    merchant_map = {}  # Maps display number to (merchant_id, name)

    # Define category order for church non-profit
    category_order = [
        "Gifts and Love Offerings",
        "Ministers and Workers",
        "Presents for ROL Friends and Members",
        "Food & Supplies",
        "Other"
    ]

    for cat in category_order:
        if cat in grouped:
            print(f"  --- {cat} ---")
            for merchant_id, name in sorted(grouped[cat], key=lambda x: x[1]):
                print(f"  {index}. {name}")
                merchant_map[index] = (merchant_id, name)
                index += 1
            print()

    print(f"  {index}. Enter custom merchant name")
    print(f"  {index + 1}. Cancel")

    custom_option = index
    cancel_option = index + 1

    while True:
        choice = input("\n  Please select an option: ")
        if choice.isdigit():
            choice = int(choice)
            if choice in merchant_map:
                return merchant_map[choice]
            elif choice == custom_option:
                custom_name = input("\n  Enter merchant name: ").strip()
                if custom_name:
                    # Ask for category
                    print("\n  Select category:")
                    print("  1. Gifts and Love Offerings")
                    print("  2. Ministers and Workers")
                    print("  3. Presents for ROL Friends and Members")
                    print("  4. Food & Supplies")
                    print("  5. Other")
                    cat_choice = input("  Category (1-5): ").strip()

                    category_map = {
                        "1": "Gifts and Love Offerings",
                        "2": "Ministers and Workers",
                        "3": "Presents for ROL Friends and Members",
                        "4": "Food & Supplies",
                        "5": "Other"
                    }
                    category = category_map.get(cat_choice, "Other")

                    # Add new merchant to database
                    merchant_id = add_new_merchant(custom_name, category)
                    if merchant_id:
                        return (merchant_id, custom_name)
                print("  Invalid name. Please try again.")
            elif choice == cancel_option:
                return None
            else:
                print("  Invalid selection. Please try again.")
        else:
            print("  Invalid selection. Please try again.")


def add_new_merchant(name: str, category: str = "Food & Supplies") -> Optional[int]:
    """Add a new merchant to the database"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO merchants (name, category)
                VALUES (%s, %s)
            """, (name, category))
            conn.commit()
            return cursor.lastrowid
    except Exception as e:
        print(f"Error adding merchant: {e}")
        return None


def get_categories():
    """Fetch available categories from database with hierarchical path"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                WITH RECURSIVE category_hierarchy AS (
                    SELECT id, name, parent_id, name as full_path, 0 as level
                    FROM categories
                    WHERE parent_id IS NULL
                    UNION ALL
                    SELECT c.id, c.name, c.parent_id,
                           CONCAT(ch.full_path, ' > ', c.name) as full_path,
                           ch.level + 1
                    FROM categories c
                    INNER JOIN category_hierarchy ch ON c.parent_id = ch.id
                )
                SELECT id, name, full_path
                FROM category_hierarchy
                ORDER BY full_path
            """)
            return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching categories: {e}")
        return []


def display_categories(categories):
    """Display categories in a simple numbered list"""
    os.system('clear')
    print("\n" * 2)
    print("  =======================")
    print("  === Select Category ===")
    print("  =======================\n")

    for index, (cat_id, name, path) in enumerate(categories, start=1):
        print(f"  {index}. {path or name}")


def select_category(categories):
    """Prompt user to select a category"""
    display_categories(categories)

    print(f"  {len(categories) + 1}. Cancel")

    while True:
        try:
            choice = input("\n  Please select an option: ")
            if choice.isdigit():
                choice = int(choice)
                if 1 <= choice <= len(categories):
                    # Return the category_id (first element of the tuple)
                    return categories[choice - 1][0]
                elif choice == len(categories) + 1:
                    return None
                else:
                    print("  Invalid selection. Please try again.")
            else:
                print("  Please enter a valid number.")
        except KeyboardInterrupt:
            return None


def enter_receipt_data():
    """Prompt user to enter receipt information"""
    os.system('clear')
    print("\n" * 2)
    print("  ==========================")
    print("  === Enter Receipt Data ===")
    print("  ==========================\n")

    # Select merchant from list
    merchants = get_merchants()
    if not merchants:
        print("  No merchants found. Please add merchants first.")
        return None

    merchant_result = display_merchants_menu(merchants)
    if merchant_result is None:
        return None

    merchant_id, merchant_name = merchant_result

    # Get transaction date
    while True:
        date_str = input(f"\n  Transaction date (YYYY-MM-DD) [{datetime.now().strftime('%Y-%m-%d')}]: ")
        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")
        try:
            transaction_date = datetime.strptime(date_str, "%Y-%m-%d").date()
            break
        except ValueError:
            print("  Invalid date format. Use YYYY-MM-DD")

    # Get total amount
    while True:
        try:
            amount_str = input("  Total amount: $")
            total_amount = float(amount_str)
            break
        except ValueError:
            print("  Please enter a valid number.")

    # Get description/notes
    description = input("  Description/Notes (optional): ")

    return {
        "merchant_id": merchant_id,
        "merchant_name": merchant_name,
        "transaction_date": transaction_date,
        "total_amount": total_amount,
        "description": description
    }


def save_expense(receipt_data, category_id):
    """Save the expense to the database"""
    try:
        with get_connection() as conn:
            cursor = conn.cursor()

            # Insert into expenses table
            insert_sql = """
                INSERT INTO expenses (
                    org_id, expense_date, amount, category_id,
                    merchant_id, method, description, created_at
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """

            description = f"{receipt_data['merchant_name']}"
            if receipt_data['description']:
                description += f" - {receipt_data['description']}"

            cursor.execute(insert_sql, (
                1,  # Default org_id
                receipt_data["transaction_date"],
                receipt_data["total_amount"],
                category_id,
                receipt_data["merchant_id"],
                "CASH",  # Default payment method
                description,
                datetime.now()
            ))

            conn.commit()
            expense_id = cursor.lastrowid

            print(f"\n  ✓ Expense saved successfully! (ID: {expense_id})")
            return True

    except Exception as e:
        print(f"  ✗ Error saving expense: {e}")
        return False


def main():
    """Main entry point"""
    try:
        print_header()

        # Fetch categories
        print("  Loading categories...")
        categories = get_categories()

        if not categories:
            print("  No categories found. Please initialize the database first.")
            return

        print(f"  Found {len(categories)} categories\n")
        input("  Press Enter to continue...")

        while True:
            # Enter receipt data
            receipt_data = enter_receipt_data()

            if receipt_data is None:
                print("\n  Entry cancelled.")
                break

            # Display summary
            os.system('clear')
            print("\n" * 2)
            print("  =======================")
            print("  === Receipt Summary ===")
            print("  =======================\n")
            print(f"  Merchant:    {receipt_data['merchant_name']}")
            print(f"  Date:        {receipt_data['transaction_date']}")
            print(f"  Amount:      ${receipt_data['total_amount']:.2f}")
            print(f"  Description: {receipt_data['description'] or 'N/A'}")
            print()

            # Select category
            print("  Select a category for this expense...")
            input("  Press Enter to continue...")
            category_id = select_category(categories)

            if category_id is None:
                print("\n  Entry cancelled.")
                break

            # Confirm and save
            os.system('clear')
            print("\n" * 2)
            print(f"  Save this expense?")
            print(f"  Merchant: {receipt_data['merchant_name']}")
            print(f"  Amount: ${receipt_data['total_amount']:.2f}")
            confirm = input("\n  (y/n): ").strip().lower()

            if confirm == 'y':
                if save_expense(receipt_data, category_id):
                    # Ask if user wants to enter another
                    another = input("\n  Enter another receipt? (y/n): ").strip().lower()
                    if another != 'y':
                        break
                else:
                    print("  Failed to save expense.")
                    break
            else:
                print("  Expense not saved.")
                another = input("\n  Enter another receipt? (y/n): ").strip().lower()
                if another != 'y':
                    break

        print("\n  Thank you for using Manual Entry Tool!\n")

    except KeyboardInterrupt:
        print("\n\n  Cancelled by user.\n")
    except Exception as e:
        print(f"\n  Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
