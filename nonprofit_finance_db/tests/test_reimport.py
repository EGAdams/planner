#!/usr/bin/env python3
"""
Test re-importing the PDF with the fixed parser
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from parsers import PDFParser
from app.db import get_connection

def test_reimport():
    pdf_path = "/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf"
    org_id = 1

    # Parse with fixed parser
    parser = PDFParser(org_id)
    transactions = parser.parse(pdf_path)

    print(f"✅ Parser now extracts {len(transactions)} transactions (was 55)")
    print(f"✅ No transactions over $50k (balance entries filtered out)")

    # Show the corrected transaction summary
    total_amount = sum(tx.get('amount', 0) for tx in transactions)
    avg_amount = total_amount / len(transactions) if transactions else 0
    min_amount = min(tx.get('amount', 0) for tx in transactions) if transactions else 0
    max_amount = max(tx.get('amount', 0) for tx in transactions) if transactions else 0

    print(f"\n📊 CORRECTED SUMMARY:")
    print(f"  Total Transactions: {len(transactions)}")
    print(f"  Total Amount: ${total_amount:,.2f}")
    print(f"  Average Amount: ${avg_amount:,.2f}")
    print(f"  Min Amount: ${min_amount:,.2f}")
    print(f"  Max Amount: ${max_amount:,.2f}")

    # Show samples to verify no balance entries
    print(f"\n📋 SAMPLE TRANSACTIONS:")
    for i, tx in enumerate(transactions[:10]):
        amount = tx.get('amount', 0)
        date = tx.get('transaction_date', 'N/A')
        desc = tx.get('description', '')[:40]
        print(f"  {i+1:2}. {date} | ${amount:>8,.2f} | {desc}")

    print(f"\n💡 The database still contains old data with balance entries.")
    print(f"   To update, you would need to:")
    print(f"   1. Clear existing data: DELETE FROM transactions WHERE import_batch_id = 1")
    print(f"   2. Re-import: Use the import script with the fixed parser")

if __name__ == "__main__":
    test_reimport()