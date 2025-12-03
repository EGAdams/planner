#!/usr/bin/env python3
"""
Debug PDF Table Extraction

This script shows detailed information about all tables extracted from a PDF,
helping identify why some tables might not be parsed as transactions.

Usage:
    python scripts/debug_pdf_tables.py <pdf_file_path>
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pdf_extractor import DoclingPDFExtractor


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/debug_pdf_tables.py <pdf_file_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    print(f"="*70)
    print(f"PDF TABLE EXTRACTION DEBUG")
    print(f"="*70)
    print(f"File: {pdf_path}\n")

    extractor = DoclingPDFExtractor(org_id=1)

    # Extract tables
    print("Extracting tables...")
    tables = extractor.extract_tables(pdf_path)
    print(f"Found {len(tables)} table groups\n")

    # Show details for each table
    for page_idx, page_tables in enumerate(tables):
        print(f"\n{'='*70}")
        print(f"PAGE {page_idx + 1} - {len(page_tables)} tables")
        print(f"{'='*70}")

        for table_idx, table in enumerate(page_tables):
            print(f"\nTable {page_idx + 1}.{table_idx + 1}:")
            print(f"  Rows: {len(table)}")

            if len(table) > 0:
                # Show header
                header = table[0]
                header_text = ' '.join(str(h) for h in header).lower()
                print(f"  Header: {header}")
                print(f"  Header text: '{header_text}'")

                # Check if it matches transaction patterns
                is_transaction = any(
                    keyword in header_text
                    for keyword in ['withdrawal', 'deposit', 'debit', 'credit', 'checks', 'date']
                )
                print(f"  Matches transaction pattern: {is_transaction}")

                # Check if it looks like a balance table
                is_balance = any(
                    keyword in header_text
                    for keyword in ['daily balance summary', 'balance summary', 'account summary']
                )
                print(f"  Looks like balance table: {is_balance}")

                # Show first 3 data rows
                print(f"  First 3 data rows:")
                for i, row in enumerate(table[1:4]):
                    print(f"    Row {i+1}: {row}")

            print()

    # Extract and parse transactions
    print(f"\n{'='*70}")
    print(f"TRANSACTION PARSING RESULT")
    print(f"{'='*70}\n")

    transactions = extractor.parse_transactions(pdf_path)
    print(f"Total transactions parsed: {len(transactions)}\n")

    if transactions:
        print("First 5 transactions:")
        for i, txn in enumerate(transactions[:5]):
            print(f"  {i+1}. {txn.get('transaction_date')} | ${txn.get('amount', 0):>10.2f} | {txn.get('description', 'N/A')[:50]}")

    # Extract account summary
    print(f"\n{'='*70}")
    print(f"ACCOUNT SUMMARY")
    print(f"{'='*70}\n")

    account_info = extractor.extract_account_info(pdf_path)
    summary = account_info.get('summary', {})

    if summary:
        print("Expected from summary:")
        print(f"  Checks: {summary.get('checks', {})}")
        print(f"  Withdrawals: {summary.get('withdrawals', {})}")
        print(f"  Deposits: {summary.get('deposits', {})}")
        print(f"  Beginning Balance: ${summary.get('beginning_balance', 0):.2f}")
        print(f"  Ending Balance: ${summary.get('ending_balance', 0):.2f}")
    else:
        print("No summary information found")


if __name__ == "__main__":
    main()
