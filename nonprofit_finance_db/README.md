# Nonprofit Finance Database - Bank Statement Integration

A comprehensive bank statement parsing and integration system for nonprofit organizations with advanced duplicate detection, data validation, and automated categorization.

## Features

### 🏦 Bank Statement Parsing
- **Multi-format support**: CSV, PDF, and OFX file formats
- **Intelligent header mapping**: Automatically detects and maps various bank CSV formats
- **Data standardization**: Converts all transaction data to consistent format
- **Advanced CSV parsing**: Handles separate debit/credit columns and various date formats

### 🔍 Duplicate Detection
- **Multiple algorithms**: Exact matching, fuzzy matching, and composite scoring
- **Configurable thresholds**: Customizable confidence levels for different match types
- **Smart comparison**: Date tolerance, amount matching, and description similarity
- **Detailed reporting**: Comprehensive duplicate detection reports with confidence scores

### ✅ Data Validation & Processing
- **Transaction validation**: Required field checks, data type validation, and range validation
- **File validation**: File size, format, and accessibility checks
- **Auto-categorization**: Rule-based transaction categorization
- **Data cleaning**: Description enhancement and merchant name standardization

### 📊 Import Pipeline
- **Batch processing**: Handle large files with progress tracking
- **Error handling**: Comprehensive error logging and recovery
- **Import tracking**: Complete audit trail of all import operations
- **Configurable processing**: Customizable pipeline settings

### 🖥️ Command Line Interface
- **Rich UI**: Beautiful terminal interface with progress bars and tables
- **Multiple commands**: Import files, validate data, view history, and retry failed imports
- **Flexible options**: Dry-run mode, auto-processing, and output formatting
- **Batch operations**: Import entire directories with pattern matching

### 📝 Comprehensive Logging
- **Structured logging**: JSON-formatted logs with structured data
- **Multiple levels**: Configurable log levels and handlers
- **Performance tracking**: Function execution time monitoring
- **Import auditing**: Detailed logging of all import operations

### 🧪 Testing Suite
- **Unit tests**: Comprehensive test coverage for all components
- **Sample data**: Realistic bank statement samples for testing
- **Mock data**: Test fixtures for various scenarios including duplicates
- **Test automation**: Easy-to-run test suite with coverage reporting

## Installation

### Prerequisites
- Python 3.8 or higher
- MySQL 5.7 or higher
- Virtual environment (recommended)

### Setup

1. **Clone and navigate to the project:**
   ```bash
   cd /home/adamsl/planner/nonprofit_finance_db
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

5. **Initialize database:**
   ```bash
   python scripts/init_db.py
   ```

## WSL2 Access Configuration (Windows Users)

**IMPORTANT**: If you're running this application in WSL2 on Windows, you cannot access the web interface using `localhost` from your Windows browser. You must use the WSL2 IP address.

### Quick Access Method

1. **Get your WSL2 IP address:**
   ```bash
   hostname -I | awk '{print $1}'
   ```
   Example output: `172.30.171.179`

2. **Access from Windows browser:**
   ```
   http://[YOUR_WSL2_IP]:8080
   ```
   Example: `http://172.30.171.179:8080`

3. **Verify server is accessible:**
   ```bash
   curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" http://$(hostname -I | awk '{print $1}'):8080/
   ```

### Permanent localhost Solution (Optional)

To make `localhost:8080` work from Windows, add port forwarding in **Windows PowerShell (Administrator)**:

```powershell
# Get WSL2 IP first (run in WSL2 terminal)
# Example: 172.30.171.179

# Add port forwarding (run in Windows PowerShell as Admin)
netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0 connectport=8080 connectaddress=172.30.171.179
```

**Note**: WSL2 IP addresses can change after restarting WSL2. If `localhost` stops working, you'll need to:
1. Get the new WSL2 IP: `hostname -I | awk '{print $1}'`
2. Delete old port forward: `netsh interface portproxy delete v4tov4 listenport=8080 listenaddress=0.0.0.0`
3. Add new port forward with updated IP

**View all port forwards:**
```powershell
netsh interface portproxy show all
```

### Starting the Web Server

```bash
# From the nonprofit_finance_db directory
source venv/bin/activate
export NON_PROFIT_PASSWORD=tinman  # Or your MySQL password
python api_server.py
```

Server will be available at:
- Main App: `http://[WSL2_IP]:8080/`
- API Documentation: `http://[WSL2_IP]:8080/docs`
- Category Picker: `http://[WSL2_IP]:8080/ui`

## Configuration

### Environment Variables

Create a `.env` file with the following configuration:

```env
# Database Configuration
DB_HOST=127.0.0.1
DB_PORT=3306
NON_PROFIT_USER=your_username
NON_PROFIT_PASSWORD=your_password
NON_PROFIT_DB_NAME=nonprofit_finance
POOL_SIZE=5

# Logging Configuration
LOG_LEVEL=INFO
ENABLE_STRUCTURED_LOGGING=true
ENABLE_CONSOLE_LOGGING=true

# Pipeline Configuration
AUTO_PROCESS_DUPLICATES=true
DUPLICATE_CONFIDENCE_THRESHOLD=0.95
MAX_FILE_SIZE=52428800
```

## Usage

### Command Line Interface

The main CLI tool provides several commands for managing bank statement imports:

#### Import a single file
```bash
python scripts/import_statements.py import-file --org-id 1 path/to/statement.csv
```

#### Import all files from a directory
```bash
python scripts/import_statements.py import-directory --org-id 1 --pattern "*.csv" path/to/statements/
```

#### Validate a file without importing
```bash
python scripts/import_statements.py validate --org-id 1 path/to/statement.csv
```

#### View import history
```bash
python scripts/import_statements.py history --org-id 1 --limit 20
```

#### Retry a failed import
```bash
python scripts/import_statements.py retry --org-id 1 batch_id
```

### Programmatic Usage

```python
from ingestion.pipeline import IngestionPipeline

# Initialize pipeline
pipeline = IngestionPipeline(org_id=1)

# Import a file
result = pipeline.ingest_file('path/to/statement.csv', auto_process=True)

if result['success']:
    print(f"Imported {result['successful_imports']} transactions")
    print(f"Found {result['duplicate_count']} duplicates")
else:
    print("Import failed:", result['validation_errors'])
```

## Architecture

### Project Structure
```
nonprofit_finance_db/
├── app/                  # Core application code
│   ├── models/           # Data models
│   ├── repositories/     # Database repositories
│   ├── db/               # Database configuration
│   └── logging_config.py # Logging setup
├── parsers/              # Bank statement parsers
│   ├── base_parser.py    # Base parser interface
│   └── csv_parser.py     # CSV implementation
├── detection/            # Duplicate detection
│   ├── duplicate_detector.py
│   └── matching_algorithms.py
├── ingestion/           # Data ingestion pipeline
│   ├── pipeline.py      # Main pipeline
│   ├── validators.py    # Data validation
│   └── processors.py    # Data processing
├── tests/               # Test suite
│   ├── sample_data/     # Test data
│   └── test_*.py        # Test files
├── scripts/             # CLI and utility scripts
└── logs/               # Application logs
```

### Data Models

#### Transaction
- Core transaction record with all financial data
- Links to organization and import batch
- Includes raw data for audit trail

#### ImportBatch
- Tracks each import operation
- Records success/failure statistics
- Maintains processing metadata

#### DuplicateFlag
- Records potential duplicate transactions
- Includes confidence scores and match criteria
- Supports manual review workflow

## Testing

### Run All Tests
```bash
python tests/run_tests.py all
```

### Run Specific Test Categories
```bash
python tests/run_tests.py parsers
python tests/run_tests.py detection
python tests/run_tests.py ingestion
```

### Run with Coverage
```bash
python tests/run_tests.py all --coverage
```

## Bank Statement Formats

### Supported CSV Formats

The system automatically detects and handles various CSV formats:

#### Standard Format
```csv
Date,Description,Amount,Balance
2024-01-01,DONATION - JOHN SMITH,250.00,5250.00
2024-01-02,OFFICE SUPPLIES,-45.67,5204.33
```

#### Separate Debit/Credit Columns
```csv
Date,Description,Debit,Credit,Balance
2024-01-01,DONATION - JOHN SMITH,,250.00,5250.00
2024-01-02,OFFICE SUPPLIES,45.67,,5204.33
```

#### Bank-Specific Variations
- Different date formats (MM/DD/YYYY, DD/MM/YYYY, etc.)
- Various column names (Transaction Date, Trans Date, etc.)
- Different amount representations (parentheses for negatives)

### Adding New Formats

To add support for PDF or OFX formats:

1. Create new parser in `parsers/` directory
2. Implement `BaseParser` interface
3. Register parser in `IngestionPipeline`
4. Add tests in `tests/test_parsers.py`

## Duplicate Detection

### Algorithm Types

#### Exact Matching
- Perfect matches on date, amount, and description
- Configurable date tolerance
- Best for finding true duplicates

#### Fuzzy Matching
- String similarity on descriptions
- Amount tolerance for small differences
- Good for slight variations in bank formatting

#### Composite Matching
- Combines multiple algorithms with weighted scoring
- Provides confidence levels
- Balanced approach for most use cases

### Configuration

```python
from detection.duplicate_detector import DuplicateDetector

detector = DuplicateDetector(
    exact_threshold=1.0,
    fuzzy_threshold=0.85,
    use_composite=True
)
```

## Categorization Rules

### Default Categories

The system includes built-in categorization rules for common nonprofit transactions:

- **Office Supplies**: Office depot, staples, supplies
- **Travel**: Uber, taxi, hotel, airline
- **Meals**: Restaurant, food, cafe
- **Donations**: Donation, contribution, grant
- **Bank Fees**: Fee, charge, penalty
- **Utilities**: Electric, gas, water, internet

### Custom Rules

Add custom categorization rules in `TransactionProcessor`:

```python
def _load_custom_category_rules(self):
    return [
        {
            'category_id': 10,
            'keywords': ['zoom', 'webex', 'teams'],
            'transaction_type': 'DEBIT',
            'description': 'Video conferencing'
        }
    ]
```

## Error Handling

### Common Issues

#### File Format Issues
- **Unsupported format**: Ensure file has .csv, .pdf, or .ofx extension
- **Encoding problems**: Files should be UTF-8 encoded
- **Empty files**: Check file has content and proper headers

#### Data Validation Issues
- **Missing required fields**: Ensure date, amount, and description are present
- **Invalid dates**: Use standard date formats (YYYY-MM-DD preferred)
- **Invalid amounts**: Amounts should be numeric

#### Database Issues
- **Connection errors**: Check database configuration in .env
- **Permission errors**: Ensure database user has required permissions

### Troubleshooting

Enable verbose logging for detailed error information:

```bash
export LOG_LEVEL=DEBUG
python scripts/import_statements.py import-file --verbose --org-id 1 file.csv
```

Check logs in the `logs/` directory for detailed error traces.

## Performance

### Optimization Tips

1. **Large Files**: Use batch processing for files with >10,000 transactions
2. **Duplicate Detection**: Limit existing transaction lookback period
3. **Database**: Ensure proper indexing on transaction date and amount
4. **Memory**: Monitor memory usage with large CSV files

### Benchmarks

Typical performance on modern hardware:
- **CSV parsing**: ~1,000 transactions/second
- **Duplicate detection**: ~500 transaction pairs/second
- **Database insertion**: ~2,000 transactions/second

## Contributing

### Development Setup

1. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

2. Install pre-commit hooks:
   ```bash
   pre-commit install
   ```

3. Run tests before committing:
   ```bash
   python tests/run_tests.py all --coverage
   ```

### Code Style

- Follow PEP 8 style guidelines
- Use type hints for all function signatures
- Add docstrings for all public methods
- Maintain >80% test coverage

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Check the troubleshooting section above
- Review logs in the `logs/` directory
- Create detailed issue reports with sample data (anonymized)