"""
Tests for ingestion pipeline and related components
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import os

from ingestion.validators import TransactionValidator, FileValidator, ValidationError
from ingestion.processors import TransactionProcessor, ImportBatchProcessor
from ingestion.pipeline import IngestionPipeline


class TestTransactionValidator:
    """Test transaction validation"""

    def test_validate_valid_transaction(self):
        """Test validation of a valid transaction"""
        validator = TransactionValidator()

        valid_transaction = {
            'org_id': 1,
            'transaction_date': '2024-01-01',
            'amount': 100.50,
            'description': 'Test transaction'
        }

        result = validator.validate_transaction(valid_transaction)

        assert result['org_id'] == 1
        assert result['transaction_date'] == '2024-01-01'
        assert result['amount'] == 100.50
        assert result['description'] == 'Test transaction'
        assert result['transaction_type'] == 'CREDIT'

    def test_validate_missing_required_field(self):
        """Test validation with missing required field"""
        validator = TransactionValidator()

        invalid_transaction = {
            'org_id': 1,
            'transaction_date': '2024-01-01',
            # Missing amount and description
        }

        with pytest.raises(ValidationError):
            validator.validate_transaction(invalid_transaction)

    def test_validate_invalid_date_format(self):
        """Test validation with invalid date format"""
        validator = TransactionValidator()

        invalid_transaction = {
            'org_id': 1,
            'transaction_date': 'invalid-date',
            'amount': 100.00,
            'description': 'Test'
        }

        with pytest.raises(ValidationError):
            validator.validate_transaction(invalid_transaction)

    def test_validate_invalid_amount(self):
        """Test validation with invalid amount"""
        validator = TransactionValidator()

        invalid_transaction = {
            'org_id': 1,
            'transaction_date': '2024-01-01',
            'amount': 'not-a-number',
            'description': 'Test'
        }

        with pytest.raises(ValidationError):
            validator.validate_transaction(invalid_transaction)

    def test_validate_batch(self):
        """Test batch validation"""
        validator = TransactionValidator()

        transactions = [
            {
                'org_id': 1,
                'transaction_date': '2024-01-01',
                'amount': 100.00,
                'description': 'Valid transaction'
            },
            {
                'org_id': 1,
                'transaction_date': 'invalid-date',
                'amount': 100.00,
                'description': 'Invalid transaction'
            }
        ]

        result = validator.validate_batch(transactions)

        assert len(result['validated_transactions']) == 1
        assert len(result['failed_transactions']) == 1
        assert result['summary']['total_transactions'] == 2
        assert result['summary']['valid_transactions'] == 1
        assert result['summary']['invalid_transactions'] == 1

    def test_validate_org_id(self):
        """Test organization ID validation"""
        validator = TransactionValidator()

        # Valid org IDs
        assert validator._validate_org_id(1) == 1
        assert validator._validate_org_id('1') == 1

        # Invalid org IDs
        with pytest.raises(ValidationError):
            validator._validate_org_id(0)

        with pytest.raises(ValidationError):
            validator._validate_org_id(-1)

        with pytest.raises(ValidationError):
            validator._validate_org_id('not-a-number')

    def test_validate_description_cleaning(self):
        """Test description validation and cleaning"""
        validator = TransactionValidator()

        # Test cleaning
        dirty_desc = '  Test <script>alert("xss")</script> "payment"  '
        clean_desc = validator._validate_description(dirty_desc)
        assert '<script>' not in clean_desc
        assert 'alert(' not in clean_desc
        assert clean_desc.strip() == clean_desc

        # Test length limit
        long_desc = 'x' * 300
        truncated = validator._validate_description(long_desc)
        assert len(truncated) <= validator.max_description_length

    def test_validate_transaction_type(self):
        """Test transaction type validation"""
        validator = TransactionValidator()

        assert validator._validate_transaction_type('DEBIT') == 'DEBIT'
        assert validator._validate_transaction_type('debit') == 'DEBIT'
        assert validator._validate_transaction_type('invalid') == 'UNKNOWN'
        assert validator._validate_transaction_type(None) == 'UNKNOWN'


class TestFileValidator:
    """Test file validation"""

    def test_validate_nonexistent_file(self):
        """Test validation of nonexistent file"""
        validator = FileValidator()

        result = validator.validate_file('nonexistent_file.csv')

        assert result['is_valid'] == False
        assert 'File does not exist' in result['errors']

    @patch('os.path.exists')
    @patch('os.path.getsize')
    def test_validate_file_size(self, mock_getsize, mock_exists):
        """Test file size validation"""
        validator = FileValidator()
        mock_exists.return_value = True

        # Test oversized file
        mock_getsize.return_value = validator.max_file_size + 1
        result = validator.validate_file('large_file.csv')
        assert result['is_valid'] == False
        assert any('size' in error for error in result['errors'])

        # Test empty file
        mock_getsize.return_value = 0
        result = validator.validate_file('empty_file.csv')
        assert result['is_valid'] == False
        assert any('empty' in error.lower() for error in result['errors'])

    @patch('os.path.exists')
    @patch('os.path.getsize')
    def test_validate_file_extension(self, mock_getsize, mock_exists):
        """Test file extension validation"""
        validator = FileValidator()
        mock_exists.return_value = True
        mock_getsize.return_value = 1000

        # Valid extensions
        for ext in ['.csv', '.pdf', '.ofx']:
            with patch('builtins.open', mock_open_file()):
                result = validator.validate_file(f'test{ext}')
                assert ext not in result['errors']  # Should not have extension error

        # Invalid extension
        with patch('builtins.open', mock_open_file()):
            result = validator.validate_file('test.txt')
            assert result['is_valid'] == False
            assert any('extension' in error for error in result['errors'])


def mock_open_file():
    """Mock file opening for testing"""
    mock_file = MagicMock()
    mock_file.read.return_value = 'test content'
    return mock_file


class TestTransactionProcessor:
    """Test transaction processing"""

    def test_process_transaction(self):
        """Test basic transaction processing"""
        processor = TransactionProcessor()

        transaction = {
            'transaction_date': '2024-01-01',
            'amount': -45.67,
            'description': '  OFFICE DEPOT - SUPPLIES  '
        }

        processed = processor.process_transaction(transaction)

        assert 'processed_at' in processed
        assert processed['description'] == 'OFFICE DEPOT - SUPPLIES'
        assert processed['transaction_type'] == 'DEBIT'

    def test_auto_categorize(self):
        """Test automatic categorization"""
        processor = TransactionProcessor()

        # Test office supplies transaction
        transaction = {
            'amount': -45.67,
            'description': 'OFFICE DEPOT SUPPLIES'
        }

        category_id = processor._auto_categorize(transaction)
        assert category_id is not None  # Should find a matching category

    def test_process_batch(self):
        """Test batch processing"""
        processor = TransactionProcessor()

        transactions = [
            {
                'transaction_date': '2024-01-01',
                'amount': 100.00,
                'description': 'Test transaction 1'
            },
            {
                'transaction_date': '2024-01-02',
                'amount': -50.00,
                'description': 'Test transaction 2'
            }
        ]

        result = processor.process_batch(transactions)

        assert len(result['processed_transactions']) == 2
        assert result['summary']['total_transactions'] == 2
        assert result['summary']['processed_transactions'] == 2

    def test_enhance_description(self):
        """Test description enhancement"""
        processor = TransactionProcessor()

        # Test cleaning
        dirty_desc = '  **AMAZON** MARKETPLACE  ***  '
        enhanced = processor._enhance_description(dirty_desc)
        assert enhanced == 'AMAZON MARKETPLACE'

    def test_standardize_merchant_names(self):
        """Test merchant name standardization"""
        processor = TransactionProcessor()

        # Test Amazon
        standardized = processor._standardize_merchant_names('AMZN MKTP PURCHASE')
        assert 'Amazon Marketplace' in standardized

        # Test PayPal
        standardized = processor._standardize_merchant_names('PAYPAL *TRANSFER')
        assert 'PayPal' in standardized


class TestImportBatchProcessor:
    """Test import batch processing"""

    def test_create_import_batch(self):
        """Test import batch creation"""
        processor = ImportBatchProcessor()

        batch = processor.create_import_batch(
            org_id=1,
            filename='test.csv',
            file_format='CSV',
            total_transactions=10
        )

        assert batch['org_id'] == 1
        assert batch['filename'] == 'test.csv'
        assert batch['file_format'] == 'CSV'
        assert batch['total_transactions'] == 10
        assert batch['status'] == 'PENDING'
        assert 'import_date' in batch

    def test_update_batch_status(self):
        """Test batch status updates"""
        processor = ImportBatchProcessor()

        batch = {
            'status': 'PENDING',
            'successful_imports': 0,
            'failed_imports': 0
        }

        updated_batch = processor.update_batch_status(
            batch,
            new_status='COMPLETED',
            successful_imports=8,
            failed_imports=2
        )

        assert updated_batch['status'] == 'COMPLETED'
        assert updated_batch['successful_imports'] == 8
        assert updated_batch['failed_imports'] == 2

    def test_generate_batch_summary(self):
        """Test batch summary generation"""
        processor = ImportBatchProcessor()

        batch = {
            'id': 1,
            'filename': 'test.csv',
            'status': 'COMPLETED',
            'total_transactions': 10,
            'successful_imports': 8,
            'failed_imports': 2,
            'duplicate_count': 1,
            'import_date': datetime.now()
        }

        summary = processor.generate_batch_summary(batch)

        assert summary['total_transactions'] == 10
        assert summary['successful_imports'] == 8
        assert summary['failed_imports'] == 2
        assert summary['success_rate'] == 80.0


class TestIngestionPipeline:
    """Test main ingestion pipeline"""

    def test_detect_file_format(self):
        """Test file format detection"""
        pipeline = IngestionPipeline(org_id=1)

        assert pipeline._detect_file_format('test.csv') == 'CSV'
        assert pipeline._detect_file_format('test.CSV') == 'CSV'
        assert pipeline._detect_file_format('test.pdf') == 'PDF'
        assert pipeline._detect_file_format('test.ofx') == 'OFX'
        assert pipeline._detect_file_format('test.txt') == 'UNKNOWN'

    @patch('os.path.exists')
    @patch('os.path.getsize')
    def test_ingest_file_validation_failure(self, mock_getsize, mock_exists):
        """Test ingestion with file validation failure"""
        pipeline = IngestionPipeline(org_id=1)

        # Mock invalid file
        mock_exists.return_value = False

        result = pipeline.ingest_file('nonexistent.csv')

        assert result['success'] == False
        assert len(result['validation_errors']) > 0

    def test_transactions_match(self):
        """Test transaction matching logic"""
        pipeline = IngestionPipeline(org_id=1)

        tx1 = {
            'transaction_date': '2024-01-01',
            'amount': 100.00,
            'description': 'Test transaction'
        }

        tx2 = {
            'transaction_date': '2024-01-01',
            'amount': 100.00,
            'description': 'Test transaction'
        }

        tx3 = {
            'transaction_date': '2024-01-02',
            'amount': 200.00,
            'description': 'Different transaction'
        }

        assert pipeline._transactions_match(tx1, tx2) == True
        assert pipeline._transactions_match(tx1, tx3) == False


if __name__ == '__main__':
    pytest.main([__file__])