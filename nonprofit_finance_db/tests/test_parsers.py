"""
Tests for bank statement parsers
"""

import pytest
import os
from unittest.mock import Mock, patch
from parsers.csv_parser import CSVParser
from parsers.base_parser import BaseParser


class TestBaseParser:
    """Test the base parser functionality"""

    def test_standardize_transaction(self):
        """Test transaction standardization"""
        parser = CSVParser(org_id=1)

        raw_data = {
            'date': '2024-01-01',
            'amount': '-45.67',
            'description': '  OFFICE DEPOT - SUPPLIES  ',
            'reference': 'REF001'
        }

        standardized = parser.standardize_transaction(raw_data)

        assert standardized['org_id'] == 1
        assert standardized['transaction_date'] == '2024-01-01'
        assert standardized['amount'] == -45.67
        assert standardized['description'] == 'OFFICE DEPOT - SUPPLIES'
        assert standardized['transaction_type'] == 'DEBIT'
        assert standardized['bank_reference'] == 'REF001'

    def test_parse_date_formats(self):
        """Test parsing various date formats"""
        parser = CSVParser(org_id=1)

        test_cases = [
            ('2024-01-01', '2024-01-01'),
            ('01/01/2024', '2024-01-01'),
            ('1/1/2024', '2024-01-01'),
            ('01-01-2024', '2024-01-01'),
            ('01/01/24', '2024-01-01'),
        ]

        for input_date, expected in test_cases:
            result = parser._parse_date(input_date)
            assert result == expected, f"Failed to parse {input_date}"

    def test_parse_amount(self):
        """Test amount parsing"""
        parser = CSVParser(org_id=1)

        test_cases = [
            ('100.50', 100.50),
            ('-45.67', -45.67),
            ('(45.67)', -45.67),
            ('$1,234.56', 1234.56),
            ('1234', 1234.0),
            (1234, 1234.0),
        ]

        for input_amount, expected in test_cases:
            result = parser._parse_amount(input_amount)
            assert result == expected, f"Failed to parse {input_amount}"

    def test_determine_transaction_type(self):
        """Test transaction type determination"""
        parser = CSVParser(org_id=1)

        assert parser._determine_type(100.0) == 'CREDIT'
        assert parser._determine_type(-100.0) == 'DEBIT'
        assert parser._determine_type(0) == 'CREDIT'
        assert parser._determine_type(None) == 'UNKNOWN'


class TestCSVParser:
    """Test CSV parser functionality"""

    @pytest.fixture
    def sample_csv_path(self):
        """Return path to sample CSV file"""
        return os.path.join(os.path.dirname(__file__), 'sample_data', 'sample_bank_statement.csv')

    @pytest.fixture
    def duplicate_csv_path(self):
        """Return path to CSV with duplicates"""
        return os.path.join(os.path.dirname(__file__), 'sample_data', 'sample_with_duplicates.csv')

    def test_validate_format(self):
        """Test CSV format validation"""
        parser = CSVParser(org_id=1)

        # Mock file existence
        with patch('os.path.exists', return_value=True):
            assert parser.validate_format('test.csv') == True
            assert parser.validate_format('test.CSV') == True
            assert parser.validate_format('test.pdf') == False
            assert parser.validate_format('test.txt') == False

    def test_parse_sample_file(self, sample_csv_path):
        """Test parsing a sample CSV file"""
        if not os.path.exists(sample_csv_path):
            pytest.skip("Sample CSV file not found")

        parser = CSVParser(org_id=1)
        transactions = parser.parse(sample_csv_path)

        assert len(transactions) > 0

        # Check first transaction
        first_tx = transactions[0]
        assert 'org_id' in first_tx
        assert 'transaction_date' in first_tx
        assert 'amount' in first_tx
        assert 'description' in first_tx
        assert first_tx['org_id'] == 1

    def test_parse_with_duplicates(self, duplicate_csv_path):
        """Test parsing CSV with duplicate transactions"""
        if not os.path.exists(duplicate_csv_path):
            pytest.skip("Duplicate CSV file not found")

        parser = CSVParser(org_id=1)
        transactions = parser.parse(duplicate_csv_path)

        assert len(transactions) > 0

        # Should include duplicates (duplicate detection happens later)
        descriptions = [tx['description'] for tx in transactions]
        assert 'DONATION - JOHN SMITH' in descriptions

    def test_header_mapping(self):
        """Test CSV header mapping functionality"""
        parser = CSVParser(org_id=1)

        # Test standard headers
        headers = ['Date', 'Description', 'Amount', 'Balance']
        mapping = parser._get_header_mapping(headers)

        assert 'date' in mapping
        assert 'description' in mapping
        assert 'amount' in mapping
        assert 'balance' in mapping

    def test_map_row_data(self):
        """Test row data mapping"""
        parser = CSVParser(org_id=1)

        row = {
            'Date': '2024-01-01',
            'Description': 'Test Transaction',
            'Amount': '100.00',
            'Balance': '1000.00'
        }

        header_mapping = {
            'date': 'Date',
            'description': 'Description',
            'amount': 'Amount',
            'balance': 'Balance'
        }

        mapped_data = parser._map_row_data(row, header_mapping)

        assert mapped_data['date'] == '2024-01-01'
        assert mapped_data['description'] == 'Test Transaction'
        assert mapped_data['amount'] == '100.00'
        assert mapped_data['balance'] == '1000.00'

    def test_separate_debit_credit_columns(self):
        """Test handling separate debit/credit columns"""
        parser = CSVParser(org_id=1)

        # Test debit transaction
        row_debit = {'Debit': '45.67', 'Credit': ''}
        header_mapping = {'debit': 'Debit', 'credit': 'Credit'}

        mapped_data = parser._map_row_data(row_debit, header_mapping)
        assert mapped_data['amount'] == -45.67

        # Test credit transaction
        row_credit = {'Debit': '', 'Credit': '100.00'}
        mapped_data = parser._map_row_data(row_credit, header_mapping)
        assert mapped_data['amount'] == 100.00

    def test_invalid_file(self):
        """Test handling of invalid files"""
        parser = CSVParser(org_id=1)

        with pytest.raises(ValueError):
            parser.parse('nonexistent_file.csv')

        with pytest.raises(ValueError):
            parser.parse('test.pdf')

    def test_is_valid_transaction(self):
        """Test transaction validation"""
        parser = CSVParser(org_id=1)

        # Valid transaction
        valid_tx = {
            'transaction_date': '2024-01-01',
            'amount': 100.0,
            'description': 'Test transaction'
        }
        assert parser._is_valid_transaction(valid_tx) == True

        # Invalid transactions
        invalid_tx_no_date = {
            'amount': 100.0,
            'description': 'Test transaction'
        }
        assert parser._is_valid_transaction(invalid_tx_no_date) == False

        invalid_tx_no_amount = {
            'transaction_date': '2024-01-01',
            'description': 'Test transaction'
        }
        assert parser._is_valid_transaction(invalid_tx_no_amount) == False


if __name__ == '__main__':
    pytest.main([__file__])