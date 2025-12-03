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
BEGINNING_BAL_RE = re.compile(r'Beginning\s+Balance[^\n$]*\$\s*\(?([\d,]+\.\d{2})\)?', re.I)
ENDING_BAL_RE = re.compile(r'Ending\s+Balance[^\n$]*\$\s*\(?([\d,]+\.\d{2})\)?', re.I)
SUMMARY_LINE_PATTERNS = {
    'checks': re.compile(r'(?P<count>\d+)\s+Checks?\s+\$?\(?\s*(?P<amount>[\d,]+\.\d{2})\)?', re.I),
    'withdrawals': re.compile(r'(?P<count>\d+)\s+Withdrawals\s*/\s*Debits?\s+\$?\(?\s*(?P<amount>[\d,]+\.\d{2})\)?', re.I),
    'deposits': re.compile(r'(?P<count>\d+)\s+Deposits?\s*/\s*Credits?\s+\$?\(?\s*(?P<amount>[\d,]+\.\d{2})\)?', re.I),
}


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

    def _parse_currency(self, value: str, absolute: bool = False) -> Optional[float]:
        """Parse a currency-like string into a float, respecting parentheses for negatives."""
        if value is None:
            return None
        text = str(value)
        is_negative = ('(' in text and ')' in text) or text.strip().startswith('-')
        cleaned = re.sub(r'[^0-9.\-]', '', text)
        try:
            number = float(cleaned)
            number = -number if is_negative and not absolute else number
            return round(abs(number) if absolute else number, 2)
        except ValueError:
            return None

    def _extract_account_summary_from_text(self, text: str) -> Dict[str, Any]:
        """Extract beginning/ending balances and high-level counts from statement body."""
        if not text:
            return {}

        summary: Dict[str, Any] = {}

        # 1) Friendly regex matches when labels exist inline
        begin_match = BEGINNING_BAL_RE.search(text)
        if begin_match:
            summary['beginning_balance'] = self._parse_currency(begin_match.group(1))

        end_match = ENDING_BAL_RE.search(text)
        if end_match:
            summary['ending_balance'] = self._parse_currency(end_match.group(1))

        for key, pattern in SUMMARY_LINE_PATTERNS.items():
            matched = pattern.search(text)
            if matched:
                summary[key] = {
                    "count": int(matched.group('count')),
                    "total": self._parse_currency(matched.group('amount'), absolute=True)
                }

        # 2) Fallback: the summary often renders as a block of currency lines after "Account Summary"
        #    (amounts first, labels later). Capture the first 5 currency values in that block.
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'account summary' in line.lower():
                currency_vals = []
                counts = []
                window = lines[i + 1:i + 30]
                for block_line in window:
                    stripped = block_line.strip()
                    if not stripped:
                        continue
                    # Skip obvious dates so they don't contaminate currency list
                    if '/' in stripped and not re.search(r'[$()]', stripped):
                        if re.fullmatch(r'\d{1,2}/\d{1,2}(?:/\d{2,4})?', stripped):
                            continue
                    # Count lines are plain integers without currency formatting
                    if re.fullmatch(r'\d+', stripped):
                        counts.append(int(stripped))
                        if len(currency_vals) >= 5 and len(counts) >= 3:
                            break
                        continue

                    # For markdown tables, extract only the currency values (those with $ symbol)
                    # This prevents combining count numbers with amounts (e.g., "4" + "439.99" = "4439.99")
                    currency_matches = re.findall(r'\$\s*\(?\s*([\d,]+\.\d{2})\)?', stripped)
                    if currency_matches:
                        for curr_str in currency_matches:
                            # Check if this is in parentheses (negative) by looking at context
                            is_negative = '(' in stripped and ')' in stripped
                            amt = self._parse_currency(curr_str, absolute=False)
                            if amt is not None:
                                amt = -abs(amt) if is_negative else amt
                                currency_vals.append(amt)
                                if len(currency_vals) >= 5:
                                    break
                        if len(currency_vals) >= 5 and len(counts) >= 3:
                            break
                        continue

                    # Fallback to old behavior for non-table formats
                    amt = self._parse_currency(stripped, absolute=False)
                    if amt is not None and re.search(r'[\d$.,()]', stripped):
                        currency_vals.append(amt)
                        if len(currency_vals) >= 5 and len(counts) >= 3:
                            break
                        continue
                    if len(currency_vals) >= 5 and len(counts) >= 3:
                        break

                if len(currency_vals) >= 5:
                    summary.setdefault('beginning_balance', currency_vals[0])
                    summary.setdefault('checks', {"count": None, "total": abs(currency_vals[1])})
                    summary.setdefault('withdrawals', {"count": None, "total": abs(currency_vals[2])})
                    summary.setdefault('deposits', {"count": None, "total": abs(currency_vals[3])})
                    summary.setdefault('ending_balance', currency_vals[4])

                if len(counts) >= 3:
                    checks_group = summary.setdefault('checks', {})
                    withdrawals_group = summary.setdefault('withdrawals', {})
                    deposits_group = summary.setdefault('deposits', {})
                    if checks_group.get('count') is None:
                        checks_group['count'] = counts[0]
                    if withdrawals_group.get('count') is None:
                        withdrawals_group['count'] = counts[1]
                    if deposits_group.get('count') is None:
                        deposits_group['count'] = counts[2]

                break

        return summary

    def extract_account_summary(self, file_path: str) -> Dict[str, Any]:
        """Public helper to extract account summary directly from a statement file."""
        try:
            text = self.extract_text(file_path)
            return self._extract_account_summary_from_text(text)
        except Exception:
            return {}

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

            summary = self._extract_account_summary_from_text(text)
            if summary:
                account_info['summary'] = summary
                if summary.get('ending_balance') is not None:
                    account_info['statement_total'] = summary['ending_balance']

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
        last_sign_hint = 0  # Track sign_hint from previous table for continuation tables

        # Tables now come as [page][tables] format
        for page_tables in tables:
            for table in page_tables:
                if len(table) < 2:  # Skip tables with no data rows
                    continue

                # Check if this looks like a transaction table
                header = table[0] if table else []
                header_text = ' '.join(str(h) for h in header).lower()
                logger.debug(f"Table header: {header}")

                sign_hint = 0

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

                if 'withdrawal' in header_text or 'debit' in header_text or 'checks' in header_text:
                    sign_hint = -1
                elif 'deposit' in header_text or 'credit' in header_text:
                    sign_hint = 1

                # Also check for explicit transaction table patterns
                if not is_transaction_table:
                    # Look for date/amount/description patterns in header
                    is_transaction_table = (
                        'date' in header_text and
                        ('amount' in header_text or 'description' in header_text)
                    )

                    # If this looks like a continuation table (generic Date/Amount/Description header),
                    # inherit the sign hint from the previous transaction table
                    if is_transaction_table and sign_hint == 0 and last_sign_hint != 0:
                        sign_hint = last_sign_hint
                        logger.debug(f"Continuation table detected, using sign_hint={sign_hint} from previous table")

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
                            if 'check' in header_text and len(row) >= 3:
                                multi = self._extract_multiple_transactions_from_row(row, start_date, end_date, sign_hint, header_text)
                                if multi:
                                    transactions.extend(multi)
                                    continue

                            transaction = self._extract_transaction_from_row(row, start_date, end_date, sign_hint, header_text)
                            if transaction:
                                transactions.append(transaction)

                    # Remember this sign_hint for potential continuation tables
                    if sign_hint != 0:
                        last_sign_hint = sign_hint

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
                                    end_date: Optional[date],
                                    sign_hint: int = 0,
                                    header_text: str = "") -> Optional[Dict[str, Any]]:
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

                return self._create_transaction_dict(date_str, description, amount_str, start_date, end_date, sign_hint, header_text)

        except Exception as e:
            logger.debug(f"Failed to extract transaction from row {row}: {e}")

        return None

    def _extract_multiple_transactions_from_row(self, row: List[str],
                                      start_date: Optional[date],
                                      end_date: Optional[date],
                                      sign_hint: int = 0,
                                      header_text: str = "") -> List[Dict[str, Any]]:
        """
        Some check tables pack multiple check number/date/amount triplets into a single row.
        Split those out so each check becomes its own transaction.
        """
        transactions: List[Dict[str, Any]] = []
        cleaned = [cell.strip() if cell else '' for cell in row]

        for i in range(0, len(cleaned), 3):
            chunk = cleaned[i:i+3]
            if len(chunk) < 3:
                continue

            check_fragment, date_cell, amount_cell = chunk
            date_cell = str(date_cell).strip()
            amount_cell = str(amount_cell).strip()

            if not DATE_MD.match(date_cell) or not self._is_amount(amount_cell):
                continue

            description = check_fragment or "Check"
            match = re.search(r'(\d{3,8})', description)
            if match:
                description = f"Check #{match.group(1)}"

            txn = self._create_transaction_dict(
                date_cell,
                description,
                amount_cell,
                start_date,
                end_date,
                sign_hint,
                header_text
            )
            if txn:
                transactions.append(txn)

        return transactions

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
                               start_date: Optional[date], end_date: Optional[date],
                               sign_hint: int = 0, header_text: str = "") -> Optional[Dict[str, Any]]:
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
            amount = self._apply_sign_hints(amount, description, sign_hint, header_text)

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

    def _apply_sign_hints(self, amount: float, description: str, sign_hint: int, header_text: str) -> float:
        """Apply sign hints from headers and description keywords."""
        if amount is None:
            return amount

        # Explicit negatives should stay negative
        if amount < 0:
            return amount

        header = (header_text or "").lower()
        desc = (description or "").lower()

        if sign_hint == -1:
            return -abs(amount)
        if sign_hint == 1:
            return abs(amount)

        debit_keywords = [
            'withdrawal', 'debit', 'purchase', 'pymt', 'payment', 'withdraw',
            'atm', 'ach', 'transfer to', 'bill pay', 'check #', 'check#',
            'pos ', 'card purchase', 'merchant payment'
        ]
        credit_keywords = [
            'deposit', 'refund', 'credit', 'reversal', 'transfer from', 'interest',
            'payroll', 'ssa', 'irs', 'treas'
        ]

        if any(keyword in desc for keyword in debit_keywords):
            return -abs(amount)
        if any(keyword in desc for keyword in credit_keywords):
            return abs(amount)

        # Fallback to header cues if description is inconclusive
        if 'withdrawal' in header or 'debit' in header or 'check' in header:
            return -abs(amount)
        if 'deposit' in header or 'credit' in header:
            return abs(amount)

        return amount

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

        explicit_check_match = re.match(r'^check\s*#?\s*(\d{3,8})', description, re.I)
        if explicit_check_match:
            return f"Check #{explicit_check_match.group(1)}"

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
