# Transaction Data Viewing Guide

## Overview

You now have multiple powerful ways to view and analyze your transaction data, from quick summaries to detailed interactive exploration.

## 🚀 Quick Start

### 1. Interactive Dashboard (Recommended)
```bash
# Activate virtual environment and run dashboard
source venv/bin/activate
PYTHONPATH=. python3 scripts/view_transactions.py
```

**Features:**
- 📊 Real-time summary statistics
- 🔍 Advanced filtering (date, amount, type, description search)
- 📄 Pagination through large datasets
- 📈 Sorting by any field
- 💾 Export to CSV/JSON
- 🎯 Interactive menu system

### 2. Quick Summary View
```bash
# Get instant overview without interactive mode
source venv/bin/activate
PYTHONPATH=. python3 scripts/view_transactions.py --summary-only
```

### 3. Direct Export
```bash
# Export all data to CSV
PYTHONPATH=. python3 scripts/view_transactions.py --export csv

# Export all data to JSON
PYTHONPATH=. python3 scripts/view_transactions.py --export json
```

## 📊 Database Views Explorer

### List All Available Views
```bash
source venv/bin/activate
PYTHONPATH=. python3 scripts/explore_views.py --list
```

### Explore Specific Views
```bash
# View transaction patterns
PYTHONPATH=. python3 scripts/explore_views.py transaction_patterns

# View daily summaries
PYTHONPATH=. python3 scripts/explore_views.py daily_transaction_summary

# View large transactions
PYTHONPATH=. python3 scripts/explore_views.py large_transactions
```

## 🗂️ Available Database Views

### Core Analysis Views
- **`vw_daily_transaction_summary`** - Daily breakdowns by type
- **`vw_weekly_transaction_summary`** - Weekly aggregations
- **`vw_monthly_transaction_summary`** - Monthly summaries (existing)
- **`vw_account_transaction_summary`** - Per-account statistics

### Pattern & Insights Views
- **`vw_transaction_patterns`** - Common transaction types and patterns
- **`vw_large_transactions`** - Transactions above statistical average
- **`vw_recent_transactions`** - Last 30 days of activity

### Import & Quality Views
- **`vw_import_performance`** - Import batch success rates and statistics
- **`vw_duplicate_analysis`** - Potential duplicate transaction analysis

### Balance Tracking Views
- **`vw_monthly_balance_progression`** - Account balance changes over time

## 🎯 Common Use Cases

### View Recent Activity
```bash
# Interactive dashboard with recent filter
python3 scripts/view_transactions.py
# Then: f -> 1 -> enter start date (e.g., 2025-06-01)
```

### Find Large Transactions
```bash
# View largest transactions using database view
python3 scripts/explore_views.py large_transactions
```

### Export Filtered Data
```bash
# Use interactive dashboard
python3 scripts/view_transactions.py
# Apply filters, then: e -> 1 (for CSV export)
```

### Analyze Transaction Patterns
```bash
# View common transaction types
python3 scripts/explore_views.py transaction_patterns
```

### Check Import Quality
```bash
# Review import batch performance
python3 scripts/explore_views.py import_performance
```

## 📋 Interactive Dashboard Controls

### Main Navigation
- **`n`** - Next page
- **`p`** - Previous page
- **`f`** - Apply filters
- **`s`** - Change sorting
- **`e`** - Export data
- **`r`** - Reset all filters/sorting
- **`q`** - Quit

### Filter Options
1. **Date range** - Filter by start/end dates
2. **Transaction type** - CREDIT, DEBIT, or TRANSFER
3. **Amount range** - Min/max amount filters
4. **Search description** - Text search in descriptions
5. **Account number** - Filter by specific account
6. **Clear all filters** - Reset all filters

### Sort Options
- Transaction date
- Amount
- Description
- Transaction type
- Ascending or descending order

## 📈 Sample Workflows

### Daily Review Workflow
1. Run `python3 scripts/view_transactions.py --summary-only` for quick overview
2. Open interactive dashboard for detailed review
3. Filter to recent transactions (last 7-30 days)
4. Export important data if needed

### Monthly Analysis Workflow
1. Use `explore_views.py monthly_transaction_summary` for high-level trends
2. Check `transaction_patterns` for spending behavior
3. Review `large_transactions` for significant activity
4. Export monthly data for external analysis

### Import Validation Workflow
1. Check `import_performance` view after each import
2. Review `duplicate_analysis` for data quality
3. Use interactive dashboard to spot-check specific transactions

## 🔧 Technical Details

### Virtual Environment
All scripts require the virtual environment to be activated:
```bash
source venv/bin/activate
```

### Database Views
- Views are automatically updated when underlying transaction data changes
- Views use optimized queries for better performance
- All views include org_id filtering for multi-tenant support

### Export Formats
- **CSV**: Compatible with Excel, Google Sheets, and other tools
- **JSON**: Suitable for programmatic processing and APIs

## 💡 Pro Tips

1. **Use summary mode first** - Get quick overview before diving into details
2. **Apply filters early** - Narrow down data before browsing large datasets
3. **Export filtered data** - Save specific subsets for external analysis
4. **Explore views regularly** - Database views provide pre-calculated insights
5. **Check import performance** - Monitor data quality after each import

## 🆘 Troubleshooting

### "ModuleNotFoundError: No module named 'mysql'"
Make sure virtual environment is activated:
```bash
source venv/bin/activate
```

### "Permission denied" errors
Make scripts executable:
```bash
chmod +x scripts/view_transactions.py
chmod +x scripts/explore_views.py
```

### Database connection issues
Verify database credentials in `.env` file and ensure MySQL is running.

## 📝 Summary

You now have comprehensive transaction data viewing capabilities:

✅ **Interactive CLI dashboard** with filtering, search, and export
✅ **15 database views** for pre-calculated insights
✅ **Export functionality** for external analysis
✅ **Quick summary tools** for daily reviews
✅ **Pattern analysis** for spending behavior insights

The system handles your current 55 transactions efficiently and will scale to handle thousands more as your data grows.