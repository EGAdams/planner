from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
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

        # Cache existing transactions fetched from the database so we do not
        # re-query for every duplicate check run.
        self._existing_transactions_cache: Optional[List[Dict[str, Any]]] = None

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
            import_batch = self._save_import_batch(import_batch)
            import_batch = self.batch_processor.update_batch_status(
                import_batch,
                'PROCESSING'
            )
            self._update_import_batch(import_batch)
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
                processed_transactions, duplicate_flags, auto_process, import_batch
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
            self._update_import_batch(import_batch)
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
                self._update_import_batch(import_batch)
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
        if self._existing_transactions_cache is not None:
            return self._existing_transactions_cache

        if not self.db_connection:
            logger.warning("No database connection available for duplicate detection")
            self._existing_transactions_cache = []
            return self._existing_transactions_cache

        try:
            query = (
                "SELECT id, org_id, transaction_date, amount, description, "
                "transaction_type, account_number, bank_reference, balance_after "
                "FROM transactions WHERE org_id = %s"
            )
            with self.db_connection.cursor(dictionary=True) as cursor:
                cursor.execute(query, (self.org_id,))
                rows = cursor.fetchall()

            # Normalize date fields to strings for downstream processing
            normalized_rows = []
            for row in rows:
                tx = dict(row)
                tx_date = tx.get('transaction_date')
                if isinstance(tx_date, (datetime, date)):
                    tx['transaction_date'] = tx_date.strftime('%Y-%m-%d')
                elif tx_date is None:
                    tx['transaction_date'] = None
                else:
                    tx['transaction_date'] = str(tx_date)
                normalized_rows.append(tx)

            self._existing_transactions_cache = normalized_rows
            return self._existing_transactions_cache

        except Exception as e:
            logger.error(f"Error fetching existing transactions: {str(e)}")
            self._existing_transactions_cache = []
            return self._existing_transactions_cache

    def _import_transactions(self,
                           transactions: List[Dict[str, Any]],
                           duplicate_flags: List[Dict[str, Any]],
                           auto_process: bool,
                           import_batch: Dict[str, Any]) -> Dict[str, Any]:
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

        if not self.db_connection:
            raise RuntimeError("Database connection required for importing transactions")

        # Create set of transaction indices that are duplicates
        duplicate_indices = set()
        if auto_process:
            high_confidence_duplicates = self.duplicate_detector.get_high_confidence_duplicates(
                duplicate_flags, confidence_threshold=0.95
            )
            for flag in high_confidence_duplicates:
                new_tx = flag['new_transaction']
                for i, tx in enumerate(transactions):
                    if self._transactions_match(tx, new_tx):
                        duplicate_indices.add(i)
                        break

        seen_keys = set()

        for i, transaction in enumerate(transactions):
            tx_key = self._get_transaction_key(transaction)
            if tx_key in seen_keys:
                duplicate_indices.add(i)
            else:
                seen_keys.add(tx_key)

            if i in duplicate_indices:
                import_result['skipped_duplicates'] += 1
                continue

            try:
                transaction['import_batch_id'] = import_batch.get('id')
                transaction_id = self._save_transaction(transaction)

                if transaction_id:
                    import_result['successful_imports'] += 1
                    # Augment cache so subsequent duplicate checks during the same
                    # ingest run are aware of the newly inserted transaction.
                    if self._existing_transactions_cache is not None:
                        cached_tx = transaction.copy()
                        cached_tx['id'] = transaction_id
                        self._existing_transactions_cache.append(cached_tx)
                else:
                    import_result['failed_imports'] += 1

            except Exception as e:
                logger.error(f"Error importing transaction {i}: {str(e)}")
                import_result['failed_imports'] += 1

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

    def _get_transaction_key(self, transaction: Dict[str, Any]) -> str:
        """Create a normalized key used for de-duplication within a batch."""
        date_part = transaction.get('transaction_date') or ''
        amount_part = transaction.get('amount') if transaction.get('amount') is not None else ''
        description = (transaction.get('description') or '').strip().lower()[:120]
        return f"{date_part}|{amount_part}|{description}"

    def _save_transaction(self, transaction: Dict[str, Any]) -> Optional[int]:
        """
        Persist a transaction to the database and return its primary key.

        Args:
            transaction: Transaction to save

        Returns:
            Inserted transaction ID, or None on failure
        """
        if not self.db_connection:
            logger.warning("No database connection available for saving transaction")
            return None

        required_fields = ['org_id', 'transaction_date', 'amount', 'description', 'transaction_type']
        for field in required_fields:
            if transaction.get(field) in (None, ''):
                raise ValueError(f"Missing required field '{field}' for transaction save")

        payload = {
            'org_id': transaction['org_id'],
            'transaction_date': transaction['transaction_date'],
            'amount': transaction['amount'],
            'description': transaction.get('description', '')[:255],
            'transaction_type': transaction.get('transaction_type', 'UNKNOWN'),
            'account_number': transaction.get('account_number'),
            'bank_reference': transaction.get('bank_reference'),
            'balance_after': transaction.get('balance_after'),
            'category_id': transaction.get('category_id'),
            'import_batch_id': transaction.get('import_batch_id'),
            'raw_data': transaction.get('raw_data')
        }

        # Ensure raw_data is serialized JSON
        if payload['raw_data'] is not None and not isinstance(payload['raw_data'], str):
            payload['raw_data'] = json.dumps(payload['raw_data'])

        columns = []
        placeholders = []
        values: List[Any] = []

        for column, value in payload.items():
            if value is not None:
                columns.append(column)
                placeholders.append('%s')
                values.append(value)

        sql = f"INSERT INTO transactions ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"

        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(sql, tuple(values))
                transaction_id = cursor.lastrowid
            self.db_connection.commit()
            return transaction_id

        except Exception as e:
            logger.error(f"Error saving transaction: {str(e)}")
            self.db_connection.rollback()
            return None

    def _save_duplicate_flags(self, duplicate_flags: List[Dict[str, Any]]) -> bool:
        """
        Save duplicate flags to database for manual review

        Args:
            duplicate_flags: List of duplicate flags to save

        Returns:
            True if successful, False otherwise
        """
        if not self.db_connection or not duplicate_flags:
            return False

        # For now, we only log duplicate metadata for investigation. Persisting
        # duplicate candidates requires schema updates (the current
        # duplicate_flags table expects two transaction IDs). We retain this
        # hook so the pipeline surface stays consistent once that table is wired
        # up.
        logger.info("Duplicate candidates detected: %s", len(duplicate_flags))
        return True

    def _save_import_batch(self, batch: Dict[str, Any]) -> Dict[str, Any]:
        """Create an import batch record in the database and attach its ID."""
        if not self.db_connection:
            logger.warning("No database connection available for saving import batch")
            return batch

        payload = {
            'org_id': batch['org_id'],
            'filename': batch['filename'],
            'file_format': batch['file_format'],
            'import_date': batch.get('import_date', datetime.now()),
            'total_transactions': batch.get('total_transactions', 0),
            'successful_imports': batch.get('successful_imports', 0),
            'failed_imports': batch.get('failed_imports', 0),
            'duplicate_count': batch.get('duplicate_count', 0),
            'status': batch.get('status', 'PENDING'),
            'error_log': batch.get('error_log')
        }

        columns = [col for col, val in payload.items() if val is not None]
        placeholders = ['%s'] * len(columns)
        values = [payload[col] for col in columns]

        sql = f"INSERT INTO import_batches ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"

        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(sql, tuple(values))
                batch_id = cursor.lastrowid
            self.db_connection.commit()
            saved_batch = batch.copy()
            saved_batch['id'] = batch_id
            return saved_batch

        except Exception as e:
            logger.error(f"Error saving import batch: {str(e)}")
            self.db_connection.rollback()
            return batch

    def _update_import_batch(self, batch: Dict[str, Any]) -> None:
        """Persist changes to an existing import batch record."""
        if not self.db_connection or not batch.get('id'):
            return

        sql = (
            "UPDATE import_batches SET status=%s, total_transactions=%s, "
            "successful_imports=%s, failed_imports=%s, duplicate_count=%s, error_log=%s "
            "WHERE id=%s"
        )
        params = (
            batch.get('status', 'PENDING'),
            batch.get('total_transactions', 0),
            batch.get('successful_imports', 0),
            batch.get('failed_imports', 0),
            batch.get('duplicate_count', 0),
            batch.get('error_log'),
            batch['id']
        )

        try:
            with self.db_connection.cursor() as cursor:
                cursor.execute(sql, params)
            self.db_connection.commit()
        except Exception as e:
            logger.error(f"Error updating import batch {batch['id']}: {str(e)}")
            self.db_connection.rollback()

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
