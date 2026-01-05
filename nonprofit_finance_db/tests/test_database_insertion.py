#!/usr/bin/env python3
"""
Test script to verify PDF parsing and database insertion
"""

import sys
import logging
from pathlib import Path
from datetime import datetime

# Add parent directory to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

from parsers import PDFParser
from app.db import get_connection, execute

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_pdf_parsing_and_db_insertion():
    """Test PDF parsing and database insertion"""

    pdf_path = "/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf"
    org_id = 1

    logger.info(f"Testing PDF parsing and database insertion for: {pdf_path}")

    # Step 1: Parse the PDF
    parser = PDFParser(org_id)

    if not parser.validate_format(pdf_path):
        logger.error("Invalid PDF format")
        return False

    # Parse transactions
    transactions = parser.parse(pdf_path)
    logger.info(f"Parsed {len(transactions)} transactions")

    # Get account info
    account_info = parser.extract_account_info(pdf_path)
    logger.info(f"Account info: {account_info}")

    # Step 2: Create import batch
    with get_connection() as conn:
        cursor = conn.cursor()

        # Insert import batch
        batch_sql = """
        INSERT INTO import_batches (org_id, filename, file_format, total_transactions, status)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(batch_sql, (
            org_id,
            "fifth_third_personal_june.pdf",
            "PDF",
            len(transactions),
            "PROCESSING"
        ))

        batch_id = cursor.lastrowid
        logger.info(f"Created import batch with ID: {batch_id}")

        # Insert account info
        if account_info.get('account_number'):
            account_sql = """
            INSERT INTO account_info (org_id, account_number, account_type, bank_name,
                                    statement_start_date, statement_end_date, import_batch_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(account_sql, (
                org_id,
                account_info.get('account_number'),
                account_info.get('account_type'),
                account_info.get('bank_name'),
                account_info.get('statement_start_date'),
                account_info.get('statement_end_date'),
                batch_id
            ))
            logger.info("Inserted account info")

        # Insert transactions
        transaction_sql = """
        INSERT INTO transactions (org_id, transaction_date, amount, description,
                                transaction_type, account_number, bank_reference,
                                balance_after, import_batch_id, raw_data)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        successful_inserts = 0
        failed_inserts = 0

        for transaction in transactions:
            try:
                cursor.execute(transaction_sql, (
                    org_id,
                    transaction.get('transaction_date'),
                    transaction.get('amount'),
                    transaction.get('description'),
                    transaction.get('transaction_type'),
                    transaction.get('account_number'),
                    transaction.get('bank_reference'),
                    transaction.get('balance_after'),
                    batch_id,
                    transaction.get('raw_data')
                ))
                successful_inserts += 1
            except Exception as e:
                logger.error(f"Failed to insert transaction: {e}")
                logger.error(f"Transaction data: {transaction}")
                failed_inserts += 1

        # Update batch status
        update_sql = """
        UPDATE import_batches
        SET successful_imports = %s, failed_imports = %s, status = %s
        WHERE id = %s
        """
        cursor.execute(update_sql, (successful_inserts, failed_inserts, "COMPLETED", batch_id))

        # Commit all changes
        conn.commit()

        logger.info(f"Successfully inserted {successful_inserts} transactions")
        logger.info(f"Failed to insert {failed_inserts} transactions")

        # Step 3: Verify the data
        cursor.execute("SELECT COUNT(*) FROM transactions WHERE import_batch_id = %s", (batch_id,))
        db_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM account_info WHERE import_batch_id = %s", (batch_id,))
        account_count = cursor.fetchone()[0]

        print("\n" + "="*60)
        print("DATABASE VERIFICATION RESULTS")
        print("="*60)
        print(f"Import Batch ID: {batch_id}")
        print(f"Transactions parsed: {len(transactions)}")
        print(f"Transactions in database: {db_count}")
        print(f"Account records: {account_count}")
        print(f"Success rate: {successful_inserts}/{len(transactions)} ({(successful_inserts/len(transactions)*100):.1f}%)")

        # Show sample transactions
        cursor.execute("""
        SELECT transaction_date, amount, description, transaction_type
        FROM transactions
        WHERE import_batch_id = %s
        ORDER BY transaction_date
        LIMIT 10
        """, (batch_id,))

        sample_transactions = cursor.fetchall()
        print(f"\nFirst 10 transactions in database:")
        for i, (date, amount, desc, txn_type) in enumerate(sample_transactions, 1):
            print(f"  {i}. {date} | {txn_type} | ${amount:.2f} | {desc[:60]}...")

        print("="*60)

        return successful_inserts == len(transactions)

if __name__ == "__main__":
    success = test_pdf_parsing_and_db_insertion()
    sys.exit(0 if success else 1)