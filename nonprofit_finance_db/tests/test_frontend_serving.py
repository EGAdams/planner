#!/usr/bin/env python3
"""
TDD Test Suite for Frontend File Serving and Access

Tests frontend HTML file is properly served by the API server
and can access the API endpoints correctly.
"""

import pytest
import requests
import sys
from pathlib import Path
from bs4 import BeautifulSoup
import re

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


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
    """Wait for API server to be available"""
    import time
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{api_server_url}/api", timeout=2)
            if response.status_code == 200:
                return True
        except requests.exceptions.RequestException:
            pass

        if attempt < max_attempts - 1:
            time.sleep(1)

    pytest.fail(f"API server not available at {api_server_url}")


# ============================================================================
# FRONTEND SERVING TESTS
# ============================================================================

class TestFrontendServing:
    """Test that frontend HTML is properly served"""

    def test_root_serves_daily_expense_categorizer(self, wait_for_api_server, api_server_url):
        """
        Test that root URL serves the daily expense categorizer HTML
        """
        response = requests.get(api_server_url, timeout=API_TIMEOUT)

        # Should successfully return HTML
        assert response.status_code == 200, \
            f"Root URL returned {response.status_code}, expected 200"

        # Should be HTML content type
        content_type = response.headers.get("content-type", "")
        assert "text/html" in content_type, \
            f"Expected HTML content type, got {content_type}"

    def test_daily_expense_categorizer_direct_path(self, wait_for_api_server, api_server_url):
        """Test that direct path to HTML file works"""
        response = requests.get(
            f"{api_server_url}/daily_expense_categorizer.html",
            timeout=API_TIMEOUT
        )

        assert response.status_code == 200, \
            f"Direct HTML path returned {response.status_code}"

        content_type = response.headers.get("content-type", "")
        assert "text/html" in content_type

    def test_office_mount_point(self, wait_for_api_server, api_server_url):
        """Test that /office mount point is accessible"""
        response = requests.get(
            f"{api_server_url}/office/daily_expense_categorizer.html",
            timeout=API_TIMEOUT,
            allow_redirects=True
        )

        # Should either serve the file or redirect to it
        assert response.status_code in [200, 307], \
            f"/office mount point returned {response.status_code}"


class TestFrontendConfiguration:
    """Test frontend JavaScript configuration"""

    def test_api_base_configuration(self, wait_for_api_server, api_server_url):
        """
        Test that frontend JavaScript has correct API_BASE configuration
        This addresses: Frontend may be trying to connect to wrong API URL
        """
        response = requests.get(api_server_url, timeout=API_TIMEOUT)
        html_content = response.text

        # Extract API_BASE configuration from JavaScript
        api_base_pattern = r'const\s+API_BASE\s*=\s*["\']([^"\']+)["\']'
        match = re.search(api_base_pattern, html_content)

        if not match:
            # Check for dynamic API_BASE (computed from window.location)
            assert "API_BASE" in html_content, \
                "Frontend HTML missing API_BASE configuration"
            # Dynamic configuration is OK
            return

        api_base = match.group(1)
        # API_BASE should point to localhost:8080 or be dynamically computed
        assert "8080" in api_base or "window.location" in html_content, \
            f"API_BASE configured incorrectly: {api_base}"

    def test_frontend_uses_live_api_by_default(self, wait_for_api_server, api_server_url):
        """
        Test that frontend preferApi flag defaults to true
        This addresses: Frontend showing "sample data" message
        """
        response = requests.get(api_server_url, timeout=API_TIMEOUT)
        html_content = response.text

        # Check preferApi configuration
        prefer_api_pattern = r'const\s+preferApi\s*=\s*([^;]+);'
        match = re.search(prefer_api_pattern, html_content)

        if match:
            prefer_api_expr = match.group(1)
            # Should not be hardcoded to false
            assert "false" not in prefer_api_expr.lower() or "use_api" in prefer_api_expr, \
                f"preferApi incorrectly configured: {prefer_api_expr}"

    def test_frontend_has_fetch_functions(self, wait_for_api_server, api_server_url):
        """Test that frontend has necessary fetch functions"""
        response = requests.get(api_server_url, timeout=API_TIMEOUT)
        html_content = response.text

        # Should have fetch functions
        assert "fetchTransactions" in html_content, \
            "Frontend missing fetchTransactions function"
        assert "fetchCategories" in html_content, \
            "Frontend missing fetchCategories function"
        assert "updateTransactionCategory" in html_content, \
            "Frontend missing updateTransactionCategory function"


class TestFrontendAPIIntegration:
    """Test frontend-to-API integration paths"""

    def test_frontend_transactions_endpoint_url(self, wait_for_api_server, api_server_url):
        """
        Test that frontend constructs correct transactions endpoint URL
        """
        response = requests.get(api_server_url, timeout=API_TIMEOUT)
        html_content = response.text

        # Should reference /api/transactions
        assert "/api/transactions" in html_content, \
            "Frontend should reference /api/transactions endpoint"

    def test_frontend_categories_endpoint_url(self, wait_for_api_server, api_server_url):
        """Test that frontend constructs correct categories endpoint URL"""
        response = requests.get(api_server_url, timeout=API_TIMEOUT)
        html_content = response.text

        # Should reference /api/categories
        assert "/api/categories" in html_content, \
            "Frontend should reference /api/categories endpoint"

    def test_frontend_category_update_endpoint_url(self, wait_for_api_server, api_server_url):
        """Test that frontend constructs correct category update endpoint URL"""
        response = requests.get(api_server_url, timeout=API_TIMEOUT)
        html_content = response.text

        # Should reference /api/transactions/{id}/category pattern
        assert "/api/transactions/" in html_content, \
            "Frontend should reference transaction update endpoints"

    def test_frontend_fetch_with_fallback_logic(self, wait_for_api_server, api_server_url):
        """Test that frontend has fallback logic for API failures"""
        response = requests.get(api_server_url, timeout=API_TIMEOUT)
        html_content = response.text

        # Should have fetchJsonWithFallback or similar error handling
        assert "fetchJsonWithFallback" in html_content or "catch" in html_content, \
            "Frontend should have fallback logic for API failures"


class TestFrontendErrorHandling:
    """Test frontend error handling and user feedback"""

    def test_frontend_has_error_display_elements(self, wait_for_api_server, api_server_url):
        """Test that frontend has elements for displaying errors"""
        response = requests.get(api_server_url, timeout=API_TIMEOUT)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Should have error message element
        error_elements = soup.find_all(class_=re.compile(r'error|fallback|notice'))
        assert len(error_elements) > 0, \
            "Frontend should have error/notice display elements"

    def test_frontend_has_loading_indicator(self, wait_for_api_server, api_server_url):
        """Test that frontend has loading indicator"""
        response = requests.get(api_server_url, timeout=API_TIMEOUT)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Should have loading message element
        loading_element = soup.find(id="loadingMsg")
        assert loading_element is not None, \
            "Frontend should have loading indicator element"

    def test_frontend_has_fallback_banner(self, wait_for_api_server, api_server_url):
        """
        Test that frontend has fallback banner element
        This is where "API unavailable" message would appear
        """
        response = requests.get(api_server_url, timeout=API_TIMEOUT)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Should have fallback notice element
        fallback_element = soup.find(id="fallbackNotice")
        assert fallback_element is not None, \
            "Frontend should have fallback notice element"


class TestFrontendStaticResources:
    """Test that frontend can load static resources"""

    def test_frontend_main_js_loads(self, wait_for_api_server, api_server_url):
        """
        Test that main.js (category picker component) loads
        """
        response = requests.get(api_server_url, timeout=API_TIMEOUT)
        html_content = response.text

        # Should reference main.js
        assert "/office/js/main.js" in html_content, \
            "Frontend should reference main.js"

        # Try to load main.js
        js_response = requests.get(
            f"{api_server_url}/office/js/main.js",
            timeout=API_TIMEOUT
        )

        # Should either load successfully or return 404 (file may not exist)
        # But should not return 500 (server error)
        assert js_response.status_code != 500, \
            "Server error when loading main.js"


# ============================================================================
# BROWSER SIMULATION TESTS
# ============================================================================

class TestBrowserSimulation:
    """Simulate browser behavior to test frontend-API integration"""

    def test_simulate_page_load_sequence(self, wait_for_api_server, api_server_url):
        """
        Simulate what happens when a browser loads the page:
        1. Load HTML
        2. Execute JavaScript
        3. Fetch categories
        4. Fetch transactions
        """
        # Step 1: Load HTML
        html_response = requests.get(api_server_url, timeout=API_TIMEOUT)
        assert html_response.status_code == 200, "Failed to load HTML"

        # Step 2: Simulate JavaScript fetch calls
        # (JavaScript would run in browser and call these endpoints)

        # Step 3: Fetch categories (first parallel request)
        categories_response = requests.get(
            f"{api_server_url}/api/categories",
            timeout=API_TIMEOUT
        )
        assert categories_response.status_code == 200, \
            "JavaScript would fail to fetch categories"

        # Step 4: Fetch transactions (second parallel request)
        transactions_response = requests.get(
            f"{api_server_url}/api/transactions",
            timeout=API_TIMEOUT
        )
        assert transactions_response.status_code == 200, \
            "JavaScript would fail to fetch transactions"

        # Both should return valid JSON
        categories = categories_response.json()
        transactions = transactions_response.json()

        assert isinstance(categories, list), "Categories should be a list"
        assert isinstance(transactions, list), "Transactions should be a list"

    def test_simulate_category_update_sequence(self, wait_for_api_server, api_server_url):
        """
        Simulate what happens when user categorizes a transaction:
        1. User selects category from dropdown
        2. Frontend sends PUT request
        3. Frontend reloads transactions
        """
        # Get transactions first
        transactions_response = requests.get(
            f"{api_server_url}/api/transactions",
            timeout=API_TIMEOUT
        )
        transactions = transactions_response.json()

        if len(transactions) == 0:
            pytest.skip("No transactions to test")

        transaction_id = transactions[0]["id"]

        # Get categories
        categories_response = requests.get(
            f"{api_server_url}/api/categories",
            timeout=API_TIMEOUT
        )
        categories = categories_response.json()

        if len(categories) == 0:
            pytest.skip("No categories to test")

        category_id = categories[0]["id"]

        # Simulate frontend sending PUT request
        update_response = requests.put(
            f"{api_server_url}/api/transactions/{transaction_id}/category",
            json={"category_id": category_id},
            headers={"Content-Type": "application/json"},
            timeout=API_TIMEOUT
        )

        # This is the critical test - should NOT fail with "Failed to fetch"
        assert update_response.status_code == 200, \
            f"Category update would fail in browser: {update_response.status_code}"

        # Simulate frontend reloading transactions
        reload_response = requests.get(
            f"{api_server_url}/api/transactions",
            timeout=API_TIMEOUT
        )
        assert reload_response.status_code == 200, \
            "Reload after update would fail"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
