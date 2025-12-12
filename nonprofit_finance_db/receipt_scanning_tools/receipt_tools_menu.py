#!/usr/bin/env python3
"""
Receipt Scanning Tools Menu

Main menu for accessing various receipt and expense management tools.

Usage:
    python receipt_scanning_tools/receipt_tools_menu.py
"""

import sys
import os
from pathlib import Path
import subprocess

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def clear_screen():
    """Clear the terminal screen"""
    os.system('clear')


def print_header():
    """Print the menu header"""
    clear_screen()
    print("\n" * 4)
    print("  ==============================")
    print("  === Receipt Scanning Tools ===")
    print("  ==============================\n")


def manual_entry():
    """Launch manual receipt entry tool"""
    script_path = Path(__file__).parent / "manual_entry.py"
    subprocess.run([sys.executable, str(script_path)])


def delete_by_date():
    """Launch delete expenses by date tool"""
    script_path = Path(__file__).parent / "delete_expenses_by_date.py"
    subprocess.run([sys.executable, str(script_path)])


def view_recent_expenses():
    """View recent expenses"""
    from app.db import get_connection

    clear_screen()
    print("\n" * 2)
    print("  =======================")
    print("  === Recent Expenses ===")
    print("  =======================\n")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT e.id, e.expense_date, e.amount, e.description, m.name as merchant
            FROM expenses e
            LEFT JOIN merchants m ON e.merchant_id = m.id
            ORDER BY e.created_at DESC
            LIMIT 20
        ''')

        expenses = cursor.fetchall()

        if not expenses:
            print("  No expenses found.\n")
        else:
            print(f"  {'ID':<6} {'Date':<12} {'Amount':<10} {'Merchant':<20} {'Description':<30}")
            print("  " + "-" * 80)

            for exp_id, date, amount, desc, merchant in expenses:
                merchant_str = merchant or "N/A"
                desc_str = (desc or "N/A")[:27]
                print(f"  {exp_id:<6} {str(date):<12} ${amount:<9.2f} {merchant_str:<20} {desc_str:<30}")

    print()
    input("  Press Enter to continue...")


def merchant_management():
    """Manage merchants"""
    from app.db import get_connection

    clear_screen()
    print("\n" * 2)
    print("  ===========================")
    print("  === Merchant Management ===")
    print("  ===========================\n")

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, category
            FROM merchants
            ORDER BY name
        ''')

        merchants = cursor.fetchall()

        if not merchants:
            print("  No merchants found.\n")
        else:
            print(f"  {'ID':<6} {'Name':<30} {'Category':<20}")
            print("  " + "-" * 58)

            for merchant_id, name, category in merchants:
                category_str = category or "N/A"
                print(f"  {merchant_id:<6} {name:<30} {category_str:<20}")

    print()
    print("  Options:")
    print("  1. Add new merchant")
    print("  2. Back to main menu")

    choice = input("\n  Select option: ").strip()

    if choice == "1":
        name = input("\n  Enter merchant name: ").strip()
        category = input("  Enter category [Food & Supplies]: ").strip()
        if not category:
            category = "Food & Supplies"

        if name:
            with get_connection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute('''
                        INSERT INTO merchants (name, category)
                        VALUES (%s, %s)
                    ''', (name, category))
                    conn.commit()
                    print(f"\n  ✓ Added merchant: {name}")
                except Exception as e:
                    print(f"\n  ✗ Error: {e}")

            input("\n  Press Enter to continue...")


def main_menu():
    """Display and handle main menu"""

    menu_items = [
        ("Manual Receipt Entry", manual_entry),
        ("Delete Expenses by Date", delete_by_date),
        ("View Recent Expenses", view_recent_expenses),
        ("Manage Merchants", merchant_management),
    ]

    while True:
        print_header()

        for index, (title, _) in enumerate(menu_items, start=1):
            print(f"  {index}. {title}")

        print(f"  {len(menu_items) + 1}. Exit")

        choice = input("\n  Please select an option: ").strip()

        if choice.isdigit():
            choice_num = int(choice)

            if 1 <= choice_num <= len(menu_items):
                # Execute the selected function
                menu_items[choice_num - 1][1]()
            elif choice_num == len(menu_items) + 1:
                print("\n  Thank you for using Receipt Scanning Tools!\n")
                break
            else:
                print("\n  Invalid selection. Press Enter to continue...")
                input()
        else:
            print("\n  Invalid selection. Press Enter to continue...")
            input()


if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print("\n\n  Cancelled by user.\n")
    except Exception as e:
        print(f"\n  Unexpected error: {e}\n")
        import traceback
        traceback.print_exc()
