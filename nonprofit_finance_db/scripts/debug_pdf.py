#!/usr/bin/env python3
"""Debug script to examine PDF structure"""

import sys
import pdfplumber
from pathlib import Path

def clean_spaced_text(text: str) -> str:
    """Clean up spaced-out text common in some PDFs"""
    import re
    lines = text.split('\n')
    cleaned_lines = []

    for line in lines:
        # Find patterns like "C u s to m e r" or "A c c o u n t"
        spaced_pattern = r'\b([A-Za-z]\s+){2,}[A-Za-z]\b'

        def fix_spaced_word(match):
            spaced_word = match.group()
            return re.sub(r'\s+', '', spaced_word)

        cleaned_line = re.sub(spaced_pattern, fix_spaced_word, line)

        # Fix spaced numbers like "8 0 0 -9 7 2 -3 0 3 0"
        number_pattern = r'\b(\d\s+){3,}\d\b'

        def fix_spaced_number(match):
            spaced_number = match.group()
            return re.sub(r'\s+(?=\d)', '', spaced_number)

        cleaned_line = re.sub(number_pattern, fix_spaced_number, cleaned_line)
        cleaned_lines.append(cleaned_line)

    return '\n'.join(cleaned_lines)

def debug_pdf_structure(pdf_path: str):
    """Debug PDF structure to understand layout"""
    print(f"Analyzing PDF: {pdf_path}")

    with pdfplumber.open(pdf_path) as pdf:
        print(f"Total pages: {len(pdf.pages)}")

        for page_num, page in enumerate(pdf.pages):
            print(f"\n{'='*60}")
            print(f"PAGE {page_num + 1}")
            print(f"{'='*60}")

            # Extract tables
            tables = page.extract_tables()
            print(f"Tables found: {len(tables)}")

            if tables:
                for table_num, table in enumerate(tables):
                    print(f"\nTable {table_num + 1}:")
                    print(f"Rows: {len(table)}")
                    print(f"Columns: {len(table[0]) if table else 0}")

                    # Show first few rows
                    print("First 5 rows:")
                    for i, row in enumerate(table[:5]):
                        print(f"  Row {i+1}: {row}")

                    if len(table) > 5:
                        print(f"  ... and {len(table) - 5} more rows")

            # Extract raw text
            text = page.extract_text()
            if text:
                lines = text.split('\n')
                print(f"\nText lines: {len(lines)}")
                print("First 20 lines (original):")
                for i, line in enumerate(lines[:20]):
                    if line.strip():
                        print(f"  {i+1:2d}: {line}")

                if len(lines) > 20:
                    print(f"  ... and {len(lines) - 20} more lines")

                # Show cleaned text
                cleaned_text = clean_spaced_text(text)
                cleaned_lines = cleaned_text.split('\n')
                print(f"\nCleaned text (first 20 lines):")
                for i, line in enumerate(cleaned_lines[:20]):
                    if line.strip():
                        print(f"  {i+1:2d}: {line}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_pdf.py <pdf_path>")
        sys.exit(1)

    debug_pdf_structure(sys.argv[1])