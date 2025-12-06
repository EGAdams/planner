#!/usr/bin/env python3
"""
Migrate transactions from the transactions table to the expenses table.

This script converts bank transactions (from PDFs) into expense records
that can be displayed in the Daily Expense Categorizer.

Only DEBIT transactions (expenses) are migrated. CREDIT transactions (income)
are skipped since they're not expenses.
"""

import sys
from pathlib import Path
from typing import Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_connection


def determine_payment_method(description: str, transaction_type: str) -> str:
    """
    Determine payment method from transaction description.

    Returns: 'CASH', 'CARD', 'BANK', or 'OTHER'
    """
    desc_lower = description.lower()

    # Check for common patterns
    if 'check' in desc_lower or 'ck #' in desc_lower:
        return 'OTHER'  # Checks
    elif 'transfer' in desc_lower or 'online pymt' in desc_lower or 'online transfer' in desc_lower:
        return 'BANK'
    elif 'purchase' in desc_lower or 'debit' in desc_lower or 'pos' in desc_lower:
        return 'CARD'
    elif 'cash' in desc_lower or 'atm' in desc_lower:
        return 'CASH'
    else:
        return 'OTHER'


def migrate_transactions_to_expenses(start_date: str = None, end_date: str = None, dry_run: bool = False):
    """
    Migrate transactions from transactions table to expenses table.

    Args:
        start_date: Only migrate transactions on or after this date (YYYY-MM-DD)
        end_date: Only migrate transactions on or before this date (YYYY-MM-DD)
        dry_run: If True, only show what would be migrated without making changes
    """
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)

        # Build query to fetch DEBIT transactions (expenses only)
        query = """
            SELECT
                id,
                org_id,
                transaction_date,
                amount,
                description,
                transaction_type,
                category_id
            FROM transactions
            WHERE transaction_type = 'DEBIT'
        """

        params = []
        if start_date:
            query += " AND transaction_date >= %s"
            params.append(start_date)
        if end_date:
            query += " AND transaction_date <= %s"
            params.append(end_date)

        query += " ORDER BY transaction_date, id"

        cursor.execute(query, tuple(params))
        transactions = cursor.fetchall()

        print(f"Found {len(transactions)} DEBIT transactions to migrate")

        if len(transactions) == 0:
            print("No transactions to migrate.")
            cursor.close()
            return

        # Check for existing expenses to avoid duplicates
        # Build a signature based on date + amount + description prefix
        migrated_count = 0
        skipped_count = 0
        would_migrate_count = 0

        for txn in transactions:
            # Create a signature to check for duplicates
            # Use first 100 chars of description to match
            desc_prefix = txn['description'][:100] if txn['description'] else ''

            # Check if expense already exists
            check_sql = """
                SELECT id FROM expenses
                WHERE org_id = %s
                AND expense_date = %s
                AND amount = %s
                AND description LIKE %s
                LIMIT 1
            """
            cursor.execute(check_sql, (
                txn['org_id'],
                txn['transaction_date'],
                abs(txn['amount']),  # Convert to positive for expense
                f"{desc_prefix}%"
            ))

            existing = cursor.fetchone()

            if existing:
                skipped_count += 1
                if dry_run:
                    print(f"  SKIP (exists): {txn['transaction_date']} ${abs(txn['amount']):.2f} - {desc_prefix[:40]}")
                continue

            # Prepare expense record
            payment_method = determine_payment_method(txn['description'], txn['transaction_type'])

            expense_data = {
                'org_id': txn['org_id'],
                'expense_date': txn['transaction_date'],
                'amount': abs(txn['amount']),  # Convert negative to positive
                'description': txn['description'],
                'category_id': txn['category_id'],
                'method': payment_method,
                'paid_by_contact_id': None  # Not tracked in transactions table
            }

            if dry_run:
                print(f"  WOULD MIGRATE: {expense_data['expense_date']} ${expense_data['amount']:.2f} ({payment_method}) - {expense_data['description'][:40]}")
                would_migrate_count += 1
            else:
                # Insert into expenses table
                insert_sql = """
                    INSERT INTO expenses (
                        org_id, expense_date, amount, description,
                        category_id, method, paid_by_contact_id
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s
                    )
                """
                cursor.execute(insert_sql, (
                    expense_data['org_id'],
                    expense_data['expense_date'],
                    expense_data['amount'],
                    expense_data['description'],
                    expense_data['category_id'],
                    expense_data['method'],
                    expense_data['paid_by_contact_id']
                ))
                migrated_count += 1

        if not dry_run:
            conn.commit()
            print(f"\n✓ Successfully migrated {migrated_count} transactions to expenses")
        else:
            print(f"\n[DRY RUN] Would migrate {would_migrate_count} transactions")

        print(f"✓ Skipped {skipped_count} transactions (already exist in expenses)")

        cursor.close()


def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Migrate transactions to expenses')
    parser.add_argument('--start-date', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be migrated without making changes')

    args = parser.parse_args()

    print("="*70)
    print("TRANSACTION TO EXPENSE MIGRATION")
    print("="*70)

    if args.dry_run:
        print("Running in DRY RUN mode - no changes will be made")

    if args.start_date:
        print(f"Start date: {args.start_date}")
    if args.end_date:
        print(f"End date: {args.end_date}")

    print()

    migrate_transactions_to_expenses(
        start_date=args.start_date,
        end_date=args.end_date,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()
