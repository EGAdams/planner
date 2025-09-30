#!/usr/bin/env python3
"""
Scrollable Transaction Viewer with Page Navigation

Usage:
    python scripts/scrollable_viewer.py [--page N]

Controls:
    --page N       - Jump to specific page
    --page-size N  - Set transactions per page (default: 20)

Interactive mode (when available):
    j/k or ↑/↓     - Scroll up/down one transaction
    n/p            - Next/Previous page
    q              - Quit
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional

# Rich imports for beautiful terminal output
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from rich import box
from rich.console import Group

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_connection

class ScrollableTransactionViewer:
    """Scrollable transaction viewer with page-based navigation"""

    def __init__(self, org_id: int = 1, page_size: int = 20):
        self.org_id = org_id
        self.console = Console()
        self.page_size = page_size
        self.current_page = 1
        self.transactions = []
        self.total_pages = 0

    def get_all_transactions(self) -> List[Dict[str, Any]]:
        """Get all transactions for display"""
        with get_connection() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT id, transaction_date, transaction_type, amount,
                       description, account_number, bank_reference
                FROM transactions
                WHERE org_id = %s
                ORDER BY transaction_date DESC, id DESC
            """, (self.org_id,))

            columns = [desc[0] for desc in cursor.description]
            transactions = []

            for row in cursor.fetchall():
                tx = dict(zip(columns, row))
                transactions.append(tx)

            return transactions

    def create_transaction_table(self, start_idx: int, count: int) -> Table:
        """Create transaction table for specified range"""
        # Create main table
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=3, justify="right")
        table.add_column("Date", style="cyan", width=10)
        table.add_column("Type", style="yellow", width=6)
        table.add_column("Amount", style="green", width=12, justify="right")
        table.add_column("Description", style="white", min_width=50, max_width=70)
        table.add_column("Reference", style="blue", width=15)

        # Add transactions for this range
        end_idx = min(start_idx + count, len(self.transactions))

        for i in range(start_idx, end_idx):
            tx = self.transactions[i]

            # Format amount with color coding
            amount = tx['amount']
            if amount >= 0:
                amount_str = f"[green]+${amount:,.2f}[/green]"
            else:
                amount_str = f"[red]-${abs(amount):,.2f}[/red]"

            desc = tx['description'] or 'N/A'

            reference = tx['bank_reference'] or 'N/A'
            if len(reference) > 17:
                reference = reference[:14] + "..."

            # Alternate row colors
            row_style = "on grey11" if (i - start_idx) % 2 == 0 else None

            table.add_row(
                str(i + 1),
                str(tx['transaction_date']),
                tx['transaction_type'],
                amount_str,
                desc,
                reference,
                style=row_style
            )

        return table

    def create_page_display(self, page_num: int) -> Panel:
        """Create display for specific page"""
        # Calculate page boundaries
        start_idx = (page_num - 1) * self.page_size

        # Header with page info
        header = Text()
        header.append("🏦 SCROLLABLE TRANSACTION VIEWER", style="bold bright_white")
        header.append(f"  -  Page {page_num} of {self.total_pages}", style="bold yellow")

        # Summary info
        total_tx = len(self.transactions)
        current_range = f"{start_idx + 1}-{min(start_idx + self.page_size, total_tx)}"

        summary = Text()
        summary.append("Showing transactions ", style="dim")
        summary.append(current_range, style="bold cyan")
        summary.append(" of ", style="dim")
        summary.append(str(total_tx), style="bold cyan")

        # Main table
        table = self.create_transaction_table(start_idx, self.page_size)

        # Navigation info
        nav_info = Text()
        nav_info.append("Navigation: ", style="dim")
        if page_num > 1:
            nav_info.append("Previous: ", style="dim")
            nav_info.append(f"--page {page_num - 1}", style="bold green")
            nav_info.append("  ", style="dim")
        if page_num < self.total_pages:
            nav_info.append("Next: ", style="dim")
            nav_info.append(f"--page {page_num + 1}", style="bold green")

        # Combine everything
        content = Group(
            Align.center(header),
            "",
            Align.center(summary),
            "",
            table,
            "",
            Align.center(nav_info)
        )

        return Panel(
            content,
            style="bold bright_blue",
            box=box.DOUBLE,
            padding=(1, 2)
        )

    def show_full_statement(self):
        """Show the entire statement (all transactions on one screen)"""
        # Header
        header = Text()
        header.append("🏦 COMPLETE TRANSACTION STATEMENT", style="bold bright_white")

        # Summary
        total_tx = len(self.transactions)
        total_amount = sum(tx['amount'] for tx in self.transactions)

        summary_table = Table(box=box.MINIMAL, show_header=False)
        summary_table.add_column("Metric", style="cyan", width=20)
        summary_table.add_column("Value", style="bold green")

        summary_table.add_row("Total Transactions", f"{total_tx:,}")
        summary_table.add_row("Total Amount", f"${total_amount:,.2f}")
        if self.transactions:
            date_range = f"{self.transactions[-1]['transaction_date']} to {self.transactions[0]['transaction_date']}"
            summary_table.add_row("Date Range", date_range)

        # Full transaction table
        full_table = self.create_transaction_table(0, len(self.transactions))

        # Combine everything
        content = Group(
            Align.center(header),
            "",
            Panel(summary_table, title="Summary", border_style="green"),
            "",
            full_table
        )

        return Panel(
            content,
            style="bold bright_blue",
            box=box.DOUBLE,
            padding=(1, 2)
        )

    def run(self, page: Optional[int] = None, show_all: bool = False):
        """Run the viewer"""
        try:
            # Load transactions
            self.console.print("Loading transactions...", style="yellow")
            self.transactions = self.get_all_transactions()

            if not self.transactions:
                self.console.print("❌ No transactions found", style="bold red")
                return

            # Calculate total pages
            self.total_pages = (len(self.transactions) + self.page_size - 1) // self.page_size

            if show_all:
                # Show complete statement
                self.console.clear()
                display = self.show_full_statement()
                self.console.print(display)
            else:
                # Show specific page
                if page:
                    self.current_page = min(max(1, page), self.total_pages)

                self.console.clear()
                display = self.create_page_display(self.current_page)
                self.console.print(display)

                # Show usage info
                self.console.print(f"\n💡 [bold green]Usage:[/bold green]")
                self.console.print(f"   • Next page: [cyan]--page {min(self.current_page + 1, self.total_pages)}[/cyan]")
                if self.current_page > 1:
                    self.console.print(f"   • Previous page: [cyan]--page {self.current_page - 1}[/cyan]")
                self.console.print(f"   • Full statement: [cyan]--all[/cyan]")
                self.console.print(f"   • Custom page size: [cyan]--page-size N[/cyan]")

        except Exception as e:
            self.console.print(f"❌ Error: {str(e)}", style="bold red")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Scrollable Transaction Viewer')
    parser.add_argument('--page', type=int, default=1, help='Page number to display (default: 1)')
    parser.add_argument('--page-size', type=int, default=20, help='Transactions per page (default: 20)')
    parser.add_argument('--all', action='store_true', help='Show all transactions on one screen')

    args = parser.parse_args()

    viewer = ScrollableTransactionViewer(org_id=1, page_size=args.page_size)
    viewer.run(page=args.page, show_all=args.all)

if __name__ == "__main__":
    main()