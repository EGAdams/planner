"""
Tests for bank statement parsers
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import date
from parsers.csv_parser import CSVParser
from parsers.pdf_parser import PDFParser
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


class TestPDFParser:
    """Test PDF parser functionality with Docling extractor"""

    @pytest.fixture
    def mock_docling_extractor(self):
        """Create a mock Docling extractor for testing"""
        mock = MagicMock()
        mock.validate_format.return_value = True
        mock.parse_transactions.return_value = [
            {
                'date': date(2024, 1, 15),
                'description': 'Test Transaction 1',
                'amount': -45.67,
                'raw_date': '01/15',
                'raw_amount': '(45.67)',
                'raw_description': 'Test Transaction 1'
            },
            {
                'date': date(2024, 1, 16),
                'description': 'Test Transaction 2',
                'amount': 100.00,
                'raw_date': '01/16',
                'raw_amount': '100.00',
                'raw_description': 'Test Transaction 2'
            }
        ]
        mock.extract_account_info.return_value = {
            'account_number': '****1234',
            'account_type': 'Checking',
            'bank_name': 'Fifth Third Bank',
            'statement_date': None
        }
        mock.extract_statement_period.return_value = (date(2024, 1, 1), date(2024, 1, 31))
        mock.extract_text.return_value = "Sample PDF text content"
        mock.extract_tables.return_value = [[['Date', 'Description', 'Amount'], ['01/15', 'Test Transaction', '-45.67']]]
        return mock

    def test_pdf_parser_initialization(self):
        """Test PDF parser initialization"""
        parser = PDFParser(org_id=1)
        assert parser.org_id == 1
        assert 'PDF' in parser.supported_formats
        assert hasattr(parser, 'extractor')

    @patch('parsers.pdf_parser.DoclingPDFExtractor')
    def test_validate_format(self, mock_extractor_class, mock_docling_extractor):
        """Test PDF format validation"""
        mock_extractor_class.return_value = mock_docling_extractor

        parser = PDFParser(org_id=1)

        # Test valid PDF
        assert parser.validate_format('test.pdf') == True
        mock_docling_extractor.validate_format.assert_called_with('test.pdf')

        # Test invalid PDF
        mock_docling_extractor.validate_format.return_value = False
        assert parser.validate_format('invalid.pdf') == False

    @patch('parsers.pdf_parser.DoclingPDFExtractor')
    def test_parse_transactions(self, mock_extractor_class, mock_docling_extractor):
        """Test PDF transaction parsing"""
        mock_extractor_class.return_value = mock_docling_extractor

        parser = PDFParser(org_id=1)
        transactions = parser.parse('test.pdf')

        assert len(transactions) == 2
        mock_docling_extractor.parse_transactions.assert_called_with('test.pdf')

        # Check first transaction standardization
        first_tx = transactions[0]
        assert first_tx['org_id'] == 1
        assert 'transaction_date' in first_tx
        assert 'amount' in first_tx
        assert 'description' in first_tx

    @patch('parsers.pdf_parser.DoclingPDFExtractor')
    def test_extract_account_info(self, mock_extractor_class, mock_docling_extractor):
        """Test account information extraction"""
        mock_extractor_class.return_value = mock_docling_extractor

        parser = PDFParser(org_id=1)
        account_info = parser.extract_account_info('test.pdf')

        assert account_info['account_number'] == '****1234'
        assert account_info['account_type'] == 'Checking'
        assert account_info['bank_name'] == 'Fifth Third Bank'
        assert 'statement_start_date' in account_info
        assert 'statement_end_date' in account_info

        mock_docling_extractor.extract_account_info.assert_called_with('test.pdf')
        mock_docling_extractor.extract_statement_period.assert_called_with('test.pdf')

    @patch('parsers.pdf_parser.DoclingPDFExtractor')
    def test_extract_statement_period(self, mock_extractor_class, mock_docling_extractor):
        """Test statement period extraction"""
        mock_extractor_class.return_value = mock_docling_extractor

        parser = PDFParser(org_id=1)
        start_date, end_date = parser.extract_statement_period('test.pdf')

        assert start_date == date(2024, 1, 1)
        assert end_date == date(2024, 1, 31)
        mock_docling_extractor.extract_statement_period.assert_called_with('test.pdf')

    @patch('parsers.pdf_parser.DoclingPDFExtractor')
    def test_extract_text(self, mock_extractor_class, mock_docling_extractor):
        """Test text extraction"""
        mock_extractor_class.return_value = mock_docling_extractor

        parser = PDFParser(org_id=1)
        text = parser.extract_text('test.pdf')

        assert text == "Sample PDF text content"
        mock_docling_extractor.extract_text.assert_called_with('test.pdf')

    @patch('parsers.pdf_parser.DoclingPDFExtractor')
    def test_extract_tables(self, mock_extractor_class, mock_docling_extractor):
        """Test table extraction"""
        mock_extractor_class.return_value = mock_docling_extractor

        parser = PDFParser(org_id=1)
        tables = parser.extract_tables('test.pdf')

        assert len(tables) == 1
        assert len(tables[0]) == 2  # Header + 1 data row
        mock_docling_extractor.extract_tables.assert_called_with('test.pdf')

    @patch('parsers.pdf_parser.DoclingPDFExtractor')
    def test_parse_error_handling(self, mock_extractor_class, mock_docling_extractor):
        """Test error handling during parsing"""
        mock_extractor_class.return_value = mock_docling_extractor
        mock_docling_extractor.parse_transactions.side_effect = Exception("Parse error")

        parser = PDFParser(org_id=1)
        transactions = parser.parse('test.pdf')

        assert transactions == []  # Should return empty list on error

    @patch('parsers.pdf_parser.DoclingPDFExtractor')
    def test_account_info_error_handling(self, mock_extractor_class, mock_docling_extractor):
        """Test error handling during account info extraction"""
        mock_extractor_class.return_value = mock_docling_extractor
        mock_docling_extractor.extract_account_info.side_effect = Exception("Extract error")

        parser = PDFParser(org_id=1)
        account_info = parser.extract_account_info('test.pdf')

        # Should return default structure with None values
        assert account_info['account_number'] is None
        assert account_info['account_type'] is None
        assert account_info['bank_name'] is None

    def test_pdf_format_validation_file_extension(self):
        """Test that only PDF files are accepted"""
        parser = PDFParser(org_id=1)

        # These should be validated by the extractor, but let's test the interface
        with patch.object(parser.extractor, 'validate_format', return_value=False):
            assert parser.validate_format('test.csv') == False
            assert parser.validate_format('test.txt') == False


if __name__ == '__main__':
    pytest.main([__file__])