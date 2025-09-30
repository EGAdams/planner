#!/usr/bin/env python3
"""
Stable Transaction Viewer - No Flickering
Uses simple terminal output with manual screen clearing for stable display

Usage:
    python scripts/stable_viewer.py

Controls:
    j/k or ↑/↓     - Scroll up/down one line
    u/d            - Scroll up/down 5 lines
    g/G            - Go to top/bottom
    n/p            - Next/Previous page (20 lines)
    q              - Quit
    h              - Help
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Rich imports for beautiful terminal output (no Live display)
from rich.console import Console
from rich.table import Table
from rich.text import Text
from rich.panel import Panel
from rich.align import Align
from rich import box

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_connection

class StableTransactionViewer:
    """Stable transaction viewer with no flickering"""

    def __init__(self, org_id: int = 1):
        self.org_id = org_id
        self.console = Console()
        self.scroll_offset = 0
        self.transactions = []
        self.lines_per_screen = 15  # Conservative for stability

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

    def create_transaction_lines(self) -> List[str]:
        """Create formatted transaction lines (plain text for stability)"""
        lines = []

        # Header
        lines.append("=" * 100)
        lines.append("🏦 BANK STATEMENT VIEWER")
        lines.append("=" * 100)
        lines.append("")

        # Summary
        total_tx = len(self.transactions)
        total_amount = sum(tx['amount'] for tx in self.transactions)
        lines.append(f"📊 Summary: {total_tx} transactions, Total: ${total_amount:,.2f}")
        lines.append("")

        # Table header
        lines.append(f"{'#':<4} {'Date':<12} {'Type':<8} {'Amount':<15} {'Description':<50}")
        lines.append("-" * 100)

        # Transaction lines
        for i, tx in enumerate(self.transactions):
            amount = tx['amount']
            amount_str = f"${amount:,.2f}"
            if amount >= 0:
                amount_str = f"+{amount_str}"

            desc = tx['description'] or 'N/A'
            if len(desc) > 47:
                desc = desc[:44] + "..."

            line = f"{i+1:<4} {tx['transaction_date']:<12} {tx['transaction_type']:<8} {amount_str:<15} {desc:<50}"
            lines.append(line)

        lines.append("")
        lines.append("-" * 100)
        lines.append(f"📍 Line {self.scroll_offset + 1}-{min(self.scroll_offset + self.lines_per_screen, len(lines))} of {len(lines)}")
        lines.append("Controls: j/k=scroll, u/d=5 lines, g/G=top/bottom, n/p=page, q=quit, h=help")

        return lines

    def display_current_view(self):
        """Display current view without flickering"""
        lines = self.create_transaction_lines()

        # Calculate what to show
        start_line = max(0, self.scroll_offset)
        end_line = min(len(lines), start_line + self.lines_per_screen)

        # Clear screen once
        os.system('clear' if os.name == 'posix' else 'cls')

        # Print visible lines
        for i in range(start_line, end_line):
            print(lines[i])

        # Print navigation at bottom
        print(f"\n📍 Viewing lines {start_line + 1}-{end_line} of {len(lines)}")
        print("j/k=↑↓ | u/d=±5 | g/G=top/bottom | n/p=page | q=quit | h=help")

    def show_help(self):
        """Show help screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
        help_text = """
🏦 STABLE TRANSACTION VIEWER - HELP

NAVIGATION CONTROLS:
  j or ↓         Scroll down one line
  k or ↑         Scroll up one line
  u              Scroll up 5 lines
  d              Scroll down 5 lines
  n              Next page (down 15 lines)
  p              Previous page (up 15 lines)
  g              Go to top
  G              Go to bottom
  q              Quit viewer
  h              Show this help

FEATURES:
  • No flickering or blinking
  • Stable terminal display
  • Full statement scrolling
  • 48 total transactions
  • Date range: 2025-05-22 to 2025-06-20
  • Total amount: $21,810.13

Press any key to return to statement view...
"""
        print(help_text)

    def get_single_char(self):
        """Get single character input (cross-platform)"""
        try:
            # Try Unix-style input
            import termios, tty
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                char = sys.stdin.read(1)
                # Handle escape sequences
                if char == '\x1b':
                    char += sys.stdin.read(2)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return char
        except:
            # Fallback to input() for Windows/sandbox
            return input("Enter command (j/k/u/d/n/p/g/G/q/h): ").strip().lower()

    def handle_input(self, char: str) -> bool:
        """Handle user input. Returns False to quit."""
        max_offset = max(0, len(self.create_transaction_lines()) - self.lines_per_screen)

        if char in ['q', 'Q']:
            return False
        elif char in ['j', '\x1b[B']:  # j or down arrow
            self.scroll_offset = min(max_offset, self.scroll_offset + 1)
        elif char in ['k', '\x1b[A']:  # k or up arrow
            self.scroll_offset = max(0, self.scroll_offset - 1)
        elif char in ['d', 'D']:  # down 5 lines
            self.scroll_offset = min(max_offset, self.scroll_offset + 5)
        elif char in ['u', 'U']:  # up 5 lines
            self.scroll_offset = max(0, self.scroll_offset - 5)
        elif char in ['n', 'N']:  # next page
            self.scroll_offset = min(max_offset, self.scroll_offset + self.lines_per_screen)
        elif char in ['p', 'P']:  # previous page
            self.scroll_offset = max(0, self.scroll_offset - self.lines_per_screen)
        elif char in ['g']:  # go to top
            self.scroll_offset = 0
        elif char in ['G']:  # go to bottom
            self.scroll_offset = max_offset
        elif char in ['h', 'H']:  # help
            self.show_help()
            self.get_single_char()  # Wait for keypress

        return True

    def run(self):
        """Run the stable viewer"""
        try:
            # Load transactions
            print("Loading transactions...")
            self.transactions = self.get_all_transactions()

            if not self.transactions:
                print("❌ No transactions found")
                return

            print(f"✅ Loaded {len(self.transactions)} transactions")
            print("Starting viewer... (press 'h' for help)")

            # Main loop
            while True:
                self.display_current_view()

                try:
                    char = self.get_single_char()
                    if not self.handle_input(char):
                        break
                except KeyboardInterrupt:
                    break

        except Exception as e:
            print(f"❌ Error: {str(e)}")
        finally:
            os.system('clear' if os.name == 'posix' else 'cls')
            print("👋 Thanks for using the stable transaction viewer!")

def main():
    """Main entry point"""
    viewer = StableTransactionViewer(org_id=1)
    viewer.run()

if __name__ == "__main__":
    main()