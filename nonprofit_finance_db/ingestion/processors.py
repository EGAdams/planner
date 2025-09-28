from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import re

logger = logging.getLogger(__name__)

class TransactionProcessor:
    """Processor for bank transaction data"""

    def __init__(self):
        self.category_rules = self._load_default_category_rules()

    def process_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single transaction with business logic

        Args:
            transaction: Transaction to process

        Returns:
            Processed transaction with additional fields
        """
        processed_transaction = transaction.copy()

        # Auto-categorize transaction
        processed_transaction['category_id'] = self._auto_categorize(transaction)

        # Add processing metadata
        processed_transaction['processed_at'] = datetime.now()

        # Clean and enhance description
        processed_transaction['description'] = self._enhance_description(
            transaction.get('description', '')
        )

        # Determine transaction type if not set
        if not processed_transaction.get('transaction_type'):
            processed_transaction['transaction_type'] = self._determine_type(
                transaction.get('amount')
            )

        return processed_transaction

    def process_batch(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Process a batch of transactions

        Args:
            transactions: List of transactions to process

        Returns:
            Processing results dictionary
        """
        processed_transactions = []
        processing_summary = {
            'total_transactions': len(transactions),
            'processed_transactions': 0,
            'categorized_transactions': 0,
            'uncategorized_transactions': 0,
            'processing_errors': []
        }

        for i, transaction in enumerate(transactions):
            try:
                processed_tx = self.process_transaction(transaction)
                processed_transactions.append(processed_tx)
                processing_summary['processed_transactions'] += 1

                if processed_tx.get('category_id'):
                    processing_summary['categorized_transactions'] += 1
                else:
                    processing_summary['uncategorized_transactions'] += 1

            except Exception as e:
                logger.error(f"Error processing transaction {i}: {str(e)}")
                processing_summary['processing_errors'].append({
                    'transaction_index': i,
                    'error': str(e)
                })
                # Add transaction without processing
                processed_transactions.append(transaction)

        return {
            'processed_transactions': processed_transactions,
            'summary': processing_summary
        }

    def _auto_categorize(self, transaction: Dict[str, Any]) -> Optional[int]:
        """
        Automatically categorize transaction based on description

        Args:
            transaction: Transaction to categorize

        Returns:
            Category ID or None if no match found
        """
        description = transaction.get('description', '').lower()
        amount = transaction.get('amount', 0)

        # Apply category rules
        for rule in self.category_rules:
            if self._matches_rule(description, amount, rule):
                return rule['category_id']

        return None

    def _matches_rule(self, description: str, amount: float, rule: Dict[str, Any]) -> bool:
        """Check if transaction matches a categorization rule"""
        # Check keywords
        keywords = rule.get('keywords', [])
        if keywords:
            for keyword in keywords:
                if keyword.lower() in description:
                    break
            else:
                return False

        # Check amount range
        min_amount = rule.get('min_amount')
        max_amount = rule.get('max_amount')

        if min_amount is not None and amount < min_amount:
            return False

        if max_amount is not None and amount > max_amount:
            return False

        # Check transaction type
        transaction_type = rule.get('transaction_type')
        if transaction_type:
            if transaction_type == 'DEBIT' and amount >= 0:
                return False
            if transaction_type == 'CREDIT' and amount < 0:
                return False

        return True

    def _enhance_description(self, description: str) -> str:
        """Enhance transaction description with cleaning and standardization"""
        if not description:
            return description

        # Remove extra whitespace
        enhanced = ' '.join(description.strip().split())

        # Remove common bank formatting
        enhanced = re.sub(r'\*+', '', enhanced)
        enhanced = re.sub(r'#+', '', enhanced)

        # Standardize common merchant names
        enhanced = self._standardize_merchant_names(enhanced)

        return enhanced

    def _standardize_merchant_names(self, description: str) -> str:
        """Standardize common merchant names"""
        # Common merchant name mappings
        merchant_mappings = {
            r'AMZN MKTP': 'Amazon Marketplace',
            r'PAYPAL \*': 'PayPal',
            r'SQ \*': 'Square',
            r'TST\* ': '',  # Remove test prefixes
            r'POS ': '',    # Remove POS prefixes
        }

        standardized = description
        for pattern, replacement in merchant_mappings.items():
            standardized = re.sub(pattern, replacement, standardized, flags=re.IGNORECASE)

        return standardized.strip()

    def _determine_type(self, amount: Any) -> str:
        """Determine transaction type based on amount"""
        if amount is None:
            return 'UNKNOWN'

        try:
            amount_float = float(amount)
            return 'DEBIT' if amount_float < 0 else 'CREDIT'
        except (ValueError, TypeError):
            return 'UNKNOWN'

    def _load_default_category_rules(self) -> List[Dict[str, Any]]:
        """Load default categorization rules"""
        return [
            {
                'category_id': 1,  # Office Supplies
                'keywords': ['office depot', 'staples', 'amazon', 'supplies'],
                'transaction_type': 'DEBIT',
                'max_amount': -5.00
            },
            {
                'category_id': 2,  # Travel
                'keywords': ['uber', 'lyft', 'taxi', 'hotel', 'airline', 'gas station'],
                'transaction_type': 'DEBIT'
            },
            {
                'category_id': 3,  # Meals
                'keywords': ['restaurant', 'food', 'cafe', 'starbucks', 'lunch', 'dinner'],
                'transaction_type': 'DEBIT',
                'max_amount': -5.00
            },
            {
                'category_id': 4,  # Donations/Revenue
                'keywords': ['donation', 'contribution', 'grant', 'funding'],
                'transaction_type': 'CREDIT'
            },
            {
                'category_id': 5,  # Bank Fees
                'keywords': ['fee', 'charge', 'penalty', 'overdraft', 'maintenance'],
                'transaction_type': 'DEBIT',
                'max_amount': -1.00
            },
            {
                'category_id': 6,  # Utilities
                'keywords': ['electric', 'gas', 'water', 'internet', 'phone', 'utility'],
                'transaction_type': 'DEBIT'
            }
        ]

class ImportBatchProcessor:
    """Processor for import batch operations"""

    def __init__(self):
        self.batch_status_transitions = {
            'PENDING': ['PROCESSING', 'FAILED'],
            'PROCESSING': ['COMPLETED', 'FAILED'],
            'COMPLETED': [],
            'FAILED': ['PENDING']  # Allow retry
        }

    def create_import_batch(self,
                          org_id: int,
                          filename: str,
                          file_format: str,
                          total_transactions: int) -> Dict[str, Any]:
        """
        Create a new import batch record

        Args:
            org_id: Organization ID
            filename: Name of the imported file
            file_format: Format of the file (CSV, PDF, OFX)
            total_transactions: Total number of transactions in file

        Returns:
            Import batch dictionary
        """
        return {
            'org_id': org_id,
            'filename': filename,
            'file_format': file_format.upper(),
            'import_date': datetime.now(),
            'total_transactions': total_transactions,
            'successful_imports': 0,
            'failed_imports': 0,
            'duplicate_count': 0,
            'status': 'PENDING',
            'error_log': None,
            'created_at': datetime.now()
        }

    def update_batch_status(self,
                          batch: Dict[str, Any],
                          new_status: str,
                          successful_imports: int = None,
                          failed_imports: int = None,
                          duplicate_count: int = None,
                          error_log: str = None) -> Dict[str, Any]:
        """
        Update import batch status and statistics

        Args:
            batch: Import batch to update
            new_status: New status
            successful_imports: Number of successful imports
            failed_imports: Number of failed imports
            duplicate_count: Number of duplicates found
            error_log: Error log if applicable

        Returns:
            Updated batch dictionary
        """
        current_status = batch.get('status', 'PENDING')

        # Validate status transition
        if new_status not in self.batch_status_transitions.get(current_status, []):
            logger.warning(f"Invalid status transition from {current_status} to {new_status}")

        updated_batch = batch.copy()
        updated_batch['status'] = new_status

        if successful_imports is not None:
            updated_batch['successful_imports'] = successful_imports

        if failed_imports is not None:
            updated_batch['failed_imports'] = failed_imports

        if duplicate_count is not None:
            updated_batch['duplicate_count'] = duplicate_count

        if error_log is not None:
            updated_batch['error_log'] = error_log

        return updated_batch

    def generate_batch_summary(self, batch: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary report for import batch"""
        total_transactions = batch.get('total_transactions', 0)
        successful_imports = batch.get('successful_imports', 0)
        failed_imports = batch.get('failed_imports', 0)
        duplicate_count = batch.get('duplicate_count', 0)

        success_rate = (successful_imports / total_transactions * 100) if total_transactions > 0 else 0

        return {
            'batch_id': batch.get('id'),
            'filename': batch.get('filename'),
            'status': batch.get('status'),
            'total_transactions': total_transactions,
            'successful_imports': successful_imports,
            'failed_imports': failed_imports,
            'duplicate_count': duplicate_count,
            'success_rate': round(success_rate, 2),
            'import_date': batch.get('import_date'),
            'processing_time': self._calculate_processing_time(batch)
        }

    def _calculate_processing_time(self, batch: Dict[str, Any]) -> Optional[float]:
        """Calculate processing time for completed batches"""
        import_date = batch.get('import_date')
        status = batch.get('status')

        if not import_date or status not in ['COMPLETED', 'FAILED']:
            return None

        # For now, return None since we don't track completion time
        # In a real implementation, you'd store completion_time
        return None