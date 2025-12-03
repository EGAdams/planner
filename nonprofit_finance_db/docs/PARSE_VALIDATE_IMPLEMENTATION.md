# Parse and Validate PDF Implementation

## Overview
Implemented the "Parse and Validate PDF" menu item for the Finance Report → Process Bank Statements section of the Smart Menu. This feature allows users to parse bank PDF statements and validate them against the statement summary/totals section.

## Files Created

### 1. `/scripts/parse_and_validate_pdf.py`
**Purpose**: Core validation script that parses PDFs and verifies balances

**Key Features**:
- Validates PDF format before processing
- Extracts account information from PDF header/metadata
- Parses all transactions using Docling extractor (with Gemini fallback)
- Classifies transactions as: CHECK, WITHDRAWAL, or DEPOSIT
- Computes breakdown of transaction types (counts and totals)
- Validates against statement summary:
  - Transaction type counts match
  - Transaction type totals match (within $0.01 tolerance)
  - Beginning balance is correct
  - Ending balance calculation matches: `beginning + credits - debits = ending`
  - Net transaction amount balances correctly
- On successful validation, writes the parsed transactions to the MySQL `transactions`
  table, verifying existing rows for mismatches before inserting new data. Any
  mismatch halts the run and records details in `database_corrupt.md` for follow-up.

**Output**:
- Color-coded validation results (✓ for pass, ✗ for fail)
- Transaction type verification details
- Balance calculations
- Sample transaction list (first 10 + last 5)
- Pass/fail summary with specific error messages
- Database sync status plus directions to `database_corrupt.md` if a mismatch is found

**Usage**:
```bash
python3 nonprofit_finance_db/scripts/parse_and_validate_pdf.py /path/to/statement.pdf [org_id]
```

### 2. `/scripts/interactive_parse_validate.sh`
**Purpose**: Interactive wrapper for user-friendly PDF selection

**Key Features**:
- Searches common directories (Downloads, Documents, /tmp, current dir)
- Presents numbered menu of available PDFs
- Allows direct path entry if preferred
- Validates file exists before processing
- Calls the Python validation script
- Reports success/failure clearly

**Usage**:
```bash
bash /home/adamsl/planner/nonprofit_finance_db/scripts/interactive_parse_validate.sh
```

## Smart Menu Integration

Updated `/home/adamsl/planner/smart_menu/menu_configurations/config.json`:

```
Finance Report
  └─ Process Bank Statements
      ├─ Parse and Validate PDF ← NEW (interactive menu)
      ├─ Parse Receipts
      ├─ Put parsed data into database
      └─ Tests (existing)
```

The "Parse and Validate PDF" menu item now:
1. Opens an interactive shell interface
2. Searches for PDF files in common locations
3. Presents user with a numbered menu of available PDFs
4. Runs the validation script on the selected file
5. Displays detailed validation results in the terminal

## Validation Logic

The script validates against the latest PDF parsing implementation from `api_server.py` (Nov 24, 2024), which includes:

### Account Summary Extraction
- Beginning balance
- Ending balance
- Transaction type counts and totals:
  - Checks (count, total)
  - Withdrawals/Debits (count, total)
  - Deposits/Credits (count, total)

### Transaction Classification
1. Uses `bank_item_type` hint from parser if available (CHECK, WITHDRAWAL, DEPOSIT)
2. Falls back to description keywords if hint not present
3. Uses amount sign as final fallback (positive = deposit, negative = withdrawal)

### Balance Verification
```
Ending Balance = Beginning Balance + Credits - Checks - Withdrawals
```

**Tolerance**: Amounts compared within ±$0.01 to handle rounding

## What It Validates
✓ PDF is readable and valid
✓ Account information extracted
✓ Transaction count matches statement summary
✓ Transaction totals match statement summary
✓ All transaction types classified correctly
✓ Ending balance calculation is correct
✓ Beginning balance is recorded
✓ All individual transactions parsed completely

## Error Handling
- Clear error messages for missing files
- Specific validation failure messages (which check failed)
- Graceful handling of missing data
- Detailed logging for debugging

## Integration with Existing System
- Uses existing `PDFParser` from `parsers/pdf_parser.py`
- Follows same extraction pipeline as API endpoint
- Reuses transaction classification logic from `api_server.py`
- Compatible with both Docling and Gemini extraction methods

## Next Steps
If validation fails:
1. Review specific error messages (count mismatch, total mismatch, balance mismatch)
2. Check if PDF is a supported bank format
3. Run individual test suite for detailed debugging: `Tests → Test Docling Account Summary`
4. Use API endpoint `/api/parse-bank-pdf` for more detailed response data
