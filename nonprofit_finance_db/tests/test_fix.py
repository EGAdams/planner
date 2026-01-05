#!/usr/bin/env python3
"""
Quick test to verify the balance filtering fix
"""

import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from parsers import PDFParser

def test_fix():
    parser = PDFParser(1)
    transactions = parser.parse('/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf')

    print(f'Total transactions: {len(transactions)}')

    large_txns = [tx for tx in transactions if tx.get('amount', 0) > 50000]
    print(f'Large transactions (>$50k): {len(large_txns)}')

    for i, tx in enumerate(large_txns):
        print(f'  {i+1}. {tx.get("transaction_date")} | ${tx.get("amount"):,.2f} | {tx.get("description")[:50]}')

    print(f"\nFirst 10 transactions:")
    for i, tx in enumerate(transactions[:10]):
        print(f'  {i+1}. {tx.get("transaction_date")} | ${tx.get("amount"):,.2f} | {tx.get("description")[:30]}')

if __name__ == "__main__":
    test_fix()