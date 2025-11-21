# Data Cleanup Tool Guide

## Overview

The cleanup tool (`scripts/cleanup_data.py`) safely removes old transaction data that contains balance entries and optionally re-imports with the fixed parser.

## Usage

### Basic Commands

```bash
# Always activate virtual environment first
source venv/bin/activate

# Show what would be deleted (safe preview)
PYTHONPATH=. python3 scripts/cleanup_data.py --dry-run

# Create backup and delete old data
PYTHONPATH=. python3 scripts/cleanup_data.py --backup

# Delete and re-import in one step
PYTHONPATH=. python3 scripts/cleanup_data.py --backup --reimport /path/to/pdf

# Force deletion without confirmation
PYTHONPATH=. python3 scripts/cleanup_data.py --force
```

### Command Options

| Option | Description |
|--------|-------------|
| `--batch-id ID` | Delete specific import batch (default: 1) |
| `--dry-run` | Preview what would be deleted without doing it |
| `--backup` | Create SQL backup file before deletion |
| `--reimport PATH` | Re-import PDF file after cleanup |
| `--force` | Skip confirmation prompts |

## Step-by-Step Process

### 1. Preview the Cleanup (Recommended First Step)
```bash
source venv/bin/activate
PYTHONPATH=. python3 scripts/cleanup_data.py --dry-run
```

**This shows you:**
- Current transaction count and totals
- Problematic large transactions (balance entries)
- What would be deleted

### 2. Create Backup and Clean Data
```bash
PYTHONPATH=. python3 scripts/cleanup_data.py --backup
```

**This will:**
- Show current data summary
- Ask for confirmation
- Create backup SQL file
- Delete old transactions, account info, and batch records

### 3. Re-import with Fixed Parser
```bash
PYTHONPATH=. python3 scripts/cleanup_data.py --backup --reimport /mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf
```

**This does steps 2 + imports clean data in one command**

## What Gets Cleaned Up

The tool removes all data associated with an import batch:
- ✅ **Transactions** - All 55 transaction records (including 6 balance entries)
- ✅ **Account Info** - Bank account metadata
- ✅ **Duplicate Flags** - Any duplicate detection records
- ✅ **Import Batch** - The batch tracking record

## Safety Features

### 1. Dry Run Mode
Always preview changes before making them:
```bash
--dry-run  # Shows what would be deleted without doing it
```

### 2. Backup Creation
Automatically creates SQL backup file:
```bash
--backup  # Creates: transaction_backup_1_YYYYMMDD_HHMMSS.sql
```

### 3. Confirmation Prompts
Requires explicit confirmation unless `--force` is used:
```
⚠️  WARNING: This will permanently delete all data for batch 1
Continue? (type 'yes' to confirm):
```

### 4. Error Handling
- Validates file paths before import
- Handles database transaction rollbacks
- Shows detailed error messages

## Expected Results

### Before Cleanup
```
Total Transactions: 55
Total Amount: $519,847.18
Max Amount: $82,193.81  (balance entry)
```

### After Cleanup + Re-import
```
Total Transactions: 48
Total Amount: $21,810.13
Max Amount: $2,900.00   (actual transaction)
```

## Sample Output

```bash
$ PYTHONPATH=. python3 scripts/cleanup_data.py --dry-run

🧹 TRANSACTION DATA CLEANUP TOOL
============================================================
📊 CURRENT DATA SUMMARY (Batch 1)
============================================================
Total Transactions: 55
Total Amount: $519,847.18
Date Range: 2025-05-22 to 2026-07-31
Amount Range: $3.95 to $82,193.81

⚠️  PROBLEMATIC LARGE TRANSACTIONS (>$50k - likely balance entries):
   1. 2025-05-30 | $ 82,193.81 | 06/10
   2. 2025-05-23 | $ 81,559.51 | 06/03
   3. 2025-05-27 | $ 81,266.19 | 06/05
   ...

🔍 DRY RUN - Would delete the following:
  - 55 transactions
  - 1 account info records
  - 0 duplicate flag records
  - 1 import batch record
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'mysql'"
```bash
# Make sure virtual environment is activated
source venv/bin/activate
```

### "File not found" error
```bash
# Check file path is correct
ls -la /mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf
```

### Database connection issues
```bash
# Verify MySQL is running and credentials in .env are correct
mysql -u adamsl -p'Tinman@2' nonprofit_finance -e "SELECT 1"
```

## Recovery

If something goes wrong, you can restore from backup:
```bash
# Restore from backup file
mysql -u adamsl -p'Tinman@2' nonprofit_finance < transaction_backup_1_20250929_143000.sql
```

## Complete Workflow Example

```bash
# 1. Activate environment
source venv/bin/activate

# 2. Preview cleanup
PYTHONPATH=. python3 scripts/cleanup_data.py --dry-run

# 3. Clean and re-import in one step
PYTHONPATH=. python3 scripts/cleanup_data.py --backup --reimport /mnt/c/Users/NewUser/Downloads/fifth_third_personal_june.pdf

# 4. Verify results
PYTHONPATH=. python3 scripts/view_transactions.py --summary-only
```

## Summary

The cleanup tool provides a safe, comprehensive way to:
✅ Remove incorrect balance entries from your transaction data
✅ Create backups for safety
✅ Re-import with the fixed parser
✅ Verify results with detailed reporting

This ensures your financial data is accurate and ready for analysis.