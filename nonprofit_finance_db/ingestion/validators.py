from typing import Dict, Any, List, Optional
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class TransactionValidator:
    """Validator for bank transaction data"""

    def __init__(self):
        self.required_fields = ['org_id', 'transaction_date', 'amount', 'description']
        self.date_format = '%Y-%m-%d'
        self.max_description_length = 255
        self.max_amount = 999999999.99  # Maximum transaction amount
        self.min_amount = -999999999.99  # Minimum transaction amount

    def validate_transaction(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a single transaction

        Args:
            transaction: Transaction dictionary to validate

        Returns:
            Validated and potentially cleaned transaction

        Raises:
            ValidationError: If validation fails
        """
        errors = []
        validated_transaction = transaction.copy()

        # Validate required fields
        for field in self.required_fields:
            if field not in transaction or transaction[field] is None:
                errors.append(f"Missing required field: {field}")

        if errors:
            raise ValidationError(f"Validation failed: {', '.join(errors)}")

        # Validate and clean individual fields
        try:
            validated_transaction['org_id'] = self._validate_org_id(transaction['org_id'])
            validated_transaction['transaction_date'] = self._validate_date(transaction['transaction_date'])
            validated_transaction['amount'] = self._validate_amount(transaction['amount'])
            validated_transaction['description'] = self._validate_description(transaction['description'])
            validated_transaction['transaction_type'] = self._validate_transaction_type(
                transaction.get('transaction_type'), validated_transaction['amount']
            )

            # Optional fields
            if 'account_number' in transaction:
                validated_transaction['account_number'] = self._validate_account_number(
                    transaction['account_number']
                )

            if 'bank_reference' in transaction:
                validated_transaction['bank_reference'] = self._validate_bank_reference(
                    transaction['bank_reference']
                )

            if 'balance_after' in transaction:
                validated_transaction['balance_after'] = self._validate_balance(
                    transaction['balance_after']
                )

        except ValidationError as e:
            raise e
        except Exception as e:
            raise ValidationError(f"Unexpected validation error: {str(e)}")

        return validated_transaction

    def validate_batch(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate a batch of transactions

        Args:
            transactions: List of transactions to validate

        Returns:
            Dictionary with validation results
        """
        validated_transactions = []
        failed_transactions = []
        validation_summary = {
            'total_transactions': len(transactions),
            'valid_transactions': 0,
            'invalid_transactions': 0,
            'errors': []
        }

        for i, transaction in enumerate(transactions):
            try:
                validated_tx = self.validate_transaction(transaction)
                validated_transactions.append(validated_tx)
                validation_summary['valid_transactions'] += 1
            except ValidationError as e:
                failed_transactions.append({
                    'transaction_index': i,
                    'transaction': transaction,
                    'error': str(e)
                })
                validation_summary['invalid_transactions'] += 1
                validation_summary['errors'].append(f"Transaction {i}: {str(e)}")

        return {
            'validated_transactions': validated_transactions,
            'failed_transactions': failed_transactions,
            'summary': validation_summary
        }

    def _validate_org_id(self, org_id: Any) -> int:
        """Validate organization ID"""
        try:
            org_id_int = int(org_id)
            if org_id_int <= 0:
                raise ValidationError("Organization ID must be positive")
            return org_id_int
        except (ValueError, TypeError):
            raise ValidationError("Organization ID must be a valid integer")

    def _validate_date(self, date_str: Any) -> str:
        """Validate transaction date"""
        if not isinstance(date_str, str):
            raise ValidationError("Transaction date must be a string")

        try:
            # Parse and reformat to ensure consistency
            parsed_date = datetime.strptime(date_str, self.date_format)
            return parsed_date.strftime(self.date_format)
        except ValueError:
            raise ValidationError(f"Transaction date must be in format {self.date_format}")

    def _validate_amount(self, amount: Any) -> float:
        """Validate transaction amount"""
        try:
            amount_float = float(amount)

            if amount_float < self.min_amount or amount_float > self.max_amount:
                raise ValidationError(f"Amount must be between {self.min_amount} and {self.max_amount}")

            # Round to 2 decimal places for currency
            return round(amount_float, 2)

        except (ValueError, TypeError):
            raise ValidationError("Amount must be a valid number")

    def _validate_description(self, description: Any) -> str:
        """Validate and clean transaction description"""
        if not isinstance(description, str):
            raise ValidationError("Description must be a string")

        # Clean the description
        cleaned_desc = description.strip()

        if not cleaned_desc:
            raise ValidationError("Description cannot be empty")

        if len(cleaned_desc) > self.max_description_length:
            cleaned_desc = cleaned_desc[:self.max_description_length]

        # Remove potentially harmful HTML/script content
        cleaned_desc = re.sub(r'<script[^>]*>.*?</script>', '', cleaned_desc, flags=re.IGNORECASE | re.DOTALL)
        cleaned_desc = re.sub(r'<[^>]*>', '', cleaned_desc)
        # Remove potentially harmful characters
        cleaned_desc = re.sub(r'["\']', '', cleaned_desc)

        return cleaned_desc

    def _validate_transaction_type(self, transaction_type: Any, amount: float = None) -> str:
        """Validate transaction type"""
        valid_types = ['DEBIT', 'CREDIT', 'TRANSFER', 'UNKNOWN']

        if not transaction_type:
            # Auto-determine based on amount if not provided
            if amount is not None:
                return 'CREDIT' if amount > 0 else 'DEBIT'
            return 'UNKNOWN'

        if isinstance(transaction_type, str):
            transaction_type = transaction_type.upper().strip()

        if transaction_type not in valid_types:
            return 'UNKNOWN'

        return transaction_type

    def _validate_account_number(self, account_number: Any) -> Optional[str]:
        """Validate account number"""
        if account_number is None:
            return None

        if not isinstance(account_number, str):
            account_number = str(account_number)

        # Clean account number
        cleaned_account = re.sub(r'[^0-9A-Za-z\-]', '', account_number.strip())

        if len(cleaned_account) > 50:  # Reasonable limit
            raise ValidationError("Account number too long")

        return cleaned_account if cleaned_account else None

    def _validate_bank_reference(self, bank_reference: Any) -> Optional[str]:
        """Validate bank reference"""
        if bank_reference is None:
            return None

        if not isinstance(bank_reference, str):
            bank_reference = str(bank_reference)

        cleaned_ref = bank_reference.strip()

        if len(cleaned_ref) > 100:  # Reasonable limit
            cleaned_ref = cleaned_ref[:100]

        return cleaned_ref if cleaned_ref else None

    def _validate_balance(self, balance: Any) -> Optional[float]:
        """Validate balance after transaction"""
        if balance is None:
            return None

        try:
            balance_float = float(balance)
            return round(balance_float, 2)
        except (ValueError, TypeError):
            logger.warning(f"Invalid balance value: {balance}")
            return None

class FileValidator:
    """Validator for bank statement files"""

    def __init__(self):
        self.max_file_size = 50 * 1024 * 1024  # 50MB
        self.allowed_extensions = ['.csv', '.pdf', '.ofx']

    def validate_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate bank statement file

        Args:
            file_path: Path to the file to validate

        Returns:
            Validation result dictionary
        """
        import os

        validation_result = {
            'is_valid': True,
            'errors': [],
            'file_info': {}
        }

        try:
            # Check if file exists
            if not os.path.exists(file_path):
                validation_result['is_valid'] = False
                validation_result['errors'].append("File does not exist")
                return validation_result

            # Check file size
            file_size = os.path.getsize(file_path)
            validation_result['file_info']['size'] = file_size

            if file_size > self.max_file_size:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f"File size ({file_size} bytes) exceeds maximum ({self.max_file_size} bytes)")

            if file_size == 0:
                validation_result['is_valid'] = False
                validation_result['errors'].append("File is empty")

            # Check file extension
            file_extension = os.path.splitext(file_path.lower())[1]
            validation_result['file_info']['extension'] = file_extension

            if file_extension not in self.allowed_extensions:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f"File extension {file_extension} not supported. Allowed: {self.allowed_extensions}")

            # Basic file readability check
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    f.read(100)  # Try to read first 100 characters
            except UnicodeDecodeError:
                # Try binary mode for PDF/OFX files
                try:
                    with open(file_path, 'rb') as f:
                        f.read(100)
                except Exception as e:
                    validation_result['is_valid'] = False
                    validation_result['errors'].append(f"File is not readable: {str(e)}")
            except Exception as e:
                validation_result['is_valid'] = False
                validation_result['errors'].append(f"File access error: {str(e)}")

        except Exception as e:
            validation_result['is_valid'] = False
            validation_result['errors'].append(f"Unexpected error during file validation: {str(e)}")

        return validation_result