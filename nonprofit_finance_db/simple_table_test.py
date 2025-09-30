#!/usr/bin/env python3
"""
Simple test to see actual table content
"""

from docling.document_converter import DocumentConverter

def simple_table_test(pdf_path: str):
    """Simple table test."""
    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    document = result.document

    print(f"Found {len(document.tables)} tables")

    for i, table in enumerate(document.tables):
        print(f"\n=== TABLE {i} ===")

        # Try the export_to_dataframe method directly
        try:
            import pandas as pd
            df = table.export_to_dataframe()
            print(f"DataFrame shape: {df.shape}")
            print(f"DataFrame:\n{df}")

            # If this table has transaction-like data, print it
            if df.shape[1] >= 3 and df.shape[0] > 1:  # At least 3 columns and more than header
                print(f"*** Potential transaction table ***")

        except Exception as e:
            print(f"DataFrame export failed: {e}")

        # Try markdown export
        try:
            markdown = table.export_to_markdown()
            print(f"Markdown length: {len(markdown)}")
            if len(markdown) > 50:  # If there's substantial content
                print(f"Markdown preview:\n{markdown[:500]}")
        except Exception as e:
            print(f"Markdown export failed: {e}")

if __name__ == "__main__":
    pdf_path = "/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf"
    simple_table_test(pdf_path)