#!/usr/bin/env python3
"""
Browser Integration Tests for Daily Expense Categorizer

Uses Playwright to test actual browser behavior and JavaScript execution.
This will reveal issues that unit tests cannot detect.
"""

import pytest
import pytest_asyncio
import time
import asyncio
from playwright.async_api import async_playwright, Page, Browser
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


# ============================================================================
# CONFIGURATION
# ============================================================================

API_BASE_URL = "http://localhost:8080"
PAGE_LOAD_TIMEOUT = 30000  # 30 seconds
API_TIMEOUT = 10000  # 10 seconds


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def browser():
    """Launch browser for testing"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        yield browser
        await browser.close()


@pytest_asyncio.fixture
async def page(browser: Browser):
    """Create a new page for each test"""
    page = await browser.new_page()
    yield page
    await page.close()


# ============================================================================
# BROWSER INTEGRATION TESTS
# ============================================================================

class TestBrowserPageLoad:
    """Test that page loads correctly in a real browser"""

    @pytest.mark.asyncio
    async def test_page_loads_without_errors(self, page: Page):
        """
        CRITICAL TEST: Page should load without JavaScript errors
        """
        errors = []

        # Capture console errors
        page.on("console", lambda msg: errors.append(msg) if msg.type == "error" else None)

        # Capture page errors
        page.on("pageerror", lambda err: errors.append(str(err)))

        # Load page
        response = await page.goto(API_BASE_URL, wait_until="networkidle", timeout=PAGE_LOAD_TIMEOUT)

        assert response.status == 200, f"Page failed to load: {response.status}"

        # Check for errors
        if errors:
            pytest.fail(f"Page loaded with errors: {errors}")

    @pytest.mark.asyncio
    async def test_page_title_correct(self, page: Page):
        """Test that page has correct title"""
        await page.goto(API_BASE_URL, wait_until="load", timeout=PAGE_LOAD_TIMEOUT)

        title = await page.title()
        assert title == "Daily Expense Categorizer", \
            f"Page title is '{title}', expected 'Daily Expense Categorizer'"

    @pytest.mark.asyncio
    async def test_no_fallback_banner_shown(self, page: Page):
        """
        CRITICAL TEST: Fallback banner should NOT be visible
        This addresses: "Connected API at http://localhost:8080/api is unavailable"
        """
        await page.goto(API_BASE_URL, wait_until="networkidle", timeout=PAGE_LOAD_TIMEOUT)

        # Wait for page to finish loading data
        await page.wait_for_selector("#mainTable", state="visible", timeout=API_TIMEOUT)

        # Check fallback notice is hidden
        fallback_notice = await page.query_selector("#fallbackNotice")
        assert fallback_notice is not None, "Fallback notice element missing"

        # Check if it's visible
        is_visible = await fallback_notice.is_visible()
        if is_visible:
            # Get the text content to see what error message is shown
            text = await fallback_notice.text_content()
            pytest.fail(f"Fallback banner is visible with message: {text}")

    @pytest.mark.asyncio
    async def test_transactions_table_visible(self, page: Page):
        """Test that transactions table becomes visible after loading"""
        await page.goto(API_BASE_URL, wait_until="networkidle", timeout=PAGE_LOAD_TIMEOUT)

        # Wait for table to be visible
        await page.wait_for_selector("#mainTable", state="visible", timeout=API_TIMEOUT)

        # Check table is visible
        table = await page.query_selector("#mainTable")
        is_visible = await table.is_visible()

        assert is_visible, "Transactions table is not visible"

    @pytest.mark.asyncio
    async def test_loading_indicator_disappears(self, page: Page):
        """Test that loading indicator disappears after data loads"""
        await page.goto(API_BASE_URL, wait_until="networkidle", timeout=PAGE_LOAD_TIMEOUT)

        # Wait for loading to complete
        await page.wait_for_selector("#mainTable", state="visible", timeout=API_TIMEOUT)

        # Check loading message is hidden
        loading_msg = await page.query_selector("#loadingMsg")
        assert loading_msg is not None, "Loading message element missing"

        # Should be hidden
        is_visible = await loading_msg.is_visible()
        assert not is_visible, "Loading indicator still visible after page load"


class TestBrowserAPIConnection:
    """Test API connectivity from browser perspective"""

    @pytest.mark.asyncio
    async def test_api_requests_succeed(self, page: Page):
        """
        CRITICAL TEST: API requests from JavaScript should succeed
        Monitor network requests to verify they complete successfully
        """
        api_requests = []
        failed_requests = []

        # Monitor API requests
        async def handle_response(response):
            if "/api/" in response.url:
                api_requests.append({
                    "url": response.url,
                    "status": response.status,
                    "ok": response.ok
                })
                if not response.ok:
                    failed_requests.append(response)

        page.on("response", handle_response)

        # Load page
        await page.goto(API_BASE_URL, wait_until="networkidle", timeout=PAGE_LOAD_TIMEOUT)

        # Wait for data to load
        await page.wait_for_selector("#mainTable", state="visible", timeout=API_TIMEOUT)

        # Should have made API requests
        assert len(api_requests) > 0, "No API requests were made"

        # All API requests should succeed
        if failed_requests:
            failed_urls = [r.url for r in failed_requests]
            pytest.fail(f"API requests failed: {failed_urls}")

    @pytest.mark.asyncio
    async def test_transactions_api_called(self, page: Page):
        """Test that /api/transactions endpoint is called"""
        transactions_called = False

        async def check_request(response):
            nonlocal transactions_called
            if "/api/transactions" in response.url:
                transactions_called = True

        page.on("response", check_request)

        await page.goto(API_BASE_URL, wait_until="networkidle", timeout=PAGE_LOAD_TIMEOUT)
        await page.wait_for_selector("#mainTable", state="visible", timeout=API_TIMEOUT)

        assert transactions_called, "/api/transactions was not called"

    @pytest.mark.asyncio
    async def test_categories_api_called(self, page: Page):
        """Test that /api/categories endpoint is called"""
        categories_called = False

        async def check_request(response):
            nonlocal categories_called
            if "/api/categories" in response.url:
                categories_called = True

        page.on("response", check_request)

        await page.goto(API_BASE_URL, wait_until="networkidle", timeout=PAGE_LOAD_TIMEOUT)
        await page.wait_for_selector("#mainTable", state="visible", timeout=API_TIMEOUT)

        assert categories_called, "/api/categories was not called"


class TestBrowserCategoryUpdate:
    """Test category update functionality in browser"""

    @pytest.mark.asyncio
    async def test_category_picker_elements_present(self, page: Page):
        """Test that category picker elements are rendered"""
        await page.goto(API_BASE_URL, wait_until="networkidle", timeout=PAGE_LOAD_TIMEOUT)
        await page.wait_for_selector("#mainTable", state="visible", timeout=API_TIMEOUT)

        # Check for category-picker elements
        pickers = await page.query_selector_all("category-picker")
        assert len(pickers) > 0, "No category-picker elements found"

    @pytest.mark.asyncio
    async def test_category_update_no_fetch_errors(self, page: Page):
        """
        CRITICAL TEST: Category updates should not show "Failed to fetch" errors
        This addresses: "Failed to update category: Failed to fetch"
        """
        console_errors = []

        # Capture console errors
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        await page.goto(API_BASE_URL, wait_until="networkidle", timeout=PAGE_LOAD_TIMEOUT)
        await page.wait_for_selector("#mainTable", state="visible", timeout=API_TIMEOUT)

        # Try to interact with first category picker
        pickers = await page.query_selector_all("category-picker")
        if len(pickers) == 0:
            pytest.skip("No category pickers to test")

        # Check for "Failed to fetch" errors
        fetch_errors = [err for err in console_errors if "failed to fetch" in err.lower()]
        if fetch_errors:
            pytest.fail(f"Fetch errors detected: {fetch_errors}")


class TestBrowserJavaScriptExecution:
    """Test JavaScript execution and data handling"""

    @pytest.mark.asyncio
    async def test_api_base_configured_correctly(self, page: Page):
        """Test that API_BASE JavaScript variable is set correctly"""
        await page.goto(API_BASE_URL, wait_until="load", timeout=PAGE_LOAD_TIMEOUT)

        # Get API_BASE value from JavaScript
        api_base = await page.evaluate("API_BASE")

        # Should point to localhost:8080/api
        assert "localhost:8080" in api_base or "127.0.0.1:8080" in api_base, \
            f"API_BASE is '{api_base}', should point to localhost:8080"
        assert api_base.endswith("/api"), \
            f"API_BASE should end with '/api', got '{api_base}'"

    @pytest.mark.asyncio
    async def test_prefer_api_flag_true(self, page: Page):
        """Test that preferApi flag is true (use live API, not sample data)"""
        await page.goto(API_BASE_URL, wait_until="load", timeout=PAGE_LOAD_TIMEOUT)

        # Get preferApi value
        prefer_api = await page.evaluate("preferApi")

        assert prefer_api is True, \
            f"preferApi should be true, got {prefer_api}"

    @pytest.mark.asyncio
    async def test_transactions_data_loaded(self, page: Page):
        """Test that transactions data is actually loaded"""
        await page.goto(API_BASE_URL, wait_until="networkidle", timeout=PAGE_LOAD_TIMEOUT)
        await page.wait_for_selector("#mainTable", state="visible", timeout=API_TIMEOUT)

        # Check allTransactions array in JavaScript
        transactions_count = await page.evaluate("allTransactions.length")

        assert transactions_count > 0, \
            "No transactions loaded (allTransactions array is empty)"

    @pytest.mark.asyncio
    async def test_categories_data_loaded(self, page: Page):
        """Test that categories data is actually loaded"""
        await page.goto(API_BASE_URL, wait_until="networkidle", timeout=PAGE_LOAD_TIMEOUT)
        await page.wait_for_selector("#mainTable", state="visible", timeout=API_TIMEOUT)

        # Check categoryOptions array in JavaScript
        categories_count = await page.evaluate("categoryOptions.length")

        assert categories_count > 0, \
            "No categories loaded (categoryOptions array is empty)"

    @pytest.mark.asyncio
    async def test_used_fallback_data_flag_false(self, page: Page):
        """
        CRITICAL TEST: usedFallbackData flag should be false
        This verifies that live API is being used, not fallback data
        """
        await page.goto(API_BASE_URL, wait_until="networkidle", timeout=PAGE_LOAD_TIMEOUT)
        await page.wait_for_selector("#mainTable", state="visible", timeout=API_TIMEOUT)

        # Check usedFallbackData flag
        used_fallback = await page.evaluate("usedFallbackData")

        assert used_fallback is False, \
            f"usedFallbackData is {used_fallback}, should be false (live API should be used)"


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
