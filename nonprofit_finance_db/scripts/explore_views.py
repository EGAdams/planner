#!/usr/bin/env python3
"""
Quick explorer for database views

Usage:
    python scripts/explore_views.py [view_name]

Shows available views and sample data
"""

import sys
import argparse
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db import get_connection

def list_available_views():
    """List all available views in the database"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES LIKE 'vw_%'")
        views = [row[0] for row in cursor.fetchall()]
        return sorted(views)

def describe_view(view_name: str):
    """Describe the structure of a view"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"DESCRIBE {view_name}")
        columns = cursor.fetchall()
        return columns

def sample_view_data(view_name: str, limit: int = 10):
    """Get sample data from a view"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM {view_name} LIMIT {limit}")
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return columns, rows

def main():
    parser = argparse.ArgumentParser(description='Explore database views')
    parser.add_argument('view_name', nargs='?', help='Name of view to explore')
    parser.add_argument('--limit', type=int, default=10, help='Number of sample rows to show')
    parser.add_argument('--list', action='store_true', help='List all available views')

    args = parser.parse_args()

    try:
        if args.list or not args.view_name:
            print("🔍 AVAILABLE DATABASE VIEWS")
            print("=" * 50)
            views = list_available_views()
            for i, view in enumerate(views, 1):
                print(f"{i:2}. {view}")

            if not args.view_name:
                print(f"\nUsage: python {sys.argv[0]} <view_name>")
                print(f"Example: python {sys.argv[0]} vw_daily_transaction_summary")
                return

        if args.view_name:
            if not args.view_name.startswith('vw_'):
                args.view_name = 'vw_' + args.view_name

            print(f"📊 VIEW: {args.view_name.upper()}")
            print("=" * 80)

            # Show structure
            columns = describe_view(args.view_name)
            print("\n🔧 STRUCTURE:")
            print("-" * 40)
            for col in columns:
                field, field_type, null, key, default, extra = col
                nullable = "NULL" if null == "YES" else "NOT NULL"
                key_info = f" ({key})" if key else ""
                print(f"  {field:<25} {field_type:<20} {nullable:<8}{key_info}")

            # Show sample data
            try:
                columns, rows = sample_view_data(args.view_name, args.limit)
                print(f"\n📋 SAMPLE DATA (showing up to {args.limit} rows):")
                print("-" * 80)

                if not rows:
                    print("  No data available in this view")
                    return

                # Print header
                header = " | ".join(f"{col[:15]:<15}" for col in columns)
                print(f"  {header}")
                print("  " + "-" * len(header))

                # Print rows
                for row in rows:
                    row_str = " | ".join(f"{str(val)[:15]:<15}" if val is not None else f"{'NULL':<15}" for val in row)
                    print(f"  {row_str}")

                print(f"\n💡 Total rows shown: {len(rows)}")

            except Exception as e:
                print(f"\n❌ Error fetching sample data: {str(e)}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())