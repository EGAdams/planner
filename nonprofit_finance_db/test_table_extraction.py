#!/usr/bin/env python3
"""
Test script to examine table data in Docling document
"""

from docling.document_converter import DocumentConverter

def test_table_extraction(pdf_path: str):
    """Test table extraction from Docling document."""

    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    document = result.document

    print(f"Number of tables found: {len(document.tables)}")

    for i, table in enumerate(document.tables):
        print(f"\n=== TABLE {i} ===")
        print(f"Table type: {type(table)}")
        print(f"Table attributes: {[attr for attr in dir(table) if not attr.startswith('_')]}")

        # Try to get table data
        if hasattr(table, 'data'):
            print(f"Has data: {table.data is not None}")
            if table.data:
                print(f"Data type: {type(table.data)}")
                print(f"Data attributes: {[attr for attr in dir(table.data) if not attr.startswith('_')]}")

                if hasattr(table.data, 'table'):
                    print(f"Table data type: {type(table.data.table)}")
                    print(f"Table data attributes: {[attr for attr in dir(table.data.table) if not attr.startswith('_')]}")

                    # Try to access table cells
                    if hasattr(table.data, 'table_cells'):
                        print(f"Table cells type: {type(table.data.table_cells)}")
                        print(f"Number of rows: {len(table.data.table_cells)}")

                        # Show first few rows
                        for row_idx, row in enumerate(table.data.table_cells[:3]):
                            print(f"  Row {row_idx}: {[cell.text if hasattr(cell, 'text') else str(cell) for cell in row]}")

                    # Try export_to_dataframe method
                    try:
                        df = table.export_to_dataframe()
                        print(f"DataFrame shape: {df.shape}")
                        print(f"DataFrame columns: {list(df.columns)}")
                        if not df.empty:
                            print(f"First few rows:\n{df.head(3)}")
                    except Exception as e:
                        print(f"DataFrame export failed: {e}")

                    # Try alternative access methods
                    if hasattr(table.data.table, 'grid'):
                        print(f"Table grid: {table.data.table.grid}")

        # Try to get text content
        if hasattr(table, 'text'):
            print(f"Table text preview: {table.text[:200] if table.text else 'No text'}")

if __name__ == "__main__":
    pdf_path = "/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf"
    test_table_extraction(pdf_path)