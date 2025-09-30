#!/usr/bin/env python3
"""
Full-screen Transaction Viewer with Arrow Key Navigation

Usage:
    python scripts/fullscreen_viewer.py

Controls:
    ↑/↓ or j/k - Scroll up/down one line
    Page Up/Down - Scroll by page
    Home/End - Go to top/bottom
    q - Quit
"""

import sys
import os
import termios
import tty
from pathlib import Path
from typing import List, Dict, Any, Optional

# Rich imports for beautiful terminal output
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from rich import box
from rich.live import Live

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_connection

class FullScreenTransactionViewer:
    """Full-screen transaction viewer with arrow key navigation"""

    def __init__(self, org_id: int = 1):
        self.org_id = org_id
        self.console = Console()
        self.scroll_offset = 0
        self.transactions = []
        self.visible_lines = 0
        self.total_lines = 0

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

    def create_transaction_display(self) -> Table:
        """Create the full transaction table for display"""
        # Calculate visible area (leave space for header and controls)
        terminal_height = self.console.size.height
        self.visible_lines = max(1, terminal_height - 8)  # Reserve space for header/footer

        # Create main table
        table = Table(box=box.ROUNDED, show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("Date", style="cyan", width=12)
        table.add_column("Type", style="yellow", width=10)
        table.add_column("Amount", style="green", width=15, justify="right")
        table.add_column("Description", style="white", min_width=40)
        table.add_column("Reference", style="blue", width=15)

        # Calculate which transactions to show based on scroll
        start_idx = self.scroll_offset
        end_idx = min(start_idx + self.visible_lines, len(self.transactions))

        for i in range(start_idx, end_idx):
            tx = self.transactions[i]

            # Format amount with color coding
            amount = tx['amount']
            if amount >= 0:
                amount_str = f"[green]+${amount:,.2f}[/green]"
            else:
                amount_str = f"[red]-${abs(amount):,.2f}[/red]"

            desc = tx['description'] or 'N/A'
            if len(desc) > 50:
                desc = desc[:47] + "..."

            reference = tx['bank_reference'] or 'N/A'
            if len(reference) > 12:
                reference = reference[:9] + "..."

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

    def create_status_bar(self) -> Text:
        """Create status bar with navigation info"""
        total_tx = len(self.transactions)
        current_range = f"{self.scroll_offset + 1}-{min(self.scroll_offset + self.visible_lines, total_tx)}"

        status = Text()
        status.append("Transactions: ", style="dim")
        status.append(current_range, style="bold yellow")
        status.append(" of ", style="dim")
        status.append(str(total_tx), style="bold yellow")
        status.append("  |  ", style="dim")
        status.append("Controls: ", style="dim")
        status.append("↑↓", style="bold green")
        status.append("/", style="dim")
        status.append("jk", style="bold green")
        status.append(" scroll  ", style="dim")
        status.append("PgUp/PgDn", style="bold blue")
        status.append(" page  ", style="dim")
        status.append("Home/End", style="bold blue")
        status.append(" top/bottom  ", style="dim")
        status.append("q", style="bold red")
        status.append(" quit", style="dim")

        return status

    def create_full_display(self):
        """Create the complete display"""
        # Header
        header = Text("🏦 FULL-SCREEN TRANSACTION VIEWER", style="bold bright_white")

        # Main table
        table = self.create_transaction_display()

        # Status bar
        status = self.create_status_bar()

        # Create a renderable group
        from rich.console import Group
        content = Group(
            Align.center(header),
            "",
            table,
            "",
            Align.center(status)
        )

        return Panel(
            content,
            style="bold bright_blue",
            box=box.DOUBLE,
            padding=(1, 2)
        )

    def get_key(self):
        """Get a single keypress from stdin"""
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            key = sys.stdin.read(1)

            # Handle escape sequences (arrow keys, etc.)
            if key == '\x1b':  # ESC sequence
                key += sys.stdin.read(2)

        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

        return key

    def handle_navigation(self, key: str) -> bool:
        """Handle navigation keys. Returns False if should quit."""
        max_offset = max(0, len(self.transactions) - self.visible_lines)

        if key == 'q':
            return False
        elif key == '\x1b[A' or key == 'k':  # Up arrow or k
            self.scroll_offset = max(0, self.scroll_offset - 1)
        elif key == '\x1b[B' or key == 'j':  # Down arrow or j
            self.scroll_offset = min(max_offset, self.scroll_offset + 1)
        elif key == '\x1b[5~':  # Page Up
            self.scroll_offset = max(0, self.scroll_offset - self.visible_lines)
        elif key == '\x1b[6~':  # Page Down
            self.scroll_offset = min(max_offset, self.scroll_offset + self.visible_lines)
        elif key == '\x1b[H':  # Home
            self.scroll_offset = 0
        elif key == '\x1b[F':  # End
            self.scroll_offset = max_offset

        return True

    def run(self):
        """Run the full-screen viewer"""
        try:
            # Load transactions
            self.console.print("Loading transactions...", style="yellow")
            self.transactions = self.get_all_transactions()

            if not self.transactions:
                self.console.print("❌ No transactions found", style="bold red")
                return

            # Clear screen and enter full-screen mode
            self.console.clear()
            self.console.print("Use arrow keys or j/k to scroll, q to quit", style="dim")

            # Main loop with Live display
            with Live(self.create_full_display(), console=self.console, refresh_per_second=10) as live:
                while True:
                    # Update display
                    live.update(self.create_full_display())

                    # Get key input
                    key = self.get_key()

                    # Handle navigation
                    if not self.handle_navigation(key):
                        break

        except KeyboardInterrupt:
            pass
        finally:
            self.console.clear()
            self.console.print("👋 Thanks for using the transaction viewer!", style="green")

def main():
    """Main entry point"""
    viewer = FullScreenTransactionViewer(org_id=1)
    viewer.run()

if __name__ == "__main__":
    main()