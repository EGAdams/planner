#!/usr/bin/env python3
"""
Enhanced PDF debugging script to understand structure and table detection
"""
import sys
import pdfplumber
import json
from pathlib import Path

def debug_pdf_structure(pdf_path: str):
    """Debug PDF structure and content extraction"""
    print(f"\n{'='*60}")
    print(f"DETAILED PDF STRUCTURE ANALYSIS")
    print(f"{'='*60}")
    print(f"File: {pdf_path}")

    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"\nTotal pages: {len(pdf.pages)}")

            for page_num, page in enumerate(pdf.pages):
                print(f"\n{'-'*40}")
                print(f"PAGE {page_num + 1}")
                print(f"{'-'*40}")

                # Page dimensions
                print(f"Page size: {page.width} x {page.height}")

                # Raw text
                text = page.extract_text()
                if text:
                    print(f"\nRAW TEXT ({len(text)} chars):")
                    print("=" * 30)
                    lines = text.split('\n')
                    for i, line in enumerate(lines[:20], 1):  # First 20 lines
                        print(f"{i:2d}: {line}")
                    if len(lines) > 20:
                        print(f"... ({len(lines) - 20} more lines)")
                else:
                    print("\nNO TEXT EXTRACTED")

                # Table extraction
                tables = page.extract_tables()
                print(f"\nTABLES DETECTED: {len(tables)}")

                for table_idx, table in enumerate(tables):
                    print(f"\n  Table {table_idx + 1}:")
                    print(f"  Rows: {len(table)}")
                    if table:
                        print(f"  Columns in first row: {len(table[0]) if table[0] else 0}")

                        # Show first few rows
                        for row_idx, row in enumerate(table[:5]):
                            print(f"    Row {row_idx + 1}: {row}")

                        if len(table) > 5:
                            print(f"    ... ({len(table) - 5} more rows)")

                # Objects on page
                objects = page.objects
                print(f"\nPAGE OBJECTS:")
                for obj_type in ['char', 'line', 'rect', 'curve']:
                    if obj_type in objects:
                        count = len(objects[obj_type])
                        print(f"  {obj_type}: {count}")

                # Try different table extraction settings
                print(f"\nTABLE EXTRACTION WITH DIFFERENT SETTINGS:")

                # Default settings
                default_tables = page.extract_tables()
                print(f"  Default: {len(default_tables)} tables")

                # With explicit lines
                line_tables = page.extract_tables(table_settings={
                    "vertical_strategy": "lines",
                    "horizontal_strategy": "lines"
                })
                print(f"  Lines strategy: {len(line_tables)} tables")

                # With text strategy
                text_tables = page.extract_tables(table_settings={
                    "vertical_strategy": "text",
                    "horizontal_strategy": "text"
                })
                print(f"  Text strategy: {len(text_tables)} tables")

                # Find potential table areas based on text patterns
                print(f"\nTEXT ANALYSIS FOR POTENTIAL TRANSACTIONS:")
                if text:
                    lines = text.split('\n')
                    date_lines = []
                    amount_lines = []

                    import re

                    for i, line in enumerate(lines):
                        # Look for dates
                        if re.search(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}', line):
                            date_lines.append((i, line.strip()))

                        # Look for monetary amounts
                        if re.search(r'\$\d+\.\d{2}|\d+\.\d{2}', line):
                            amount_lines.append((i, line.strip()))

                    print(f"  Lines with dates: {len(date_lines)}")
                    for line_num, line in date_lines[:5]:
                        print(f"    {line_num}: {line}")

                    print(f"  Lines with amounts: {len(amount_lines)}")
                    for line_num, line in amount_lines[:5]:
                        print(f"    {line_num}: {line}")

                print(f"\n{'='*40}")

    except Exception as e:
        print(f"Error analyzing PDF: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python debug_pdf_detailed.py <pdf_file>")
        sys.exit(1)

    pdf_path = sys.argv[1]
    if not Path(pdf_path).exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    debug_pdf_structure(pdf_path)

if __name__ == "__main__":
    main()