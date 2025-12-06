#!/usr/bin/env python3
"""
Wipe and Re-import Script

This script:
1. Backs up current data
2. Clears transactions and expenses tables
3. Re-imports May and June PDFs
4. Migrates transactions to expenses
"""

import sys
from pathlib import Path
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_connection

# Import the parsing function
from scripts.parse_and_validate_pdf import parse_and_validate_pdf


def backup_data(conn, backup_dir: Path):
    """Create a backup of current data"""
    cursor = conn.cursor(dictionary=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"backup_{timestamp}.json"

    # Backup transactions
    cursor.execute('SELECT * FROM transactions')
    transactions = cursor.fetchall()

    # Backup expenses
    cursor.execute('SELECT * FROM expenses')
    expenses = cursor.fetchall()

    # Convert dates/decimals to strings for JSON
    def convert_for_json(obj):
        if hasattr(obj, 'isoformat'):
            return obj.isoformat()
        if hasattr(obj, '__float__'):
            return float(obj)
        return str(obj)

    backup_data = {
        'timestamp': timestamp,
        'transactions': transactions,
        'expenses': expenses
    }

    backup_file.write_text(json.dumps(backup_data, default=convert_for_json, indent=2))

    cursor.close()
    print(f"✓ Backup created: {backup_file}")
    print(f"  - Transactions: {len(transactions)}")
    print(f"  - Expenses: {len(expenses)}")

    return backup_file


def wipe_tables(conn, tables: list):
    """Wipe specified tables"""
    cursor = conn.cursor()

    for table in tables:
        cursor.execute(f"DELETE FROM {table}")
        count = cursor.rowcount
        print(f"✓ Cleared {count} records from {table} table")

    conn.commit()
    cursor.close()


def migrate_transactions_to_expenses_simple(conn):
    """
    Simple migration that converts ALL negative transactions to expenses.
    This handles both properly classified DEBIT and misclassified CREDIT transactions.
    """
    cursor = conn.cursor(dictionary=True)

    # Get all transactions with negative amounts (these are expenses)
    cursor.execute("""
        SELECT
            id,
            org_id,
            transaction_date,
            amount,
            description,
            transaction_type,
            category_id
        FROM transactions
        WHERE amount < 0
        ORDER BY transaction_date, id
    """)

    transactions = cursor.fetchall()
    print(f"\nFound {len(transactions)} expense transactions (amount < 0)")

    migrated = 0

    for txn in transactions:
        # Determine payment method
        desc_lower = txn['description'].lower()
        if 'check' in desc_lower or 'ck #' in desc_lower:
            method = 'OTHER'
        elif 'transfer' in desc_lower or 'online pymt' in desc_lower or 'online transfer' in desc_lower:
            method = 'BANK'
        elif 'purchase' in desc_lower or 'debit' in desc_lower or 'pos' in desc_lower:
            method = 'CARD'
        elif 'cash' in desc_lower or 'atm' in desc_lower:
            method = 'CASH'
        else:
            method = 'OTHER'

        # Insert into expenses
        cursor.execute("""
            INSERT INTO expenses (
                org_id, expense_date, amount, description,
                category_id, method, paid_by_contact_id
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            txn['org_id'],
            txn['transaction_date'],
            abs(txn['amount']),  # Convert to positive
            txn['description'],
            txn['category_id'],
            method,
            None
        ))
        migrated += 1

    conn.commit()
    print(f"✓ Migrated {migrated} transactions to expenses table")

    cursor.close()


def main():
    """Main function"""
    print("="*70)
    print("WIPE AND RE-IMPORT DATABASE")
    print("="*70)
    print()

    # Paths
    base_dir = Path(__file__).parent.parent
    backup_dir = base_dir / "backups"
    backup_dir.mkdir(exist_ok=True)

    may_pdf = base_dir / "may_statement.pdf"
    june_pdf = base_dir / "june_statement.pdf"

    # Check PDFs exist
    if not may_pdf.exists():
        print(f"✗ Error: May PDF not found at {may_pdf}")
        return
    if not june_pdf.exists():
        print(f"✗ Error: June PDF not found at {june_pdf}")
        return

    print(f"✓ Found May PDF: {may_pdf}")
    print(f"✓ Found June PDF: {june_pdf}")
    print()

    with get_connection() as conn:
        # Step 1: Backup
        print("Step 1: Creating backup...")
        backup_file = backup_data(conn, backup_dir)
        print()

        # Step 2: Wipe tables
        print("Step 2: Wiping tables...")
        wipe_tables(conn, ['expenses', 'transactions'])
        print()

    # Step 3: Re-import PDFs
    print("Step 3: Re-importing PDFs...")
    print("\n--- Importing May PDF ---")
    may_success = parse_and_validate_pdf(str(may_pdf), org_id=1)

    print("\n--- Importing June PDF ---")
    june_success = parse_and_validate_pdf(str(june_pdf), org_id=1)

    if not (may_success and june_success):
        print("\n✗ IMPORT FAILED - One or both PDFs failed validation")
        print(f"Backup available at: {backup_file}")
        print("Database has been wiped but import incomplete. Restore from backup if needed.")
        return

    # Step 4: Migrate to expenses
    print("\nStep 4: Migrating transactions to expenses...")
    with get_connection() as conn:
        migrate_transactions_to_expenses_simple(conn)

    # Step 5: Verify
    print("\nStep 5: Verifying data...")
    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                DATE_FORMAT(transaction_date, '%Y-%m') as month,
                COUNT(*) as count
            FROM transactions
            GROUP BY DATE_FORMAT(transaction_date, '%Y-%m')
            ORDER BY month
        """)
        txn_summary = cursor.fetchall()

        cursor.execute("""
            SELECT
                DATE_FORMAT(expense_date, '%Y-%m') as month,
                COUNT(*) as count
            FROM expenses
            GROUP BY DATE_FORMAT(expense_date, '%Y-%m')
            ORDER BY month
        """)
        exp_summary = cursor.fetchall()

        print("\nTransactions by month:")
        for row in txn_summary:
            print(f"  {row['month']}: {row['count']}")

        print("\nExpenses by month:")
        for row in exp_summary:
            print(f"  {row['month']}: {row['count']}")

        cursor.close()

    print("\n" + "="*70)
    print("✓ WIPE AND RE-IMPORT COMPLETE")
    print("="*70)
    print(f"\nBackup saved to: {backup_file}")


if __name__ == "__main__":
    main()
