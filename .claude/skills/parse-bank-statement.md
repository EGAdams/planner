# Parse Bank Statement Skill

Parse and validate PDF bank statements, extracting transactions and verifying balances.

## What This Skill Does

This skill helps you:
1. Parse PDF bank statements (supports Fifth Third Bank format and similar)
2. Extract all transactions with dates, amounts, and descriptions
3. Extract account information (account number, type, bank name, statement period)
4. Validate transactions against the statement summary/totals
5. Verify that all balances match (checks, withdrawals, deposits, ending balance)

## How to Use

When the user provides a PDF bank statement or asks to parse/validate a statement:

### Step 1: Locate the PDF file
- Ask user for the PDF file path, or
- Search common locations: Downloads, Documents, current directory

### Step 2: Run the validation script
```bash
python3 scripts/parse_and_validate_pdf.py <pdf_file_path> [org_id]
```

Example:
```bash
python3 scripts/parse_and_validate_pdf.py /path/to/june_statement.pdf 1
```

### Step 3: Interpret the results

The script will output:
- ✓ **Validation Passed**: All totals match the statement summary
- ✗ **Validation Failed**: Shows which totals don't match and by how much

#### Success Output Example:
```
======================================================================
VALIDATION RESULTS
======================================================================

Transaction Type Verification:
  Expected vs Calculated:

  Checks:
    Total: ✓ Expected: $439.99, Calculated: $439.99

  Withdrawals:
    Total: ✓ Expected: $8991.13, Calculated: $8991.13

  Deposits:
    Total: ✓ Expected: $12594.00, Calculated: $12594.00

  Ending Balance:
    ✓ Expected: $83095.41, Calculated: $83095.41

======================================================================
✓ VALIDATION PASSED - All balances and counts match!
======================================================================
```

#### Failure Output Example:
```
======================================================================
✗ VALIDATION FAILED

Errors found:
  - withdrawals total mismatch
  - ending balance mismatch
======================================================================
```

## What Gets Validated

1. **Transaction Counts**: Number of checks, withdrawals, deposits
2. **Transaction Totals**: Dollar amounts for each transaction type
3. **Ending Balance**: Calculated vs. expected ending balance
4. **Balance Formula**: `Beginning Balance + Deposits - Checks - Withdrawals = Ending Balance`

## Supported Bank Formats

Currently supports:
- **Fifth Third Bank** statements (primary support)
- Banks with similar PDF table formats

The parser handles:
- Multi-page transaction tables
- Tables with continuation across pages
- Markdown-formatted PDF extractions
- Mixed transaction types (checks, debits, credits)

## Transaction Data Extracted

For each transaction:
- **Date**: Transaction date (YYYY-MM-DD format)
- **Amount**: Dollar amount (negative for debits, positive for credits)
- **Description**: Transaction description
- **Type**: CHECK, WITHDRAWAL, or DEPOSIT
- **Metadata**: Source file, extraction method, timestamp

## Common Issues & Solutions

### Issue: "No transactions found in PDF"
**Solution**: The PDF might not be in a supported format. Check if it has tables with Date/Amount/Description columns.

### Issue: "Validation failed - totals mismatch"
**Possible causes**:
1. Some transactions weren't extracted (check transaction count)
2. OCR errors in amount parsing
3. Unsupported statement format

**Debug steps**:
```bash
# Run the debug script to see table extraction details
python3 scripts/debug_pdf_tables.py <pdf_file_path>
```

### Issue: "Invalid or unreadable PDF format"
**Solution**: Ensure the PDF is not encrypted or password-protected.

## Integration with Database

After validation passes, transactions can be imported to the database using:
```bash
# Put parsed data into database (via Smart Menu)
Finance Report → Process Bank Statements → Put parsed data into database
```

## For Developers

### Key Files
- `/scripts/parse_and_validate_pdf.py` - Main validation script
- `/scripts/debug_pdf_tables.py` - Table extraction debugger
- `/pdf_extractor/docling_extractor.py` - PDF extraction engine
- `/parsers/pdf_parser.py` - Parser interface

### Recent Fixes (Dec 2024)
1. **Account summary extraction**: Fixed markdown table parsing that was combining count numbers with amounts
2. **Table continuation detection**: Added logic to carry forward sign hints for multi-page transaction tables

### Extending Support
To add support for new bank formats:
1. Test with `debug_pdf_tables.py` to see table structure
2. Update regex patterns in `docling_extractor.py` if needed
3. Add bank name detection in `extract_account_info()`

## Examples

### Example 1: Validate June statement
```bash
python3 scripts/parse_and_validate_pdf.py june_statement.pdf
```

### Example 2: Parse with specific org_id
```bash
python3 scripts/parse_and_validate_pdf.py may_statement.pdf 2
```

### Example 3: Debug table extraction
```bash
python3 scripts/debug_pdf_tables.py june_statement.pdf
```

## Success Criteria

The skill is successful when:
- All transaction totals match the statement summary (within $0.01 tolerance)
- All transaction counts match
- Ending balance calculation is correct
- User receives clear validation results

## Tips for Users

1. **Always validate first**: Run the validation script before importing to database
2. **Check the sample transactions**: Review the first 10 and last 5 transactions to ensure they look correct
3. **Use debug script**: If validation fails, run `debug_pdf_tables.py` to see what's being extracted
4. **Verify manually**: For important statements, spot-check a few random transactions against the PDF

## Related Skills

- **Parse Receipts**: For individual receipt parsing (separate skill)
- **Database Import**: For importing validated transactions to database
- **Financial Reports**: For generating reports from imported data
