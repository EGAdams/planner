"""
Tests for show_one_expense_day.py script
Following TDD methodology - RED phase: tests written first
"""
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from show_one_expense_day import (
    validate_date_format,
    parse_date_to_mysql_format,
    fetch_expenses_for_date,
    format_expense_report,
    generate_report_filename
)


class TestDateValidation(unittest.TestCase):
    """Test date validation and parsing"""

    def test_valid_date_format(self):
        """Test that valid dates pass validation"""
        self.assertTrue(validate_date_format("01/15/2024"))
        self.assertTrue(validate_date_format("12/31/2023"))

    def test_invalid_date_format(self):
        """Test that invalid formats are rejected"""
        self.assertFalse(validate_date_format("2024-01-15"))
        self.assertFalse(validate_date_format("01-15-2024"))
        self.assertFalse(validate_date_format("invalid"))

    def test_parse_date_to_mysql_format(self):
        """Test conversion from MM/DD/YYYY to YYYY-MM-DD"""
        self.assertEqual(parse_date_to_mysql_format("01/15/2024"), "2024-01-15")
        self.assertEqual(parse_date_to_mysql_format("12/31/2023"), "2023-12-31")


class TestExpenseQuery(unittest.TestCase):
    """Test database query for expenses"""

    @patch('show_one_expense_day.query_all')
    def test_fetch_expenses_success(self, mock_query):
        """Test successful expense fetching"""
        mock_query.return_value = [
            {
                'id': 1,
                'org_id': 1,
                'expense_date': datetime(2024, 1, 15),
                'amount': 150.50,
                'category_id': 2,
                'description': 'Office supplies',
                'method': 'CARD'
            }
        ]

        expenses = fetch_expenses_for_date("2024-01-15")
        self.assertEqual(len(expenses), 1)
        self.assertEqual(expenses[0]['amount'], 150.50)

    @patch('show_one_expense_day.query_all')
    def test_fetch_expenses_empty(self, mock_query):
        """Test fetching when no expenses exist for date"""
        mock_query.return_value = []

        expenses = fetch_expenses_for_date("2024-01-15")
        self.assertEqual(len(expenses), 0)


class TestReportFormatting(unittest.TestCase):
    """Test report generation and formatting"""

    def test_format_expense_report(self):
        """Test that expense data is formatted correctly"""
        expenses = [
            {
                'id': 1,
                'org_id': 1,
                'expense_date': datetime(2024, 1, 15),
                'amount': 150.50,
                'category_id': 2,
                'description': 'Office supplies',
                'method': 'CARD',
                'paid_by_contact_id': 3,
                'receipt_url': None
            }
        ]

        report = format_expense_report(expenses, "01/15/2024")
        self.assertIn("DAILY EXPENSE REPORT", report)
        self.assertIn("01/15/2024", report)
        self.assertIn("150.50", report)
        self.assertIn("Office supplies", report)

    def test_generate_report_filename(self):
        """Test report filename generation"""
        filename = generate_report_filename("01/15/2024")
        self.assertIn("expense_report", filename)
        self.assertIn("2024-01-15", filename)
        self.assertTrue(filename.endswith(".txt"))


if __name__ == '__main__':
    unittest.main()
