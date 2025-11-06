#!/usr/bin/env python3
"""
TDD Test Suite for Daily Expense Categorizer API Connectivity Issues

PHASE 1 - RED: Tests written first to expose connectivity problems
PHASE 2 - GREEN: Fixes implemented to make tests pass
PHASE 3 - REFACTOR: Improvements to robustness and error handling

This test suite focuses on:
1. API server accessibility on port 8080
2. Database connectivity
3. CORS configuration for frontend
4. Category update functionality
5. Error handling and fallback behavior
6. Health checks and monitoring
"""

import pytest
import requests
import time
import sys
from pathlib import Path
from typing import Dict, Any
import mysql.connector
from unittest.mock import patch, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_connection, query_one, query_all, execute
from app.config import settings


# ============================================================================
# CONFIGURATION
# ============================================================================

API_BASE_URL = "http://localhost:8080"
API_TIMEOUT = 10  # seconds


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def api_server_url():
    """Return the base URL for the API server"""
    return API_BASE_URL


@pytest.fixture(scope="session")
def wait_for_api_server(api_server_url):
    """
    Wait for API server to be available before running tests
    Maximum wait time: 30 seconds
    """
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{api_server_url}/api", timeout=2)
            if response.status_code == 200:
                print(f"\nAPI server is ready at {api_server_url}")
                return True
        except requests.exceptions.RequestException:
            pass

        if attempt < max_attempts - 1:
            time.sleep(1)

    pytest.fail(f"API server not available at {api_server_url} after {max_attempts} seconds")


@pytest.fixture
def db_connection():
    """
    Fixture to provide a database connection for testing
    Tests database connectivity independently
    """
    try:
        conn = get_connection()
        yield conn
        conn.close()
    except Exception as e:
        pytest.fail(f"Failed to connect to database: {e}")


# ============================================================================
# PHASE 1 - RED: API SERVER CONNECTIVITY TESTS
# ============================================================================

class TestAPIServerAvailability:
    """Test that API server is running and accessible"""

    def test_api_server_is_running(self, wait_for_api_server, api_server_url):
        """
        CRITICAL TEST: API server must be running on port 8080
        This addresses: "Connected API at http://localhost:8080/api is unavailable"
        """
        try:
            response = requests.get(f"{api_server_url}/api", timeout=API_TIMEOUT)
            assert response.status_code == 200, \
                f"API server returned {response.status_code} instead of 200"
        except requests.exceptions.ConnectionError as e:
            pytest.fail(f"Cannot connect to API server at {api_server_url}: {e}")
        except requests.exceptions.Timeout:
            pytest.fail(f"API server at {api_server_url} timed out")

    def test_api_root_returns_status(self, wait_for_api_server, api_server_url):
        """Test that API root endpoint returns valid status"""
        response = requests.get(f"{api_server_url}/api", timeout=API_TIMEOUT)
        data = response.json()

        assert "status" in data, "API response missing 'status' field"
        assert data["status"] == "running", f"API status is '{data['status']}', expected 'running'"
        assert "message" in data, "API response missing 'message' field"

    def test_api_server_port_8080(self, wait_for_api_server, api_server_url):
        """Test that API is specifically accessible on port 8080"""
        assert ":8080" in api_server_url or api_server_url.endswith("8080"), \
            "API server must run on port 8080"

        response = requests.get(f"{api_server_url}/api", timeout=API_TIMEOUT)
        assert response.status_code == 200

    def test_api_responds_within_timeout(self, wait_for_api_server, api_server_url):
        """Test that API responds quickly (< 5 seconds)"""
        start_time = time.time()
        response = requests.get(f"{api_server_url}/api", timeout=API_TIMEOUT)
        elapsed_time = time.time() - start_time

        assert response.status_code == 200
        assert elapsed_time < 5.0, \
            f"API took {elapsed_time:.2f}s to respond, should be < 5s"


# ============================================================================
# PHASE 1 - RED: DATABASE CONNECTIVITY TESTS
# ============================================================================

class TestDatabaseConnectivity:
    """Test that database is accessible and properly configured"""

    def test_database_connection_succeeds(self, db_connection):
        """
        CRITICAL TEST: Database must be accessible
        Verifies connection pool is working
        """
        assert db_connection is not None, "Database connection is None"
        assert db_connection.is_connected(), "Database connection is not active"

    def test_database_credentials_configured(self):
        """Test that database credentials are properly configured"""
        assert settings.host, "Database host not configured"
        assert settings.user, "Database user not configured"
        assert settings.password, "Database password not configured"
        assert settings.database, "Database name not configured"

    def test_database_name_correct(self):
        """Test that we're connecting to the correct database"""
        assert settings.database == "nonprofit_finance", \
            f"Expected database 'nonprofit_finance', got '{settings.database}'"

    def test_query_one_works(self):
        """Test that query_one function works correctly"""
        result = query_one("SELECT 1 as test_value")
        assert result is not None, "query_one returned None"
        assert result["test_value"] == 1, "query_one returned wrong value"

    def test_query_all_works(self):
        """Test that query_all function works correctly"""
        results = query_all("SELECT 1 as test_value UNION SELECT 2")
        assert results is not None, "query_all returned None"
        assert len(results) == 2, f"Expected 2 results, got {len(results)}"

    def test_transactions_table_exists(self):
        """Test that transactions table exists and is accessible"""
        result = query_one(
            "SELECT COUNT(*) as count FROM information_schema.tables "
            "WHERE table_schema = %s AND table_name = 'transactions'",
            (settings.database,)
        )
        assert result["count"] == 1, "transactions table does not exist"

    def test_categories_table_exists(self):
        """Test that categories table exists and is accessible"""
        result = query_one(
            "SELECT COUNT(*) as count FROM information_schema.tables "
            "WHERE table_schema = %s AND table_name = 'categories'",
            (settings.database,)
        )
        assert result["count"] == 1, "categories table does not exist"


# ============================================================================
# PHASE 1 - RED: API ENDPOINT LIVE TESTS
# ============================================================================

class TestAPIEndpointsLive:
    """Test that API endpoints work with live database"""

    def test_transactions_endpoint_accessible(self, wait_for_api_server, api_server_url):
        """
        CRITICAL TEST: Transactions endpoint must be accessible
        This addresses: Frontend shows "Showing sample data" message
        """
        response = requests.get(f"{api_server_url}/api/transactions", timeout=API_TIMEOUT)
        assert response.status_code == 200, \
            f"Transactions endpoint returned {response.status_code}"

    def test_transactions_endpoint_returns_json(self, wait_for_api_server, api_server_url):
        """Test that transactions endpoint returns valid JSON"""
        response = requests.get(f"{api_server_url}/api/transactions", timeout=API_TIMEOUT)
        assert response.headers["content-type"] == "application/json", \
            "Transactions endpoint should return JSON"

        data = response.json()
        assert isinstance(data, list), "Transactions endpoint should return a list"

    def test_categories_endpoint_accessible(self, wait_for_api_server, api_server_url):
        """Test that categories endpoint is accessible"""
        response = requests.get(f"{api_server_url}/api/categories", timeout=API_TIMEOUT)
        assert response.status_code == 200, \
            f"Categories endpoint returned {response.status_code}"

    def test_categories_endpoint_returns_data(self, wait_for_api_server, api_server_url):
        """Test that categories endpoint returns category data"""
        response = requests.get(f"{api_server_url}/api/categories", timeout=API_TIMEOUT)
        data = response.json()

        assert isinstance(data, list), "Categories endpoint should return a list"
        # Should have at least some categories
        assert len(data) > 0, "Categories endpoint returned empty list"

        # Verify structure
        if len(data) > 0:
            category = data[0]
            assert "id" in category, "Category missing 'id' field"
            assert "name" in category, "Category missing 'name' field"


# ============================================================================
# PHASE 1 - RED: CATEGORY UPDATE FUNCTIONALITY TESTS
# ============================================================================

class TestCategoryUpdateLive:
    """Test category update functionality with live API"""

    def test_category_update_endpoint_exists(self, wait_for_api_server, api_server_url):
        """
        CRITICAL TEST: Category update endpoint must exist
        This addresses: "Failed to update category: Failed to fetch"
        """
        # Get a test transaction first
        response = requests.get(f"{api_server_url}/api/transactions", timeout=API_TIMEOUT)
        transactions = response.json()

        if len(transactions) == 0:
            pytest.skip("No transactions in database to test update")

        transaction_id = transactions[0]["id"]

        # Attempt to update (we'll test actual update in next test)
        response = requests.put(
            f"{api_server_url}/api/transactions/{transaction_id}/category",
            json={"category_id": None},
            timeout=API_TIMEOUT
        )

        # Should not be 404 (endpoint exists)
        assert response.status_code != 404, \
            "Category update endpoint not found (404)"

        # Should be 200 or another valid response
        assert response.status_code in [200, 400, 422, 500], \
            f"Unexpected status code {response.status_code}"

    def test_category_update_with_valid_data(self, wait_for_api_server, api_server_url):
        """Test that category can be updated successfully"""
        # Get transactions
        response = requests.get(f"{api_server_url}/api/transactions", timeout=API_TIMEOUT)
        transactions = response.json()

        if len(transactions) == 0:
            pytest.skip("No transactions in database to test update")

        transaction_id = transactions[0]["id"]

        # Get categories
        response = requests.get(f"{api_server_url}/api/categories", timeout=API_TIMEOUT)
        categories = response.json()

        if len(categories) == 0:
            pytest.skip("No categories in database to test update")

        category_id = categories[0]["id"]

        # Update category
        response = requests.put(
            f"{api_server_url}/api/transactions/{transaction_id}/category",
            json={"category_id": category_id},
            timeout=API_TIMEOUT
        )

        assert response.status_code == 200, \
            f"Category update failed with status {response.status_code}: {response.text}"

        data = response.json()
        assert "success" in data, "Response missing 'success' field"
        assert data["success"] is True, "Category update reported failure"

    def test_category_update_returns_json(self, wait_for_api_server, api_server_url):
        """Test that category update returns proper JSON response"""
        response = requests.get(f"{api_server_url}/api/transactions", timeout=API_TIMEOUT)
        transactions = response.json()

        if len(transactions) == 0:
            pytest.skip("No transactions in database")

        transaction_id = transactions[0]["id"]

        response = requests.put(
            f"{api_server_url}/api/transactions/{transaction_id}/category",
            json={"category_id": None},
            timeout=API_TIMEOUT
        )

        assert response.headers["content-type"] == "application/json", \
            "Category update should return JSON"


# ============================================================================
# PHASE 1 - RED: CORS CONFIGURATION TESTS
# ============================================================================

class TestCORSConfiguration:
    """Test CORS headers to ensure frontend can access API"""

    def test_cors_headers_present(self, wait_for_api_server, api_server_url):
        """
        CRITICAL TEST: CORS headers must be present for cross-origin requests
        This ensures frontend can access API from different port
        """
        # Make request with Origin header (simulates frontend request)
        headers = {"Origin": "http://localhost:8081"}
        response = requests.get(
            f"{api_server_url}/api/transactions",
            headers=headers,
            timeout=API_TIMEOUT
        )

        # Check for CORS headers
        assert "access-control-allow-origin" in response.headers, \
            "Missing 'Access-Control-Allow-Origin' CORS header"

    def test_cors_allows_all_origins(self, wait_for_api_server, api_server_url):
        """Test that CORS allows requests from any origin"""
        headers = {"Origin": "http://localhost:8081"}
        response = requests.get(
            f"{api_server_url}/api",
            headers=headers,
            timeout=API_TIMEOUT
        )

        allow_origin = response.headers.get("access-control-allow-origin", "")
        assert allow_origin in ["*", "http://localhost:8081"], \
            f"CORS should allow origin, got: {allow_origin}"

    def test_cors_allows_put_method(self, wait_for_api_server, api_server_url):
        """Test that CORS allows PUT method for category updates"""
        # OPTIONS preflight request
        headers = {
            "Origin": "http://localhost:8081",
            "Access-Control-Request-Method": "PUT",
            "Access-Control-Request-Headers": "content-type"
        }

        response = requests.options(
            f"{api_server_url}/api/transactions/1/category",
            headers=headers,
            timeout=API_TIMEOUT
        )

        # Should not reject CORS preflight
        # FastAPI/Starlette should handle this automatically
        assert response.status_code in [200, 204], \
            f"CORS preflight failed with status {response.status_code}"

    def test_cors_allows_json_content_type(self, wait_for_api_server, api_server_url):
        """Test that CORS allows application/json content type"""
        headers = {
            "Origin": "http://localhost:8081",
            "Content-Type": "application/json"
        }

        response = requests.get(
            f"{api_server_url}/api",
            headers=headers,
            timeout=API_TIMEOUT
        )

        # Should succeed with JSON content type
        assert response.status_code == 200


# ============================================================================
# PHASE 1 - RED: ERROR HANDLING AND FALLBACK TESTS
# ============================================================================

class TestErrorHandlingLive:
    """Test error handling and fallback behavior"""

    def test_invalid_transaction_id_returns_404(self, wait_for_api_server, api_server_url):
        """Test that updating non-existent transaction returns proper error"""
        response = requests.put(
            f"{api_server_url}/api/transactions/999999/category",
            json={"category_id": 1},
            timeout=API_TIMEOUT
        )

        assert response.status_code == 404, \
            f"Expected 404 for invalid transaction, got {response.status_code}"

    def test_malformed_json_returns_422(self, wait_for_api_server, api_server_url):
        """Test that malformed JSON returns proper error"""
        response = requests.put(
            f"{api_server_url}/api/transactions/1/category",
            data="invalid json",
            headers={"Content-Type": "application/json"},
            timeout=API_TIMEOUT
        )

        assert response.status_code == 422, \
            f"Expected 422 for malformed JSON, got {response.status_code}"

    def test_api_handles_database_errors_gracefully(self):
        """Test that API handles database connection errors gracefully"""
        # This test verifies error handling code exists
        # We can't actually disconnect the database in live tests
        # So we verify the error handling path in the code

        from api_server import get_transactions
        import inspect

        # Check that error handling exists in the endpoint
        source = inspect.getsource(get_transactions)
        assert "except" in source, "get_transactions should have exception handling"
        assert "HTTPException" in source, "get_transactions should raise HTTPException"


# ============================================================================
# PHASE 1 - RED: HEALTH CHECK AND MONITORING TESTS
# ============================================================================

class TestHealthChecks:
    """Test health check endpoints and monitoring capabilities"""

    def test_api_root_serves_as_health_check(self, wait_for_api_server, api_server_url):
        """Test that /api endpoint can serve as a health check"""
        response = requests.get(f"{api_server_url}/api", timeout=API_TIMEOUT)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"

    def test_api_responds_consistently(self, wait_for_api_server, api_server_url):
        """Test that API responds consistently across multiple requests"""
        response_times = []

        for _ in range(5):
            start = time.time()
            response = requests.get(f"{api_server_url}/api", timeout=API_TIMEOUT)
            elapsed = time.time() - start

            assert response.status_code == 200
            response_times.append(elapsed)

        # Average response time should be reasonable
        avg_time = sum(response_times) / len(response_times)
        assert avg_time < 2.0, f"Average response time {avg_time:.2f}s is too slow"

    def test_database_connection_pool_healthy(self):
        """Test that database connection pool is properly configured"""
        # Get multiple connections to test pool
        connections = []

        try:
            for _ in range(3):
                conn = get_connection()
                assert conn.is_connected()
                connections.append(conn)

            # All connections should be valid
            for conn in connections:
                assert conn.is_connected()

        finally:
            # Clean up
            for conn in connections:
                conn.close()


# ============================================================================
# PHASE 1 - RED: INTEGRATION TESTS (Frontend Simulation)
# ============================================================================

class TestFrontendIntegration:
    """Test API from frontend perspective to catch integration issues"""

    def test_frontend_workflow_load_transactions(self, wait_for_api_server, api_server_url):
        """
        Simulate frontend workflow: Load transactions
        This is what daily_expense_categorizer.html does on page load
        """
        # Frontend fetches categories first
        categories_response = requests.get(
            f"{api_server_url}/api/categories",
            timeout=API_TIMEOUT
        )
        assert categories_response.status_code == 200, \
            "Frontend cannot load categories"

        # Then fetches transactions
        transactions_response = requests.get(
            f"{api_server_url}/api/transactions",
            timeout=API_TIMEOUT
        )
        assert transactions_response.status_code == 200, \
            "Frontend cannot load transactions"

        # Should not show "API unavailable" message
        categories = categories_response.json()
        transactions = transactions_response.json()

        assert isinstance(categories, list), "Categories should be a list"
        assert isinstance(transactions, list), "Transactions should be a list"

    def test_frontend_workflow_categorize_transaction(self, wait_for_api_server, api_server_url):
        """
        Simulate frontend workflow: User categorizes a transaction
        This addresses: "Failed to update category: Failed to fetch"
        """
        # Get transactions
        transactions_response = requests.get(
            f"{api_server_url}/api/transactions",
            timeout=API_TIMEOUT
        )
        transactions = transactions_response.json()

        if len(transactions) == 0:
            pytest.skip("No transactions to test categorization")

        # Get categories
        categories_response = requests.get(
            f"{api_server_url}/api/categories",
            timeout=API_TIMEOUT
        )
        categories = categories_response.json()

        if len(categories) == 0:
            pytest.skip("No categories to test categorization")

        transaction_id = transactions[0]["id"]
        category_id = categories[0]["id"]

        # User categorizes transaction
        update_response = requests.put(
            f"{api_server_url}/api/transactions/{transaction_id}/category",
            json={"category_id": category_id},
            headers={"Content-Type": "application/json"},
            timeout=API_TIMEOUT
        )

        # This is the critical test - should NOT be "Failed to fetch"
        assert update_response.status_code == 200, \
            f"Categorization failed: {update_response.status_code} - {update_response.text}"

        result = update_response.json()
        assert result["success"] is True, "Category update should report success"

    def test_frontend_workflow_reload_after_update(self, wait_for_api_server, api_server_url):
        """
        Simulate frontend workflow: Reload data after categorization
        Frontend calls reloadTransactions() after successful update
        """
        # Reload transactions (like frontend does)
        response = requests.get(
            f"{api_server_url}/api/transactions",
            headers={"Cache-Control": "no-store"},
            timeout=API_TIMEOUT
        )

        assert response.status_code == 200, "Failed to reload transactions"
        transactions = response.json()
        assert isinstance(transactions, list), "Reloaded data should be a list"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "not slow"])
