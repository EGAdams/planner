#!/usr/bin/env python3
"""
Test script to verify the Docling PDF extraction migration

This script demonstrates that:
1. Old PDF parsing libraries (PyPDF2, pdfplumber) have been removed
2. New PDF extractor structure is in place
3. System architecture is correct
"""

import sys
import os
from pathlib import Path

def test_old_libraries_removed():
    """Test that old PDF libraries are no longer available"""
    print("Testing old PDF library removal...")

    try:
        import PyPDF2
        print("❌ FAIL: PyPDF2 is still available")
        return False
    except ImportError:
        print("✅ PASS: PyPDF2 successfully removed")

    try:
        import pdfplumber
        print("❌ FAIL: pdfplumber is still available")
        return False
    except ImportError:
        print("✅ PASS: pdfplumber successfully removed")

    return True

def test_new_structure():
    """Test that new PDF extractor structure exists"""
    print("\nTesting new PDF extractor structure...")

    # Check if pdf_extractor directory exists
    pdf_extractor_dir = Path(__file__).parent / "pdf_extractor"
    if not pdf_extractor_dir.exists():
        print("❌ FAIL: pdf_extractor directory not found")
        return False
    print("✅ PASS: pdf_extractor directory exists")

    # Check if __init__.py exists
    init_file = pdf_extractor_dir / "__init__.py"
    if not init_file.exists():
        print("❌ FAIL: pdf_extractor/__init__.py not found")
        return False
    print("✅ PASS: pdf_extractor/__init__.py exists")

    # Check if docling_extractor.py exists
    extractor_file = pdf_extractor_dir / "docling_extractor.py"
    if not extractor_file.exists():
        print("❌ FAIL: pdf_extractor/docling_extractor.py not found")
        return False
    print("✅ PASS: pdf_extractor/docling_extractor.py exists")

    return True

def test_parser_structure():
    """Test that parser structure is correct"""
    print("\nTesting parser structure...")

    # Check if new pdf_parser.py exists
    parser_file = Path(__file__).parent / "parsers" / "pdf_parser.py"
    if not parser_file.exists():
        print("❌ FAIL: parsers/pdf_parser.py not found")
        return False
    print("✅ PASS: parsers/pdf_parser.py exists")

    # Check content of the parser file
    try:
        with open(parser_file, 'r') as f:
            content = f.read()

        if "DoclingPDFExtractor" not in content:
            print("❌ FAIL: pdf_parser.py doesn't import DoclingPDFExtractor")
            return False
        print("✅ PASS: pdf_parser.py imports DoclingPDFExtractor")

        if "pdfplumber" in content or "PyPDF2" in content:
            print("❌ FAIL: pdf_parser.py still references old libraries")
            return False
        print("✅ PASS: pdf_parser.py doesn't reference old libraries")

    except Exception as e:
        print(f"❌ FAIL: Error reading pdf_parser.py: {e}")
        return False

    return True

def test_requirements():
    """Test that requirements.txt has been updated"""
    print("\nTesting requirements.txt...")

    req_file = Path(__file__).parent / "requirements.txt"
    if not req_file.exists():
        print("❌ FAIL: requirements.txt not found")
        return False

    try:
        with open(req_file, 'r') as f:
            content = f.read()

        if "PyPDF2" in content:
            print("❌ FAIL: requirements.txt still contains PyPDF2")
            return False
        print("✅ PASS: PyPDF2 removed from requirements.txt")

        if "pdfplumber" in content:
            print("❌ FAIL: requirements.txt still contains pdfplumber")
            return False
        print("✅ PASS: pdfplumber removed from requirements.txt")

        if "docling" not in content:
            print("❌ FAIL: requirements.txt doesn't contain docling")
            return False
        print("✅ PASS: docling added to requirements.txt")

    except Exception as e:
        print(f"❌ FAIL: Error reading requirements.txt: {e}")
        return False

    return True

def test_imports():
    """Test basic import structure (without Docling dependencies)"""
    print("\nTesting import structure...")

    # Test that we can import the base parser structure
    sys.path.insert(0, str(Path(__file__).parent))

    try:
        from parsers.base_parser import BaseParser
        print("✅ PASS: BaseParser import successful")
    except Exception as e:
        print(f"❌ FAIL: BaseParser import failed: {e}")
        return False

    try:
        from parsers.csv_parser import CSVParser
        print("✅ PASS: CSVParser import successful")
    except Exception as e:
        print(f"❌ FAIL: CSVParser import failed: {e}")
        return False

    # Note: PDFParser will fail without Docling dependencies, but that's expected
    print("ℹ️  INFO: PDFParser import will fail without Docling dependencies (expected)")

    return True

def main():
    """Run all tests"""
    print("🚀 Starting Docling Migration Test Suite")
    print("=" * 50)

    tests = [
        test_old_libraries_removed,
        test_new_structure,
        test_parser_structure,
        test_requirements,
        test_imports
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print("=" * 50)
    print(f"📊 TEST RESULTS: {passed}/{total} test suites passed")

    if passed == total:
        print("🎉 SUCCESS: All tests passed! Migration structure is complete.")
        print("📝 NOTE: Full functionality requires Docling dependencies to be installed.")
        return True
    else:
        print("❌ FAILURE: Some tests failed. Please review the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)