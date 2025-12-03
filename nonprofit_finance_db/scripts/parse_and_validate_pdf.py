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
import json
import logging
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add parent directory to path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from parsers import PDFParser
from ingestion.processors import TransactionProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DATABASE_CORRUPT_PATH = Path(__file__).resolve().parent.parent / "database_corrupt.md"
TRANSACTION_PROCESSOR = TransactionProcessor()


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


def _normalize_description(value: Optional[str]) -> str:
    """Normalize descriptions for comparison and transaction keys."""
    if not value:
        return ''
    return ' '.join(value.strip().split()).lower()


def _build_transaction_key(org_id: int,
                           transaction_date: Optional[str],
                           amount: Optional[float],
                           description: Optional[str]) -> str:
    """Create a stable key for matching transactions."""
    amount_part = "NONE" if amount is None else f"{float(amount):.2f}"
    date_part = transaction_date or "NO_DATE"
    desc_part = _normalize_description(description)[:160]
    return f"{org_id}|{date_part}|{amount_part}|{desc_part}"


def _resolve_transaction_type(transaction: Dict[str, Any]) -> str:
    """Ensure we only write valid transaction types to the database."""
    tx_type = (transaction.get('transaction_type') or '').upper()
    if tx_type in ('DEBIT', 'CREDIT', 'TRANSFER'):
        return tx_type

    amount = transaction.get('amount')
    if amount is None:
        return 'TRANSFER'

    try:
        amount_value = float(amount)
    except (ValueError, TypeError):
        return 'TRANSFER'

    if abs(amount_value) < 0.005:
        return 'TRANSFER'
    return 'DEBIT' if amount_value < 0 else 'CREDIT'


def _default_json_serializer(obj: Any) -> str:
    """Fallback serializer for datetime objects inside debug payloads."""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def _prepare_transactions_for_db(transactions: List[Dict[str, Any]],
                                 org_id: int,
                                 pdf_path: str) -> Dict[str, Any]:
    """
    Clean transactions for DB insertion and collect warnings about skipped rows.
    """
    prepared: List[Dict[str, Any]] = []
    skipped: List[str] = []

    for idx, txn in enumerate(transactions):
        processed = TRANSACTION_PROCESSOR.process_transaction(txn)
        processed['org_id'] = processed.get('org_id') or org_id
        transaction_date = processed.get('transaction_date')
        amount = processed.get('amount')

        if transaction_date is None:
            skipped.append(f"Transaction #{idx + 1} missing transaction_date")
            continue
        if amount is None:
            skipped.append(f"Transaction #{idx + 1} missing amount")
            continue

        description = processed.get('description') or processed.get('raw_description') or ''
        raw_payload = processed.get('raw_data')
        if raw_payload:
            try:
                raw_json = json.loads(raw_payload)
            except (json.JSONDecodeError, TypeError):
                raw_json = {'raw_value': raw_payload}
        else:
            raw_json = processed.copy()

        raw_json.setdefault('source_file', pdf_path)
        prepared.append({
            'org_id': processed['org_id'],
            'transaction_date': transaction_date,
            'amount': round(float(amount), 2),
            'description': description[:255],
            'transaction_type': _resolve_transaction_type(processed),
            'account_number': processed.get('account_number'),
            'bank_reference': processed.get('bank_reference'),
            'balance_after': processed.get('balance_after'),
            'category_id': processed.get('category_id'),
            'import_batch_id': processed.get('import_batch_id'),
            'raw_data': json.dumps(raw_json, default=_default_json_serializer)
        })

    return {'prepared': prepared, 'skipped': skipped}


def _fetch_existing_transactions(connection,
                                 org_id: int,
                                 transactions: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Load existing transactions from the database keyed by our normalized signature."""
    dates = [tx['transaction_date'] for tx in transactions if tx.get('transaction_date')]
    query = (
        "SELECT id, transaction_date, amount, description, transaction_type, "
        "account_number, bank_reference, balance_after "
        "FROM transactions WHERE org_id = %s"
    )
    params: List[Any] = [org_id]

    if dates:
        start_date = min(dates)
        end_date = max(dates)
        query += " AND transaction_date BETWEEN %s AND %s"
        params.extend([start_date, end_date])

    with connection.cursor(dictionary=True) as cursor:
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()

    existing: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        tx_date = row.get('transaction_date')
        if hasattr(tx_date, 'strftime'):
            tx_date = tx_date.strftime('%Y-%m-%d')
        amount = float(row.get('amount') or 0.0)
        key = _build_transaction_key(org_id, tx_date, amount, row.get('description'))
        existing.setdefault(key, []).append(row)

    return existing


def _compare_transactions(parsed_tx: Dict[str, Any],
                          existing_tx: Dict[str, Any]) -> List[str]:
    """Return a list of differences between parsed transaction and DB record."""
    differences: List[str] = []

    parsed_amount = parsed_tx.get('amount')
    existing_amount = float(existing_tx.get('amount') or 0.0)
    if not close_enough(parsed_amount, existing_amount):
        differences.append(f"Amount mismatch (parsed {parsed_amount}, db {existing_amount})")

    parsed_desc = _normalize_description(parsed_tx.get('description'))
    existing_desc = _normalize_description(existing_tx.get('description'))
    if parsed_desc != existing_desc:
        differences.append("Description mismatch")

    parsed_type = parsed_tx.get('transaction_type')
    existing_type = existing_tx.get('transaction_type')
    if parsed_type != existing_type:
        differences.append(f"Transaction type mismatch (parsed {parsed_type}, db {existing_type})")

    parsed_account = parsed_tx.get('account_number')
    if parsed_account and existing_tx.get('account_number') != parsed_account:
        differences.append("Account number mismatch")

    parsed_reference = parsed_tx.get('bank_reference')
    if parsed_reference and existing_tx.get('bank_reference') != parsed_reference:
        differences.append("Bank reference mismatch")

    return differences


def _write_database_corrupt_report(pdf_path: str, mismatches: List[Dict[str, Any]]) -> None:
    """Write mismatch details to database_corrupt.md for debugging."""
    timestamp = datetime.utcnow().isoformat()
    lines = [
        "# Database Corruption Detected",
        "",
        f"- Timestamp: {timestamp} UTC",
        f"- Source PDF: {pdf_path}",
        f"- Total mismatches: {len(mismatches)}",
        "",
        "## Mismatch Details"
    ]

    for idx, mismatch in enumerate(mismatches, start=1):
        parsed = mismatch['parsed']
        existing = mismatch['existing']
        differences = mismatch['differences']
        lines.append(f"### Transaction {idx}")
        lines.append(f"- Key: `{mismatch['key']}`")
        lines.append(f"- Parsed Date: {parsed.get('transaction_date')}")
        lines.append(f"- Parsed Amount: {parsed.get('amount')}")
        lines.append(f"- Parsed Description: {parsed.get('description')}")
        lines.append(f"- Existing Date: {existing.get('transaction_date')}")
        lines.append(f"- Existing Amount: {existing.get('amount')}")
        lines.append(f"- Existing Description: {existing.get('description')}")
        lines.append(f"- Differences:")
        for diff in differences:
            lines.append(f"  - {diff}")
        lines.append("")

    DATABASE_CORRUPT_PATH.write_text('\n'.join(lines), encoding='utf-8')


def _sync_transactions_with_database(transactions: List[Dict[str, Any]],
                                     org_id: int,
                                     pdf_path: str) -> bool:
    """
    Ensure parsed transactions exist in the DB and match stored values.
    """
    if not transactions:
        print("⚠ No transactions available for database sync")
        return True

    prepared_summary = _prepare_transactions_for_db(transactions, org_id, pdf_path)
    prepared = prepared_summary['prepared']
    skipped = prepared_summary['skipped']

    if skipped:
        print("⚠ Some transactions were skipped during preparation:")
        for reason in skipped:
            print(f"  - {reason}")

    if not prepared:
        print("✗ Unable to sync transactions: nothing to write after preparation")
        return False

    if DATABASE_CORRUPT_PATH.exists():
        DATABASE_CORRUPT_PATH.unlink()

    try:
        from app.db import get_connection
    except ImportError as exc:
        print(f"✗ Unable to import database connection utilities: {exc}")
        return False

    try:
        with get_connection() as connection:
            existing_map = _fetch_existing_transactions(connection, org_id, prepared)
            mismatches: List[Dict[str, Any]] = []
            to_insert: List[Dict[str, Any]] = []

            for tx in prepared:
                key = _build_transaction_key(org_id, tx['transaction_date'], tx['amount'], tx.get('description'))
                existing_bucket = existing_map.get(key, [])

                if existing_bucket:
                    existing_record = existing_bucket.pop(0)
                    differences = _compare_transactions(tx, existing_record)
                    if differences:
                        mismatches.append({
                            'key': key,
                            'parsed': tx,
                            'existing': existing_record,
                            'differences': differences
                        })
                else:
                    to_insert.append(tx)

            if mismatches:
                _write_database_corrupt_report(pdf_path, mismatches)
                print("✗ Database mismatch detected. See database_corrupt.md for details.")
                return False

            inserted_count = 0
            if to_insert:
                columns = (
                    "org_id", "transaction_date", "amount", "description",
                    "transaction_type", "account_number", "bank_reference",
                    "balance_after", "category_id", "import_batch_id", "raw_data"
                )
                placeholders = ", ".join(["%s"] * len(columns))
                sql = f"INSERT INTO transactions ({', '.join(columns)}) VALUES ({placeholders})"
                values = [tuple(tx.get(col) for col in columns) for tx in to_insert]

                with connection.cursor() as cursor:
                    cursor.executemany(sql, values)
                connection.commit()
                inserted_count = len(to_insert)

            if inserted_count:
                print(f"✓ {inserted_count} transaction(s) inserted into database")
            else:
                print("✓ All transactions already present in database")

            return True

    except Exception as exc:
        print(f"✗ Database synchronization failed: {exc}")
        return False


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

        db_synced = True
        if passes and not errors:
            print(f"\n> Syncing parsed transactions with database...", flush=True)
            sys.stdout.flush()
            db_synced = _sync_transactions_with_database(transactions, org_id, pdf_path)

        return (passes and not errors) and db_synced

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
