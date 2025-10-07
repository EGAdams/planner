"""
Docling-based PDF Extractor

This module provides advanced PDF document extraction using Docling's AI-powered
document understanding capabilities. It extracts text, tables, and metadata
with superior accuracy compared to traditional PDF parsing libraries.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
import re
from pathlib import Path

from docling.document_converter import DocumentConverter
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend

logger = logging.getLogger(__name__)

# Bank statement parsing patterns
DATE_MD = re.compile(r'^(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?$')
START_LINE_RE = re.compile(r'^(?P<md>\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s+(?P<amount>[\$\(\)\-\d,\.]+)\s+(?P<desc>.*)$')
CHECK_TRIPLE_RE = re.compile(r'(\d{3,8})\s+(?:[is]\s*)?(\d{1,2}/\d{1,2})\s+([\d,]+\.\d{2})')
STATEMENT_PERIOD_RE = re.compile(r'Statement\s+Period\s+Date\s*:\s*(\d{1,2}/\d{1,2}/\d{4})\s*-\s*(\d{1,2}/\d{1,2}/\d{4})', re.I)
ACCOUNT_NUMBER_RE = re.compile(r'Account\s*Number\s*:\s*([\dxX*]+)', re.I)
ACCOUNT_TYPE_RE = re.compile(r'Account\s*Type\s*:\s*(.+)', re.I)


class DoclingPDFExtractor:
    """
    Advanced PDF extractor using Docling for superior document understanding.

    This class handles:
    - PDF validation and format checking
    - Text extraction with better accuracy
    - Table extraction and structure recognition
    - Metadata extraction (account info, statement periods)
    - Bank statement transaction parsing
    """

    def __init__(self, org_id: int):
        """
        Initialize the Docling PDF extractor.

        Args:
            org_id: Organization ID for transaction attribution
        """
        self.org_id = org_id
        self.supported_formats = ['PDF']

        # Initialize document converter with default settings (most stable)
        self.converter = DocumentConverter()

        # Cache for processed documents to avoid redundant processing
        self._document_cache = {}

        logger.info("Docling PDF extractor initialized")

    def _get_cached_document(self, file_path: str):
        """Get cached document or convert and cache it."""
        if file_path not in self._document_cache:
            logger.info(f"[DOCLING] Converting PDF document: {file_path}")
            logger.info(f"[DOCLING] Starting Docling conversion process...")
            result = self.converter.convert(file_path)
            logger.info(f"[DOCLING] Conversion completed, caching result")
            self._document_cache[file_path] = result
            logger.info(f"[DOCLING] PDF conversion completed: {file_path}")
        else:
            logger.info(f"[DOCLING] Using cached document: {file_path}")
        return self._document_cache[file_path]

    def validate_format(self, file_path: str) -> bool:
        """
        Validate that the file is a readable PDF document.

        Args:
            file_path: Path to the PDF file

        Returns:
            bool: True if file is a valid PDF, False otherwise
        """
        try:
            logger.info(f"[DOCLING] Step 1/4: Checking file existence for {file_path}")
            path = Path(file_path)
            if not path.exists():
                logger.error(f"File does not exist: {file_path}")
                return False

            logger.info(f"[DOCLING] Step 2/4: Verifying PDF extension")
            if not path.suffix.lower() == '.pdf':
                logger.error(f"File is not a PDF: {file_path}")
                return False

            logger.info(f"[DOCLING] Step 3/4: Converting document with Docling (this may take 30-60 seconds)...")
            # Try to convert the document to validate it (will be cached)
            result = self._get_cached_document(file_path)

            logger.info(f"[DOCLING] Step 4/4: Validating conversion result")
            if result.document and len(result.document.pages) > 0:
                logger.info(f"[DOCLING] PDF validation successful: {len(result.document.pages)} pages")
                return True
            else:
                logger.error(f"PDF has no readable pages: {file_path}")
                return False

        except Exception as e:
            logger.error(f"[DOCLING] PDF validation failed for {file_path}: {e}")
            import traceback
            logger.error(f"[DOCLING] Traceback: {traceback.format_exc()}")
            return False

    def extract_text(self, file_path: str) -> str:
        """
        Extract all text content from the PDF.

        Args:
            file_path: Path to the PDF file

        Returns:
            str: Extracted text content
        """
        try:
            logger.info(f"[DOCLING] Getting document for text extraction...")
            result = self._get_cached_document(file_path)
            if result.document:
                logger.info(f"[DOCLING] Exporting document to markdown...")
                # Extract markdown text which preserves structure better
                text = result.document.export_to_markdown()
                logger.info(f"[DOCLING] Text extraction successful")
                return text
            else:
                logger.warning(f"No document content extracted from {file_path}")
                return ""

        except Exception as e:
            logger.error(f"Text extraction failed for {file_path}: {e}")
            import traceback
            logger.error(f"[DOCLING] Traceback: {traceback.format_exc()}")
            return ""

    def extract_tables(self, file_path: str) -> List[List[List[str]]]:
        """
        Extract structured table data from the PDF.

        Args:
            file_path: Path to the PDF file

        Returns:
            List[List[List[str]]]: Tables as nested lists [table][row][cell]
        """
        try:
            logger.info(f"[DOCLING] Getting document for table extraction...")
            result = self._get_cached_document(file_path)
            all_tables = []

            if result.document and result.document.tables:
                logger.info(f"[DOCLING] Found {len(result.document.tables)} tables in document")
                for i, table in enumerate(result.document.tables):
                    try:
                        logger.info(f"[DOCLING] Processing table {i+1}/{len(result.document.tables)}...")
                        # Use the modern export_to_dataframe API
                        df = table.export_to_dataframe(result.document)

                        # Convert DataFrame to nested list format
                        table_data = []

                        # Add header row
                        table_data.append(list(df.columns))

                        # Add data rows
                        for _, row in df.iterrows():
                            table_data.append([str(cell) for cell in row])

                        all_tables.append(table_data)
                        logger.info(f"[DOCLING] Table {i+1} extracted: {len(table_data)} rows")

                    except Exception as e:
                        logger.warning(f"[DOCLING] Failed to extract table {i+1} as dataframe: {e}")
                        # Fallback: try to get table data directly
                        table_data = []
                        if hasattr(table, 'data') and table.data and hasattr(table.data, 'table_cells'):
                            for row in table.data.table_cells:
                                table_data.append([cell.text if hasattr(cell, 'text') else str(cell) for cell in row])
                        all_tables.append(table_data)
                        logger.info(f"[DOCLING] Table {i+1} extracted via fallback: {len(table_data)} rows")

            logger.info(f"[DOCLING] Extracted {len(all_tables)} tables from {file_path}")
            return [all_tables]  # Return as [tables] to match expected format

        except Exception as e:
            logger.error(f"[DOCLING] Table extraction failed for {file_path}: {e}")
            import traceback
            logger.error(f"[DOCLING] Traceback: {traceback.format_exc()}")
            return []

    def extract_account_info(self, file_path: str) -> Dict[str, Optional[str]]:
        """
        Extract account information from the bank statement.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dict containing account_number, account_type, and other metadata
        """
        try:
            text = self.extract_text(file_path)

            account_info = {
                'account_number': None,
                'account_type': None,
                'bank_name': None,
                'statement_date': None
            }

            # Extract account number
            account_match = ACCOUNT_NUMBER_RE.search(text)
            if account_match:
                account_info['account_number'] = account_match.group(1)

            # Extract account type
            type_match = ACCOUNT_TYPE_RE.search(text)
            if type_match:
                account_info['account_type'] = type_match.group(1).strip()

            # Extract bank name (look for common patterns)
            if 'fifth third' in text.lower():
                account_info['bank_name'] = 'Fifth Third Bank'
            elif 'chase' in text.lower():
                account_info['bank_name'] = 'Chase Bank'
            elif 'wells fargo' in text.lower():
                account_info['bank_name'] = 'Wells Fargo'

            logger.debug(f"Extracted account info: {account_info}")
            return account_info

        except Exception as e:
            logger.error(f"Account info extraction failed for {file_path}: {e}")
            return {'account_number': None, 'account_type': None, 'bank_name': None, 'statement_date': None}

    def extract_statement_period(self, file_path: str) -> Tuple[Optional[date], Optional[date]]:
        """
        Extract the statement period dates from the PDF.

        Args:
            file_path: Path to the PDF file

        Returns:
            Tuple of (start_date, end_date) or (None, None) if not found
        """
        try:
            text = self.extract_text(file_path)

            # Look for statement period pattern
            period_match = STATEMENT_PERIOD_RE.search(text)
            if period_match:
                start_str, end_str = period_match.groups()

                try:
                    start_date = datetime.strptime(start_str, '%m/%d/%Y').date()
                    end_date = datetime.strptime(end_str, '%m/%d/%Y').date()

                    logger.debug(f"Statement period: {start_date} to {end_date}")
                    return start_date, end_date

                except ValueError as e:
                    logger.warning(f"Failed to parse statement dates: {e}")

            logger.warning(f"No statement period found in {file_path}")
            return None, None

        except Exception as e:
            logger.error(f"Statement period extraction failed for {file_path}: {e}")
            return None, None

    def parse_transactions(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse bank transactions from the PDF statement.

        Args:
            file_path: Path to the PDF file

        Returns:
            List of transaction dictionaries
        """
        try:
            logger.info(f"[DOCLING] Parsing transactions from PDF: {file_path}")

            # Get statement period
            logger.info(f"[DOCLING] Extracting statement period...")
            start_date, end_date = self.extract_statement_period(file_path)
            logger.info(f"[DOCLING] Statement period: {start_date} to {end_date}")

            # Extract text for transaction parsing
            logger.info(f"[DOCLING] Extracting text from document...")
            text = self.extract_text(file_path)
            logger.info(f"[DOCLING] Extracted {len(text)} characters of text")

            # Also try table extraction for better structured data
            logger.info(f"[DOCLING] Extracting tables from document...")
            tables = self.extract_tables(file_path)
            logger.info(f"[DOCLING] Extracted {len(tables)} table groups")

            transactions = []

            # First try to parse from tables (more reliable)
            logger.info(f"[DOCLING] Attempting to parse transactions from tables...")
            try:
                table_transactions = self._parse_transactions_from_tables(tables, start_date, end_date)
                transactions.extend(table_transactions)
                logger.info(f"[DOCLING] Parsed {len(table_transactions)} transactions from tables")
            except Exception as e:
                logger.error(f"[DOCLING] Table parsing failed: {e}")
                import traceback
                logger.error(f"[DOCLING] Table parsing traceback: {traceback.format_exc()}")

            # If no transactions found in tables, fall back to text parsing
            if not transactions:
                logger.info(f"[DOCLING] No transactions from tables, falling back to text parsing...")
                try:
                    text_transactions = self._parse_transactions_from_text(text, start_date, end_date)
                    transactions.extend(text_transactions)
                    logger.info(f"[DOCLING] Parsed {len(text_transactions)} transactions from text")
                except Exception as e:
                    logger.error(f"[DOCLING] Text parsing failed: {e}")
                    import traceback
                    logger.error(f"[DOCLING] Text parsing traceback: {traceback.format_exc()}")

            # Add metadata to all transactions
            logger.info(f"[DOCLING] Adding metadata to {len(transactions)} transactions...")
            for txn in transactions:
                txn.update({
                    'org_id': self.org_id,
                    'source_file': file_path,
                    'file_format': 'PDF',
                    'extraction_method': 'docling',
                    'created_at': datetime.utcnow()
                })

            logger.info(f"[DOCLING] Extracted {len(transactions)} transactions from {file_path}")
            return transactions

        except Exception as e:
            logger.error(f"[DOCLING] Transaction parsing failed for {file_path}: {e}")
            import traceback
            logger.error(f"[DOCLING] Traceback: {traceback.format_exc()}")
            return []

    def _parse_transactions_from_tables(self, tables: List[List[List[str]]],
                                      start_date: Optional[date],
                                      end_date: Optional[date]) -> List[Dict[str, Any]]:
        """Parse transactions from extracted table data."""
        transactions = []

        # Tables now come as [page][tables] format
        for page_tables in tables:
            for table in page_tables:
                if len(table) < 2:  # Skip tables with no data rows
                    continue

                # Check if this looks like a transaction table
                header = table[0] if table else []
                header_text = ' '.join(str(h) for h in header).lower()
                logger.debug(f"Table header: {header}")

                # Skip balance summary tables explicitly
                if any(keyword in header_text for keyword in [
                    'daily balance summary', 'balance summary', 'daily balance',
                    'account summary', 'myadvance', 'point balance', 'points'
                ]):
                    logger.debug(f"Skipping balance/summary table: {header_text}")
                    continue

                # Look for transaction indicators in headers
                is_transaction_table = any(
                    keyword in header_text
                    for keyword in ['withdrawal', 'deposit', 'debit', 'credit', 'checks']
                )

                # Also check for explicit transaction table patterns
                if not is_transaction_table:
                    # Look for date/amount/description patterns in header
                    is_transaction_table = (
                        'date' in header_text and
                        ('amount' in header_text or 'description' in header_text)
                    )

                if is_transaction_table:
                    logger.debug(f"Processing transaction table with {len(table)-1} rows")

                    # Additional filtering: check first few rows to confirm it's not a balance table
                    is_balance_table = False
                    for row in table[1:3]:  # Check first 2 data rows
                        if len(row) >= 2:
                            # Check if amounts are very large (likely balances)
                            try:
                                amount_str = str(row[1]).replace('$', '').replace(',', '').strip()
                                if amount_str and float(amount_str) > 50000:
                                    logger.debug(f"Detected large amounts (balance table): {amount_str}")
                                    is_balance_table = True
                                    break
                            except (ValueError, IndexError):
                                pass

                            # Check for balance-related text in row
                            row_text = ' '.join(str(cell) for cell in row).lower()
                            if any(keyword in row_text for keyword in [
                                'beginning balance', 'ending balance', 'previous balance',
                                'total balance', 'credit limit', 'available credit'
                            ]):
                                logger.debug(f"Detected balance-related text: {row_text}")
                                is_balance_table = True
                                break

                    if is_balance_table:
                        logger.debug("Skipping table identified as balance table")
                        continue

                    # Look for transaction-like patterns in table
                    for row in table[1:]:  # Skip header row
                        if len(row) >= 2:  # Need at least date and amount (description might be combined)
                            transaction = self._extract_transaction_from_row(row, start_date, end_date)
                            if transaction:
                                transactions.append(transaction)

        return transactions

    def _parse_transactions_from_text(self, text: str,
                                    start_date: Optional[date],
                                    end_date: Optional[date]) -> List[Dict[str, Any]]:
        """Parse transactions from raw text using regex patterns."""
        transactions = []
        lines = text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Try to match transaction pattern
            match = START_LINE_RE.match(line)
            if match:
                transaction = self._extract_transaction_from_match(match, start_date, end_date)
                if transaction:
                    transactions.append(transaction)

        return transactions

    def _extract_transaction_from_row(self, row: List[str],
                                    start_date: Optional[date],
                                    end_date: Optional[date]) -> Optional[Dict[str, Any]]:
        """Extract transaction data from a table row."""
        try:
            # Clean the row data
            row = [cell.strip() if cell else '' for cell in row]

            # Try different column patterns based on common bank statement formats
            date_str = None
            amount_str = None
            description = None

            # Pattern 1: Date, Amount, Description (3 columns)
            if len(row) >= 3:
                potential_date = str(row[0]).strip()
                potential_amount = str(row[1]).strip()
                potential_desc = str(row[2]).strip()

                if DATE_MD.match(potential_date) and self._is_amount(potential_amount):
                    date_str = potential_date
                    amount_str = potential_amount
                    description = potential_desc

            # Pattern 2: Search for date and amount in any position
            if not date_str:
                for i, cell in enumerate(row):
                    cell_str = str(cell).strip()

                    # Look for date pattern
                    if DATE_MD.match(cell_str):
                        date_str = cell_str

                    # Look for amount pattern (more flexible)
                    if self._is_amount(cell_str) and not amount_str:
                        amount_str = cell_str

                # Use remaining cells as description
                if date_str and amount_str:
                    desc_parts = []
                    for cell in row:
                        cell_str = str(cell).strip()
                        if cell_str != date_str and cell_str != amount_str and cell_str:
                            desc_parts.append(cell_str)
                    description = ' '.join(desc_parts)

            if date_str and amount_str:
                if not description:
                    description = "Transaction"  # Default description

                return self._create_transaction_dict(date_str, description, amount_str, start_date, end_date)

        except Exception as e:
            logger.debug(f"Failed to extract transaction from row {row}: {e}")

        return None

    def _is_amount(self, cell: str) -> bool:
        """Check if a cell contains a monetary amount."""
        if not cell:
            return False

        cell = cell.strip()

        # Check for amount patterns
        amount_patterns = [
            r'^\$?[\d,]+\.\d{2}$',  # $1,234.56 or 1,234.56
            r'^\([\d,]+\.\d{2}\)$',  # (1,234.56) - negative
            r'^[\d,]+\.\d{2}$',     # 1,234.56
            r'^\$[\d,]+$',          # $1234 - whole dollars
            r'^[\d,]+$'             # 1234 - whole dollars
        ]

        return any(re.match(pattern, cell) for pattern in amount_patterns)

    def _extract_transaction_from_match(self, match,
                                      start_date: Optional[date],
                                      end_date: Optional[date]) -> Optional[Dict[str, Any]]:
        """Extract transaction data from regex match."""
        try:
            date_str = match.group('md')
            description = match.group('desc').strip()
            amount_str = match.group('amount')

            return self._create_transaction_dict(date_str, description, amount_str, start_date, end_date)

        except Exception as e:
            logger.debug(f"Failed to extract transaction from match: {e}")
            return None

    def _create_transaction_dict(self, date_str: str, description: str, amount_str: str,
                               start_date: Optional[date], end_date: Optional[date]) -> Optional[Dict[str, Any]]:
        """Create a standardized transaction dictionary."""
        try:
            # Ensure inputs are strings
            date_str = str(date_str).strip() if date_str else ''
            description = str(description).strip() if description else ''
            amount_str = str(amount_str).strip() if amount_str else ''

            # Parse date
            transaction_date = self._parse_transaction_date(date_str, start_date, end_date)
            if not transaction_date:
                return None

            # Parse amount
            amount = self._parse_amount(amount_str)
            if amount is None:
                return None

            # Clean description
            description = self._clean_description(description)

            return {
                'date': transaction_date,
                'description': description,
                'amount': amount,
                'raw_date': date_str,
                'raw_amount': amount_str,
                'raw_description': description
            }

        except Exception as e:
            logger.debug(f"Failed to create transaction dict: {e}")
            return None

    def _parse_transaction_date(self, date_str: str,
                              start_date: Optional[date],
                              end_date: Optional[date]) -> Optional[date]:
        """Parse transaction date with intelligent year inference."""
        try:
            match = DATE_MD.match(date_str)
            if not match:
                return None

            month, day, year = match.groups()
            month, day = int(month), int(day)

            if year:
                year = int(year)
                if year < 100:  # 2-digit year
                    year += 2000 if year < 50 else 1900
            else:
                # Infer year from statement period
                if start_date:
                    year = start_date.year
                elif end_date:
                    year = end_date.year
                else:
                    year = datetime.now().year

            return date(year, month, day)

        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to parse date '{date_str}': {e}")
            return None

    def _parse_amount(self, amount_str: str) -> Optional[float]:
        """Parse monetary amount from string."""
        try:
            # Remove currency symbols and formatting
            amount_str = re.sub(r'[\$,]', '', amount_str.strip())

            # Handle parentheses for negative amounts
            is_negative = amount_str.startswith('(') and amount_str.endswith(')')
            if is_negative:
                amount_str = amount_str[1:-1]

            # Handle negative sign
            if amount_str.startswith('-'):
                is_negative = True
                amount_str = amount_str[1:]

            amount = float(amount_str)
            return -amount if is_negative else amount

        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to parse amount '{amount_str}': {e}")
            return None

    def _clean_description(self, description: str) -> str:
        """Clean and normalize transaction description."""
        if not description:
            return ""

        # Remove extra whitespace
        description = re.sub(r'\s+', ' ', description.strip())

        # Check for check number patterns and convert to meaningful description

        # Pattern 1: Simple single check (e.g., "9342*i", "9342 i")
        simple_check_pattern = re.match(r'^(\d{3,8})\s*\*?\s*[is]?\s*$', description, re.I)
        if simple_check_pattern:
            check_number = simple_check_pattern.group(1)
            return f"Check #{check_number}"

        # Pattern 2: Complex multi-check summary (e.g., "3921 i 05/29 9343 i 200.00 9344 i 14.99")
        multi_check_pattern = re.match(r'^(\d{3,8}\s+[is]\s+\d{2}/\d{2}\s+)*(\d{3,8}\s+[is]\s+[\d,]+\.\d{2}\s*)+(\d{3,8}\s+[is]\s+[\d,]+\.\d{2})\s*$', description, re.I)
        if multi_check_pattern:
            # Extract all check numbers from the complex pattern
            check_numbers = re.findall(r'(\d{3,8})\s+[is]', description, re.I)
            if check_numbers:
                if len(check_numbers) == 1:
                    return f"Check #{check_numbers[0]}"
                else:
                    return f"Checks #{', #'.join(check_numbers)}"

        # Remove common prefixes/suffixes that aren't useful
        description = re.sub(r'^(DEBIT CARD|CREDIT CARD|ACH|CHECK)\s*-?\s*', '', description, flags=re.I)

        return description