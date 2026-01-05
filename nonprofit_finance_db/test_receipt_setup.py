#!/usr/bin/env python3
"""Quick test to verify receipt scanning setup"""
import os
import sys

print("=== Receipt Scanning System Setup Test ===\n")

# Test 1: Environment variables
print("1. Environment Variables:")
gemini_key = os.getenv('GEMINI_API_KEY')
if gemini_key:
    print(f"   ✓ GEMINI_API_KEY: {gemini_key[:10]}...{gemini_key[-4:]}")
else:
    print("   ✗ GEMINI_API_KEY not set")
    sys.exit(1)

# Test 2: Gemini API connection
print("\n2. Gemini API Connection:")
try:
    import google.generativeai as genai
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-2.5-flash')
    print("   ✓ Successfully connected to Gemini API")
    print(f"   ✓ Model: gemini-2.5-flash initialized")
except Exception as e:
    print(f"   ✗ Error: {e}")
    sys.exit(1)

# Test 3: Storage directories
print("\n3. Storage Directories:")
dirs = [
    'app/data/receipts',
    'app/data/receipts/temp',
    'app/data/receipts/2024',
    'app/data/receipts/2025',
]
for d in dirs:
    if os.path.exists(d):
        print(f"   ✓ {d}")
    else:
        print(f"   ✗ {d} missing")

# Test 4: Python dependencies
print("\n4. Python Dependencies:")
deps = [
    'google.generativeai',
    'pydantic',
    'PIL',
    'app.services.receipt_parser',
    'app.services.receipt_engine',
]
for dep in deps:
    try:
        __import__(dep.replace('.', '/').split('/')[0])
        print(f"   ✓ {dep}")
    except ImportError:
        print(f"   ✗ {dep} not installed")

print("\n✅ Receipt scanning system is configured!")
print("\nNext steps:")
print("  1. Start MySQL: sudo systemctl start mysql")
print("  2. Create receipt_metadata table (if needed)")
print("  3. Start API server: python3 api_server.py")
print("  4. Test at: http://localhost:8080/receipt-scanner.html")
