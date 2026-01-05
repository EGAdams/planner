#!/usr/bin/env python3
"""Build a February 2025 spreadsheet directly from the MySQL data."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import List, Sequence, Tuple

import xlsxwriter
from mysql.connector import Error as MySQLError

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from app.config import settings  # noqa: E402
from app.db import get_connection  # noqa: E402

OUTPUT_DIR = Path(__file__).resolve().parent / "generated_spreadsheets"
OUTPUT_FILE = OUTPUT_DIR / "february_2025_daily_spreadsheet.xlsx"
FEB_START = date(2025, 2, 1)
FEB_END = date(2025, 2, 28)
DEFAULT_ORG_ID = 1


@dataclass
class SpreadsheetRow:
    date: date
    description: str
    category: str | None
    expense_type: str | None
    source: str
    ledger_type: str
    amount: Decimal
    net_change: Decimal
    notes: str


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
        cursor.execute(query, (DEFAULT_ORG_ID, FEB_START, FEB_END))
        for record in cursor.fetchall():
            amount = Decimal(record["amount"])
            ledger_type, direction, note = classify_transaction_type(record["transaction_type"])
            net_change = amount * direction
            rows.append(
                SpreadsheetRow(
                    date=record["transaction_date"],
                    description=record["description"],
                    category=None,
                    expense_type=record["transaction_type"],
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
        SELECT e.expense_date, e.description, e.amount, e.method, c.name as category
        FROM expenses e
        LEFT JOIN categories c ON e.category_id = c.id
        WHERE e.org_id = %s
          AND e.expense_date BETWEEN %s AND %s
        ORDER BY e.expense_date ASC, e.id ASC
    """
    rows: List[SpreadsheetRow] = []

    with cnx.cursor(dictionary=True) as cursor:
        cursor.execute(query, (DEFAULT_ORG_ID, FEB_START, FEB_END))
        for record in cursor.fetchall():
            amount = Decimal(record["amount"])
            payment_method = record["method"] or "OTHER"
            rows.append(
                SpreadsheetRow(
                    date=record["expense_date"],
                    description=record["description"],
                    category=record["category"],
                    expense_type=payment_method,
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
        raise RuntimeError("No February 2025 data found in transactions or expenses.")

    return sorted(rows, key=lambda row: (row.date, row.source))


def write_daily_spreadsheet(all_rows: List[SpreadsheetRow]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    workbook = xlsxwriter.Workbook(str(OUTPUT_FILE))

    # ----------------------------
    # Formats
    # ----------------------------
    title_fmt = workbook.add_format({"bold": True, "font_size": 14})
    meta_key_fmt = workbook.add_format({"bold": True})
    header_fmt = workbook.add_format({"bold": True, "bg_color": "#EDEDED", "border": 1})
    text_fmt = workbook.add_format({"text_wrap": True, "valign": "top"})
    date_fmt = workbook.add_format({"num_format": "yyyy-mm-dd"})
    money_fmt = workbook.add_format({"num_format": "$#,##0.00"})
    money_neg_fmt = workbook.add_format({"num_format": "$#,##0.00;[Red]$#,##0.00"})
    money_bold_fmt = workbook.add_format({"num_format": "$#,##0.00", "bold": True})
    label_bold_fmt = workbook.add_format({"bold": True})

    # Create a sheet for each day of February (1-28)
    for day in range(1, 29):
        # Filter rows for this specific day
        target_date = date(2025, 2, day)
        day_rows = [row for row in all_rows if row.date == target_date]

        # Create worksheet
        sheet_name = f"Feb {day:02d}"
        ws = workbook.add_worksheet(sheet_name)

        # Column widths
        ws.set_column("A:A", 12)
        ws.set_column("B:B", 42)
        ws.set_column("C:C", 28)
        ws.set_column("D:D", 16)
        ws.set_column("E:E", 14)
        ws.set_column("F:F", 14)
        ws.set_column("G:I", 14)
        ws.set_column("J:J", 52)

        # ----------------------------
        # Title + metadata
        # ----------------------------
        ws.write(0, 0, f"February {day}, 2025 - Financial Activity", title_fmt)
        ws.write(2, 0, "Database:", meta_key_fmt)
        ws.write(2, 1, str(settings.database))
        ws.write(3, 0, "Host:", meta_key_fmt)
        ws.write(3, 1, f"{settings.host}:{settings.port}")
        ws.write(4, 0, "Org ID:", meta_key_fmt)
        ws.write_number(4, 1, int(DEFAULT_ORG_ID))

        # ----------------------------
        # Table header
        # ----------------------------
        start_row = 6
        headers = [
            "Date",
            "Description",
            "Expense Category",
            "Expense Type",
            "Source",
            "Ledger Type",
            "Amount",
            "Net Change",
            "Running Net",
            "Notes",
        ]
        for col, h in enumerate(headers):
            ws.write(start_row, col, h, header_fmt)

        ws.freeze_panes(start_row + 1, 0)

        # ----------------------------
        # Data rows
        # ----------------------------
        data_first_row = start_row + 1
        r = data_first_row

        running_total = Decimal("0")
        total_inflows = Decimal("0")
        total_outflows = Decimal("0")

        if day_rows:
            # Write actual expense data
            for row in day_rows:
                running_total += row.net_change
                if row.net_change >= 0:
                    total_inflows += row.net_change
                else:
                    total_outflows -= row.net_change

                ws.write_datetime(r, 0, row.date, date_fmt)
                ws.write_string(r, 1, row.description or "", text_fmt)
                ws.write_string(r, 2, row.category or "", text_fmt)
                ws.write_string(r, 3, row.expense_type or "", text_fmt)
                ws.write_string(r, 4, row.source or "", text_fmt)
                ws.write_string(r, 5, row.ledger_type or "", text_fmt)

                ws.write_number(r, 6, float(row.amount), money_fmt)
                ws.write_number(r, 7, float(row.net_change), money_neg_fmt)
                ws.write_number(r, 8, float(running_total), money_neg_fmt)

                ws.write_string(r, 9, row.notes or "", text_fmt)
                r += 1

            data_last_row = r - 1

            # Add table formatting if we have data
            ws.add_table(
                start_row,
                0,
                data_last_row,
                len(headers) - 1,
                {
                    "style": "Table Style Light 9",
                    "columns": [{"header": h} for h in headers],
                },
            )

            # Conditional formatting for negative values
            ws.conditional_format(
                data_first_row,
                7,
                data_last_row,
                7,
                {
                    "type": "cell",
                    "criteria": "<",
                    "value": 0,
                    "format": workbook.add_format({"font_color": "red"}),
                },
            )
        else:
            # No expenses for this day - write a single row with 0.00
            ws.write_datetime(r, 0, target_date, date_fmt)
            ws.write_string(r, 1, "No expenses", text_fmt)
            ws.write_string(r, 2, "", text_fmt)
            ws.write_string(r, 3, "", text_fmt)
            ws.write_string(r, 4, "", text_fmt)
            ws.write_string(r, 5, "", text_fmt)
            ws.write_number(r, 6, 0.00, money_fmt)
            ws.write_number(r, 7, 0.00, money_neg_fmt)
            ws.write_number(r, 8, 0.00, money_neg_fmt)
            ws.write_string(r, 9, "No activity for this day", text_fmt)

            data_last_row = r

            # Add table with single row
            ws.add_table(
                start_row,
                0,
                data_last_row,
                len(headers) - 1,
                {
                    "style": "Table Style Light 9",
                    "columns": [{"header": h} for h in headers],
                },
            )

        # ----------------------------
        # Summary section
        # ----------------------------
        summary_row = data_last_row + 3
        ws.write(summary_row, 0, "Daily Summary", title_fmt)

        ws.write(summary_row + 2, 0, "Total Records", label_bold_fmt)
        ws.write_number(summary_row + 2, 1, int(len(day_rows)))

        ws.write(summary_row + 3, 0, "Total Inflows", label_bold_fmt)
        ws.write_number(summary_row + 3, 1, float(total_inflows), money_bold_fmt)

        ws.write(summary_row + 4, 0, "Total Outflows", label_bold_fmt)
        ws.write_number(summary_row + 4, 1, float(total_outflows), money_bold_fmt)

        ws.write(summary_row + 5, 0, "Net Change", label_bold_fmt)
        ws.write_number(summary_row + 5, 1, float(running_total), money_bold_fmt)

    workbook.close()
    return OUTPUT_FILE


def main() -> None:
    rows = gather_rows()
    out_path = write_daily_spreadsheet(rows)
    print(f"✓ Daily Excel spreadsheet created: {out_path.resolve()}")
    print(f"  - Created 28 sheets (one for each day of February)")


if __name__ == "__main__":
    try:
        main()
    except MySQLError as exc:
        print(f"MySQL error: {exc}")
        raise
    except Exception as exc:
        print(f"Failed to build February spreadsheet: {exc}")
        raise
