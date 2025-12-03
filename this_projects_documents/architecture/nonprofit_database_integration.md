# Nonprofit Database Integration Project

## Project Overview
Bank statement parser module for nonprofit financial data management with duplicate detection and automated data ingestion.

## Core Features

### 1. Bank Statement Parser
**Purpose**: Extract and standardize financial transaction data from multiple bank statement formats

**Supported Formats**:
- CSV (Comma Separated Values)
- PDF (Portable Document Format)
- OFX (Open Financial Exchange)

**Data Extraction**:
- Transaction date
- Amount (debit/credit)
- Description/memo
- Transaction type
- Account information

### 2. Duplicate Detection System
**Detection Criteria**:
- Date matching (exact or within tolerance)
- Amount matching (exact)
- Description similarity (fuzzy matching)

**Workflow**:
- Compare incoming transactions against existing database records
- Flag potential duplicates for manual review
- Auto-skip confirmed duplicates
- Maintain duplicate detection metadata

### 3. Data Ingestion Pipeline
**Validation Steps**:
- Data format validation
- Required field verification
- Amount and date range checks
- Description sanitization

**Processing**:
- Categorize transactions (income, expense, transfer)
- Apply business rules and mappings
- Generate import reports and summaries
- Handle errors and rejected transactions

## Database Schema Requirements

### Core Tables
- `transactions` - Main transaction records with unique constraints
- `import_batches` - Track import sessions and metadata
- `duplicate_flags` - Store duplicate detection results
- `audit_trail` - Log all import activities and changes

### Key Constraints
- Unique transaction identification
- Foreign key relationships
- Data integrity validation
- Audit trail requirements

## Implementation Phases

### Phase 1: Core Parser (Current)
- CSV parser implementation
- Basic duplicate detection
- Database schema setup
- Simple validation rules

### Phase 2: Enhanced Detection
- Advanced duplicate detection algorithms
- Fuzzy string matching for descriptions
- Configurable matching criteria
- Manual review interface

### Phase 3: Multi-Format Support
- PDF statement parsing
- OFX format support
- Format auto-detection
- Error handling improvements

### Phase 4: Advanced Features
- Automated categorization
- Import scheduling
- Reporting dashboard
- API endpoints

## Technical Stack
- **Backend**: Python
- **Database**: MySQL
- **Parser Libraries**: pandas (CSV), PyPDF2 (PDF), ofxparse (OFX)
- **Duplicate Detection**: difflib, fuzzywuzzy
- **Web Interface**: Flask/FastAPI (future)

## File Structure
```
nonprofit_finance_db/
├── parsers/
│   ├── csv_parser.py
│   ├── pdf_parser.py
│   └── ofx_parser.py
├── detection/
│   ├── duplicate_detector.py
│   └── matching_algorithms.py
├── database/
│   ├── models.py
│   ├── schema.sql
│   └── migrations/
├── ingestion/
│   ├── pipeline.py
│   ├── validators.py
│   └── processors.py
└── tests/
    ├── test_parsers.py
    ├── test_detection.py
    └── sample_data/
```

## Success Metrics
- 99%+ duplicate detection accuracy
- Support for 3+ bank statement formats
- <5% false positive duplicate rate
- Automated processing of 95% of transactions
- Complete audit trail for all imports

## Next Steps
1. Set up database schema and models
2. Implement basic CSV parser
3. Create duplicate detection algorithm
4. Build validation and ingestion pipeline
5. Add error handling and logging
6. Create test suite with sample data

---

**Status**: Planning Complete - Ready for Implementation
**Priority**: High
**Estimated Timeline**: 2-3 weeks
**Last Updated**: September 26, 2025