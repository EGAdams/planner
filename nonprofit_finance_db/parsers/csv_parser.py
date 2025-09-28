import csv
import os
from typing import List, Dict, Any, Optional
from .base_parser import BaseParser

class CSVParser(BaseParser):
    """Parser for CSV bank statement files"""

    def __init__(self, org_id: int):
        super().__init__(org_id)
        self.supported_formats = ['.csv']

    def validate_format(self, file_path: str) -> bool:
        """Check if file is a CSV format"""
        return file_path.lower().endswith('.csv') and os.path.exists(file_path)

    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse CSV bank statement file

        Args:
            file_path: Path to CSV file

        Returns:
            List of standardized transaction dictionaries
        """
        if not self.validate_format(file_path):
            raise ValueError(f"Invalid CSV file: {file_path}")

        transactions = []

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                # Try to detect dialect
                sample = file.read(1024)
                file.seek(0)
                dialect = csv.Sniffer().sniff(sample)

                reader = csv.DictReader(file, dialect=dialect)

                # Map common CSV headers to standard fields
                header_mapping = self._get_header_mapping(reader.fieldnames)

                for row in reader:
                    if self._is_valid_row(row):
                        raw_data = self._map_row_data(row, header_mapping)
                        transaction = self.standardize_transaction(raw_data)

                        if self._is_valid_transaction(transaction):
                            transactions.append(transaction)

        except Exception as e:
            raise ValueError(f"Error parsing CSV file {file_path}: {str(e)}")

        return transactions

    def _get_header_mapping(self, fieldnames: List[str]) -> Dict[str, str]:
        """
        Map CSV headers to standard field names

        Args:
            fieldnames: List of CSV column headers

        Returns:
            Dictionary mapping CSV headers to standard field names
        """
        header_mapping = {}

        if not fieldnames:
            return header_mapping

        # Normalize headers for comparison
        normalized_headers = {header.lower().strip(): header for header in fieldnames}

        # Common date field variations
        date_fields = ['date', 'transaction date', 'trans date', 'posting date', 'effective date']
        for field in date_fields:
            if field in normalized_headers:
                header_mapping['date'] = normalized_headers[field]
                break

        # Common amount field variations
        amount_fields = ['amount', 'transaction amount', 'debit amount', 'credit amount', 'value']
        for field in amount_fields:
            if field in normalized_headers:
                header_mapping['amount'] = normalized_headers[field]
                break

        # Check for separate debit/credit columns
        if 'debit' in normalized_headers and 'credit' in normalized_headers:
            header_mapping['debit'] = normalized_headers['debit']
            header_mapping['credit'] = normalized_headers['credit']

        # Common description field variations
        desc_fields = ['description', 'transaction description', 'memo', 'details', 'particulars']
        for field in desc_fields:
            if field in normalized_headers:
                header_mapping['description'] = normalized_headers[field]
                break

        # Balance field variations
        balance_fields = ['balance', 'running balance', 'account balance', 'balance after']
        for field in balance_fields:
            if field in normalized_headers:
                header_mapping['balance'] = normalized_headers[field]
                break

        # Reference field variations
        ref_fields = ['reference', 'ref', 'reference number', 'transaction id', 'check number']
        for field in ref_fields:
            if field in normalized_headers:
                header_mapping['reference'] = normalized_headers[field]
                break

        return header_mapping

    def _map_row_data(self, row: Dict[str, str], header_mapping: Dict[str, str]) -> Dict[str, Any]:
        """
        Map CSV row data using header mapping

        Args:
            row: CSV row data
            header_mapping: Mapping of standard fields to CSV headers

        Returns:
            Mapped row data
        """
        mapped_data = {}

        # Map standard fields
        for standard_field, csv_header in header_mapping.items():
            if csv_header in row:
                mapped_data[standard_field] = row[csv_header]

        # Handle separate debit/credit columns
        if 'debit' in header_mapping and 'credit' in header_mapping:
            debit_val = self._parse_amount(mapped_data.get('debit'))
            credit_val = self._parse_amount(mapped_data.get('credit'))

            if debit_val and debit_val != 0:
                mapped_data['amount'] = -abs(debit_val)  # Debits are negative
            elif credit_val and credit_val != 0:
                mapped_data['amount'] = abs(credit_val)  # Credits are positive
            else:
                mapped_data['amount'] = 0

        return mapped_data

    def _is_valid_row(self, row: Dict[str, str]) -> bool:
        """Check if CSV row contains valid transaction data"""
        if not row:
            return False

        # Row should have some non-empty values
        non_empty_values = [v for v in row.values() if v and str(v).strip()]
        return len(non_empty_values) > 0

    def _is_valid_transaction(self, transaction: Dict[str, Any]) -> bool:
        """Check if parsed transaction has required fields"""
        required_fields = ['transaction_date', 'amount', 'description']

        for field in required_fields:
            if not transaction.get(field):
                return False

        # Amount should be a valid number
        try:
            float(transaction['amount'])
        except (ValueError, TypeError):
            return False

        return True

class AdvancedCSVParser(CSVParser):
    """Enhanced CSV parser with bank-specific configurations"""

    def __init__(self, org_id: int, bank_config: Optional[Dict[str, Any]] = None):
        super().__init__(org_id)
        self.bank_config = bank_config or {}

    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse CSV with bank-specific configurations"""
        if self.bank_config:
            return self._parse_with_config(file_path)
        else:
            return super().parse(file_path)

    def _parse_with_config(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse CSV using bank-specific configuration"""
        transactions = []

        with open(file_path, 'r', encoding=self.bank_config.get('encoding', 'utf-8')) as file:
            # Skip header rows if configured
            skip_rows = self.bank_config.get('skip_rows', 0)
            for _ in range(skip_rows):
                next(file)

            # Use custom delimiter if specified
            delimiter = self.bank_config.get('delimiter', ',')
            reader = csv.DictReader(file, delimiter=delimiter)

            # Use predefined field mapping if available
            header_mapping = self.bank_config.get('field_mapping', self._get_header_mapping(reader.fieldnames))

            for row in reader:
                if self._is_valid_row(row):
                    raw_data = self._map_row_data(row, header_mapping)

                    # Apply bank-specific transformations
                    if 'transformations' in self.bank_config:
                        raw_data = self._apply_transformations(raw_data, self.bank_config['transformations'])

                    transaction = self.standardize_transaction(raw_data)

                    if self._is_valid_transaction(transaction):
                        transactions.append(transaction)

        return transactions

    def _apply_transformations(self, data: Dict[str, Any], transformations: Dict[str, Any]) -> Dict[str, Any]:
        """Apply bank-specific data transformations"""
        for field, transform_config in transformations.items():
            if field in data and data[field]:
                transform_type = transform_config.get('type')

                if transform_type == 'regex_replace':
                    import re
                    pattern = transform_config['pattern']
                    replacement = transform_config['replacement']
                    data[field] = re.sub(pattern, replacement, str(data[field]))

                elif transform_type == 'prefix_strip':
                    prefix = transform_config['prefix']
                    if str(data[field]).startswith(prefix):
                        data[field] = str(data[field])[len(prefix):]

        return data