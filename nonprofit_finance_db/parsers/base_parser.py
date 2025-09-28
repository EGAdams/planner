from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

class BaseParser(ABC):
    """Base class for all bank statement parsers"""

    def __init__(self, org_id: int):
        self.org_id = org_id
        self.supported_formats = []

    @abstractmethod
    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse a bank statement file and return a list of transaction dictionaries

        Args:
            file_path: Path to the bank statement file

        Returns:
            List of transaction dictionaries with standardized fields
        """
        pass

    @abstractmethod
    def validate_format(self, file_path: str) -> bool:
        """
        Check if the file format is supported by this parser

        Args:
            file_path: Path to the file to validate

        Returns:
            True if format is supported, False otherwise
        """
        pass

    def standardize_transaction(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert raw transaction data to standardized format

        Args:
            raw_data: Raw transaction data from bank statement

        Returns:
            Standardized transaction dictionary
        """
        return {
            'org_id': self.org_id,
            'transaction_date': self._parse_date(raw_data.get('date')),
            'amount': self._parse_amount(raw_data.get('amount')),
            'description': self._clean_description(raw_data.get('description', '')),
            'transaction_type': self._determine_type(raw_data.get('amount')),
            'account_number': raw_data.get('account_number'),
            'bank_reference': raw_data.get('reference'),
            'balance_after': self._parse_amount(raw_data.get('balance')),
            'raw_data': json.dumps(raw_data)
        }

    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse various date formats to YYYY-MM-DD"""
        if not date_str:
            return None

        # Common date formats
        formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%d/%m/%Y',
            '%m-%d-%Y',
            '%d-%m-%Y',
            '%Y/%m/%d',
            '%m/%d/%y',
            '%d/%m/%y'
        ]

        for fmt in formats:
            try:
                parsed_date = datetime.strptime(date_str.strip(), fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue

        return None

    def _parse_amount(self, amount_str: Any) -> Optional[float]:
        """Parse amount string to float"""
        if amount_str is None:
            return None

        if isinstance(amount_str, (int, float)):
            return float(amount_str)

        # Clean amount string
        clean_amount = str(amount_str).strip().replace(',', '').replace('$', '')

        # Handle parentheses for negative amounts
        if clean_amount.startswith('(') and clean_amount.endswith(')'):
            clean_amount = '-' + clean_amount[1:-1]

        try:
            return float(clean_amount)
        except ValueError:
            return None

    def _clean_description(self, description: str) -> str:
        """Clean and standardize transaction description"""
        if not description:
            return ''

        # Remove extra whitespace
        cleaned = ' '.join(description.strip().split())

        # Remove common bank codes and formatting
        cleaned = cleaned.replace('**', '').replace('***', '')

        return cleaned[:255]  # Limit length

    def _determine_type(self, amount: Any) -> str:
        """Determine transaction type based on amount"""
        if amount is None:
            return 'UNKNOWN'

        parsed_amount = self._parse_amount(amount)
        if parsed_amount is None:
            return 'UNKNOWN'

        return 'DEBIT' if parsed_amount < 0 else 'CREDIT'