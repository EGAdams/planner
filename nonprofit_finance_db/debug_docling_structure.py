#!/usr/bin/env python3
"""
Debug script to understand Docling document structure
"""

from docling.document_converter import DocumentConverter
import json

def debug_document_structure(pdf_path: str):
    """Debug the structure of a Docling document."""

    converter = DocumentConverter()
    result = converter.convert(pdf_path)
    document = result.document

    print("=== DOCUMENT STRUCTURE DEBUG ===")
    print(f"Document type: {type(document)}")
    print(f"Document attributes: {dir(document)}")

    # Check what pages actually contains
    print(f"Pages type: {type(document.pages)}")
    print(f"Number of pages: {len(document.pages)}")
    print(f"Pages content: {document.pages}")

    # Check for elements directly on document
    if hasattr(document, 'elements'):
        print(f"\nDocument has elements: {len(document.elements)}")
        for j, element in enumerate(document.elements):
            print(f"  Element {j}: {type(element)} - Label: {getattr(element, 'label', 'No label')}")

            # Check if it's a table
            if hasattr(element, 'label') and element.label == "Table":
                print(f"    Table element details:")
                print(f"    Has data attribute: {hasattr(element, 'data')}")
                if hasattr(element, 'data') and element.data:
                    print(f"    Data type: {type(element.data)}")
                    print(f"    Data attributes: {dir(element.data)}")
                    if hasattr(element.data, 'table'):
                        print(f"    Table type: {type(element.data.table)}")
                        print(f"    Table attributes: {dir(element.data.table)}")

            # Show first few characters of text if available
            if hasattr(element, 'text'):
                text_preview = element.text[:100] if element.text else "No text"
                print(f"    Text preview: {text_preview}")

    # Try to understand page structure better
    for i, page_id in enumerate(document.pages):
        print(f"\n--- Page {i+1} (ID: {page_id}) ---")
        # Maybe pages are accessed differently?
        if hasattr(document, 'page_by_id'):
            try:
                page = document.page_by_id(page_id)
                print(f"Page type: {type(page)}")
                if hasattr(page, 'elements'):
                    print(f"Number of elements: {len(page.elements)}")
            except Exception as e:
                print(f"Error accessing page: {e}")

        # Or maybe pages are accessed by index?
        try:
            page = document.pages[i]
            print(f"Page by index type: {type(page)}")
        except Exception as e:
            print(f"Error accessing page by index: {e}")

    # Export structure for inspection
    print("\n=== EXPORT METHODS ===")

    # Try markdown export
    try:
        markdown = document.export_to_markdown()
        print(f"Markdown export length: {len(markdown)}")
        print("First 500 chars of markdown:")
        print(markdown[:500])
    except Exception as e:
        print(f"Markdown export failed: {e}")

    # Try JSON export
    try:
        json_data = document.export_to_dict()
        print(f"\nJSON export keys: {list(json_data.keys())}")

        # Save to file for inspection
        with open('/tmp/claude/document_structure.json', 'w') as f:
            json.dump(json_data, f, indent=2, default=str)
        print("JSON structure saved to /tmp/claude/document_structure.json")

    except Exception as e:
        print(f"JSON export failed: {e}")

if __name__ == "__main__":
    pdf_path = "/mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf"
    debug_document_structure(pdf_path)