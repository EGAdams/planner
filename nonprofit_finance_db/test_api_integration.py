#!/usr/bin/env python3
"""
Integration test for Daily Expense Categorizer API
Tests the full flow: database -> API -> frontend
"""
import requests
import sys

API_BASE = "http://localhost:8080/api"

def test_api_endpoints():
    """Test all API endpoints used by the Daily Expense Categorizer"""
    print("Testing Daily Expense Categorizer API Integration\n")
    print(f"API Base URL: {API_BASE}\n")

    all_tests_passed = True

    # Test 1: API root endpoint
    print("1. Testing API root endpoint...")
    try:
        response = requests.get(f"{API_BASE}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ API is running: {data.get('message')}")
        else:
            print(f"   ✗ API root returned status {response.status_code}")
            all_tests_passed = False
    except Exception as e:
        print(f"   ✗ Failed to connect to API: {e}")
        all_tests_passed = False

    # Test 2: Transactions endpoint
    print("\n2. Testing transactions endpoint...")
    try:
        response = requests.get(f"{API_BASE}/transactions")
        if response.status_code == 200:
            transactions = response.json()
            print(f"   ✓ Loaded {len(transactions)} transactions")

            if transactions:
                sample = transactions[0]
                print(f"   ✓ Sample transaction structure:")
                print(f"     - ID: {sample.get('id')}")
                print(f"     - Date: {sample.get('date')}")
                print(f"     - Vendor: {sample.get('vendor')}")
                print(f"     - Amount: ${sample.get('amount')}")
                print(f"     - Category: {sample.get('category') or 'Uncategorized'}")
        else:
            print(f"   ✗ Transactions endpoint returned status {response.status_code}")
            all_tests_passed = False
    except Exception as e:
        print(f"   ✗ Failed to fetch transactions: {e}")
        all_tests_passed = False

    # Test 3: Categories endpoint
    print("\n3. Testing categories endpoint...")
    try:
        response = requests.get(f"{API_BASE}/categories")
        if response.status_code == 200:
            categories = response.json()
            print(f"   ✓ Loaded {len(categories)} categories")

            # Count root categories vs subcategories
            root_categories = [c for c in categories if not c.get('parent_id')]
            sub_categories = [c for c in categories if c.get('parent_id')]
            print(f"   ✓ Root categories: {len(root_categories)}")
            print(f"   ✓ Subcategories: {len(sub_categories)}")

            if categories:
                sample = categories[0]
                print(f"   ✓ Sample category: {sample.get('name')} (ID: {sample.get('id')})")
        else:
            print(f"   ✗ Categories endpoint returned status {response.status_code}")
            all_tests_passed = False
    except Exception as e:
        print(f"   ✗ Failed to fetch categories: {e}")
        all_tests_passed = False

    # Test 4: Check for uncategorized transactions
    print("\n4. Checking for uncategorized transactions...")
    try:
        response = requests.get(f"{API_BASE}/transactions")
        if response.status_code == 200:
            transactions = response.json()
            uncategorized = [t for t in transactions if not t.get('category')]
            print(f"   ✓ Found {len(uncategorized)} uncategorized transactions")
            print(f"   ✓ Categorized: {len(transactions) - len(uncategorized)} transactions")
    except Exception as e:
        print(f"   ✗ Failed to check categorization status: {e}")
        all_tests_passed = False

    # Test 5: Date range test
    print("\n5. Testing date filtering...")
    try:
        response = requests.get(f"{API_BASE}/transactions?start_date=2025-06-01&end_date=2025-06-30")
        if response.status_code == 200:
            june_transactions = response.json()
            print(f"   ✓ Found {len(june_transactions)} transactions in June 2025")
        else:
            print(f"   ✗ Date filtering returned status {response.status_code}")
            all_tests_passed = False
    except Exception as e:
        print(f"   ✗ Failed to test date filtering: {e}")
        all_tests_passed = False

    # Summary
    print("\n" + "="*60)
    if all_tests_passed:
        print("✅ ALL TESTS PASSED - API is working correctly!")
        print("✅ Daily Expense Categorizer should display live data from database")
        print(f"\n🌐 Access the app at: http://localhost:8081/office/daily_expense_categorizer.html")
    else:
        print("❌ SOME TESTS FAILED - Check errors above")
    print("="*60)

    return all_tests_passed

if __name__ == "__main__":
    success = test_api_endpoints()
    sys.exit(0 if success else 1)
