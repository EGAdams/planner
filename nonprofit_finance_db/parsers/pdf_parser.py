
import pdfplumber
import PyPDF2
from typing import List, Dict, Any, Optional, Tuple
import re
import logging
from datetime import datetime, date
try:
    # Keep your existing BaseParser import (project structure)
    from .base_parser import BaseParser  # type: ignore
except Exception:  # pragma: no cover
    # Fallback so this file can be linted/loaded standalone
    class BaseParser:  # minimal stub
        def __init__(self, org_id: int):
            self.org_id = org_id
        def standardize_transaction(self, raw: Dict[str, Any]) -> Dict[str, Any]:
            return raw

logger = logging.getLogger(__name__)

DATE_MD = re.compile(r'^(\d{1,2})/(\d{1,2})(?:/(\d{2,4}))?$')  # 04/24 or 04/24/2025
START_LINE_RE = re.compile(r'^(?P<md>\d{1,2}/\d{1,2}(?:/\d{2,4})?)\s+(?P<amount>[\$\(\)\-\d,\.]+)\s+(?P<desc>.*)$')
CHECK_TRIPLE_RE = re.compile(r'(\d{3,8})\s+(?:[is]\s*)?(\d{1,2}/\d{1,2})\s+([\d,]+\.\d{2})')
STATEMENT_PERIOD_RE = re.compile(r'Statement\s+Period\s+Date\s*:\s*(\d{1,2}/\d{1,2}/\d{4})\s*-\s*(\d{1,2}/\d{1,2}/\d{4})', re.I)
ACCOUNT_NUMBER_RE = re.compile(r'Account\s*Number\s*:\s*([\dxX*]+)', re.I)
ACCOUNT_TYPE_RE = re.compile(r'Account\s*Type\s*:\s*(.+)', re.I)

class PDFParser(BaseParser):
    """Parser for PDF bank statements (Fifth Third–friendly)."""

    def __init__(self, org_id: int):
        super().__init__(org_id)
        self.supported_formats = ['PDF']

    # ---------------- Core entrypoints ----------------

    def validate_format(self, file_path: str) -> bool:
        """Check if file is a valid PDF"""
        try:
            with pdfplumber.open(file_path) as pdf:
                return len(pdf.pages) > 0
        except Exception as e:
            logger.error(f"PDF validation failed: {e}")
            return False

    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse PDF bank statement and extract transactions."""
        logger.info(f"Parsing PDF bank statement: {file_path}")
        transactions: List[Dict[str, Any]] = []

        try:
            # Try pdfplumber first
            with pdfplumber.open(file_path) as pdf:
                plumber_pages = len(pdf.pages)

            # Check with PyPDF2 to see if we're missing pages
            with open(file_path, 'rb') as f:
                pypdf_reader = PyPDF2.PdfReader(f)
                pypdf_pages = len(pypdf_reader.pages)

            logger.debug(f"Page count: pdfplumber={plumber_pages}, PyPDF2={pypdf_pages}")

            # Use PyPDF2 if it detects more pages or if pdfplumber fails
            if pypdf_pages > plumber_pages:
                logger.info(f"Using PyPDF2 fallback (detected {pypdf_pages} pages vs {plumber_pages})")
                return self._parse_with_pypdf2(file_path)
            else:
                # Use original pdfplumber logic
                with pdfplumber.open(file_path) as pdf:
                    start_dt, end_dt = self._statement_period_from_pdf(pdf)
                    logger.debug(f"Statement period inferred: start={start_dt} end={end_dt}")

                    # Prefer text parsing for Fifth Third layout; tables on these PDFs are inconsistent
                    for page_num, page in enumerate(pdf.pages, start=1):
                        logger.debug(f"Processing page {page_num}")
                        page_text = page.extract_text(x_tolerance=2, y_tolerance=2) or ''
                        if not page_text.strip():
                            # fallback to tables if text is empty
                            page_transactions = self._extract_transactions_from_tables(page)
                        else:
                            cleaned = self._clean_spaced_text(page_text)
                            page_transactions = self._parse_transactions_from_text(cleaned, start_dt, end_dt)

                        transactions.extend(page_transactions)

            logger.info(f"Extracted {len(transactions)} raw transactions from PDF")

            # Standardize
            standardized_transactions = []
            for raw in transactions:
                std = self.standardize_transaction(raw) if hasattr(self, 'standardize_transaction') else raw
                # Ensure normalization even if parent class didn't handle it
                std = self._force_standardize(std, raw, default_year=(end_dt.year if end_dt else None))
                if self._is_valid_transaction(std):
                    standardized_transactions.append(std)

            logger.info(f"Standardized {len(standardized_transactions)} valid transactions")
            return standardized_transactions

        except Exception as e:
            logger.error(f"Error parsing PDF: {e}")
            raise

    def _parse_with_pypdf2(self, file_path: str) -> List[Dict[str, Any]]:
        """Parse PDF using PyPDF2 as fallback when pdfplumber fails."""
        logger.info("Using PyPDF2 fallback parser")
        transactions: List[Dict[str, Any]] = []

        try:
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)

                # Extract statement period from first page
                start_dt, end_dt = self._statement_period_from_pypdf2(pdf_reader)
                logger.debug(f"Statement period inferred: start={start_dt} end={end_dt}")

                # Process all pages
                all_text = ""
                for page_num, page in enumerate(pdf_reader.pages, start=1):
                    logger.debug(f"Processing page {page_num}")
                    page_text = page.extract_text() or ''
                    all_text += page_text + "\n"

                # Clean and parse the combined text
                cleaned = self._clean_spaced_text(all_text)
                transactions = self._parse_transactions_from_text(cleaned, start_dt, end_dt)

            logger.info(f"Extracted {len(transactions)} raw transactions from PDF using PyPDF2")

            # Standardize
            standardized_transactions = []
            for raw in transactions:
                std = self.standardize_transaction(raw) if hasattr(self, 'standardize_transaction') else raw
                # Ensure normalization even if parent class didn't handle it
                std = self._force_standardize(std, raw, default_year=(end_dt.year if end_dt else None))
                if self._is_valid_transaction(std):
                    standardized_transactions.append(std)

            logger.info(f"Standardized {len(standardized_transactions)} valid transactions")
            return standardized_transactions

        except Exception as e:
            logger.error(f"Error parsing PDF with PyPDF2: {e}")
            raise

    def _statement_period_from_pypdf2(self, pdf_reader) -> Tuple[Optional[date], Optional[date]]:
        """Extract statement period using PyPDF2."""
        start_dt: Optional[date] = None
        end_dt: Optional[date] = None
        try:
            if pdf_reader.pages:
                first_page_text = pdf_reader.pages[0].extract_text() or ''
                first_page_text = self._clean_spaced_text(first_page_text)
                m = STATEMENT_PERIOD_RE.search(first_page_text)
                if m:
                    start_dt = datetime.strptime(m.group(1), '%m/%d/%Y').date()
                    end_dt = datetime.strptime(m.group(2), '%m/%d/%Y').date()
        except Exception as e:
            logger.debug(f'Failed to parse statement period with PyPDF2: {e}')
        return start_dt, end_dt

    # ---------------- Table fallback (rarely hits for 53 PDFs) ----------------

    def _extract_transactions_from_tables(self, page) -> List[Dict[str, Any]]:
        transactions: List[Dict[str, Any]] = []
        try:
            tables = page.extract_tables() or []
        except Exception:
            tables = []
        for table in tables:
            transactions.extend(self._parse_table_transactions(table))
        return transactions

    def _parse_table_transactions(self, table: List[List[str]]) -> List[Dict[str, Any]]:
        transactions: List[Dict[str, Any]] = []
        if not table or len(table) < 2:
            return transactions

        header_mapping = self._detect_column_mapping(table[0] if table else [])
        if not header_mapping and len(table) > 1:
            header_mapping = self._detect_column_mapping(table[1])
            table = table[1:]

        if not header_mapping:
            logger.debug("No usable table header mapping detected; skipping table.")
            return transactions

        for row in table[1:]:
            if not row or all((c or '').strip() == '' for c in row):
                continue
            tx = self._parse_table_row(row, header_mapping)
            if tx:
                transactions.append(tx)
        return transactions

    # ---------------- Text-first Fifth Third parser ----------------

    def _parse_transactions_from_text(self, text: str, start_dt: Optional[date], end_dt: Optional[date]) -> List[Dict[str, Any]]:
        """Parse sections: Withdrawals / Debits, Deposits / Credits, Checks."""
        lines = [ln.strip() for ln in text.split('\n')]
        results: List[Dict[str, Any]] = []

        # Join pages might repeat headers/footers; skip noise lines
        def is_noise(ln: str) -> bool:
            if not ln:
                return True
            low = ln.lower()
            return (
                low.startswith('page ') or
                'ftcstmt' in low or
                low.startswith('internet banking') or
                low.startswith('banking center') or
                low.startswith('customer service') or
                low.startswith('real life rewards') or
                low.startswith('this page intentionally left blank') or
                low.startswith('daily balance summary') or
                low.startswith('myadvance') or
                low.startswith('account summary -') or
                low.startswith('account summary') or
                low.startswith('checks ')  # do not drop header, we handle separately
                and False
            )

        # Build a single string for regex slicing
        full = '\n'.join([ln for ln in lines if not is_noise(ln)])

        # Extract sections by headers
        def slice_between(src: str, start_pat: str, end_pats: List[str]) -> str:
            m = re.search(start_pat, src, re.I)
            if not m:
                return ''
            start_idx = m.end()
            end_idx = len(src)
            for ep in end_pats:
                m2 = re.search(ep, src[start_idx:], re.I)
                if m2:
                    end_idx = start_idx + m2.start()
                    break
            return src[start_idx:end_idx].strip()

        withdrawals = slice_between(full, r'Withdrawals\s*(?:/|and)\s*Debits(?:\s*\(continued\))?', [r'Deposits\s*(?:/|and)\s*Credits', r'Daily Balance Summary', r'Page \d+ of \d+'])
        deposits    = slice_between(full, r'Deposits\s*(?:/|and)\s*Credits(?:\s*\(continued\))?', [r'Daily Balance Summary', r'Page \d+ of \d+', r'Real Life Rewards', r'This page intentionally left blank'])
        checks      = slice_between(full, r'Checks\b',                [r'Withdrawals\s*(?:/|and)\s*Debits', r'Deposits\s*(?:/|and)\s*Credits', r'Daily Balance Summary', r'Page \d+ of \d+'])

        if withdrawals:
            results.extend(self._parse_amount_block(withdrawals, start_dt, end_dt, sign=-1.0, section='Withdrawals / Debits'))
        if deposits:
            results.extend(self._parse_amount_block(deposits, start_dt, end_dt, sign=+1.0, section='Deposits / Credits'))
        if checks:
            results.extend(self._parse_checks_block(checks, start_dt, end_dt))

        return results

    def _parse_amount_block(self, block: str, start_dt: Optional[date], end_dt: Optional[date], sign: float, section: str) -> List[Dict[str, Any]]:
        """Parse lines like: 05/05 9.53 DESCRIPTION ... with wrapped continuations."""
        out: List[Dict[str, Any]] = []
        pending: Optional[Dict[str, Any]] = None
        for raw_ln in block.split('\n'):
            ln = raw_ln.strip()
            if not ln:
                continue

            m = START_LINE_RE.match(ln)
            if m:
                # flush previous
                if pending:
                    out.append(pending)
                    pending = None

                md = m.group('md')
                amt = m.group('amount')
                desc = m.group('desc').strip()

                # Normalize amount -> float, keep sign based on section (debit/credit)
                amount = self._to_amount(amt) * sign

                # Convert date
                tx_dt = self._mmdd_to_date(md, start_dt, end_dt)

                pending = {
                    'date': tx_dt.strftime('%Y-%m-%d') if tx_dt else md,
                    'description': desc,
                    'amount': amount,
                    'balance': None,
                    'reference': '',
                    'section': section
                }
            else:
                # continuation: append to description if we have a pending item
                if pending:
                    # Avoid duplicating card masks as separate transactions; append to description
                    if pending['description']:
                        pending['description'] += ' '
                    pending['description'] += ln
                else:
                    # No pending; ignore stray lines in the block
                    pass

        if pending:
            out.append(pending)
        return out

    def _parse_checks_block(self, block: str, start_dt: Optional[date], end_dt: Optional[date]) -> List[Dict[str, Any]]:
        """Parse the condensed check grid like: 9338 i 05/16 200.00 ..."""
        text = re.sub(r'\s+', ' ', block.strip())
        out: List[Dict[str, Any]] = []
        for m in CHECK_TRIPLE_RE.finditer(text):
            chk_no, md, amt = m.groups()
            tx_dt = self._mmdd_to_date(md, start_dt, end_dt)
            amount = -abs(self._to_amount(amt))  # checks are debits
            desc = f'Check {chk_no}'
            out.append({
                'date': tx_dt.strftime('%Y-%m-%d') if tx_dt else md,
                'description': desc,
                'amount': amount,
                'balance': None,
                'reference': chk_no,
                'section': 'Checks'
            })
        return out

    # ---------------- Helpers ----------------

    def _statement_period_from_pdf(self, pdf) -> Tuple[Optional[date], Optional[date]]:
        start_dt: Optional[date] = None
        end_dt: Optional[date] = None
        try:
            if pdf.pages:
                first = pdf.pages[0].extract_text(x_tolerance=2, y_tolerance=2) or ''
                first = self._clean_spaced_text(first)
                m = STATEMENT_PERIOD_RE.search(first)
                if m:
                    start_dt = datetime.strptime(m.group(1), '%m/%d/%Y').date()
                    end_dt = datetime.strptime(m.group(2), '%m/%d/%Y').date()
        except Exception as e:
            logger.debug(f'Failed to parse statement period: {e}')
        return start_dt, end_dt

    def _mmdd_to_date(self, md: str, start_dt: Optional[date], end_dt: Optional[date]) -> Optional[date]:
        """Infer full date from MM/DD (or MM/DD/YY/YYY). Prefer year within statement period."""
        m = DATE_MD.match(md.strip())
        if not m:
            return None
        mm, dd, yy = m.groups()
        mm_i, dd_i = int(mm), int(dd)
        if yy:
            yy_i = int(yy)
            if yy_i < 100:
                yy_i += 2000 if yy_i < 70 else 1900
            return date(yy_i, mm_i, dd_i)
        # infer year
        if start_dt and end_dt:
            # If within same year
            if start_dt.year == end_dt.year:
                return date(end_dt.year, mm_i, dd_i)
            # Cross-year (e.g., Dec-Jan). Choose year closest to end date by month distance.
            # If month >= start.month -> start.year else end.year
            return date(start_dt.year if mm_i >= start_dt.month else end_dt.year, mm_i, dd_i)
        # Fallback: use current year
        return date(datetime.utcnow().year, mm_i, dd_i)

    def _to_amount(self, s: Any) -> float:
        if s is None:
            return 0.0
        txt = str(s).strip()
        neg = False
        if txt.startswith('(') and txt.endswith(')'):
            neg = True
            txt = txt[1:-1]
        txt = txt.replace('$', '').replace(',', '').replace(' ', '')
        try:
            val = float(txt)
        except ValueError:
            # sometimes amounts look like '-123.45'
            txt2 = re.sub(r'[^\d\.-]', '', txt)
            val = float(txt2) if txt2 not in ('', '-', '.') else 0.0
        return -val if neg else val

    def _clean_spaced_text(self, text: str) -> str:
        """Fix spaced-out OCR artifacts (e.g., 'C u s t o m e r')."""
        lines = text.split('\n')
        out_lines = []
        spaced_pattern = r'\b([A-Za-z]\s+){2,}[A-Za-z]\b'
        number_pattern = r'\b(\d\s+){3,}\d\b'

        def fix_spaced_word(m):
            return re.sub(r'\s+', '', m.group())

        def fix_spaced_number(m):
            return re.sub(r'\s+(?=\d)', '', m.group())

        for ln in lines:
            ln2 = re.sub(spaced_pattern, fix_spaced_word, ln)
            ln3 = re.sub(number_pattern, fix_spaced_number, ln2)
            out_lines.append(ln3)
        return '\n'.join(out_lines)

    def _detect_column_mapping(self, header_row: List[str]) -> Optional[Dict[str, int]]:
        if not header_row:
            return None
        mapping: Dict[str, int] = {}
        norm = []
        for c in header_row:
            cleaned = self._clean_spaced_text(str(c) if c is not None else '').lower().strip()
            norm.append(cleaned)
        patterns = {
            'date': ['date', 'trans date', 'transaction date', 'posting date', 'effective date', 'process date'],
            'description': ['description', 'memo', 'transaction', 'details', 'payee', 'merchant', 'reference'],
            'amount': ['amount', 'debit', 'credit', 'withdrawal', 'deposit', 'transaction amount'],
            'balance': ['balance', 'running balance', 'account balance', 'available balance'],
            'reference': ['reference', 'ref', 'check', 'check number', 'ref #', 'check #']
        }
        for idx, header in enumerate(norm):
            for field, keywords in patterns.items():
                if any(k in header for k in keywords):
                    mapping[field] = idx
                    break
        if 'date' not in mapping or ('amount' not in mapping and 'description' not in mapping):
            return None
        return mapping

    def _parse_table_row(self, row: List[str], mapping: Dict[str, int]) -> Optional[Dict[str, Any]]:
        try:
            while len(row) <= max(mapping.values()):
                row.append('')
            tx = {
                'date': row[mapping.get('date', -1)] if 'date' in mapping else '',
                'description': row[mapping.get('description', -1)] if 'description' in mapping else '',
                'amount': row[mapping.get('amount', -1)] if 'amount' in mapping else '',
                'balance': row[mapping.get('balance', -1)] if 'balance' in mapping else '',
                'reference': row[mapping.get('reference', -1)] if 'reference' in mapping else ''
            }
            for k, v in list(tx.items()):
                tx[k] = '' if v is None else str(v).strip()
            if not tx['date'] or not (tx['amount'] or tx['description']):
                return None
            # amount may be textual; convert later in standardization
            return tx
        except Exception as e:
            logger.debug(f"Error parsing table row: {e}")
            return None

    def _is_valid_transaction(self, transaction: Dict[str, Any]) -> bool:
        # Must have standardized date & amount and non-empty description
        if not transaction.get('transaction_date'):
            return False
        if transaction.get('amount') is None:
            return False
        if str(transaction.get('description', '')).strip() == '':
            return False
        return True

    # Ensure a consistent standardized output even if parent class doesn't do it.
    def _force_standardize(self, std: Dict[str, Any], raw: Dict[str, Any], default_year: Optional[int] = None) -> Dict[str, Any]:
        out = dict(std) if std else {}
        # date -> transaction_date
        if not out.get('transaction_date'):
            raw_date = out.get('date') or raw.get('date')
            if isinstance(raw_date, (datetime, date)):
                d = raw_date
            elif isinstance(raw_date, str) and raw_date:
                # Try ISO first, then mm/dd
                d = None
                try:
                    d = datetime.strptime(raw_date, '%Y-%m-%d').date()
                except Exception:
                    try:
                        # mm/dd or mm/dd/yy/yyy
                        m = DATE_MD.match(raw_date.strip())
                        if m:
                            mm, dd, yy = m.groups()
                            if yy:
                                d = self._mmdd_to_date(raw_date, None, None)
                            else:
                                # infer year from default_year if provided
                                y = default_year or datetime.utcnow().year
                                d = date(y, int(mm), int(dd))
                    except Exception:
                        d = None
            else:
                d = None
            if d:
                out['transaction_date'] = d.strftime('%Y-%m-%d')

        # amount -> float
        if out.get('amount') is None:
            amt_src = out.get('amount') if 'amount' in out else raw.get('amount')
            out['amount'] = self._to_amount(amt_src)

        # balance -> float or None
        bal_src = out.get('balance') if 'balance' in out else raw.get('balance')
        out['balance'] = None if bal_src in (None, '', '-') else self._to_amount(bal_src)

        # ensure description & reference
        out['description'] = out.get('description') or raw.get('description', '')
        out['reference'] = out.get('reference') or raw.get('reference', '')

        return out

    # ---------------- Account info (enhanced) ----------------

    def extract_account_info(self, file_path: str) -> Dict[str, Any]:
        info = {
            'account_number': None,
            'account_holder': None,
            'statement_period': None,
            'bank_name': 'Fifth Third Bank',
            'account_type': None,
            'beginning_balance': None,
            'ending_balance': None
        }
        try:
            with pdfplumber.open(file_path) as pdf:
                if pdf.pages:
                    t = self._clean_spaced_text(pdf.pages[0].extract_text(x_tolerance=2, y_tolerance=2) or '')
                    # Statement period
                    m = STATEMENT_PERIOD_RE.search(t)
                    if m:
                        info['statement_period'] = f"{m.group(1)} - {m.group(2)}"
                    # Account number & type
                    m2 = ACCOUNT_NUMBER_RE.search(t)
                    if m2:
                        info['account_number'] = m2.group(1)
                    m3 = ACCOUNT_TYPE_RE.search(t)
                    if m3:
                        info['account_type'] = m3.group(1).strip()
                    # Holder name(s): heuristically, look for two upper lines before address block
                    # (Keep simple to avoid overfitting; many banks render names near the top)
                    # Not strictly required for parsing transactions.
        except Exception as e:
            logger.error(f"Error extracting account info: {e}")
        return info
