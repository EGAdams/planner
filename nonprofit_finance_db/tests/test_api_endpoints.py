#!/usr/bin/env python3
"""
TDD Test Suite for Daily Expense Categorizer API
Tests the /api/transactions endpoints that the frontend expects
"""
import pytest
import requests
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

API_BASE = "http://localhost:8080/api"

class TestAPIEndpoints:
    """Test suite for API endpoints used by daily_expense_categorizer.html"""

    def test_api_root_responds(self):
        """Test that /api endpoint responds with 200"""
        response = requests.get(f"{API_BASE}")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "running"

    def test_transactions_endpoint_exists(self):
        """Test GET /api/transactions endpoint responds with 200"""
        response = requests.get(f"{API_BASE}/transactions")
        assert response.status_code == 200, \
            f"Expected 200 but got {response.status_code}. Frontend expects /api/transactions endpoint."

    def test_transactions_returns_list(self):
        """Test that /api/transactions returns a list of transactions"""
        response = requests.get(f"{API_BASE}/transactions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Expected a list of transactions"

    def test_categories_endpoint_exists(self):
        """Test GET /api/categories endpoint responds with 200"""
        response = requests.get(f"{API_BASE}/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Expected a list of categories"

    def test_update_transaction_category_endpoint(self):
        """Test PUT /api/transactions/{id}/category endpoint exists and accepts updates"""
        # First get a transaction to update
        response = requests.get(f"{API_BASE}/transactions")
        assert response.status_code == 200
        transactions = response.json()

        if len(transactions) > 0:
            transaction_id = transactions[0]["id"]

            # Try to update the category (we'll use category_id=None which is valid)
            update_response = requests.put(
                f"{API_BASE}/transactions/{transaction_id}/category",
                json={"category_id": None}
            )

            # Should accept the update (200 or 204)
            assert update_response.status_code in [200, 204], \
                f"Expected 200/204 but got {update_response.status_code}. Frontend expects PUT /api/transactions/{{id}}/category"
        else:
            pytest.skip("No transactions available to test update endpoint")

    def test_cors_headers_configured(self):
        """Test that CORS headers are configured correctly"""
        response = requests.options(f"{API_BASE}/transactions")
        # FastAPI returns 200 for OPTIONS with CORS enabled
        assert response.status_code in [200, 204]

if __name__ == "__main__":
    print("Running TDD Test Suite - RED PHASE (Tests should FAIL)")
    print("=" * 60)
    pytest.main([__file__, "-v", "--tb=short"])
