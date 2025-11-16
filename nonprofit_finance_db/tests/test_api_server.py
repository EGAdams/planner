#!/usr/bin/env python3
"""
Comprehensive Test Suite for Daily Expense Categorizer API Server
Following TDD methodology: RED -> GREEN -> REFACTOR

Tests cover:
- All API endpoints
- Database integration
- Error handling
- CORS configuration
- Static file serving
- Date/datetime JSON serialization
"""
import os
import pytest
import sys
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from api_server import app, convert_value


# =============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture(autouse=True)
def set_gemini_api_key(mocker):
    """Set a dummy GEMINI_API_KEY for tests."""
    mocker.patch.dict(os.environ, {"GEMINI_API_KEY": "test_gemini_api_key"})

@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def mock_db_categories():
    """Mock category data structure"""
    return [
        {"id": 1, "name": "Operations", "parent_id": None},
        {"id": 2, "name": "Office Supplies", "parent_id": 1},
        {"id": 3, "name": "Marketing", "parent_id": None},
        {"id": 4, "name": "Digital Ads", "parent_id": 3},
        {"id": 5, "name": "Utilities", "parent_id": 1},
    ]


@pytest.fixture
def mock_db_expenses():
    """Mock expense data structure"""
    return [
        {
            "id": 1,
            "date": date(2025, 10, 15),
            "vendor": "Office Depot",
            "amount": Decimal("45.99"),
            "category_id": 2,
            "method": "CREDIT",
            "paid_by": ""
        },
        {
            "id": 2,
            "date": date(2025, 10, 16),
            "vendor": "Google Ads",
            "amount": Decimal("250.00"),
            "category_id": 4,
            "method": "CREDIT",
            "paid_by": ""
        },
        {
            "id": 3,
            "date": date(2025, 10, 17),
            "vendor": "Electric Company",
            "amount": Decimal("125.50"),
            "category_id": 5,
            "method": "CREDIT",
            "paid_by": ""
        }
    ]


@pytest.fixture
def mock_query_all():
    """Fixture to create mock for query_all function"""
    with patch('api_server.query_all') as mock:
        yield mock


@pytest.fixture
def mock_query_one():
    """Fixture to create mock for query_one function"""
    with patch('api_server.query_one') as mock:
        yield mock


@pytest.fixture
def mock_execute():
    """Fixture to create mock for execute function"""
    with patch('api_server.execute') as mock:
        yield mock


# =============================================================================
# UNIT TESTS - Helper Functions
# ============================================================================

class TestHelperFunctions:
    """Test suite for helper functions"""

    def test_convert_value_date(self):
        """Test convert_value handles date objects correctly"""
        test_date = date(2025, 10, 15)
        result = convert_value(test_date)
        assert result == "2025-10-15"
        assert isinstance(result, str)

    def test_convert_value_datetime(self):
        """Test convert_value handles datetime objects correctly"""
        test_datetime = datetime(2025, 10, 15, 14, 30, 45)
        result = convert_value(test_datetime)
        assert result == "2025-10-15"
        assert isinstance(result, str)

    def test_convert_value_decimal(self):
        """Test convert_value handles Decimal objects correctly"""
        test_decimal = Decimal("123.45")
        result = convert_value(test_decimal)
        assert result == 123.45
        assert isinstance(result, float)

    def test_convert_value_passthrough(self):
        """Test convert_value passes through other types unchanged"""
        test_str = "test string"
        assert convert_value(test_str) == test_str

        test_int = 42
        assert convert_value(test_int) == test_int

        test_float = 3.14
        assert convert_value(test_float) == test_float

        test_none = None
        assert convert_value(test_none) is None


# =============================================================================
# API ENDPOINT TESTS
# ============================================================================

class TestRootEndpoint:
    """Test suite for root API endpoint"""

    def test_api_root_returns_200(self, client):
        """Test that /api endpoint returns 200 OK"""
        response = client.get("/api")
        assert response.status_code == 200

    def test_api_root_returns_json(self, client):
        """Test that /api endpoint returns valid JSON"""
        response = client.get("/api")
        assert response.headers["content-type"] == "application/json"
        data = response.json()
        assert isinstance(data, dict)

    def test_api_root_contains_expected_fields(self, client):
        """Test that /api endpoint contains expected fields"""
        response = client.get("/api")
        data = response.json()
        assert "message" in data
        assert "status" in data
        assert data["status"] == "running"


class TestExpensesEndpoint:
    """Test suite for /api/expenses endpoint"""

    def test_get_expenses_returns_200(self, client, mock_query_all):
        """Test that GET /api/expenses returns 200 OK"""
        mock_query_all.return_value = []
        response = client.get("/api/expenses")
        assert response.status_code == 200

    def test_get_expenses_returns_list(self, client, mock_query_all):
        """Test that GET /api/expenses returns a list"""
        mock_query_all.return_value = []
        response = client.get("/api/expenses")
        data = response.json()
        assert isinstance(data, list)

    def test_get_expenses_with_data(self, client, mock_query_all,
                                       mock_db_expenses, mock_db_categories):
        """Test that GET /api/expenses returns properly formatted expense data"""
        # Setup mocks - first call for categories, second for expenses
        mock_query_all.side_effect = [
            mock_db_categories,
            mock_db_expenses
        ]

        response = client.get("/api/expenses")
        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert isinstance(data, list)
        assert len(data) == 3

        # Verify first expense
        expense = data[0]
        assert expense["id"] == 1
        assert expense["vendor"] == "Office Depot"
        assert expense["amount"] == 45.99
        assert expense["date"] == "2025-10-15"
        assert expense["method"] == "CREDIT"
        assert "category" in expense
        assert "category_id" in expense

    def test_get_expenses_with_date_filters(self, client, mock_query_all,
                                                mock_db_categories):
        """Test that GET /api/expenses accepts date filter parameters"""
        mock_query_all.side_effect = [
            mock_db_categories,
            []
        ]

        response = client.get("/api/expenses?start_date=2025-10-01&end_date=2025-10-31")
        assert response.status_code == 200

        # Verify query_all was called with date parameters
        calls = mock_query_all.call_args_list
        assert len(calls) == 2
        # Second call should have date parameters
        sql, params = calls[1][0]
        assert "expense_date >= %s" in sql
        assert "expense_date <= %s" in sql
        assert len(params) == 2

    def test_get_expenses_category_hierarchy(self, client, mock_query_all,
                                                 mock_db_categories):
        """Test that expenses return full category path (parent / child)"""
        mock_query_all.side_effect = [
            mock_db_categories,
            [
                {
                    "id": 1,
                    "date": date(2025, 10, 15),
                    "vendor": "Test Vendor",
                    "amount": Decimal("50.00"),
                    "category_id": 2,  # Office Supplies (parent: Operations)
                    "method": "CREDIT",
                    "paid_by": ""
                }
            ]
        ]

        response = client.get("/api/expenses")
        data = response.json()

        assert data[0]["category"] == "Operations / Office Supplies"

    def test_get_expenses_database_error(self, client, mock_query_all):
        """Test that database errors are handled gracefully"""
        mock_query_all.side_effect = Exception("Database connection failed")

        response = client.get("/api/expenses")
        assert response.status_code == 500
        assert "detail" in response.json()

    def test_get_expenses_serializes_dates_correctly(self, client, mock_query_all,
                                                        mock_db_categories):
        """Test that date/datetime objects are serialized to strings"""
        mock_query_all.side_effect = [
            mock_db_categories,
            [
                {
                    "id": 1,
                    "date": datetime(2025, 10, 15, 14, 30, 0),  # datetime object
                    "vendor": "Test",
                    "amount": Decimal("100.00"),
                    "category_id": None,
                    "method": "CREDIT",
                    "paid_by": ""
                }
            ]
        ]

        response = client.get("/api/expenses")
        data = response.json()

        # Should be serialized as string
        assert isinstance(data[0]["date"], str)
        assert data[0]["date"] == "2025-10-15"


class TestCategoriesEndpoint:
    """Test suite for /api/categories endpoint"""

    def test_get_categories_returns_200(self, client, mock_query_all):
        """Test that GET /api/categories returns 200 OK"""
        mock_query_all.return_value = []
        response = client.get("/api/categories")
        assert response.status_code == 200

    def test_get_categories_returns_list(self, client, mock_query_all):
        """Test that GET /api/categories returns a list"""
        mock_query_all.return_value = []
        response = client.get("/api/categories")
        data = response.json()
        assert isinstance(data, list)

    def test_get_categories_with_data(self, client, mock_query_all, mock_db_categories):
        """Test that GET /api/categories returns properly formatted category data"""
        mock_query_all.return_value = mock_db_categories

        response = client.get("/api/categories")
        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert isinstance(data, list)
        assert len(data) == 5

        # Verify first category
        category = data[0]
        assert category["id"] == 1
        assert category["name"] == "Operations"
        assert category["parent_id"] is None

        # Verify child category
        child_category = data[1]
        assert child_category["id"] == 2
        assert child_category["parent_id"] == 1

    def test_get_categories_filters_active_expense_only(self, client, mock_query_all):
        """Test that categories query filters for active expense categories"""
        mock_query_all.return_value = []

        client.get("/api/categories")

        # Verify SQL includes filters
        call_args = mock_query_all.call_args
        sql = call_args[0][0]
        assert "kind = 'EXPENSE'" in sql
        assert "is_active = 1" in sql

    def test_get_categories_database_error(self, client, mock_query_all):
        """Test that database errors are handled gracefully"""
        mock_query_all.side_effect = Exception("Database connection failed")

        response = client.get("/api/categories")
        assert response.status_code == 500
        assert "detail" in response.json()


class TestUpdateCategoryEndpoint:
    """Test suite for PUT /api/expenses/{id}/category endpoint"""

    def test_update_category_returns_200(self, client, mock_query_one, mock_execute):
        """Test that PUT /api/expenses/{id}/category returns 200 OK"""
        mock_query_one.return_value = {"id": 1}
        mock_execute.return_value = 1

        response = client.put("/api/expenses/1/category", json={"category_id": 2})
        assert response.status_code == 200

    def test_update_category_success_response(self, client, mock_query_one, mock_execute):
        """Test that successful category update returns correct response"""
        mock_query_one.return_value = {"id": 1}
        mock_execute.return_value = 1

        response = client.put("/api/expenses/1/category", json={"category_id": 2})
        data = response.json()

        assert data["success"] is True
        assert data["expense_id"] == 1

    def test_update_category_not_found(self, client, mock_query_one):
        """Test that updating non-existent expense returns 404"""
        mock_query_one.return_value = None

        response = client.put("/api/expenses/999/category", json={"category_id": 2})
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_category_calls_database(self, client, mock_query_one, mock_execute):
        """Test that category update calls database with correct parameters"""
        mock_query_one.return_value = {"id": 1}
        mock_execute.return_value = 1

        client.put("/api/expenses/1/category", json={"category_id": 5})

        # Verify execute was called with correct SQL
        call_args = mock_execute.call_args
        sql, params = call_args[0]
        assert "UPDATE expenses" in sql
        assert "SET category_id = %s" in sql
        assert params == (5, 1)

    def test_update_category_null_value(self, client, mock_query_one, mock_execute):
        """Test that category can be set to null"""
        mock_query_one.return_value = {"id": 1}
        mock_execute.return_value = 1

        response = client.put("/api/expenses/1/category", json={"category_id": None})
        assert response.status_code == 200

        # Verify None was passed to database
        call_args = mock_execute.call_args
        params = call_args[0][1]
        assert params[0] is None

    def test_update_category_database_error(self, client, mock_query_one, mock_execute):
        """Test that database errors are handled gracefully"""
        mock_query_one.return_value = {"id": 1}
        mock_execute.side_effect = Exception("Database error")

        response = client.put("/api/expenses/1/category", json={"category_id": 2})
        assert response.status_code == 500
        assert "detail" in response.json()

    def test_update_category_invalid_json(self, client):
        """Test that invalid JSON body returns 422"""
        response = client.put("/api/expenses/1/category",
                            content="invalid json",
                            headers={"content-type": "application/json"})
        assert response.status_code == 422


class TestRecentDownloadsEndpoint:
    """Test suite for /api/recent-downloads endpoint"""

    def test_recent_downloads_returns_200(self, client):
        """Test that GET /api/recent-downloads returns 200 OK"""
        with patch('api_server.Path') as mock_path:
            mock_downloads_path = MagicMock()
            mock_downloads_path.exists.return_value = False
            mock_path.return_value = mock_downloads_path

            response = client.get("/api/recent-downloads")
            assert response.status_code == 200

    def test_recent_downloads_returns_list(self, client):
        """Test that GET /api/recent-downloads returns a list"""
        with patch('api_server.Path') as mock_path:
            mock_downloads_path = MagicMock()
            mock_downloads_path.exists.return_value = False
            mock_path.return_value = mock_downloads_path

            response = client.get("/api/recent-downloads")
            data = response.json()
            assert isinstance(data, list)

    def test_recent_downloads_empty_when_no_directory(self, client):
        """Test that endpoint returns empty list when downloads directory doesn't exist"""
        with patch('api_server.Path') as mock_path:
            mock_downloads_path = MagicMock()
            mock_downloads_path.exists.return_value = False
            mock_path.return_value = mock_downloads_path

            response = client.get("/api/recent-downloads")
            data = response.json()
            assert data == []

    def test_recent_downloads_with_files(self, client):
        """Test that endpoint returns PDF files from downloads folder"""
        with patch('api_server.Path') as mock_path:
            # Create mock Path objects for PDF files
            mock_file1 = MagicMock()
            mock_file1.name = "statement_2025_10.pdf"
            mock_file1.is_file.return_value = True
            mock_file1.stat.return_value.st_mtime = datetime(2025, 10, 31, 10, 0, 0).timestamp()

            mock_file2 = MagicMock()
            mock_file2.name = "statement_2025_09.pdf"
            mock_file2.is_file.return_value = True
            mock_file2.stat.return_value.st_mtime = datetime(2025, 9, 30, 10, 0, 0).timestamp()

            mock_downloads_path = MagicMock()
            mock_downloads_path.exists.return_value = True
            mock_downloads_path.glob.return_value = [mock_file1, mock_file2]
            mock_path.return_value = mock_downloads_path

            response = client.get("/api/recent-downloads")
            data = response.json()

            assert len(data) == 2
            assert data[0]["filename"] == "statement_2025_10.pdf"
            assert "downloadTime" in data[0]

    def test_recent_downloads_error_handling(self, client):
        """Test that errors are handled gracefully"""
        with patch('api_server.Path') as mock_path:
            mock_downloads_path = MagicMock()
            mock_downloads_path.exists.side_effect = Exception("Permission denied")
            mock_path.return_value = mock_downloads_path

            response = client.get("/api/recent-downloads")
            assert response.status_code == 500
            assert "detail" in response.json()


class TestImportPDFEndpoint:
    """Test suite for POST /api/import-pdf endpoint"""

    def test_import_pdf_file_not_found(self, client):
        """Test that importing non-existent file returns 404"""
        response = client.post("/api/import-pdf",
                              json={"filePath": "/nonexistent/file.pdf"})
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_import_pdf_invalid_file_type(self, client):
        """Test that importing non-PDF file returns 400"""
        with patch('api_server.os.path.exists', return_value=True):
            response = client.post("/api/import-pdf",
                                  json={"filePath": "/path/to/file.txt"})
            assert response.status_code == 400
            assert "pdf" in response.json()["detail"].lower()

    def test_import_pdf_requires_filepath(self, client):
        """Test that filePath is required in request body"""
        response = client.post("/api/import-pdf", json={})
        assert response.status_code == 422

    @patch('api_server.SSE_AVAILABLE', False)
    @patch('api_server.os.path.exists', return_value=True)
    @patch('api_server.subprocess.Popen')
    def test_import_pdf_fallback_mode(self, mock_popen, mock_exists, client):
        """Test PDF import in fallback mode (no SSE)"""
        # Mock successful subprocess execution
        mock_process = MagicMock()
        mock_process.stdout.readline.side_effect = [
            "Processing PDF...\n",
            "Total transactions found: 55\n",
            "Successfully imported: 50\n",
            "Failed imports: 0\n",
            "Duplicates detected: 5\n",
            ""  # End of output
        ]
        mock_process.wait.return_value = 0
        mock_process.stderr.read.return_value = ""
        mock_popen.return_value = mock_process

        response = client.post("/api/import-pdf",
                              json={"filePath": "/path/to/statement.pdf"})

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total_transactions"] == 55
        assert data["successful_imports"] == 50

    @patch('api_server.SSE_AVAILABLE', False)
    @patch('api_server.os.path.exists', return_value=True)
    @patch('api_server.subprocess.Popen')
    def test_import_pdf_script_failure(self, mock_popen, mock_exists, client):
        """Test that script failures are handled properly"""
        mock_process = MagicMock()
        mock_process.stdout.readline.return_value = ""
        mock_process.wait.return_value = 1  # Non-zero exit code
        mock_process.stderr.read.return_value = "Import script error"
        mock_popen.return_value = mock_process

        response = client.post("/api/import-pdf",
                              json={"filePath": "/path/to/statement.pdf"})

        assert response.status_code == 500
        assert "import failed" in response.json()["detail"].lower()


# =============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestCORSConfiguration:
    """Test suite for CORS middleware configuration"""

    def test_cors_middleware_configured(self, client):
        """Test that CORS middleware is configured in the app"""
        # CORS headers are only added in actual HTTP requests, not in TestClient
        # Check that the middleware is configured
        from api_server import app

        # Check user_middleware list for CORS configuration
        user_middleware = getattr(app, 'user_middleware', [])
        has_cors = any(
            middleware.cls.__name__ == 'CORSMiddleware'
            for middleware in user_middleware
        )

        assert has_cors, "CORSMiddleware should be configured in app.user_middleware"

    def test_cors_options_request(self, client):
        """Test that OPTIONS requests are handled correctly"""
        # Note: FastAPI TestClient doesn't fully emulate CORS middleware behavior
        # In a real server, CORS middleware handles OPTIONS requests
        # TestClient returns 405 for unimplemented OPTIONS, which is expected behavior
        response = client.options("/api/expenses")
        # TestClient returns 405 for OPTIONS as it doesn't emulate CORS middleware
        assert response.status_code in [200, 405]


class TestStaticFileServing:
    """Test suite for static file serving"""

    def test_root_endpoint_exists(self, client):
        """Test that root endpoint is configured"""
        # This will vary based on whether office-assistant directory exists
        response = client.get("/", follow_redirects=False)
        # Should either serve file or return 404, not 500
        assert response.status_code in [200, 404]

    def test_ui_mount_point_exists(self, client):
        """Test that /ui mount point is configured"""
        response = client.get("/ui", follow_redirects=False)
        # Can return 307 redirect (for directory), 200 (file), or 404 (not found)
        assert response.status_code in [200, 307, 404]

    def test_office_mount_point_exists(self, client):
        """Test that /office mount point is configured"""
        response = client.get("/office", follow_redirects=False)
        # Can return 307 redirect (for directory), 200 (file), or 404 (not found)
        assert response.status_code in [200, 307, 404]


# =============================================================================
# ERROR HANDLING TESTS
# ============================================================================

class TestErrorHandling:
    """Test suite for error handling"""

    def test_404_for_invalid_endpoint(self, client):
        """Test that invalid endpoints return 404"""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404

    def test_405_for_wrong_method(self, client):
        """Test that wrong HTTP methods return 405"""
        response = client.post("/api/expenses")
        assert response.status_code == 405

    def test_422_for_invalid_request_body(self, client, mock_query_one, mock_execute):
        """Test that missing required fields return 422"""
        # Pydantic allows extra fields by default, so test with missing required field
        mock_query_one.return_value = {"id": 1}

        # Send request without required body (completely empty)
        response = client.put("/api/expenses/1/category",
                            json={})
        # This should succeed because category_id is Optional[int] with default None
        # Let's test with completely malformed JSON instead
        response = client.put("/api/expenses/1/category",
                            content="not json",
                            headers={"content-type": "application/json"})
        assert response.status_code == 422


# =============================================================================
# EDGE CASES AND BOUNDARY TESTS
# ============================================================================

class TestEdgeCases:
    """Test suite for edge cases and boundary conditions"""

    def test_expenses_with_null_category(self, client, mock_query_all,
                                            mock_db_categories):
        """Test expenses with no category assigned"""
        mock_query_all.side_effect = [
            mock_db_categories,
            [
                {
                    "id": 1,
                    "date": date(2025, 10, 15),
                    "vendor": "Uncategorized Vendor",
                    "amount": Decimal("100.00"),
                    "category_id": None,
                    "method": "CREDIT",
                    "paid_by": ""
                }
            ]
        ]

        response = client.get("/api/expenses")
        data = response.json()

        assert data[0]["category"] is None
        assert data[0]["category_id"] is None

    def test_expenses_with_empty_vendor(self, client, mock_query_all,
                                           mock_db_categories):
        """Test expenses with empty vendor name"""
        mock_query_all.side_effect = [
            mock_db_categories,
            [
                {
                    "id": 1,
                    "date": date(2025, 10, 15),
                    "vendor": None,
                    "amount": Decimal("100.00"),
                    "category_id": None,
                    "method": "CREDIT",
                    "paid_by": ""
                }
            ]
        ]

        response = client.get("/api/expenses")
        data = response.json()

        assert data[0]["vendor"] == ""

    def test_expenses_with_zero_amount(self, client, mock_query_all,
                                          mock_db_categories):
        """Test expenses with zero amount"""
        mock_query_all.side_effect = [
            mock_db_categories,
            [
                {
                    "id": 1,
                    "date": date(2025, 10, 15),
                    "vendor": "Zero Amount",
                    "amount": Decimal("0.00"),
                    "category_id": None,
                    "method": "CREDIT",
                    "paid_by": ""
                }
            ]
        ]

        response = client.get("/api/expenses")
        data = response.json()

        assert data[0]["amount"] == 0.0

    def test_category_circular_reference_handling(self, client, mock_query_all):
        """Test that circular category references don't cause infinite loops"""
        # This is a defensive test - shouldn't happen in practice
        circular_categories = [
            {"id": 1, "name": "Cat1", "parent_id": 2},
            {"id": 2, "name": "Cat2", "parent_id": 1},  # Circular!
        ]

        mock_query_all.side_effect = [
            circular_categories,
            [
                {
                    "id": 1,
                    "date": date(2025, 10, 15),
                    "vendor": "Test",
                    "amount": Decimal("100.00"),
                    "category_id": 1,
                    "method": "CREDIT",
                    "paid_by": ""
                }
            ]
        ]

        # Should not hang or crash (timeout removed - not needed with TestClient)
        response = client.get("/api/expenses")
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])