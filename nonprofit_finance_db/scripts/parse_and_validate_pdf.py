#!/usr/bin/env python3
"""
Parse and Validate Bank PDF Script

This script parses a bank PDF statement and validates it against the summary/totals
section of the bank statement, ensuring all transactions balance correctly.

Usage:
    python scripts/parse_and_validate_pdf.py <pdf_file_path> [org_id]

Example:
    python scripts/parse_and_validate_pdf.py /path/to/bank_statement.pdf 1
"""

import sys
import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers import PDFParser

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def classify_transaction(txn: Dict[str, Any]) -> str:
    """Classify a transaction as CHECK, WITHDRAWAL, or DEPOSIT"""
    hint = str(txn.get("bank_item_type") or "").upper()
    if hint in ("CHECK", "WITHDRAWAL", "DEPOSIT"):
        return hint
    desc = str(txn.get("description") or "").lower()
    if "check" in desc:
        return "CHECK"
    amount = txn.get("amount")
    if amount is None:
        return "UNKNOWN"
    return "DEPOSIT" if amount > 0 else "WITHDRAWAL"


def compute_breakdown(transactions: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Compute transaction breakdown by type"""
    breakdown = {
        "checks": {"count": 0, "total": 0.0},
        "withdrawals": {"count": 0, "total": 0.0},
        "deposits": {"count": 0, "total": 0.0},
    }
    for txn in transactions:
        amount = txn.get("amount")
        if amount is None:
            continue
        bucket = classify_transaction(txn)
        if bucket == "CHECK":
            breakdown["checks"]["count"] += 1
            breakdown["checks"]["total"] += abs(amount)
        elif bucket == "DEPOSIT":
            breakdown["deposits"]["count"] += 1
            breakdown["deposits"]["total"] += abs(amount)
        else:
            breakdown["withdrawals"]["count"] += 1
            breakdown["withdrawals"]["total"] += abs(amount)

    for key in breakdown:
        breakdown[key]["total"] = round(breakdown[key]["total"], 2)
    return breakdown


def close_enough(a: Optional[float], b: Optional[float], tol: float = 0.01) -> bool:
    """Check if two values are within tolerance"""
    if a is None or b is None:
        return False
    return abs(a - b) <= tol


def parse_and_validate_pdf(pdf_path: str, org_id: int = 1) -> bool:
    """
    Parse a PDF bank statement and validate it against the statement summary.

    Args:
        pdf_path: Path to the PDF bank statement file
        org_id: Organization ID (default: 1)

    Returns:
        bool: True if validation passed, False otherwise
    """
    try:
        # Validate file exists
        if not os.path.exists(pdf_path):
            print(f"✗ ERROR: File not found: {pdf_path}", flush=True)
            return False

        print(f"✓ File found: {pdf_path}", flush=True)
        sys.stdout.flush()

        # Create parser
        parser = PDFParser(org_id=org_id)
        logger.info(f"Starting PDF validation for: {pdf_path}")

        # Validate PDF format
        print(f"> Validating PDF format...", flush=True)
        sys.stdout.flush()
        if not parser.validate_format(pdf_path):
            print(f"✗ ERROR: Invalid or unreadable PDF format", flush=True)
            return False
        print(f"✓ PDF format is valid", flush=True)

        # Extract account information
        print(f"> Extracting account information...", flush=True)
        sys.stdout.flush()
        account_info = parser.extract_account_info(pdf_path) or {}
        account_summary = account_info.get("summary", {}) if isinstance(account_info, dict) else {}

        if account_info:
            print(f"✓ Account information extracted", flush=True)
            if isinstance(account_info, dict):
                for key, value in account_info.items():
                    if key != "summary" and value:
                        print(f"  {key.replace('_', ' ').title()}: {value}")
        sys.stdout.flush()

        # Parse transactions
        print(f"> Parsing transactions from PDF...", flush=True)
        sys.stdout.flush()
        transactions = parser.parse(pdf_path) or []

        if not transactions:
            print(f"⚠ WARNING: No transactions found in PDF", flush=True)
        else:
            print(f"✓ Found {len(transactions)} transactions", flush=True)
        sys.stdout.flush()

        # Compute breakdown from parsed transactions
        print(f"> Computing transaction breakdown...", flush=True)
        sys.stdout.flush()
        breakdown = compute_breakdown(transactions)

        # Calculate ending balance
        computed_ending = None
        if account_summary.get("beginning_balance") is not None:
            computed_ending = round(
                account_summary["beginning_balance"]
                - breakdown["checks"]["total"]
                - breakdown["withdrawals"]["total"]
                + breakdown["deposits"]["total"],
                2,
            )

        # Perform validations
        print(f"\n" + "="*70)
        print(f"VALIDATION RESULTS")
        print(f"="*70)

        errors = []
        passes = True

        # Validate transaction type counts and totals
        if account_summary:
            print(f"\nTransaction Type Verification:")
            print(f"  Expected vs Calculated:")

            for key in ("checks", "withdrawals", "deposits"):
                expected_group = account_summary.get(key) or {}
                expected_count = expected_group.get("count")
                expected_total = expected_group.get("total")
                calculated_count = breakdown[key]["count"]
                calculated_total = breakdown[key]["total"]

                key_display = key.title()
                print(f"\n  {key_display}:")

                if expected_count is not None:
                    match = "✓" if expected_count == calculated_count else "✗"
                    print(f"    Count: {match} Expected: {expected_count}, Calculated: {calculated_count}")
                    if expected_count != calculated_count:
                        errors.append(f"{key} count mismatch")
                        passes = False

                if expected_total is not None:
                    match = "✓" if close_enough(expected_total, calculated_total) else "✗"
                    print(f"    Total: {match} Expected: ${expected_total:.2f}, Calculated: ${calculated_total:.2f}")
                    if not close_enough(expected_total, calculated_total):
                        errors.append(f"{key} total mismatch")
                        passes = False

            # Validate ending balance
            if account_summary.get("ending_balance") is not None and computed_ending is not None:
                expected_ending = account_summary["ending_balance"]
                match = "✓" if close_enough(expected_ending, computed_ending) else "✗"
                print(f"\n  Ending Balance:")
                print(f"    {match} Expected: ${expected_ending:.2f}, Calculated: ${computed_ending:.2f}")
                if not close_enough(expected_ending, computed_ending):
                    errors.append("ending balance mismatch")
                    passes = False
        else:
            print(f"\n⚠ WARNING: No account summary found in PDF - cannot validate against statement totals")
            passes = False

        # Calculate totals from transactions
        total_amount = sum(t.get("amount", 0) for t in transactions if t.get("amount") is not None)
        total_debits = sum(abs(t.get("amount", 0)) for t in transactions if t.get("amount", 0) < 0)
        total_credits = sum(t.get("amount", 0) for t in transactions if t.get("amount", 0) > 0)

        print(f"\nTransaction Totals:")
        print(f"  Total debits: ${total_debits:.2f}")
        print(f"  Total credits: ${total_credits:.2f}")
        print(f"  Net change: ${total_amount:.2f}")
        print(f"  Transaction count: {len(transactions)}")

        # Display summary
        print(f"\n" + "="*70)
        if passes and not errors:
            print(f"✓ VALIDATION PASSED - All balances and counts match!")
        else:
            print(f"✗ VALIDATION FAILED")
            if errors:
                print(f"\nErrors found:")
                for error in errors:
                    print(f"  - {error}")
        print(f"="*70)

        # Display transaction details if requested (show first 10 and last 5)
        if transactions:
            print(f"\nTransaction Details (showing first 10 of {len(transactions)}):")
            for i, tx in enumerate(transactions[:10]):
                print(f"  {i+1:3d}. {tx.get('transaction_date', 'N/A')} | ${tx.get('amount', 0):>10.2f} | {tx.get('description', 'N/A')[:40]}")

            if len(transactions) > 15:
                print(f"  ... ({len(transactions) - 15} more transactions) ...")
                for i, tx in enumerate(transactions[-5:], start=len(transactions)-4):
                    print(f"  {i:3d}. {tx.get('transaction_date', 'N/A')} | ${tx.get('amount', 0):>10.2f} | {tx.get('description', 'N/A')[:40]}")

        return passes and not errors

    except Exception as e:
        logger.error(f"Error during PDF validation: {str(e)}", exc_info=True)
        print(f"✗ ERROR: {str(e)}", flush=True)
        return False


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python scripts/parse_and_validate_pdf.py <pdf_file_path> [org_id]")
        print("Example: python scripts/parse_and_validate_pdf.py /path/to/bank_statement.pdf 1")
        sys.exit(1)

    pdf_path = sys.argv[1]
    org_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1

    success = parse_and_validate_pdf(pdf_path, org_id)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
