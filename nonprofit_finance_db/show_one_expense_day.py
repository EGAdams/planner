#!/usr/bin/env python3
"""
Daily Expense Report Generator
Generates a report of all expenses for a specific date
"""
import re
from datetime import datetime
from typing import List, Dict, Optional
from app.db import query_all


def validate_date_format(date_str: str) -> bool:
    """
    Validate that date string is in MM/DD/YYYY format

    Args:
        date_str: Date string to validate

    Returns:
        True if valid format, False otherwise
    """
    pattern = r'^\d{2}/\d{2}/\d{4}$'
    if not re.match(pattern, date_str):
        return False

    # Validate that it's a real date
    try:
        datetime.strptime(date_str, '%m/%d/%Y')
        return True
    except ValueError:
        return False


def parse_date_to_mysql_format(date_str: str) -> str:
    """
    Convert date from MM/DD/YYYY to YYYY-MM-DD format

    Args:
        date_str: Date in MM/DD/YYYY format

    Returns:
        Date in YYYY-MM-DD format
    """
    dt = datetime.strptime(date_str, '%m/%d/%Y')
    return dt.strftime('%Y-%m-%d')


def fetch_expenses_for_date(mysql_date: str) -> List[Dict]:
    """
    Fetch all expenses for a specific date from database

    Args:
        mysql_date: Date in YYYY-MM-DD format

    Returns:
        List of expense dictionaries
    """
    sql = """
    SELECT
        e.id,
        e.org_id,
        e.expense_date,
        e.amount,
        e.category_id,
        e.description,
        e.method,
        e.paid_by_contact_id,
        e.receipt_url,
        c.name as category_name,
        o.name as organization_name,
        ct.name as paid_by_name
    FROM expenses e
    LEFT JOIN categories c ON e.category_id = c.id
    LEFT JOIN organizations o ON e.org_id = o.id
    LEFT JOIN contacts ct ON e.paid_by_contact_id = ct.id
    WHERE e.expense_date = %s
    ORDER BY e.id
    """
    return query_all(sql, (mysql_date,))


def format_expense_report(expenses: List[Dict], date_str: str) -> str:
    """
    Format expenses into a readable text report

    Args:
        expenses: List of expense dictionaries
        date_str: Original date string (MM/DD/YYYY)

    Returns:
        Formatted report string
    """
    lines = []
    lines.append("=" * 80)
    lines.append(f"{'DAILY EXPENSE REPORT':^80}")
    lines.append(f"{'Date: ' + date_str:^80}")
    lines.append("=" * 80)
    lines.append("")

    if not expenses:
        lines.append("No expenses found for this date.")
        lines.append("")
    else:
        total_amount = 0.0

        for i, exp in enumerate(expenses, 1):
            lines.append(f"Expense #{i}")
            lines.append("-" * 80)
            lines.append(f"ID:                {exp.get('id', 'N/A')}")
            lines.append(f"Organization:      {exp.get('organization_name', 'N/A')}")
            lines.append(f"Category:          {exp.get('category_name', 'N/A')}")
            lines.append(f"Amount:            ${exp.get('amount', 0):.2f}")
            lines.append(f"Payment Method:    {exp.get('method', 'N/A')}")
            lines.append(f"Paid By:           {exp.get('paid_by_name', 'N/A')}")
            lines.append(f"Description:       {exp.get('description', 'N/A')}")

            if exp.get('receipt_url'):
                lines.append(f"Receipt URL:       {exp['receipt_url']}")

            lines.append("")
            total_amount += float(exp.get('amount', 0))

        lines.append("=" * 80)
        lines.append(f"Total Expenses:    ${total_amount:.2f}")
        lines.append(f"Number of Expenses: {len(expenses)}")
        lines.append("=" * 80)

    return "\n".join(lines)


def generate_report_filename(date_str: str) -> str:
    """
    Generate filename for the report

    Args:
        date_str: Date in MM/DD/YYYY format

    Returns:
        Filename string
    """
    mysql_date = parse_date_to_mysql_format(date_str)
    return f"expense_report_{mysql_date}.txt"


def main():
    """Main execution function"""
    print("Daily Expense Report Generator")
    print("=" * 50)

    # Get date input from user
    date_input = input("Enter date in format MM/DD/YYYY: ").strip()

    # Validate date format
    if not validate_date_format(date_input):
        print("ERROR: Invalid date format. Please use MM/DD/YYYY format.")
        print("Example: 01/15/2024")
        return 1

    try:
        # Convert to MySQL format
        mysql_date = parse_date_to_mysql_format(date_input)

        print(f"\nFetching expenses for {date_input}...")

        # Fetch expenses
        expenses = fetch_expenses_for_date(mysql_date)

        # Generate report
        report_content = format_expense_report(expenses, date_input)

        # Generate filename
        filename = generate_report_filename(date_input)

        # Write to file
        with open(filename, 'w') as f:
            f.write(report_content)

        # Display report
        print("\n" + report_content)
        print(f"\nReport saved to: {filename}")

        return 0

    except Exception as e:
        print(f"\nERROR: Database connection or query failed.")
        print(f"Details: {str(e)}")
        print("\nPlease check:")
        print("1. Database connection settings in .env file")
        print("2. Database is running and accessible")
        print("3. Required environment variables are set")
        return 1


if __name__ == "__main__":
    exit(main())
