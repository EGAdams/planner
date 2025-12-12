#!/usr/bin/env python3
"""
Delete expenses by date

Usage:
    python receipt_scanning_tools/delete_expenses_by_date.py
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_connection


def delete_expenses_by_date(date_str):
    """Delete all expenses on a specific date"""

    with get_connection() as conn:
        cursor = conn.cursor()

        # Check expenses on the date
        cursor.execute('''
            SELECT id, expense_date, amount, description
            FROM expenses
            WHERE expense_date = %s
            ORDER BY id
        ''', (date_str,))

        expenses = cursor.fetchall()

        if not expenses:
            print(f'\nNo expenses found on {date_str}')
            return

        print(f'\n=== Found {len(expenses)} expense(s) on {date_str} ===\n')

        total = 0
        for expense_id, date, amount, desc in expenses:
            print(f'  ID {expense_id:4d}: ${amount:7.2f} - {desc[:50]}')
            total += float(amount)

        print(f'\n  Total amount: ${total:.2f}')
        print(f'\n{"=" * 60}')
        print('\n⚠️  WARNING: This action cannot be undone!')

        confirm = input('\nDelete these expenses? Type "yes" to confirm: ')

        if confirm.lower() == 'yes':
            cursor.execute('''
                DELETE FROM expenses
                WHERE expense_date = %s
            ''', (date_str,))
            conn.commit()
            print(f'\n✓ Successfully deleted {cursor.rowcount} expense(s)\n')
        else:
            print('\n✗ Deletion cancelled\n')


def main():
    """Main entry point"""
    print('\n' + '=' * 60)
    print('  Delete Expenses by Date')
    print('=' * 60)

    # Default to 2024-12-31 or ask user
    default_date = '2024-12-31'
    date_input = input(f'\nEnter date to delete (YYYY-MM-DD) [{default_date}]: ').strip()

    if not date_input:
        date_input = default_date

    delete_expenses_by_date(date_input)


if __name__ == "__main__":
    main()
