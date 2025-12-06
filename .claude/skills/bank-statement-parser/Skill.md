---
name: bank-statement-parser
description: Expert in parsing bank statement PDFs using Docling, handling duplicate transaction detection, and validating against bank summaries. Use when working with bank statement imports, transaction parsing, or financial data validation.
---

# Bank Statement Parser Skill

## Overview

This skill helps parse and validate bank statement PDFs for the nonprofit finance database. It handles complex scenarios like duplicate check transactions and bank statement summary errors.

## Key Capabilities

1. **PDF Parsing with Deduplication**
   - Parses bank statement PDFs using Docling extractor
   - Automatically detects and removes duplicate check transactions
   - Handles checks that appear in both "Checks" section and "Withdrawals" section

2. **Smart Validation**
   - Validates transaction totals against bank statement summaries
   - Detects and handles bank statement errors (e.g., double-counted checks)
   - Validates ending balance with intelligent error detection

3. **Database Integration**
   - Imports parsed transactions into MySQL database
   - Migrates transactions to expenses table for UI display
   - Prevents duplicate imports

## Project Structure

```
nonprofit_finance_db/
├── parsers/
│   ├── pdf_parser.py              # Main PDF parser with deduplication
│   └── base_parser.py             # Base parser interface
├── pdf_extractor/
│   └── docling_pdf_extractor.py   # Docling-based extraction
├── scripts/
│   ├── parse_and_validate_pdf.py  # Parse + validate workflow
│   ├── wipe_and_reimport.py       # Clean reimport workflow
│   └── migrate_transactions_to_expenses.py
├── may_statement.pdf              # Test statement with duplicate check
└── june_statement.pdf             # Test statement without issues
```

## Common Issues and Solutions

### Issue 1: Duplicate Check Transactions

**Problem**: Bank statements list checks in two places:
- "Checks" section with just check number and amount
- "Withdrawals" section with payment details

This causes duplicate transactions if both are imported.

**Solution**: The `_deduplicate_check_transactions()` method in `parsers/pdf_parser.py:169`:
```python
def _deduplicate_check_transactions(self, transactions):
    # Groups transactions by date and amount
    # Removes generic "Check #XXXX" when detailed payment exists
    # Keeps the more descriptive withdrawal entry
```

**Example**: May statement Check #9341:
- Before: 2 transactions on 5/14 for $200 each
- After: 1 transaction "5/3 ONLINE PYMT TO FIRST BANK"

### Issue 2: Bank Statement Summary Errors

**Problem**: Banks may double-count checks in their summary totals:
- Checks section: $614.99 (includes Check #9341)
- Withdrawals section: $4506.60 (also includes Check #9341 as payment detail)
- Total: $5121.59 (inflated by $200)

**Solution**: Validation logic in `parse_and_validate_pdf.py:511-540`:
- Validates withdrawal totals (not affected by double-counting)
- Detects when ending balance mismatch equals check deduplication amount
- Warns but doesn't fail when bank statement has known errors

### Issue 3: Validation Hard Failures

**Principle**: Never allow silent failures. All validation errors must STOP the import immediately.

**Implementation**:
```python
# Hard fail on validation errors
if not passes or errors:
    print("✗ VALIDATION FAILED - STOPPING IMPORT")
    return False
```

## How to Use

### Parse and Validate a Single PDF

```bash
python3 scripts/parse_and_validate_pdf.py may_statement.pdf 1
```

Output includes:
- ✓/✗ Format validation
- ✓/✗ Account info extraction
- ✓/✗ Transaction parsing
- ✓/✗ Deposit totals validation
- ✓/✗ Withdrawal totals validation
- ⚠ Ending balance (with bank error detection)

### Wipe and Reimport All Statements

```bash
python3 scripts/wipe_and_reimport.py
```

This script:
1. Backs up current data
2. Clears transactions and expenses tables
3. Re-imports May and June PDFs
4. Migrates transactions to expenses
5. Verifies final data

### Migrate Transactions to Expenses

```bash
# Migrate all DEBIT transactions
python3 scripts/migrate_transactions_to_expenses.py

# Migrate specific date range
python3 scripts/migrate_transactions_to_expenses.py --start-date 2025-05-01 --end-date 2025-05-31

# Dry run to preview
python3 scripts/migrate_transactions_to_expenses.py --dry-run
```

## Validation Logic

### What Gets Validated

1. **Deposit Totals** (must match exactly)
   - Count and total amount

2. **Withdrawal Totals** (must match exactly)
   - Total amount only (count may vary due to deduplication)

3. **Ending Balance** (smart validation)
   - Checks if mismatch is due to bank error
   - Warns but doesn't fail for known bank issues

### What Doesn't Fail Validation

- Check count mismatches (due to deduplication)
- Ending balance mismatches that exactly match check deduplication amount
- These are treated as bank statement errors, not parsing errors

## Key Methods

### PDFParser._deduplicate_check_transactions()
**Location**: `parsers/pdf_parser.py:169`

Groups transactions by date/amount, identifies duplicate checks, removes generic check entries when detailed payment exists.

### parse_and_validate_pdf()
**Location**: `scripts/parse_and_validate_pdf.py:375`

Main workflow function that:
- Validates PDF format
- Extracts account info
- Parses transactions
- Validates against bank summary
- Syncs to database (only if validation passes)

### migrate_transactions_to_expenses_simple()
**Location**: `scripts/wipe_and_reimport.py:78`

Converts all negative-amount transactions from `transactions` table to `expenses` table with appropriate payment method detection.

## Database Schema

### transactions table
- Raw bank transactions (debits and credits)
- `amount`: negative for expenses, positive for income
- `transaction_type`: DEBIT or CREDIT
- `category_id`: NULL (auto-categorization disabled)

### expenses table
- Expense records for Daily Expense Categorizer UI
- `amount`: always positive
- `method`: CASH, CARD, BANK, or OTHER
- `category_id`: expense category

## Testing

### Test Case 1: May Statement (with duplicate)
```bash
python3 -c "from scripts.parse_and_validate_pdf import parse_and_validate_pdf; parse_and_validate_pdf('may_statement.pdf', 1)"
```

Expected:
- ✓ Deposits match
- ✓ Withdrawals match
- ⚠ Ending balance mismatch of $200 (bank error detected)
- ✓ Validation passes

### Test Case 2: June Statement (clean)
```bash
python3 -c "from scripts.parse_and_validate_pdf import parse_and_validate_pdf; parse_and_validate_pdf('june_statement.pdf', 1)"
```

Expected:
- ✓ All validations pass
- ✓ No warnings

### Test Case 3: May 14 Deduplication
```bash
python3 -c "
from app.db import get_connection
with get_connection() as conn:
    cursor = conn.cursor(dictionary=True)
    cursor.execute('SELECT * FROM expenses WHERE expense_date = \"2025-05-14\"')
    print(f'May 14 expenses: {len(cursor.fetchall())} (should be 1)')
"
```

## Troubleshooting

### "Docling not available" error
```bash
pip install docling
```

### "Foreign key constraint fails" on category_id
Check `scripts/parse_and_validate_pdf.py:306`:
```python
category_id = None  # Auto-categorization disabled
```

### Validation fails with "combined debits total mismatch"
This indicates a real parsing error (not a bank statement error). Check:
1. Are all transactions being parsed?
2. Is deduplication working correctly?
3. Are amounts being calculated correctly?

### Silent database failures
The system is designed to NEVER fail silently. If validation passes but database import fails, check:
1. MySQL connection
2. Table constraints
3. Data type mismatches

## Future Enhancements

1. **Pattern-based deduplication**: Extend beyond just checks to handle other duplicate patterns
2. **Multiple bank support**: Currently optimized for Fifth Third Bank format
3. **Gemini fallback improvements**: Better handling when Docling returns no results
4. **Category auto-assignment**: Re-enable with proper category validation

## Related Files

- Daily Expense Categorizer: `localhost:8080/office` (queries `expenses` table)
- Docling extractor: `/home/adamsl/planner/nonprofit_finance_db/pdf_extractor/`
- Migration scripts: `/home/adamsl/planner/nonprofit_finance_db/scripts/`

---

**Last Updated**: 2025-12-03
**Deduplication Feature**: ✓ Implemented
**Validation Mode**: Hard fail (no silent errors)
**Database**: MySQL (nonprofit_finance)
