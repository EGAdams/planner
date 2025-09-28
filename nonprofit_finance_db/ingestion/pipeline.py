from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
import logging
import os
import json

from parsers import CSVParser, PDFParser
from detection import DuplicateDetector
from .validators import TransactionValidator, FileValidator
from .processors import TransactionProcessor, ImportBatchProcessor

logger = logging.getLogger(__name__)

class IngestionPipeline:
    """Main pipeline for bank statement data ingestion"""

    def __init__(self, org_id: int, database_connection=None):
        """
        Initialize ingestion pipeline

        Args:
            org_id: Organization ID for transactions
            database_connection: Database connection for storing data
        """
        self.org_id = org_id
        self.db_connection = database_connection

        # Initialize components
        self.file_validator = FileValidator()
        self.transaction_validator = TransactionValidator()
        self.transaction_processor = TransactionProcessor()
        self.batch_processor = ImportBatchProcessor()
        self.duplicate_detector = DuplicateDetector()

        # Initialize parsers
        self.parsers = {
            'CSV': CSVParser(org_id),
            'PDF': PDFParser(org_id)
        }

    def ingest_file(self, file_path: str, auto_process: bool = True) -> Dict[str, Any]:
        """
        Main method to ingest a bank statement file

        Args:
            file_path: Path to the bank statement file
            auto_process: Whether to automatically process high-confidence duplicates

        Returns:
            Ingestion result dictionary
        """
        logger.info(f"Starting ingestion for file: {file_path}")

        result = {
            'success': False,
            'file_path': file_path,
            'import_batch': None,
            'total_transactions': 0,
            'successful_imports': 0,
            'failed_imports': 0,
            'duplicate_count': 0,
            'validation_errors': [],
            'processing_errors': [],
            'duplicate_report': None,
            'summary': None
        }

        try:
            # Step 1: Validate file
            file_validation = self.file_validator.validate_file(file_path)
            if not file_validation['is_valid']:
                result['validation_errors'] = file_validation['errors']
                return result

            # Step 2: Determine file format and get appropriate parser
            file_format = self._detect_file_format(file_path)
            if file_format not in self.parsers:
                result['validation_errors'] = [f"Unsupported file format: {file_format}"]
                return result

            parser = self.parsers[file_format]

            # Step 3: Parse file
            logger.info("Parsing bank statement file...")
            parsed_transactions = parser.parse(file_path)
            result['total_transactions'] = len(parsed_transactions)

            if not parsed_transactions:
                result['validation_errors'] = ["No transactions found in file"]
                return result

            # Step 4: Create import batch
            filename = os.path.basename(file_path)
            import_batch = self.batch_processor.create_import_batch(
                org_id=self.org_id,
                filename=filename,
                file_format=file_format,
                total_transactions=len(parsed_transactions)
            )
            result['import_batch'] = import_batch

            # Step 5: Validate transactions
            logger.info("Validating transactions...")
            validation_result = self.transaction_validator.validate_batch(parsed_transactions)
            valid_transactions = validation_result['validated_transactions']
            result['validation_errors'] = validation_result['summary']['errors']

            if not valid_transactions:
                import_batch = self.batch_processor.update_batch_status(
                    import_batch, 'FAILED', error_log="No valid transactions found"
                )
                result['import_batch'] = import_batch
                return result

            # Step 6: Process transactions
            logger.info("Processing transactions...")
            processing_result = self.transaction_processor.process_batch(valid_transactions)
            processed_transactions = processing_result['processed_transactions']
            result['processing_errors'] = processing_result['summary']['processing_errors']

            # Step 7: Detect duplicates
            logger.info("Detecting duplicates...")
            existing_transactions = self._get_existing_transactions()
            duplicate_flags = self.duplicate_detector.find_duplicates(
                processed_transactions, existing_transactions
            )
            result['duplicate_count'] = len(duplicate_flags)
            result['duplicate_report'] = self.duplicate_detector.generate_duplicate_report(duplicate_flags)

            # Step 8: Filter out duplicates and import
            logger.info("Importing transactions to database...")
            import_result = self._import_transactions(
                processed_transactions, duplicate_flags, auto_process
            )

            result['successful_imports'] = import_result['successful_imports']
            result['failed_imports'] = import_result['failed_imports']

            # Step 9: Update import batch status
            final_status = 'COMPLETED' if import_result['successful_imports'] > 0 else 'FAILED'
            import_batch = self.batch_processor.update_batch_status(
                import_batch,
                final_status,
                successful_imports=import_result['successful_imports'],
                failed_imports=import_result['failed_imports'],
                duplicate_count=len(duplicate_flags)
            )
            result['import_batch'] = import_batch

            # Step 10: Generate summary
            result['summary'] = self.batch_processor.generate_batch_summary(import_batch)
            result['success'] = True

            logger.info(f"Ingestion completed. Imported {result['successful_imports']} transactions")

        except Exception as e:
            logger.error(f"Ingestion failed: {str(e)}")
            result['processing_errors'].append(f"Pipeline error: {str(e)}")

            # Update batch status to failed if batch was created
            if result.get('import_batch'):
                import_batch = self.batch_processor.update_batch_status(
                    result['import_batch'], 'FAILED', error_log=str(e)
                )
                result['import_batch'] = import_batch

        return result

    def _detect_file_format(self, file_path: str) -> str:
        """Detect file format based on extension"""
        _, ext = os.path.splitext(file_path.lower())
        format_mapping = {
            '.csv': 'CSV',
            '.pdf': 'PDF',
            '.ofx': 'OFX'
        }
        return format_mapping.get(ext, 'UNKNOWN')

    def _get_existing_transactions(self) -> List[Dict[str, Any]]:
        """
        Get existing transactions from database for duplicate detection

        Returns:
            List of existing transactions
        """
        if not self.db_connection:
            logger.warning("No database connection available for duplicate detection")
            return []

        try:
            # This would typically query the database
            # For now, return empty list
            # TODO: Implement actual database query when repositories are connected
            return []

        except Exception as e:
            logger.error(f"Error fetching existing transactions: {str(e)}")
            return []

    def _import_transactions(self,
                           transactions: List[Dict[str, Any]],
                           duplicate_flags: List[Dict[str, Any]],
                           auto_process: bool) -> Dict[str, Any]:
        """
        Import transactions to database, handling duplicates

        Args:
            transactions: List of transactions to import
            duplicate_flags: List of duplicate flags
            auto_process: Whether to auto-process high-confidence duplicates

        Returns:
            Import result dictionary
        """
        import_result = {
            'successful_imports': 0,
            'failed_imports': 0,
            'skipped_duplicates': 0
        }

        # Create set of transaction indices that are duplicates
        duplicate_indices = set()
        if auto_process:
            high_confidence_duplicates = self.duplicate_detector.get_high_confidence_duplicates(
                duplicate_flags, confidence_threshold=0.95
            )
            for flag in high_confidence_duplicates:
                # Find index of new transaction in the list
                new_tx = flag['new_transaction']
                for i, tx in enumerate(transactions):
                    if self._transactions_match(tx, new_tx):
                        duplicate_indices.add(i)
                        break

        # Import non-duplicate transactions
        for i, transaction in enumerate(transactions):
            if i in duplicate_indices:
                import_result['skipped_duplicates'] += 1
                continue

            try:
                # Add import metadata
                transaction['import_batch_id'] = None  # Will be set when batch is saved
                transaction['created_at'] = datetime.now()

                if self._save_transaction(transaction):
                    import_result['successful_imports'] += 1
                else:
                    import_result['failed_imports'] += 1

            except Exception as e:
                logger.error(f"Error importing transaction {i}: {str(e)}")
                import_result['failed_imports'] += 1

        # Save duplicate flags for manual review
        if duplicate_flags:
            self._save_duplicate_flags(duplicate_flags)

        return import_result

    def _transactions_match(self, tx1: Dict[str, Any], tx2: Dict[str, Any]) -> bool:
        """Check if two transactions are the same"""
        key_fields = ['transaction_date', 'amount', 'description']
        for field in key_fields:
            if tx1.get(field) != tx2.get(field):
                return False
        return True

    def _save_transaction(self, transaction: Dict[str, Any]) -> bool:
        """
        Save transaction to database

        Args:
            transaction: Transaction to save

        Returns:
            True if successful, False otherwise
        """
        if not self.db_connection:
            logger.warning("No database connection available for saving transaction")
            return False

        try:
            # TODO: Implement actual database save when repositories are connected
            logger.debug(f"Would save transaction: {transaction['description'][:50]}...")
            return True

        except Exception as e:
            logger.error(f"Error saving transaction: {str(e)}")
            return False

    def _save_duplicate_flags(self, duplicate_flags: List[Dict[str, Any]]) -> bool:
        """
        Save duplicate flags to database for manual review

        Args:
            duplicate_flags: List of duplicate flags to save

        Returns:
            True if successful, False otherwise
        """
        if not self.db_connection:
            logger.warning("No database connection available for saving duplicate flags")
            return False

        try:
            # TODO: Implement actual database save when repositories are connected
            logger.debug(f"Would save {len(duplicate_flags)} duplicate flags")
            return True

        except Exception as e:
            logger.error(f"Error saving duplicate flags: {str(e)}")
            return False

    def get_import_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get import history for the organization

        Args:
            limit: Maximum number of records to return

        Returns:
            List of import batch summaries
        """
        if not self.db_connection:
            logger.warning("No database connection available for import history")
            return []

        try:
            # TODO: Implement actual database query when repositories are connected
            return []

        except Exception as e:
            logger.error(f"Error fetching import history: {str(e)}")
            return []

    def retry_failed_import(self, batch_id: int) -> Dict[str, Any]:
        """
        Retry a failed import batch

        Args:
            batch_id: ID of the batch to retry

        Returns:
            Retry result dictionary
        """
        # TODO: Implement retry logic
        logger.info(f"Retry functionality not yet implemented for batch {batch_id}")
        return {'success': False, 'message': 'Retry functionality not implemented'}

class PipelineConfig:
    """Configuration class for ingestion pipeline"""

    def __init__(self):
        self.auto_process_duplicates = True
        self.duplicate_confidence_threshold = 0.95
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.batch_size = 1000  # For processing large files in chunks
        self.enable_categorization = True
        self.enable_duplicate_detection = True

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'PipelineConfig':
        """Create config from dictionary"""
        config = cls()
        for key, value in config_dict.items():
            if hasattr(config, key):
                setattr(config, key, value)
        return config

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary"""
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_')
        }