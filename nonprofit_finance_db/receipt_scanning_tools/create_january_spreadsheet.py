#!/usr/bin/env python3
"""Build a January 2025 spreadsheet directly from the MySQL data."""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import List, Sequence, Tuple

from mysql.connector import Error as MySQLError

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app.config import settings  # noqa: E402
from app.db import get_connection  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent / "generated_spreadsheets"
OUTPUT_FILE = OUTPUT_DIR / "january_2025_spreadsheet.csv"
JAN_START = date(2025, 1, 1)
JAN_END = date(2025, 1, 31)
DEFAULT_ORG_ID = 1


@dataclass
class SpreadsheetRow:
    date: date
    description: str
    source: str
    ledger_type: str
    amount: Decimal
    net_change: Decimal
    notes: str


def format_currency(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)}"


def classify_transaction_type(txn_type: str) -> Tuple[str, int, str]:
    mapping: Sequence[Tuple[str, str, int, str]] = (
        ("CREDIT", "Income", 1, "Bank credit recorded in transactions."),
        ("DEBIT", "Expense", -1, "Bank debit recorded in transactions."),
        ("TRANSFER", "Transfer Out", -1, "Transfer recorded in transactions."),
    )
    txn_type = (txn_type or "CREDIT").upper()
    for match, ledger_type, direction, note in mapping:
        if txn_type == match:
            return ledger_type, direction, note
    return "Income", 1, f"Unmapped transaction_type={txn_type!r}; treated as income."


def fetch_transactions(cnx) -> List[SpreadsheetRow]:
    query = """
        SELECT transaction_date, description, amount, transaction_type
        FROM transactions
        WHERE org_id = %s
          AND transaction_date BETWEEN %s AND %s
        ORDER BY transaction_date ASC, id ASC
    """
    rows: List[SpreadsheetRow] = []

    with cnx.cursor(dictionary=True) as cursor:
        cursor.execute(query, (DEFAULT_ORG_ID, JAN_START, JAN_END))
        for record in cursor.fetchall():
            amount = Decimal(record["amount"])
            ledger_type, direction, note = classify_transaction_type(record["transaction_type"])
            net_change = amount * direction
            rows.append(
                SpreadsheetRow(
                    date=record["transaction_date"],
                    description=record["description"],
                    source="transactions",
                    ledger_type=ledger_type,
                    amount=amount,
                    net_change=net_change,
                    notes=note,
                )
            )

    return rows


def fetch_expenses(cnx) -> List[SpreadsheetRow]:
    query = """
        SELECT expense_date, description, amount, method
        FROM expenses
        WHERE org_id = %s
          AND expense_date BETWEEN %s AND %s
        ORDER BY expense_date ASC, id ASC
    """
    rows: List[SpreadsheetRow] = []

    with cnx.cursor(dictionary=True) as cursor:
        cursor.execute(query, (DEFAULT_ORG_ID, JAN_START, JAN_END))
        for record in cursor.fetchall():
            amount = Decimal(record["amount"])
            payment_method = record["method"] or "OTHER"
            rows.append(
                SpreadsheetRow(
                    date=record["expense_date"],
                    description=record["description"],
                    source="expenses",
                    ledger_type="Expense",
                    amount=amount,
                    net_change=-amount,
                    notes=f"Expense paid via {payment_method}.",
                )
            )

    return rows


def gather_rows() -> List[SpreadsheetRow]:
    with get_connection() as cnx:
        rows = fetch_transactions(cnx) + fetch_expenses(cnx)

    if not rows:
        raise RuntimeError("No January 2025 data found in transactions or expenses.")

    return sorted(rows, key=lambda row: (row.date, row.source))


def write_spreadsheet(rows: List[SpreadsheetRow]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    running_total = Decimal("0")
    total_inflows = Decimal("0")
    total_outflows = Decimal("0")

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["January 2025 Financial Activity (MySQL Source)"])
        writer.writerow(
            [
                f"Database: {settings.database}",
                f"Host: {settings.host}:{settings.port}",
                f"Org ID: {DEFAULT_ORG_ID}",
            ]
        )
        writer.writerow([])
        writer.writerow(
            [
                "Date",
                "Description",
                "Source",
                "Ledger Type",
                "Amount",
                "Net Change",
                "Running Net",
                "Notes",
            ]
        )

        for row in rows:
            running_total += row.net_change
            if row.net_change >= 0:
                total_inflows += row.net_change
            else:
                total_outflows -= row.net_change

            writer.writerow(
                [
                    row.date.isoformat(),
                    row.description,
                    row.source,
                    row.ledger_type,
                    format_currency(row.amount),
                    format_currency(row.net_change),
                    format_currency(running_total),
                    row.notes,
                ]
            )

        writer.writerow([])
        writer.writerow(["Summary", "Value"])
        writer.writerow(["Total Records", str(len(rows))])
        writer.writerow(["Total Inflows", format_currency(total_inflows)])
        writer.writerow(["Total Outflows", format_currency(total_outflows)])
        writer.writerow(["Net Change", format_currency(running_total)])

    return OUTPUT_FILE


def main() -> None:
    rows = gather_rows()
    spreadsheet_path = write_spreadsheet(rows)
    print(f"✓ January spreadsheet created: {spreadsheet_path}")


if __name__ == "__main__":
    try:
        main()
    except MySQLError as exc:  # pragma: no cover - CLI helper
        print(f"✗ Failed to connect to MySQL: {exc}")
        raise
    except Exception as exc:  # pragma: no cover - CLI helper
        print(f"✗ Failed to build January spreadsheet: {exc}")
        raise
