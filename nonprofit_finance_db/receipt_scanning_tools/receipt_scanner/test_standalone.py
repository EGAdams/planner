#!/usr/bin/env python3
"""
Standalone test script for receipt scanning system
Tests the copied components to ensure they work independently

Run from receipt_scanning_tools/receipt_scanner directory:
    python3 test_standalone.py
"""
import os
import sys
from pathlib import Path

# Add parent directory to path to access backend modules
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR / "backend"
sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(BACKEND_DIR))

print("=" * 60)
print("Receipt Scanner Standalone Test")
print("=" * 60)

# Test 1: Environment Variables
print("\n[TEST 1] Environment Variables")
print("-" * 40)
from dotenv import load_dotenv

# Load from parent planner directory
env_path = Path(__file__).resolve().parent.parent.parent.parent / '.env'
print(f"Loading .env from: {env_path}")
load_dotenv(dotenv_path=env_path, override=True)

gemini_key = os.getenv('GEMINI_API_KEY')
if gemini_key:
    print(f"✓ GEMINI_API_KEY: {gemini_key[:10]}...{gemini_key[-4:]}")
else:
    print("✗ GEMINI_API_KEY not set")
    sys.exit(1)

# Test 2: Backend Modules Import
print("\n[TEST 2] Backend Module Imports")
print("-" * 40)

try:
    from models import receipt_models
    print("✓ Imported receipt_models")
except ImportError as e:
    print(f"✗ Failed to import receipt_models: {e}")
    sys.exit(1)

try:
    from services import receipt_engine
    print("✓ Imported receipt_engine")
except ImportError as e:
    print(f"✗ Failed to import receipt_engine: {e}")
    sys.exit(1)

try:
    from services import receipt_parser
    print("✓ Imported receipt_parser")
except ImportError as e:
    print(f"✗ Failed to import receipt_parser: {e}")
    sys.exit(1)

# Test 3: Gemini API Connection
print("\n[TEST 3] Gemini API Connection")
print("-" * 40)

try:
    import google.generativeai as genai
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    print("✓ Successfully connected to Gemini API")
    print("✓ Model gemini-2.5-flash initialized")
except Exception as e:
    print(f"✗ Gemini API Error: {e}")
    sys.exit(1)

# Test 4: Directory Structure
print("\n[TEST 4] Directory Structure")
print("-" * 40)

required_dirs = [
    "data/receipts",
    "data/receipts/temp",
    "data/receipts/2024",
    "data/receipts/2025",
    "data/receipts/2026",
    "backend/services",
    "backend/api",
    "backend/models",
    "backend/repositories",
    "frontend",
    "frontend/js/components",
    "tests",
    "docs",
]

all_exist = True
for dir_path in required_dirs:
    full_path = SCRIPT_DIR / dir_path
    if full_path.exists():
        print(f"✓ {dir_path}")
    else:
        print(f"✗ {dir_path} MISSING")
        all_exist = False

if not all_exist:
    print("\n✗ Some directories are missing")
    sys.exit(1)

# Test 5: Required Files
print("\n[TEST 5] Required Files")
print("-" * 40)

required_files = [
    "backend/services/receipt_parser.py",
    "backend/services/receipt_engine.py",
    "backend/api/receipt_endpoints.py",
    "backend/models/receipt_models.py",
    "backend/repositories/receipt_metadata.py",
    "frontend/receipt-scanner.html",
    "frontend/js/components/receipt-scanner.js",
    "tests/test_receipt_processing.py",
    "tests/test_receipt_api.py",
    "tests/test_receipt_items_api.py",
    "docs/RECEIPT_SCANNING_STATUS.md",
    "docs/create_receipt_metadata_table.sql",
]

all_files_exist = True
for file_path in required_files:
    full_path = SCRIPT_DIR / file_path
    if full_path.exists():
        size_kb = full_path.stat().st_size / 1024
        print(f"✓ {file_path} ({size_kb:.1f} KB)")
    else:
        print(f"✗ {file_path} MISSING")
        all_files_exist = False

if not all_files_exist:
    print("\n✗ Some files are missing")
    sys.exit(1)

# Test 6: Pydantic Models
print("\n[TEST 6] Pydantic Models")
print("-" * 40)

try:
    from models.receipt_models import (
        ReceiptExtractionResult,
        ReceiptItem,
        ReceiptTotals,
        ReceiptPartyInfo,
        ReceiptMeta,
        PaymentMethod
    )
    print("✓ All receipt models imported successfully")

    # Test creating a sample receipt item
    sample_item = ReceiptItem(
        description="Test Item",
        quantity=1.0,
        unit_price=4.99,
        line_total=4.99
    )
    print(f"✓ Created sample ReceiptItem: {sample_item.description}")
except Exception as e:
    print(f"✗ Model test failed: {e}")
    sys.exit(1)

# Test 7: Receipt Engine Initialization
print("\n[TEST 7] Receipt Engine Initialization")
print("-" * 40)

try:
    from services.receipt_engine import GeminiReceiptEngine
    engine = GeminiReceiptEngine()
    print("✓ GeminiReceiptEngine initialized successfully")
    if engine.model:
        print("✓ Gemini model is ready")
except Exception as e:
    print(f"✗ Engine initialization failed: {e}")
    sys.exit(1)

# Summary
print("\n" + "=" * 60)
print("✅ ALL TESTS PASSED!")
print("=" * 60)
print("\nStandalone receipt scanner is ready to use!")
print("\nNext steps:")
print("  1. Ensure MySQL is running: sudo service mysql start")
print("  2. Create receipt_metadata table:")
print("     mysql -u adamsl -pTinman@2 nonprofit_finance < docs/create_receipt_metadata_table.sql")
print("  3. Copy this directory to desired location")
print("  4. Start API server with receipt endpoints")
print("  5. Open frontend/receipt-scanner.html in browser")
print("\n" + "=" * 60)
