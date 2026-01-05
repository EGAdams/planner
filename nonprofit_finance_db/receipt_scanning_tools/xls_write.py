#!/usr/bin/env python3
from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import List

import xlsxwriter

# Pull these from your existing January builder module.
# This assumes create_january_spreadsheet.py contains:
# - SpreadsheetRow dataclass
# - gather_rows() that returns List[SpreadsheetRow]
# - DEFAULT_ORG_ID, settings, etc.
from create_january_spreadsheet import (
    DEFAULT_ORG_ID,
    SpreadsheetRow,
    gather_rows,
    settings,
)

OUTPUT_DIR = Path(__file__).resolve().parent / "generated_spreadsheets"
OUTPUT_FILE = OUTPUT_DIR / "january_2025_spreadsheet.xlsx"


def write_spreadsheet(rows: List[SpreadsheetRow]) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    running_total = Decimal("0")
    total_inflows = Decimal("0")
    total_outflows = Decimal("0")

    workbook = xlsxwriter.Workbook(str(OUTPUT_FILE))
    ws = workbook.add_worksheet("January 2025")

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
    ws.write(0, 0, "January 2025 Financial Activity (MySQL Source)", title_fmt)
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

    for row in rows:
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

    if data_last_row >= data_first_row:
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

    summary_row = data_last_row + 3 if data_last_row >= data_first_row else start_row + 3
    ws.write(summary_row, 0, "Summary", title_fmt)

    ws.write(summary_row + 2, 0, "Total Records", label_bold_fmt)
    ws.write_number(summary_row + 2, 1, int(len(rows)))

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
    out_path = write_spreadsheet(rows)
    print(f"✓ Excel spreadsheet created: {out_path.resolve()}")


if __name__ == "__main__":
    main()
