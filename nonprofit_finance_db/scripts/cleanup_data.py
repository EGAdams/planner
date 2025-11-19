#!/usr/bin/env python3
"""
Data Cleanup Tool

This script safely deletes old transaction data and optionally re-imports
with the fixed PDF parser to remove balance entries.

Usage:
    python scripts/cleanup_data.py [options]

Options:
    --batch-id ID           Delete specific import batch (default: 1)
    --dry-run              Show what would be deleted without actually doing it
    --reimport PATH        Re-import PDF after cleanup
    --force                Skip confirmation prompts
    --backup               Create backup before deletion
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_connection

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataCleanupTool:
    """Tool for safely cleaning up transaction data"""

    def __init__(self, batch_id: int = 1):
        self.batch_id = batch_id

    def show_current_data_summary(self):
        """Show summary of current data before cleanup"""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Get overall stats
            cursor.execute("""
                SELECT COUNT(*) as total_transactions,
                       SUM(amount) as total_amount,
                       MIN(transaction_date) as earliest_date,
                       MAX(transaction_date) as latest_date,
                       MIN(amount) as min_amount,
                       MAX(amount) as max_amount
                FROM transactions
                WHERE import_batch_id = %s
            """, (self.batch_id,))

            stats = cursor.fetchone()
            if not stats or stats[0] == 0:
                print(f"❌ No transactions found for batch ID {self.batch_id}")
                return False

            total_transactions, total_amount, earliest_date, latest_date, min_amount, max_amount = stats

            print(f"📊 CURRENT DATA SUMMARY (Batch {self.batch_id})")
            print("=" * 60)
            print(f"Total Transactions: {total_transactions:,}")
            print(f"Total Amount: ${total_amount:,.2f}")
            print(f"Date Range: {earliest_date} to {latest_date}")
            print(f"Amount Range: ${min_amount:,.2f} to ${max_amount:,.2f}")

            # Show problematic large transactions
            cursor.execute("""
                SELECT transaction_date, amount, description
                FROM transactions
                WHERE import_batch_id = %s AND amount > 50000
                ORDER BY amount DESC
                LIMIT 10
            """, (self.batch_id,))

            large_transactions = cursor.fetchall()
            if large_transactions:
                print(f"\n⚠️  PROBLEMATIC LARGE TRANSACTIONS (>$50k - likely balance entries):")
                for i, (date, amount, desc) in enumerate(large_transactions, 1):
                    desc_short = desc[:40] if desc else 'N/A'
                    print(f"  {i:2}. {date} | ${amount:>10,.2f} | {desc_short}")

            # Show batch info
            cursor.execute("""
                SELECT filename, import_date, status, total_transactions,
                       successful_imports, failed_imports
                FROM import_batches
                WHERE id = %s
            """, (self.batch_id,))

            batch_info = cursor.fetchone()
            if batch_info:
                filename, import_date, status, batch_total, successful, failed = batch_info
                print(f"\n📁 IMPORT BATCH INFO:")
                print(f"  File: {filename}")
                print(f"  Import Date: {import_date}")
                print(f"  Status: {status}")
                print(f"  Reported Transactions: {batch_total}")
                print(f"  Successful: {successful}, Failed: {failed}")

            return True

    def create_backup(self):
        """Create a backup of current data"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"transaction_backup_{self.batch_id}_{timestamp}.sql"

        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                # Export transactions
                cursor.execute("""
                    SELECT * FROM transactions WHERE import_batch_id = %s
                """, (self.batch_id,))

                transactions = cursor.fetchall()
                if not transactions:
                    print("❌ No transactions to backup")
                    return None

                # Write backup file
                with open(backup_file, 'w') as f:
                    f.write(f"-- Transaction backup for batch {self.batch_id}\n")
                    f.write(f"-- Created: {datetime.now()}\n")
                    f.write(f"-- Total transactions: {len(transactions)}\n\n")

                    # Get column names
                    cursor.execute("""
                        SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS
                        WHERE TABLE_NAME = 'transactions' AND TABLE_SCHEMA = 'nonprofit_finance'
                        ORDER BY ORDINAL_POSITION
                    """)
                    columns = [row[0] for row in cursor.fetchall()]

                    for tx in transactions:
                        values = []
                        for value in tx:
                            if value is None:
                                values.append('NULL')
                            elif isinstance(value, str):
                                # Escape single quotes
                                escaped = value.replace("'", "''")
                                values.append(f"'{escaped}'")
                            else:
                                values.append(str(value))

                        f.write(f"INSERT INTO transactions ({', '.join(columns)}) VALUES ({', '.join(values)});\n")

                print(f"✅ Backup created: {backup_file}")
                return backup_file

        except Exception as e:
            print(f"❌ Backup failed: {str(e)}")
            return None

    def delete_batch_data(self, dry_run: bool = False):
        """Delete all data for the specified batch"""
        try:
            with get_connection() as conn:
                cursor = conn.cursor()

                if dry_run:
                    print(f"\n🔍 DRY RUN - Would delete the following:")

                    # Show what would be deleted
                    cursor.execute("SELECT COUNT(*) FROM transactions WHERE import_batch_id = %s", (self.batch_id,))
                    tx_count = cursor.fetchone()[0]

                    cursor.execute("SELECT COUNT(*) FROM account_info WHERE import_batch_id = %s", (self.batch_id,))
                    account_count = cursor.fetchone()[0]

                    cursor.execute("SELECT COUNT(*) FROM duplicate_flags df JOIN transactions t ON df.transaction_id = t.id WHERE t.import_batch_id = %s", (self.batch_id,))
                    duplicate_count = cursor.fetchone()[0]

                    print(f"  - {tx_count} transactions")
                    print(f"  - {account_count} account info records")
                    print(f"  - {duplicate_count} duplicate flag records")
                    print(f"  - 1 import batch record")

                    return True

                # Actual deletion
                print(f"\n🗑️  DELETING DATA FOR BATCH {self.batch_id}...")

                # Delete duplicate flags first (foreign key constraint)
                cursor.execute("""
                    DELETE df FROM duplicate_flags df
                    JOIN transactions t ON df.transaction_id = t.id
                    WHERE t.import_batch_id = %s
                """, (self.batch_id,))
                duplicate_deleted = cursor.rowcount
                print(f"  ✅ Deleted {duplicate_deleted} duplicate flag records")

                # Delete transactions
                cursor.execute("DELETE FROM transactions WHERE import_batch_id = %s", (self.batch_id,))
                tx_deleted = cursor.rowcount
                print(f"  ✅ Deleted {tx_deleted} transaction records")

                # Delete account info
                cursor.execute("DELETE FROM account_info WHERE import_batch_id = %s", (self.batch_id,))
                account_deleted = cursor.rowcount
                print(f"  ✅ Deleted {account_deleted} account info records")

                # Delete import batch
                cursor.execute("DELETE FROM import_batches WHERE id = %s", (self.batch_id,))
                batch_deleted = cursor.rowcount
                print(f"  ✅ Deleted {batch_deleted} import batch record")

                # Commit changes
                conn.commit()

                print(f"\n🎉 CLEANUP COMPLETE!")
                print(f"   Total records deleted: {tx_deleted + account_deleted + duplicate_deleted + batch_deleted}")

                return True

        except Exception as e:
            print(f"❌ Deletion failed: {str(e)}")
            return False

    def reimport_pdf(self, pdf_path: str):
        """Re-import PDF with the fixed parser"""
        try:
            print(f"\n📥 RE-IMPORTING PDF WITH FIXED PARSER...")
            print(f"   File: {pdf_path}")

            # Import the ingestion pipeline
            from ingestion.pipeline import IngestionPipeline

            # Create pipeline and import
            with get_connection() as conn:
                pipeline = IngestionPipeline(org_id=1, database_connection=conn)
                result = pipeline.ingest_file(pdf_path, auto_process=True)

                # Show results
                print(f"\n✅ RE-IMPORT COMPLETE!")
                print(f"   Success: {result['success']}")
                print(f"   Total transactions: {result['total_transactions']}")
                print(f"   Successfully imported: {result['successful_imports']}")
                print(f"   Failed imports: {result['failed_imports']}")
                print(f"   Duplicates detected: {result['duplicate_count']}")

                if result['import_batch']:
                    batch = result['import_batch']
                    print(f"   New batch ID: {batch.id}")

                return result['success']

        except Exception as e:
            print(f"❌ Re-import failed: {str(e)}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Clean up transaction data')
    parser.add_argument('--batch-id', type=int, default=1, help='Import batch ID to delete (default: 1)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be deleted without doing it')
    parser.add_argument('--reimport', type=str, help='PDF file path to re-import after cleanup')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompts')
    parser.add_argument('--backup', action='store_true', help='Create backup before deletion')

    args = parser.parse_args()

    # Initialize cleanup tool
    cleanup = DataCleanupTool(batch_id=args.batch_id)

    try:
        print("🧹 TRANSACTION DATA CLEANUP TOOL")
        print("=" * 60)

        # Show current data
        if not cleanup.show_current_data_summary():
            print("❌ No data found to clean up")
            return 1

        # Confirm action unless forced
        if not args.dry_run and not args.force:
            print(f"\n⚠️  WARNING: This will permanently delete all data for batch {args.batch_id}")
            if args.reimport:
                print(f"   Then re-import from: {args.reimport}")

            confirm = input("\nContinue? (type 'yes' to confirm): ").strip().lower()
            if confirm != 'yes':
                print("❌ Operation cancelled")
                return 1

        # Create backup if requested
        backup_file = None
        if args.backup and not args.dry_run:
            backup_file = cleanup.create_backup()
            if not backup_file:
                print("❌ Backup failed, aborting")
                return 1

        # Delete data
        if not cleanup.delete_batch_data(dry_run=args.dry_run):
            print("❌ Cleanup failed")
            return 1

        # Re-import if requested
        if args.reimport and not args.dry_run:
            if not os.path.exists(args.reimport):
                print(f"❌ File not found: {args.reimport}")
                return 1

            if not cleanup.reimport_pdf(args.reimport):
                print("❌ Re-import failed")
                return 1

        if args.dry_run:
            print(f"\n💡 To actually perform the cleanup, run without --dry-run")
        else:
            print(f"\n🎉 All operations completed successfully!")
            if backup_file:
                print(f"   Backup saved to: {backup_file}")

        return 0

    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())