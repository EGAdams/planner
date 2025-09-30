#!/usr/bin/env python3
"""
Enhanced CLI Dashboard for viewing transaction data

Usage:
    python scripts/view_transactions.py [options]

Features:
    - Interactive filtering and search
    - Summary statistics
    - Pagination
    - Export capabilities
    - Rich terminal formatting
"""

import sys
import os
import argparse
import json
import csv
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Any, Optional

# Rich imports for beautiful terminal output
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.align import Align
from rich import box

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_connection

class TransactionViewer:
    """Enhanced transaction data viewer with CLI interface"""

    def __init__(self, org_id: int = 1):
        self.org_id = org_id
        self.page_size = 20
        self.current_page = 1
        self.filters = {}
        self.sort_by = 'transaction_date'
        self.sort_order = 'DESC'
        self.console = Console()

    def get_transactions(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict[str, Any]]:
        """Get transactions with current filters and pagination"""
        with get_connection() as conn:
            cursor = conn.cursor()

            # Build WHERE clause
            where_conditions = ["org_id = %s"]
            params = [self.org_id]

            if self.filters.get('start_date'):
                where_conditions.append("transaction_date >= %s")
                params.append(self.filters['start_date'])

            if self.filters.get('end_date'):
                where_conditions.append("transaction_date <= %s")
                params.append(self.filters['end_date'])

            if self.filters.get('transaction_type'):
                where_conditions.append("transaction_type = %s")
                params.append(self.filters['transaction_type'])

            if self.filters.get('min_amount'):
                where_conditions.append("amount >= %s")
                params.append(self.filters['min_amount'])

            if self.filters.get('max_amount'):
                where_conditions.append("amount <= %s")
                params.append(self.filters['max_amount'])

            if self.filters.get('search'):
                where_conditions.append("description LIKE %s")
                params.append(f"%{self.filters['search']}%")

            if self.filters.get('account_number'):
                where_conditions.append("account_number = %s")
                params.append(self.filters['account_number'])

            where_clause = " AND ".join(where_conditions)

            # Build ORDER BY clause
            order_clause = f"ORDER BY {self.sort_by} {self.sort_order}"

            # Build LIMIT clause
            limit_clause = ""
            if limit:
                limit_clause = f"LIMIT {limit}"
                if offset > 0:
                    limit_clause += f" OFFSET {offset}"

            query = f"""
            SELECT id, transaction_date, amount, description, transaction_type,
                   account_number, bank_reference, balance_after, import_batch_id,
                   created_at
            FROM transactions
            WHERE {where_clause}
            {order_clause}
            {limit_clause}
            """

            cursor.execute(query, params)
            columns = [desc[0] for desc in cursor.description]

            return [dict(zip(columns, row)) for row in cursor.fetchall()]

    def get_transaction_count(self) -> int:
        """Get total count of transactions matching current filters"""
        with get_connection() as conn:
            cursor = conn.cursor()

            where_conditions = ["org_id = %s"]
            params = [self.org_id]

            if self.filters.get('start_date'):
                where_conditions.append("transaction_date >= %s")
                params.append(self.filters['start_date'])

            if self.filters.get('end_date'):
                where_conditions.append("transaction_date <= %s")
                params.append(self.filters['end_date'])

            if self.filters.get('transaction_type'):
                where_conditions.append("transaction_type = %s")
                params.append(self.filters['transaction_type'])

            if self.filters.get('min_amount'):
                where_conditions.append("amount >= %s")
                params.append(self.filters['min_amount'])

            if self.filters.get('max_amount'):
                where_conditions.append("amount <= %s")
                params.append(self.filters['max_amount'])

            if self.filters.get('search'):
                where_conditions.append("description LIKE %s")
                params.append(f"%{self.filters['search']}%")

            if self.filters.get('account_number'):
                where_conditions.append("account_number = %s")
                params.append(self.filters['account_number'])

            where_clause = " AND ".join(where_conditions)

            query = f"SELECT COUNT(*) FROM transactions WHERE {where_clause}"
            cursor.execute(query, params)
            return cursor.fetchone()[0]

    def get_summary_stats(self) -> Dict[str, Any]:
        """Get summary statistics for current filtered data"""
        with get_connection() as conn:
            cursor = conn.cursor()

            where_conditions = ["org_id = %s"]
            params = [self.org_id]

            if self.filters.get('start_date'):
                where_conditions.append("transaction_date >= %s")
                params.append(self.filters['start_date'])

            if self.filters.get('end_date'):
                where_conditions.append("transaction_date <= %s")
                params.append(self.filters['end_date'])

            if self.filters.get('transaction_type'):
                where_conditions.append("transaction_type = %s")
                params.append(self.filters['transaction_type'])

            if self.filters.get('min_amount'):
                where_conditions.append("amount >= %s")
                params.append(self.filters['min_amount'])

            if self.filters.get('max_amount'):
                where_conditions.append("amount <= %s")
                params.append(self.filters['max_amount'])

            if self.filters.get('search'):
                where_conditions.append("description LIKE %s")
                params.append(f"%{self.filters['search']}%")

            if self.filters.get('account_number'):
                where_conditions.append("account_number = %s")
                params.append(self.filters['account_number'])

            where_clause = " AND ".join(where_conditions)

            # Get overall stats
            query = f"""
            SELECT
                COUNT(*) as total_count,
                SUM(amount) as total_amount,
                AVG(amount) as avg_amount,
                MIN(amount) as min_amount,
                MAX(amount) as max_amount,
                MIN(transaction_date) as earliest_date,
                MAX(transaction_date) as latest_date
            FROM transactions
            WHERE {where_clause}
            """

            cursor.execute(query, params)
            stats = dict(zip([desc[0] for desc in cursor.description], cursor.fetchone()))

            # Get breakdown by type
            type_query = f"""
            SELECT transaction_type, COUNT(*) as count, SUM(amount) as total
            FROM transactions
            WHERE {where_clause}
            GROUP BY transaction_type
            """

            cursor.execute(type_query, params)
            type_breakdown = {}
            for row in cursor.fetchall():
                type_breakdown[row[0]] = {'count': row[1], 'total': float(row[2]) if row[2] else 0}

            stats['type_breakdown'] = type_breakdown
            return stats

    def print_header(self):
        """Print application header with Rich formatting"""
        header_text = Text("🏦 TRANSACTION VIEWER DASHBOARD", style="bold bright_white")
        header_panel = Panel(
            Align.center(header_text),
            style="bold bright_blue",
            box=box.DOUBLE,
            padding=(1, 2)
        )
        self.console.print(header_panel)

    def print_summary(self, stats: Dict[str, Any]):
        """Print summary statistics with Rich formatting"""
        # Create main summary table
        summary_table = Table(box=box.ROUNDED, show_header=False, padding=(0, 1))
        summary_table.add_column("Metric", style="bold cyan", width=20)
        summary_table.add_column("Value", style="bold green")

        summary_table.add_row("Total Transactions", f"{stats['total_count']:,}")

        if stats['total_amount']:
            summary_table.add_row("Total Amount", f"${stats['total_amount']:,.2f}")
            summary_table.add_row("Average Amount", f"${stats['avg_amount']:,.2f}")
            summary_table.add_row("Min Amount", f"${stats['min_amount']:,.2f}")
            summary_table.add_row("Max Amount", f"${stats['max_amount']:,.2f}")

        if stats['earliest_date'] and stats['latest_date']:
            summary_table.add_row("Date Range", f"{stats['earliest_date']} to {stats['latest_date']}")

        # Create type breakdown table if available
        if stats['type_breakdown']:
            type_table = Table(box=box.MINIMAL, show_header=True)
            type_table.add_column("Transaction Type", style="cyan")
            type_table.add_column("Count", style="yellow", justify="right")
            type_table.add_column("Total Amount", style="green", justify="right")

            for txn_type, data in stats['type_breakdown'].items():
                type_table.add_row(
                    txn_type,
                    f"{data['count']:,}",
                    f"${data['total']:,.2f}"
                )

            # Combine both tables in panels
            self.console.print(Panel(
                summary_table,
                title="📊 Summary Statistics",
                title_align="left",
                border_style="blue"
            ))
            self.console.print(Panel(
                type_table,
                title="📈 Breakdown by Type",
                title_align="left",
                border_style="green"
            ))
        else:
            self.console.print(Panel(
                summary_table,
                title="📊 Summary Statistics",
                title_align="left",
                border_style="blue"
            ))

    def print_filters(self):
        """Print current active filters with Rich formatting"""
        if not any(self.filters.values()):
            return

        filter_table = Table(box=box.MINIMAL, show_header=False)
        filter_table.add_column("Filter", style="cyan", width=15)
        filter_table.add_column("Value", style="yellow")

        for key, value in self.filters.items():
            if value:
                display_key = key.replace('_', ' ').title()
                filter_table.add_row(display_key, str(value))

        panel = Panel(
            filter_table,
            title="🔍 Active Filters",
            title_align="left",
            border_style="yellow"
        )
        self.console.print(panel)

    def print_transactions(self, transactions: List[Dict[str, Any]], start_index: int = 0):
        """Print transaction table with Rich formatting"""
        if not transactions:
            self.console.print("\n❌ No transactions found matching current filters.", style="bold red")
            return

        # Create beautiful table
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("Date", style="cyan", width=12)
        table.add_column("Type", style="yellow", width=10)
        table.add_column("Amount", style="green", width=15, justify="right")
        table.add_column("Description", style="white", min_width=30, max_width=50)
        table.add_column("Account", style="blue", width=12)

        # Add transactions with color coding
        for i, tx in enumerate(transactions):
            index = start_index + i + 1
            date_str = str(tx['transaction_date'])
            type_str = tx['transaction_type']
            amount = tx['amount']

            # Color code amount based on positive/negative
            if amount >= 0:
                amount_str = f"[green]+${amount:,.2f}[/green]"
            else:
                amount_str = f"[red]-${abs(amount):,.2f}[/red]"

            desc = tx['description'] or 'N/A'
            # Truncate description intelligently
            if len(desc) > 47:
                desc = desc[:44] + "..."

            account_str = tx['account_number'] or 'N/A'

            # Alternate row colors for better readability
            if i % 2 == 0:
                table.add_row(
                    str(index), date_str, type_str, amount_str, desc, account_str,
                    style="on grey11"
                )
            else:
                table.add_row(
                    str(index), date_str, type_str, amount_str, desc, account_str
                )

        # Print with panel
        panel = Panel(
            table,
            title="📋 Transactions",
            title_align="left",
            border_style="bright_blue"
        )
        self.console.print(panel)

    def print_pagination_info(self, total_count: int):
        """Print pagination information with Rich formatting"""
        total_pages = (total_count + self.page_size - 1) // self.page_size
        start_record = (self.current_page - 1) * self.page_size + 1
        end_record = min(self.current_page * self.page_size, total_count)

        # Page info
        page_info = Text()
        page_info.append("Page ", style="dim")
        page_info.append(f"{self.current_page}", style="bold cyan")
        page_info.append(" of ", style="dim")
        page_info.append(f"{total_pages}", style="bold cyan")
        page_info.append(" | Records ", style="dim")
        page_info.append(f"{start_record}-{end_record}", style="bold yellow")
        page_info.append(" of ", style="dim")
        page_info.append(f"{total_count}", style="bold yellow")

        # Navigation options with proper Rich Text formatting
        options_text = Text("Options: ")

        nav_options = []
        if self.current_page > 1:
            nav_options.append(("p", "green", "Previous page"))
        if self.current_page < total_pages:
            nav_options.append(("n", "green", "Next page"))

        nav_options.extend([
            ("f", "blue", "Filter"),
            ("s", "blue", "Sort"),
            ("e", "blue", "Export"),
            ("r", "yellow", "Reset"),
            ("q", "red", "Quit")
        ])

        for i, (key, color, desc) in enumerate(nav_options):
            if i > 0:
                options_text.append(" | ")
            options_text.append(key, style=f"bold {color}")
            options_text.append(f") {desc}")

        # Create panel for navigation
        nav_content = Text()
        nav_content.append(page_info)
        nav_content.append("\n\n")
        nav_content.append(options_text)

        nav_panel = Panel(
            Align.center(nav_content),
            title="Navigation",
            border_style="cyan"
        )
        self.console.print(nav_panel)

    def handle_filter_menu(self):
        """Handle filter configuration"""
        print(f"\n🔍 FILTER MENU")
        print("-" * 40)
        print("1) Date range")
        print("2) Transaction type")
        print("3) Amount range")
        print("4) Search description")
        print("5) Account number")
        print("6) Clear all filters")
        print("0) Back to main menu")

        choice = input("\nSelect filter option: ").strip()

        if choice == '1':
            start_date = input("Start date (YYYY-MM-DD) [Enter to skip]: ").strip()
            end_date = input("End date (YYYY-MM-DD) [Enter to skip]: ").strip()
            if start_date:
                self.filters['start_date'] = start_date
            if end_date:
                self.filters['end_date'] = end_date

        elif choice == '2':
            print("Transaction types: CREDIT, DEBIT, TRANSFER")
            txn_type = input("Transaction type [Enter to skip]: ").strip().upper()
            if txn_type in ['CREDIT', 'DEBIT', 'TRANSFER']:
                self.filters['transaction_type'] = txn_type
            elif txn_type:
                print("❌ Invalid transaction type")

        elif choice == '3':
            min_amount = input("Minimum amount [Enter to skip]: ").strip()
            max_amount = input("Maximum amount [Enter to skip]: ").strip()
            if min_amount:
                try:
                    self.filters['min_amount'] = float(min_amount)
                except ValueError:
                    print("❌ Invalid minimum amount")
            if max_amount:
                try:
                    self.filters['max_amount'] = float(max_amount)
                except ValueError:
                    print("❌ Invalid maximum amount")

        elif choice == '4':
            search_term = input("Search description [Enter to skip]: ").strip()
            if search_term:
                self.filters['search'] = search_term

        elif choice == '5':
            account = input("Account number [Enter to skip]: ").strip()
            if account:
                self.filters['account_number'] = account

        elif choice == '6':
            self.filters.clear()
            print("✅ All filters cleared")

        # Reset to first page when filters change
        self.current_page = 1

    def handle_sort_menu(self):
        """Handle sort configuration"""
        print(f"\n📊 SORT MENU")
        print("-" * 40)
        print("1) Transaction date")
        print("2) Amount")
        print("3) Description")
        print("4) Transaction type")
        print("0) Back to main menu")

        choice = input("\nSelect sort field: ").strip()

        sort_fields = {
            '1': 'transaction_date',
            '2': 'amount',
            '3': 'description',
            '4': 'transaction_type'
        }

        if choice in sort_fields:
            self.sort_by = sort_fields[choice]

            order = input("Sort order (a)scending or (d)escending [d]: ").strip().lower()
            self.sort_order = 'ASC' if order == 'a' else 'DESC'

            print(f"✅ Sorting by {self.sort_by} ({self.sort_order})")
            self.current_page = 1

    def export_transactions(self, format_type: str):
        """Export transactions to file"""
        transactions = self.get_transactions()

        if not transactions:
            print("❌ No transactions to export")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transactions_export_{timestamp}.{format_type}"

        try:
            if format_type == 'csv':
                with open(filename, 'w', newline='') as csvfile:
                    if transactions:
                        writer = csv.DictWriter(csvfile, fieldnames=transactions[0].keys())
                        writer.writeheader()
                        for tx in transactions:
                            # Convert date objects to strings
                            row = {}
                            for key, value in tx.items():
                                if isinstance(value, date):
                                    row[key] = value.isoformat()
                                else:
                                    row[key] = value
                            writer.writerow(row)

            elif format_type == 'json':
                def json_serializer(obj):
                    if isinstance(obj, date):
                        return obj.isoformat()
                    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

                with open(filename, 'w') as jsonfile:
                    json.dump(transactions, jsonfile, indent=2, default=json_serializer)

            print(f"✅ Exported {len(transactions)} transactions to {filename}")

        except Exception as e:
            print(f"❌ Export failed: {str(e)}")

    def handle_export_menu(self):
        """Handle export options"""
        print(f"\n💾 EXPORT MENU")
        print("-" * 40)
        print("1) Export to CSV")
        print("2) Export to JSON")
        print("0) Back to main menu")

        choice = input("\nSelect export format: ").strip()

        if choice == '1':
            self.export_transactions('csv')
        elif choice == '2':
            self.export_transactions('json')

    def reset_all(self):
        """Reset filters, sorting, and pagination"""
        self.filters.clear()
        self.current_page = 1
        self.sort_by = 'transaction_date'
        self.sort_order = 'DESC'
        print("✅ Reset to default view")

    def run_interactive(self):
        """Run interactive dashboard"""
        self.print_header()

        while True:
            try:
                # Get current data
                total_count = self.get_transaction_count()

                if total_count == 0:
                    print("\n❌ No transactions found.")
                    stats = self.get_summary_stats()
                    self.print_summary(stats)
                    self.print_filters()

                    print("\nOptions: f) Filter | r) Reset | q) Quit")
                    choice = input("\nEnter your choice: ").strip().lower()

                    if choice == 'f':
                        self.handle_filter_menu()
                    elif choice == 'r':
                        self.reset_all()
                    elif choice == 'q':
                        break
                    continue

                # Calculate offset for pagination
                offset = (self.current_page - 1) * self.page_size

                # Get transactions for current page
                transactions = self.get_transactions(limit=self.page_size, offset=offset)
                stats = self.get_summary_stats()

                # Clear screen and display
                os.system('clear' if os.name == 'posix' else 'cls')
                self.print_header()
                self.print_summary(stats)
                self.print_filters()
                self.print_transactions(transactions, offset)
                self.print_pagination_info(total_count)

                # Get user input
                choice = input("\nEnter your choice: ").strip().lower()

                if choice == 'q':
                    break
                elif choice == 'n':
                    total_pages = (total_count + self.page_size - 1) // self.page_size
                    if self.current_page < total_pages:
                        self.current_page += 1
                elif choice == 'p':
                    if self.current_page > 1:
                        self.current_page -= 1
                elif choice == 'f':
                    self.handle_filter_menu()
                elif choice == 's':
                    self.handle_sort_menu()
                elif choice == 'e':
                    self.handle_export_menu()
                elif choice == 'r':
                    self.reset_all()
                else:
                    print("❌ Invalid choice. Press Enter to continue...")
                    input()

            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}")
                input("Press Enter to continue...")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Enhanced Transaction Viewer Dashboard')
    parser.add_argument('--org-id', type=int, default=1, help='Organization ID (default: 1)')
    parser.add_argument('--page-size', type=int, default=20, help='Records per page (default: 20)')
    parser.add_argument('--export', choices=['csv', 'json'], help='Export all data and exit')
    parser.add_argument('--summary-only', action='store_true', help='Show summary statistics only')

    args = parser.parse_args()

    viewer = TransactionViewer(org_id=args.org_id)
    viewer.page_size = args.page_size

    if args.export:
        # Non-interactive export mode
        viewer.export_transactions(args.export)
        return

    if args.summary_only:
        # Summary only mode
        viewer.print_header()
        stats = viewer.get_summary_stats()
        viewer.print_summary(stats)
        return

    # Interactive mode
    viewer.run_interactive()

if __name__ == "__main__":
    main()