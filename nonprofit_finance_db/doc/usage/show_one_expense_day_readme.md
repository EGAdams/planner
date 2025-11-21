# Daily Expense Report Generator

## Overview
`show_one_expense_day.py` is a Python script that generates detailed daily expense reports from the nonprofit finance database.

## Features
- Prompts user for date in MM/DD/YYYY format
- Validates date format and handles invalid inputs
- Queries all expenses for the specified date
- Displays comprehensive expense information including:
  - Expense ID
  - Organization name
  - Category
  - Amount
  - Payment method
  - Paid by contact
  - Description
  - Receipt URL (if available)
- Calculates total expenses for the day
- Saves report to a text file with date-stamped filename
- Includes error handling for database connection issues

## Requirements
- Python 3.x
- mysql-connector-python
- Access to nonprofit_finance database
- Environment variables configured in `.env` file:
  - `DB_HOST`
  - `DB_PORT`
  - `NON_PROFIT_USER`
  - `NON_PROFIT_PASSWORD`
  - `NON_PROFIT_DB_NAME`

## Usage

### Running the Script
```bash
# Activate virtual environment
source venv/bin/activate

# Run the script
python3 show_one_expense_day.py
```

### Example Session
```
Daily Expense Report Generator
==================================================
Enter date in format MM/DD/YYYY: 09/10/2025

Fetching expenses for 09/10/2025...

================================================================================
                              DAILY EXPENSE REPORT
                                Date: 09/10/2025
================================================================================

Expense #1
--------------------------------------------------------------------------------
ID:                4
Organization:      GoodWorks Nonprofit
Category:          None
Amount:            $560.00
Payment Method:    BANK
Paid By:           None
Description:       Venue deposit for gala

================================================================================
Total Expenses:    $560.00
Number of Expenses: 1
================================================================================

Report saved to: expense_report_2025-09-10.txt
```

### Output File
The script generates a text file named `expense_report_YYYY-MM-DD.txt` in the current directory containing the formatted expense report.

## Error Handling

### Invalid Date Format
```
ERROR: Invalid date format. Please use MM/DD/YYYY format.
Example: 01/15/2024
```

### Database Connection Issues
```
ERROR: Database connection or query failed.
Details: [error message]

Please check:
1. Database connection settings in .env file
2. Database is running and accessible
3. Required environment variables are set
```

### No Expenses Found
The script will still generate a report indicating no expenses were found for the specified date.

## Testing

The script includes comprehensive unit tests in `tests/test_show_one_expense_day.py`:

```bash
# Run tests
source venv/bin/activate
python -m pytest tests/test_show_one_expense_day.py -v
```

### Test Coverage
- Date validation and format conversion
- Database query functionality
- Report formatting
- Filename generation
- Error handling

## Development Approach

This script was developed using **Test-Driven Development (TDD)** methodology:

1. **RED Phase**: Wrote failing tests first
2. **GREEN Phase**: Implemented minimal code to pass tests
3. **REFACTOR Phase**: Enhanced error handling and user experience

## Database Schema

The script queries the following tables:
- `expenses` - Primary expense data
- `categories` - Expense categories
- `organizations` - Organization information
- `contacts` - Contact information for "paid by" field

## Implementation Details

### Date Handling
- User input: MM/DD/YYYY format
- Database format: YYYY-MM-DD (MySQL DATE type)
- Automatic conversion between formats

### Query Design
- Uses LEFT JOIN to handle missing category/contact/organization data
- Returns 'N/A' for missing fields
- Orders results by expense ID

### Report Format
- 80-character wide formatted text
- Clear section separators
- Totals and summary at bottom
- Professional appearance suitable for printing

## Future Enhancements

Potential improvements:
- Date range support (from/to dates)
- Category filtering
- Organization filtering
- Export to CSV/PDF formats
- Email delivery option
- Scheduled automatic reports
