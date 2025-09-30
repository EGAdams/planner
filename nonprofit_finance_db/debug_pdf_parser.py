#!/usr/bin/env python3
"""
Debug script to analyze PDF parser output and identify balance vs transaction issues
"""

import sys
import logging
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from parsers import PDFParser
from pdf_extractor import DoclingPDFExtractor

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def debug_pdf_parsing():
    """Debug PDF parsing to identify balance vs transaction confusion"""

    pdf_path = "/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf"
    org_id = 1

    print("🔍 DEBUGGING PDF PARSER")
    print("=" * 60)
    print(f"PDF File: {pdf_path}")
    print()

    # Initialize extractor
    extractor = DoclingPDFExtractor(org_id)

    # Step 1: Extract raw text to see what we're working with
    print("📄 EXTRACTING RAW TEXT...")
    text = extractor.extract_text(pdf_path)

    # Look for balance summary sections
    print("\n🔍 SEARCHING FOR BALANCE SUMMARY SECTIONS...")
    lines = text.split('\n')
    in_balance_section = False
    balance_section_lines = []

    for i, line in enumerate(lines):
        line_lower = line.lower()

        # Look for balance summary indicators
        if any(keyword in line_lower for keyword in ['daily balance', 'balance summary', 'daily balances']):
            print(f"✅ Found balance section indicator at line {i}: {line.strip()}")
            in_balance_section = True
            balance_section_lines.append((i, line))
            continue

        # Look for transaction section indicators
        if any(keyword in line_lower for keyword in ['transaction', 'deposits', 'withdrawals', 'activity']):
            if in_balance_section:
                print(f"🛑 End of balance section at line {i}: {line.strip()}")
                in_balance_section = False
            else:
                print(f"📋 Found transaction section at line {i}: {line.strip()}")

        # Collect lines that might be in balance section
        if in_balance_section:
            balance_section_lines.append((i, line))

    print(f"\n📊 BALANCE SECTION LINES ({len(balance_section_lines)} lines):")
    for line_num, line in balance_section_lines[:20]:  # Show first 20 lines
        print(f"  {line_num:3}: {line.strip()}")

    # Step 2: Extract tables to see structure
    print("\n📋 EXTRACTING TABLES...")
    tables = extractor.extract_tables(pdf_path)

    print(f"Found {len(tables)} page(s) with tables")

    for page_idx, page_tables in enumerate(tables):
        print(f"\nPage {page_idx + 1}: {len(page_tables)} tables")

        for table_idx, table in enumerate(page_tables):
            if len(table) > 0:
                print(f"  Table {table_idx + 1}: {len(table)} rows x {len(table[0]) if table else 0} columns")

                # Show header
                if table:
                    print(f"    Header: {table[0]}")

                # Show first few data rows
                print("    Sample rows:")
                for row_idx, row in enumerate(table[1:6]):  # Show first 5 data rows
                    print(f"      Row {row_idx + 1}: {row}")

                # Look for problematic patterns
                print("    Analysis:")
                for row_idx, row in enumerate(table[1:]):
                    if len(row) >= 2:
                        # Check if this could be a balance entry
                        potential_date = str(row[0]).strip() if row[0] else ""
                        potential_amount = str(row[1]).strip() if row[1] else ""

                        # Look for large amounts that might be balances
                        try:
                            amount_clean = potential_amount.replace('$', '').replace(',', '')
                            if amount_clean and float(amount_clean) > 50000:  # Large amounts
                                print(f"      ⚠️  Large amount in row {row_idx + 1}: {potential_date} | {potential_amount}")
                        except:
                            pass

                        # Look for balance-like descriptions
                        row_text = ' '.join(str(cell) for cell in row).lower()
                        if any(keyword in row_text for keyword in ['balance', 'total', 'summary']):
                            print(f"      ⚠️  Balance-like row {row_idx + 1}: {row}")

    # Step 3: Parse transactions and analyze
    print("\n💰 PARSING TRANSACTIONS...")
    transactions = extractor.parse_transactions(pdf_path)

    print(f"Parsed {len(transactions)} transactions")

    # Analyze transactions for potential balance entries
    print("\n🚨 ANALYZING TRANSACTIONS FOR BALANCE ENTRIES...")

    large_transactions = []
    suspicious_descriptions = []

    for i, tx in enumerate(transactions):
        amount = tx.get('amount', 0)
        description = tx.get('description', '')
        date_str = tx.get('raw_date', '')

        # Flag large amounts (likely balances)
        if amount > 50000:
            large_transactions.append((i, tx))

        # Flag suspicious descriptions
        desc_lower = description.lower()
        if any(keyword in desc_lower for keyword in ['balance', 'total', 'summary', 'daily']):
            suspicious_descriptions.append((i, tx))

    print(f"\n⚠️  LARGE TRANSACTIONS (possibly balances): {len(large_transactions)}")
    for i, tx in large_transactions[:10]:  # Show first 10
        print(f"  {i+1:2}. {tx['raw_date']:10} | ${tx['amount']:>10,.2f} | {tx['description'][:50]}")

    print(f"\n⚠️  SUSPICIOUS DESCRIPTIONS: {len(suspicious_descriptions)}")
    for i, tx in suspicious_descriptions[:10]:  # Show first 10
        print(f"  {i+1:2}. {tx['raw_date']:10} | ${tx['amount']:>10,.2f} | {tx['description'][:50]}")

    # Step 4: Show specific problematic transaction
    print(f"\n🔍 LOOKING FOR THE SPECIFIC PROBLEMATIC TRANSACTION...")
    for i, tx in enumerate(transactions):
        if abs(tx.get('amount', 0) - 81266.19) < 0.01:  # Match the amount mentioned
            print(f"Found matching transaction at index {i}:")
            print(f"  Date: {tx.get('raw_date')}")
            print(f"  Amount: ${tx.get('amount'):.2f}")
            print(f"  Description: {tx.get('description')}")
            print(f"  Raw data: {tx}")
            break

    return transactions

if __name__ == "__main__":
    transactions = debug_pdf_parsing()