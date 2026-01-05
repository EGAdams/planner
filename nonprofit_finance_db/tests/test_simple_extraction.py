#!/usr/bin/env python3
"""
Simple test to extract transactions directly without complex parsing
"""

from docling.document_converter import DocumentConverter
import pandas as pd
import re
from datetime import datetime, date

def simple_transaction_extraction(pdf_path: str):
    """Extract transactions using simple logic."""

    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    document = result.document

    print(f"Found {len(document.tables)} tables")

    all_transactions = []

    # Date pattern
    DATE_MD = re.compile(r'^(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?$')

    for i, table in enumerate(document.tables):
        try:
            df = table.export_to_dataframe(document)
            print(f"\n=== TABLE {i} ===")
            print(f"Shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")

            # Check if this looks like a transaction table
            header_text = ' '.join(df.columns).lower()
            is_transaction_table = any(
                keyword in header_text
                for keyword in ['date', 'amount', 'description', 'withdrawal', 'deposit', 'debit', 'credit']
            )

            if is_transaction_table and df.shape[0] > 1:
                print(f"*** Processing transaction table ***")

                for idx, row in df.iterrows():
                    row_data = [str(cell) for cell in row]
                    print(f"Row {idx}: {row_data}")

                    # Simple extraction: look for date and amount
                    date_found = None
                    amount_found = None
                    desc_parts = []

                    for cell in row_data:
                        cell = str(cell).strip()

                        # Check for date
                        if DATE_MD.match(cell):
                            date_found = cell

                        # Check for amount (simple pattern)
                        elif re.match(r'^\d+\.\d{2}$', cell):
                            amount_found = cell

                        # Everything else is description
                        elif cell and cell != 'nan':
                            desc_parts.append(cell)

                    if date_found and amount_found:
                        transaction = {
                            'date': date_found,
                            'amount': float(amount_found),
                            'description': ' '.join(desc_parts),
                            'table_index': i
                        }
                        all_transactions.append(transaction)
                        print(f"  -> Extracted: {transaction}")

        except Exception as e:
            print(f"Error processing table {i}: {e}")

    print(f"\n=== SUMMARY ===")
    print(f"Total transactions extracted: {len(all_transactions)}")
    for txn in all_transactions[:5]:  # Show first 5
        print(f"  {txn['date']} | ${txn['amount']} | {txn['description'][:50]}")

if __name__ == "__main__":
    pdf_path = "/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf"
    simple_transaction_extraction(pdf_path)