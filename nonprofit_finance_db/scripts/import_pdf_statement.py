#!/usr/bin/env python3
"""
Script to import a PDF bank statement into the database

Usage:
    python scripts/import_pdf_statement.py <pdf_file_path> [org_id]

Example:
    python scripts/import_pdf_statement.py /path/to/bank_statement.pdf 1
"""

import sys
import os
import logging
from pathlib import Path

# Add parent directory to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from ingestion.pipeline import IngestionPipeline
from parsers import PDFParser

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def import_pdf_statement(pdf_path: str, org_id: int = 1):
    """
    Import a PDF bank statement

    Args:
        pdf_path: Path to the PDF bank statement file
        org_id: Organization ID (default: 1)
    """
    try:
        # Validate file exists
        if not os.path.exists(pdf_path):
            logger.error(f"File not found: {pdf_path}")
            return False

        logger.info(f"Starting PDF import for: {pdf_path}")
        logger.info(f"Organization ID: {org_id}")

        # Create database connection
        from app.db import get_connection

        # Create ingestion pipeline with database connection
        with get_connection() as db_connection:
            pipeline = IngestionPipeline(org_id=org_id, database_connection=db_connection)

            # Import the file
            result = pipeline.ingest_file(pdf_path, auto_process=True)

            # Print results
            print("\n" + "="*60)
            print("PDF IMPORT RESULTS")
            print("="*60)
            print(f"File: {pdf_path}")
            print(f"Success: {result['success']}")
            print(f"Total transactions found: {result['total_transactions']}")
            print(f"Successfully imported: {result['successful_imports']}")
            print(f"Failed imports: {result['failed_imports']}")
            print(f"Duplicates detected: {result['duplicate_count']}")

            if result['validation_errors']:
                print(f"\nValidation errors: {len(result['validation_errors'])}")
                for error in result['validation_errors'][:5]:  # Show first 5 errors
                    print(f"  - {error}")
                if len(result['validation_errors']) > 5:
                    print(f"  ... and {len(result['validation_errors']) - 5} more")

            if result['processing_errors']:
                print(f"\nProcessing errors: {len(result['processing_errors'])}")
                for error in result['processing_errors'][:5]:  # Show first 5 errors
                    print(f"  - {error}")
                if len(result['processing_errors']) > 5:
                    print(f"  ... and {len(result['processing_errors']) - 5} more")

            if result['duplicate_report']:
                print(f"\nDuplicate report:")
                report = result['duplicate_report']
                print(f"  High confidence duplicates: {report.get('high_confidence', 0)}")
                print(f"  Medium confidence duplicates: {report.get('medium_confidence', 0)}")
                print(f"  Low confidence duplicates: {report.get('low_confidence', 0)}")

            if result['import_batch']:
                batch = result['import_batch']
                print(f"\nImport batch details:")
                print(f"  Batch ID: {batch.get('id')}")
                print(f"  Status: {batch.get('status')}")
                print(f"  File format: {batch.get('file_format')}")

            print("="*60)

            return result['success']

    except Exception as e:
        logger.error(f"Error during PDF import: {str(e)}")
        return False

def demo_pdf_parsing(pdf_path: str, org_id: int = 1):
    """
    Demo function to show PDF parsing without full ingestion

    Args:
        pdf_path: Path to the PDF bank statement file
        org_id: Organization ID (default: 1)
    """
    try:
        logger.info(f"Parsing PDF for preview: {pdf_path}")

        # Create parser
        parser = PDFParser(org_id=org_id)

        # Validate format
        if not parser.validate_format(pdf_path):
            print("ERROR: Invalid PDF format or file cannot be read")
            return False

        # Extract account information
        account_info = parser.extract_account_info(pdf_path)

        # Parse transactions
        transactions = parser.parse(pdf_path)

        # Display results
        print("\n" + "="*60)
        print("PDF PARSING PREVIEW")
        print("="*60)
        print(f"File: {pdf_path}")

        print(f"\nAccount Information:")
        for key, value in account_info.items():
            if value:
                print(f"  {key.replace('_', ' ').title()}: {value}")

        print(f"\nTransactions found: {len(transactions)}")

        if transactions:
            print(f"\nAll transactions:")
            for i, tx in enumerate(transactions):
                print(f"  {i+1}. {tx['transaction_date']} | ${tx['amount']:.2f} | {tx['description']}")

        print("="*60)

        return True

    except Exception as e:
        logger.error(f"Error during PDF parsing: {str(e)}")
        return False

def main():
    """Main function"""
    # if len(sys.argv) < 2:
    #     print("Usage: python scripts/import_pdf_statement.py <pdf_file_path> [org_id] [--preview]")
    #     print("  --preview: Only parse and preview, don't import to database")
    #     sys.exit(1)

    # pdf_path = sys.argv[1]
    pdf_path = "/mnt/c/Users/NewUser/Downloads/fifth_third_personal_may.pdf"
    org_id = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] != '--preview' else 1
    preview_mode = '--preview' in sys.argv

    if preview_mode:
        success = demo_pdf_parsing(pdf_path, org_id)
    else:
        success = import_pdf_statement(pdf_path, org_id)

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
