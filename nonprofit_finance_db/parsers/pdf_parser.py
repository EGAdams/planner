"""
PDF Parser using Docling

This module provides a PDF parser that maintains compatibility with the existing
parser interface while using the new Docling-based PDF extractor.
"""

from typing import List, Dict, Any, Optional
import logging
from datetime import date

import pdf_extractor
from .base_parser import BaseParser
from pdf_extractor import GeminiBankFallback, DoclingPDFExtractor

DOCLING_AVAILABLE = DoclingPDFExtractor is not None
DOCLING_IMPORT_ERROR = str(getattr(pdf_extractor, "__docling_import_error__", ""))

logger = logging.getLogger(__name__)


class PDFParser(BaseParser):
    """
    PDF parser that wraps the Docling extractor to maintain interface compatibility.

    This class serves as an adapter between the existing parser interface
    and the new Docling-based PDF extraction system.
    """

    def __init__(self, org_id: int):
        """
        Initialize the PDF parser with Docling extractor.

        Args:
            org_id: Organization ID for transaction attribution
        """
        super().__init__(org_id)
        self.supported_formats = ['PDF']

        self.gemini_fallback = None
        try:
            self.gemini_fallback = GeminiBankFallback()
            logger.info("Gemini fallback initialized for PDF parsing")
        except Exception as exc:
            logger.warning("Gemini fallback unavailable: %s", exc)

        if not DOCLING_AVAILABLE:
            logger.error(f"Docling PDF extractor not available: {DOCLING_IMPORT_ERROR}")
            logger.error("Please install Docling dependencies: pip install docling")
            self.extractor = None
        else:
            self.extractor = DoclingPDFExtractor(org_id)
            logger.info("PDF parser initialized with Docling extractor")

    def validate_format(self, file_path: str) -> bool:
        """
        Validate that the file is a readable PDF document.

        Args:
            file_path: Path to the PDF file

        Returns:
            bool: True if file is a valid PDF, False otherwise
        """
        logger.info(f"PDFParser: Starting format validation for {file_path}")
        if not self.extractor:
            logger.error("PDF extractor not available - cannot validate format")
            return False

        result = self.extractor.validate_format(file_path)
        logger.info(f"PDFParser: Format validation completed. Result: {result}")
        return result

    def parse(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Parse PDF bank statement and extract transactions.

        Args:
            file_path: Path to the PDF file

        Returns:
            List of standardized transaction dictionaries
        """
        if not self.extractor:
            logger.error("PDF extractor not available - cannot parse")
            return []

        logger.info(f"Parsing PDF bank statement: {file_path}")

        try:
            # Use Docling extractor to parse transactions
            raw_transactions = self.extractor.parse_transactions(file_path)

            # Standardize transactions using base parser method
            standardized_transactions = []
            for raw_txn in raw_transactions:
                standardized_txn = self.standardize_transaction(raw_txn)
                if standardized_txn:
                    standardized_transactions.append(standardized_txn)

            logger.info(f"Successfully parsed {len(standardized_transactions)} transactions from {file_path}")

            # If Docling returned nothing, fall back to Gemini for a best-effort parse
            if not standardized_transactions and self.gemini_fallback:
                logger.info("Docling returned no transactions; invoking Gemini fallback")
                statement_text = self.extractor.extract_text(file_path) if self.extractor else ""
                fallback_transactions = self.gemini_fallback.parse_transactions(statement_text)
                for raw_txn in fallback_transactions:
                    standardized_txn = self.standardize_transaction(raw_txn)
                    if standardized_txn:
                        standardized_transactions.append(standardized_txn)

                logger.info("Gemini fallback produced %d transactions", len(standardized_transactions))

            return standardized_transactions

        except Exception as e:
            logger.error(f"Error parsing PDF {file_path}: {e}")
            return []

    def extract_account_info(self, file_path: str) -> Dict[str, Optional[str]]:
        """
        Extract account information from the bank statement.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dict containing account metadata
        """
        if not self.extractor:
            logger.error("PDF extractor not available - cannot extract account info")
            return {
                'account_number': None,
                'account_type': None,
                'bank_name': None,
                'statement_date': None,
                'statement_start_date': None,
                'statement_end_date': None
            }

        try:
            account_info = self.extractor.extract_account_info(file_path)

            # Add statement period information
            start_date, end_date = self.extractor.extract_statement_period(file_path)
            if start_date:
                account_info['statement_start_date'] = start_date.isoformat()
            if end_date:
                account_info['statement_end_date'] = end_date.isoformat()

            return account_info

        except Exception as e:
            logger.error(f"Error extracting account info from {file_path}: {e}")
            return {
                'account_number': None,
                'account_type': None,
                'bank_name': None,
                'statement_date': None,
                'statement_start_date': None,
                'statement_end_date': None
            }

    def extract_statement_period(self, file_path: str) -> tuple[Optional[date], Optional[date]]:
        """
        Extract statement period dates from the PDF.

        Args:
            file_path: Path to the PDF file

        Returns:
            Tuple of (start_date, end_date)
        """
        if not self.extractor:
            logger.error("PDF extractor not available - cannot extract statement period")
            return None, None
        return self.extractor.extract_statement_period(file_path)

    def extract_text(self, file_path: str) -> str:
        """
        Extract all text content from the PDF.

        Args:
            file_path: Path to the PDF file

        Returns:
            str: Extracted text content
        """
        if not self.extractor:
            logger.error("PDF extractor not available - cannot extract text")
            return ""
        return self.extractor.extract_text(file_path)

    def extract_tables(self, file_path: str) -> List[List[List[str]]]:
        """
        Extract structured table data from the PDF.

        Args:
            file_path: Path to the PDF file

        Returns:
            List[List[List[str]]]: Tables as nested lists [page][table][row][cell]
        """
        if not self.extractor:
            logger.error("PDF extractor not available - cannot extract tables")
            return []
        return self.extractor.extract_tables(file_path)
