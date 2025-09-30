#!/usr/bin/env python3
"""
Simple Scrolling Transaction Viewer
Ultra-stable version with basic scrolling commands

Usage:
    python scripts/simple_scroll.py [start_line]

Commands:
    python scripts/simple_scroll.py         # Start from top
    python scripts/simple_scroll.py 10      # Start from line 10
    python scripts/simple_scroll.py +5      # Scroll down 5 lines from current
    python scripts/simple_scroll.py -3      # Scroll up 3 lines from current
    python scripts/simple_scroll.py end     # Go to end
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_connection

class SimpleScrollViewer:
    """Ultra-simple, stable transaction viewer"""

    def __init__(self, org_id: int = 1):
        self.org_id = org_id
        self.transactions = []
        self.lines_per_view = 20

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

    def format_transaction_lines(self) -> List[str]:
        """Create all formatted lines"""
        lines = []

        # Header
        lines.append("🏦 COMPLETE BANK STATEMENT")
        lines.append("=" * 80)

        # Summary
        total_amount = sum(tx['amount'] for tx in self.transactions)
        lines.append(f"Total Transactions: {len(self.transactions)}")
        lines.append(f"Total Amount: ${total_amount:,.2f}")
        if self.transactions:
            lines.append(f"Date Range: {self.transactions[-1]['transaction_date']} to {self.transactions[0]['transaction_date']}")
        lines.append("")

        # Column headers
        lines.append(f"{'#':<4} {'Date':<12} {'Type':<8} {'Amount':<15} {'Description':<40}")
        lines.append("-" * 80)

        # Transaction data
        for i, tx in enumerate(self.transactions):
            amount = tx['amount']
            amount_str = f"${amount:,.2f}"
            if amount >= 0:
                amount_str = f"+{amount_str}"

            desc = tx['description'] or 'N/A'
            if len(desc) > 37:
                desc = desc[:34] + "..."

            line = f"{i+1:<4} {tx['transaction_date']:<12} {tx['transaction_type']:<8} {amount_str:<15} {desc:<40}"
            lines.append(line)

        lines.append("")
        lines.append("-" * 80)
        lines.append(f"End of statement ({len(self.transactions)} transactions)")

        return lines

    def show_lines(self, start_line: int = 0):
        """Show lines starting from start_line"""
        lines = self.format_transaction_lines()
        total_lines = len(lines)

        # Validate start_line
        start_line = max(0, min(start_line, total_lines - 1))
        end_line = min(start_line + self.lines_per_view, total_lines)

        # Clear and show
        os.system('clear' if os.name == 'posix' else 'cls')

        # Display lines
        for i in range(start_line, end_line):
            print(f"{i+1:3}: {lines[i]}")

        # Navigation info
        print(f"\n📍 Lines {start_line + 1}-{end_line} of {total_lines}")
        print(f"\nNavigation commands:")
        print(f"  Next 20: python3 scripts/simple_scroll.py {end_line}")
        if start_line > 0:
            print(f"  Prev 20: python3 scripts/simple_scroll.py {max(0, start_line - self.lines_per_view)}")
        print(f"  Jump to line: python3 scripts/simple_scroll.py <line_number>")
        print(f"  Go to end: python3 scripts/simple_scroll.py end")

    def run(self, start_line: int = 0):
        """Run the viewer"""
        try:
            print("Loading transactions...")
            self.transactions = self.get_all_transactions()

            if not self.transactions:
                print("❌ No transactions found")
                return

            self.show_lines(start_line)

        except Exception as e:
            print(f"❌ Error: {str(e)}")

def main():
    """Main entry point"""
    viewer = SimpleScrollViewer(org_id=1)

    # Parse command line argument
    start_line = 0
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == 'end':
            # Will be adjusted in show_lines to actual end
            start_line = 999999
        elif arg.startswith('+'):
            # Relative forward (not implemented in this simple version)
            start_line = int(arg[1:])
        elif arg.startswith('-'):
            # Relative backward (not implemented in this simple version)
            start_line = 0
        else:
            try:
                start_line = max(0, int(arg) - 1)  # Convert to 0-based
            except ValueError:
                print(f"Invalid line number: {arg}")
                return

    viewer.run(start_line)

if __name__ == "__main__":
    main()