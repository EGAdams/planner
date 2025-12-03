# Receipt Scanning & Parsing System Implementation

**Project:** Nonprofit Finance Database with Receipt Scanning Integration
**Date Requested:** November 14, 2025
**Requestor:** Development Team
**Status:** Awaiting Expert Planning & Code Generation

---

## EXECUTIVE SUMMARY

We need your expertise to design and implement a complete receipt scanning and parsing system for our nonprofit finance application. The system should:

1. Allow users to upload receipt images (JPG, PNG, WebP, PDF)
2. Parse receipt data using an AI vision model (Gemini 1.5 Flash recommended)
3. Extract structured data (merchant, date, items, totals, payment method)
4. Store parsed data in our existing MySQL database
5. Integrate with our expense categorizer UI for immediate categorization
6. Provide fallback mechanisms and error handling

**We need complete implementation instructions and source code in ONE markdown document.** Our engineering team will implement based on your specifications, creating all necessary directories and files.

---

## CURRENT SYSTEM ARCHITECTURE

### Technology Stack

**Backend:**
- **Framework:** FastAPI (async Python web framework)
- **Database:** MySQL 8.0.43 (running on localhost:3306, database name: `nonprofit_finance`)
- **PDF Processing:** Docling 2.0+ (AI-powered document understanding)
- **Data Validation:** Pydantic v2.7+ (type-safe schemas)
- **ORM Pattern:** Custom repository pattern (BaseRepository)
- **Connection Pooling:** MySQLConnectionPool from mysql-connector-python
- **Authentication:** Currently none (local trusted network, but needs to be considered for PII)

**Frontend:**
- **Framework:** Vanilla JavaScript (ES modules, no build step)
- **Styling:** TailwindCSS (CDN-loaded)
- **Components:** Custom Web Components (Shadow DOM for isolation)
- **Event System:** Global event bus (custom implementation in `js/event-bus.js`)

**Existing Services:**
- Ingestion pipeline for bank statement parsing (CSV + PDF)
- Duplicate detection system (using rapidfuzz)
- File upload handling system
- API server running on `http://localhost:8000`

### Directory Structure

```
/home/adamsl/planner/
├── nonprofit_finance_db/                 # Backend: Python FastAPI
│   ├── app/
│   │   ├── models/
│   │   │   ├── receipt_models.py          # ⭐ EXISTING: Receipt data models (see Models section)
│   │   │   └── expense.py                 # Expense model with receipt_url field
│   │   ├── repositories/
│   │   │   ├── base.py                    # BaseRepository pattern
│   │   │   └── expenses.py                # Expense data access methods
│   │   ├── db/
│   │   │   └── pool.py                    # MySQL connection pooling
│   │   └── config.py                      # Database config & environment variables
│   ├── ingestion/
│   │   └── pipeline.py                    # Existing bank statement ingestion pattern (reference)
│   ├── parsers/
│   │   ├── pdf_parser.py                  # Existing PDF parsing pattern (reference)
│   │   └── [NEW] receipt_parser.py        # ⭐ TO CREATE: AI receipt parsing engine
│   ├── pdf_extractor/
│   │   └── docling_extractor.py           # Docling-based PDF extraction (reference)
│   ├── uploads/                           # ⭐ TO CREATE: Receipt file storage
│   │   └── receipts/                      # ⭐ TO CREATE: Directory for receipt images
│   │       ├── 2025/11/                   # Year/month subdirectories
│   │       └── [receipt files]
│   ├── api_server.py                      # FastAPI application (add endpoints here)
│   └── requirements.txt                   # Python dependencies
│
├── office-assistant/                      # Frontend: Vanilla JS SPA
│   ├── index.html                         # Main SPA shell
│   ├── daily_expense_categorizer.html     # Expense categorizer (integration point)
│   ├── js/
│   │   ├── app.js
│   │   ├── event-bus.js                   # Global event system
│   │   └── components/
│   │       ├── category-picker.js         # Category selection component
│   │       └── [NEW] receipt-scanner.js   # ⭐ TO CREATE: Receipt scanner component
│   ├── upload-component/                  # TypeScript receipt scanner components
│   │   ├── scanner_parser.md              # ⭐ EXISTING: Implementation planning doc
│   │   └── [NEW] receipt-scanner.ts       # ⭐ TO CREATE: TypeScript component
│   └── css/
│       └── [CSS for receipt scanner UI]
│
└── [Other project files]
```

### Existing MySQL Database Schema

**Database:** `nonprofit_finance`
**Relevant Tables:**

```sql
-- Main expense table (existing)
CREATE TABLE expenses (
    id INT PRIMARY KEY AUTO_INCREMENT,
    org_id INT,
    expense_date DATE,
    amount DECIMAL(10, 2),
    category_id INT,
    description VARCHAR(500),
    paid_by_contact_id INT,
    method ENUM('CASH', 'CARD', 'BANK', 'OTHER'),
    receipt_url VARCHAR(500),              -- ⭐ ALREADY EXISTS for receipt storage
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (category_id) REFERENCES categories(id),
    FOREIGN KEY (paid_by_contact_id) REFERENCES contacts(id)
);

-- Categories (existing, hierarchical)
CREATE TABLE categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    parent_id INT,
    name VARCHAR(255),
    kind ENUM('EXPENSE', 'INCOME'),
    is_active BOOLEAN DEFAULT TRUE,
    FOREIGN KEY (parent_id) REFERENCES categories(id)
);

-- Contacts (existing)
CREATE TABLE contacts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(20),
    contact_type ENUM('PERSON', 'ORGANIZATION')
);

-- ⭐ TO CREATE: Receipt metadata (optional, for tracking parsing confidence & model info)
CREATE TABLE receipt_metadata (
    id INT PRIMARY KEY AUTO_INCREMENT,
    expense_id INT UNIQUE,
    model_name VARCHAR(100),               -- e.g., "gemini-1.5-flash"
    model_provider VARCHAR(50),            -- e.g., "google"
    engine_version VARCHAR(50),
    parsing_confidence FLOAT,              -- Overall confidence 0-1
    field_confidence JSON,                 -- Per-field confidence scores
    raw_response JSON,                     -- Full LLM response for debugging
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (expense_id) REFERENCES expenses(id) ON DELETE CASCADE
);
```

### Existing Data Models (Pydantic)

**File:** `/home/adamsl/planner/nonprofit_finance_db/app/models/receipt_models.py`

The following models **already exist** and should be used:

```python
PaymentMethod = Literal["CASH", "CARD", "BANK", "OTHER"]

class ReceiptItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    line_total: float  # Auto-computed from quantity * unit_price

class ReceiptTotals(BaseModel):
    subtotal: float
    tax_amount: Optional[float] = 0.0
    tip_amount: Optional[float] = 0.0
    discount_amount: Optional[float] = 0.0
    total_amount: float

class ReceiptPartyInfo(BaseModel):
    merchant_name: str
    merchant_phone: Optional[str]
    merchant_address: Optional[str]
    store_location: Optional[str]

class ReceiptMeta(BaseModel):
    currency: str = "USD"
    receipt_number: Optional[str]
    model_name: Optional[str]
    model_provider: Optional[str]
    engine_version: Optional[str]
    raw_text: Optional[str]

class ReceiptExtractionResult(BaseModel):
    transaction_date: date
    payment_method: PaymentMethod
    party: ReceiptPartyInfo
    items: List[ReceiptItem]
    totals: ReceiptTotals
    meta: ReceiptMeta
```

### Existing Frontend Patterns

**Event System (from `js/event-bus.js`):**
```javascript
import { emit, on } from "./event-bus.js";

// Emit events
emit('category:selected', { categoryId: 123, transactionId: 456 });

// Listen for events
on('event:name', (data) => { /* handle */ });
```

**Component Communication:**
- All components communicate via global event bus
- Data attributes used for styling: `data-[attribute]="value"`
- LocalStorage for client-side state persistence
- Web Components with Shadow DOM for style isolation

**Existing Upload Pattern (from `upload_pdf_statements.html`):**
- Accepts file uploads via drag-and-drop or file picker
- Sends to `/api/import-pdf` endpoint
- Shows progress spinner during processing
- Displays results/errors to user

### Existing API Endpoints

```
GET  /api/transactions              - List all expenses (with date filtering)
GET  /api/categories                - List all categories (hierarchical)
PUT  /api/transactions/{id}/category - Update transaction category
GET  /api/recent-downloads          - List recent PDF downloads
POST /api/import-pdf                - Import PDF bank statement
GET  /api/health                    - Server health check
```

**Response format example:**
```json
{
  "transactions": [
    { "id": 1, "date": "2025-01-15", "vendor": "Starbucks", "amount": 5.50, "category_id": 10 }
  ],
  "categories": [
    { "id": 10, "name": "Food & Dining", "parent_id": null }
  ]
}
```

---

## REQUIREMENTS & SPECIFICATIONS

### 1. User Workflow

The receipt scanner should follow this workflow:

```
User uploads receipt image
          ↓
Frontend validates file (size, format, dimensions)
          ↓
Backend stores temp copy (for retries/logging)
          ↓
AI vision model parses receipt → structured JSON
          ↓
Frontend displays parsed data in edit form
  (merchant, date, total, tax, items, payment method)
          ↓
User reviews & corrects as needed
          ↓
User selects expense category (via existing CategoryPicker)
          ↓
Backend moves file to permanent storage:
  /uploads/receipts/YYYY/MM/receipt_[timestamp]_[original].ext
          ↓
Backend creates Expense row with receipt_url set
          ↓
New expense appears in daily_expense_categorizer feed
```

### 2. File Handling Requirements

**Supported Formats:**
- JPG, PNG, WebP, PDF (1st page only for PDF)
- Max input size: 5MB
- Backend compression: downscale/compress to 1200-1600px long edge

**Storage Path Structure:**
```
/home/adamsl/planner/nonprofit_finance_db/uploads/receipts/
├── 2025/
│   ├── 11/
│   │   ├── receipt_20251114T143022Z_starbucks.jpg
│   │   ├── receipt_20251114T150530Z_whole_foods.png
│   │   └── receipt_20251114T231530Z_cvs_pharmacy.pdf
│   └── 12/
│       └── [future receipts]
```

**Database Storage:**
- Store relative path in `Expense.receipt_url`, e.g.: `receipts/2025/11/receipt_20251114T143022Z_cvs_groceries.jpg`
- Serve files via API endpoint (e.g., `/api/receipts/{path}`) with security checks

### 3. Data Extraction Requirements

For each receipt, extract:

**Merchant/Vendor:**
- merchant_name (required)
- merchant_phone (optional)
- merchant_address (optional)
- store_location (optional, city/state or full address)

**Dates:**
- transaction_date (required, normalized YYYY-MM-DD)
- transaction_time (optional, HH:MM format)

**Line Items (array of):**
- quantity (required)
- description (required)
- unit_price (required)
- line_total (auto-computed on backend)

**Totals:**
- subtotal (required)
- tax_amount (required or 0.0)
- tip_amount (optional)
- discount_amount (optional)
- total_amount (required)

**Payment:**
- payment_method (required): CASH | CARD | BANK | OTHER
- card_last4 (optional, if visible)
- card_brand (optional, if visible)

**Receipt IDs (optional):**
- receipt_number / invoice_number
- register_id, cashier (if available)

**Metadata:**
- currency (default USD unless detected)
- model_name (Gemini model used)
- field_confidence (per-field confidence 0-1, if provided)

### 4. AI Vision Model Selection

**Recommendation: Gemini 1.5 Flash or 2.5 Flash-Lite**

**Why:**
1. You already use Gemini in other parts of the system
2. Very cheap: ~$0.05 per 100 receipts/month
3. Excellent accuracy on structured document extraction
4. Fast: <1-2 seconds per receipt
5. Simple JSON instructions pattern

**Alternative Fallback Provider (pre-approved):**
- **OpenAI gpt-4o-mini (or successor gpt-5-nano when available):** ~$0.10 per 100 receipts, excellent reasoning and JSON adherence. Treat this as the only sanctioned automatic fallback if Gemini 1.5 Flash is unavailable or rate limited.

**Architecture Requirement:**
Design `receipt_parser.py` with a pluggable `ReceiptEngine` interface so you can:
- Start with `GeminiReceiptEngine` (default, must be production-grade)
- Add `OpenAIReceiptEngine` as the sanctioned fallback without refactoring call sites
- Toggle engines via environment configuration flags for on-call mitigation

### 5. Error Handling & Validation

**Frontend Validation (before sending to backend):**
- File size: reject if >5MB
- File type: accept only JPG/PNG/WebP/PDF
- Image dimensions: warn if <300px or >8000px on long edge
- File extension: validate against MIME type

**Backend Validation:**
- Receipt file integrity check
- AI parsing success/failure handling
- Confidence score thresholding (flag low-confidence fields to user)
- Image compression/downscaling (Pillow or similar)

**Error Fallback Strategy:**
1. Try primary AI engine (Gemini)
2. If timeout/error: show user message "Receipt parsing failed. Please try again or enter data manually."
3. Log full error + truncated image + model response for debugging
4. Still allow user to manually enter receipt data if AI fails
5. Optionally: store raw receipt image even if parsing failed

### 6. Security & Privacy Considerations

**Important:** Receipts may contain PII (card numbers, addresses, names, loyalty IDs, phone numbers)

**Requirements:**
- Restrict `/uploads/receipts/` directory to authenticated users only (future)
- Document receipt retention policy (recommend 7 years for compliance)
- Consider image redaction options for long-term storage
- Ensure backups don't expose raw images
- Log access to receipt data
- No receipt images in error logs or response bodies
- Validate all file access is within authorized scope

### 7. Database Integration

**Create new Expense:**
```json
POST /api/save-receipt
{
  "org_id": 1,
  "merchant_name": "Whole Foods",
  "expense_date": "2025-11-14",
  "total_amount": 45.32,
  "tax_amount": 3.42,
  "category_id": 15,
  "payment_method": "CARD",
  "description": "Groceries",
  "receipt_file_path": "receipts/2025/11/receipt_20251114T143022Z_whole_foods.jpg",
  "parsed_items": [
    { "description": "Organic Bananas", "quantity": 2, "unit_price": 0.79 },
    { "description": "Almond Butter", "quantity": 1, "unit_price": 8.99 }
  ]
}
```

**Response:**
```json
{
  "expense_id": 42,
  "receipt_url": "receipts/2025/11/receipt_20251114T143022Z_whole_foods.jpg",
  "status": "created",
  "message": "Expense saved successfully"
}
```

### 8. Integration Requirements (from legacy planner request)

**UI Component Requirements**
- Build the new `<receipt-scanner>` web component so it can sit next to the existing `<category-picker>` in `daily_expense_categorizer.html`.
- Provide editable forms populated with parsed data, an image preview, and call the CategoryPicker component directly for category assignment.

**Data Flow Integration**
1. ReceiptScanner uploads the raw image to a new backend endpoint.
2. Backend hands the file to the `ReceiptEngine` (Gemini → OpenAI fallback) and gets structured data.
3. Response hydrates the editable UI form; user changes flow back through the component state.
4. On save:
   - Persist the file beneath `/nonprofit_finance_db/uploads/receipts/YYYY/MM/receipt_[timestamp]_[original].ext`.
   - Create/update the Expense row with `receipt_url`.
   - Emit bus events so `daily_expense_categorizer` refreshes.

**Backend Endpoint Checklist**
- `POST /api/parse-receipt` – multipart upload + AI parse (new).
- `POST /api/expenses` – already present; ensure it now accepts and returns `receipt_url`.
- `GET /api/expenses` – already present; include receipt metadata so UI can display thumbnails.
- `DELETE /api/receipts/{id}` – for cleanup and storage management.

**Reference Patterns**
- Mirror the streaming/error-handling approach from `office-assistant/upload-component/upload-component.ts`.
- Use the existing event bus (`receipt:selected`, `receipt:parsing`, `receipt:complete`) to keep UI components decoupled.

---

## DELIVERABLES REQUIRED

Please provide a comprehensive markdown document that includes:

### A. Architecture & Design Document

1. **System Architecture Diagram** (ASCII art or description)
2. **Data Flow Diagram** (receipt upload → parsing → storage → UI)
3. **ReceiptEngine Interface** (pluggable design pattern)
4. **Error Handling Strategy** (with flow diagrams)
5. **File Storage Strategy** (directory layout, cleanup policy)
6. **Security Model** (PII handling, access control)

### B. Backend Implementation

**File: `/home/adamsl/planner/nonprofit_finance_db/app/services/receipt_engine.py`**
- Abstract `ReceiptEngine` base class
- `GeminiReceiptEngine` implementation
- Engine factory/selector pattern
- Retry logic with exponential backoff
- Request/response logging

**File: `/home/adamsl/planner/nonprofit_finance_db/app/services/receipt_parser.py`**
- Main orchestrator class
- File validation logic
- Image compression/normalization (Pillow integration)
- Temp file management
- Storage path generation
- Confidence score calculation

**File: `/home/adamsl/planner/nonprofit_finance_db/app/repositories/receipt_metadata.py`**
- New repository for receipt_metadata table
- Methods: create, update, get_by_expense_id, delete
- Follows existing BaseRepository pattern

**File: `/home/adamsl/planner/nonprofit_finance_db/app/api/receipt_endpoints.py`**
- FastAPI blueprint/router with endpoints:
  - `POST /api/parse-receipt` - Parse receipt image
  - `POST /api/save-receipt` - Save parsed expense to database
  - `GET /api/receipts/{id}` - Retrieve receipt metadata
  - `GET /api/receipts/file/{path}` - Serve receipt image (with security)
  - `DELETE /api/receipts/{id}` - Delete receipt (with cleanup)
- Request/response validation (Pydantic)
- Error handling with proper HTTP status codes

**File: `/home/adamsl/planner/nonprofit_finance_db/requirements.txt`**
- Add required dependencies:
  - `google-generativeai` (for Gemini API)
  - `Pillow` (for image processing)
  - `python-multipart` (for file uploads)
  - Any other dependencies needed

**Updated:** `/home/adamsl/planner/nonprofit_finance_db/api_server.py`
- Mount receipt endpoints router
- Add CORS headers if needed
- Add file serving middleware

### C. Frontend Implementation

**File: `/home/adamsl/planner/office-assistant/js/components/receipt-scanner.js`**
- Custom Web Component `<receipt-scanner>`
- Shadow DOM for style isolation
- Features:
  - Drag-and-drop file upload
  - File picker dialog
  - File validation with user feedback
  - Progress spinner during parsing
  - Receipt data display/edit form
  - Integration with existing `<category-picker>` component
  - Save/cancel buttons
  - Error display with retry option
- Events emitted: `receipt:parsed`, `receipt:saved`, `receipt:error`, `receipt:cancelled`

**File: `/home/adamsl/planner/office-assistant/receipt-scanner.html`**
- Standalone receipt scanner UI (for testing/iframe)
- Can be embedded in daily_expense_categorizer.html
- Uses `<receipt-scanner>` component
- Displays uploaded receipts in a feed
- Integration with existing expense display

**File: `/home/adamsl/planner/office-assistant/css/receipt-scanner.css`**
- TailwindCSS classes for receipt scanner UI
- Responsive design for mobile/tablet/desktop
- Loading states, error states, success states
- Print-friendly receipt display

**Updated:** `/home/adamsl/planner/office-assistant/daily_expense_categorizer.html`
- Add receipt scanner component to the UI
- Display receipts alongside other expenses
- Show receipt image thumbnail with parsed data
- Allow editing parsed data before final save

### D. Database Schema Updates

Provide SQL:
- Create `receipt_metadata` table (optional, for tracking parsing info)
- Create indexes on `expenses.receipt_url`, `expenses.expense_date`
- Create indexes on `receipt_metadata.expense_id`

### E. Configuration & Environment

**File: `.env` (sample keys)**
```
GEMINI_API_KEY=your_key_here
RECEIPT_UPLOAD_DIR=./uploads/receipts
RECEIPT_MAX_SIZE_MB=5
RECEIPT_IMAGE_MAX_WIDTH_PX=1600
RECEIPT_IMAGE_MAX_HEIGHT_PX=1600
RECEIPT_PARSE_TIMEOUT_SECONDS=15
RECEIPT_RETENTION_DAYS=2555  # 7 years
```

**File: `/home/adamsl/planner/nonprofit_finance_db/app/config.py`**
- Add receipt-related configuration loading
- Path validation
- Model selection logic
- Timeout/retry configuration

### F. Testing & Validation

1. **Unit Tests** (pytest)
   - Receipt model validation
   - Image compression logic
   - File path generation
   - ReceiptEngine interface tests (mocked AI calls)

2. **Integration Tests**
   - End-to-end receipt parsing workflow
   - Database save/retrieve
   - File storage verification
   - Error handling verification

3. **Frontend Tests**
   - Component rendering
   - Event emission
   - Form validation
   - Error state handling

### G. Documentation

1. **Installation Guide** - How to set up the receipt scanner
2. **Configuration Guide** - Environment variables & settings
3. **Usage Guide** - How to use the receipt scanner UI
4. **API Reference** - All receipt endpoints with examples
5. **Architecture Notes** - Design decisions & rationale
6. **Troubleshooting** - Common issues & solutions
7. **Future Enhancements** - Item-level splitting, fallback engines, etc.

### H. Example Prompts for AI Models

Provide the exact system prompts and structured outputs expected for:
- **Gemini 1.5 Flash** prompt for receipt parsing
- **OpenAI gpt-4o-mini** prompt (for future fallback)
- JSON schema for structured output
- Field validation logic

### I. Migration/Setup Scripts

Provide:
- SQL script to create receipt_metadata table
- Python script to create uploads/receipts directories
- Script to test Gemini API connectivity
- Script to validate existing expenses for receipt_url compatibility

---

## INTEGRATION POINTS WITH EXISTING SYSTEM

### 1. Expense Categorizer
The receipt scanner must integrate seamlessly with `/home/adamsl/planner/office-assistant/daily_expense_categorizer.html`:
- New expenses from receipts appear in the expense feed
- Use existing category selector from CategoryPicker component
- Display receipt thumbnail alongside expense
- Allow inline editing of parsed receipt data

### 2. Category System
- Reuse existing hierarchical category system
- CategoryPicker component already handles category selection
- Link receipt expenses to categories the same way as manual expenses

### 3. Repository Pattern
- Follow existing BaseRepository pattern in `/home/adamsl/planner/nonprofit_finance_db/app/repositories/base.py`
- Implement ReceiptMetadataRepository extending BaseRepository
- Reuse ExpenseRepository for saving expense data

### 4. Event Bus System
- Frontend components should emit/listen via global event-bus.js
- Examples:
  - `emit('receipt:parsed', { receiptData, expenseId })`
  - `on('receipt:saved', () => { refresh expense feed })`

### 5. API Structure
- Follow FastAPI patterns from existing endpoints
- Use Pydantic models for request/response validation
- Return consistent JSON responses
- Use proper HTTP status codes

---

## ADDITIONAL CONTEXT & NOTES

### Current Setup
- **MySQL Server:** Running on localhost:3306
- **FastAPI Server:** Runs on localhost:8000
- **Frontend:** Vanilla JS SPA, no build step
- **Google Services:** Gemini API already integrated elsewhere (`gemini_structured_outputs` folder exists)
- **File Storage:** System currently handles uploads in `nonprofit_finance_db/ingestion/` pipeline

### Future Enhancements (Not Required for MVP)
1. Receipt item-level expense splitting (create multiple expenses per receipt)
2. OCR + manual correction UI for low-confidence fields
3. Receipt image redaction (mask card numbers, PII) before storage
4. Batch receipt processing
5. Receipt template detection (different layouts per store)
6. Multi-currency support with exchange rate normalization
7. Receipt duplicate detection (same receipt uploaded twice)
8. Fallback to OpenAI gpt-5-nano or other models if Gemini unavailable
9. Document AI / Azure Document Intelligence engines
10. Local ML model fallback (Tesseract + LayoutLMv3)

### Constraints
- No major dependency upgrades without discussion
- Must maintain existing FastAPI + MySQL architecture
- Frontend must remain vanilla JS (no React/Vue frameworks)
- Must follow existing code style and patterns
- All code must include error handling and logging
- Must be compatible with Python 3.9+

---

## IMPLEMENTATION TIMELINE EXPECTATIONS

1. **Phase 1 (Backend Infrastructure)**
   - ReceiptEngine interface & GeminiReceiptEngine implementation
   - Receipt parsing service
   - API endpoints
   - Database schema updates

2. **Phase 2 (File Handling)**
   - Image validation & compression
   - Storage path management
   - Temp file cleanup
   - File serving endpoint

3. **Phase 3 (Frontend)**
   - Receipt scanner component
   - UI/UX for parsing & review
   - Category picker integration
   - Error handling UI

4. **Phase 4 (Integration & Testing)**
   - End-to-end testing
   - Integration with expense categorizer
   - Error handling & fallbacks
   - Documentation & examples

---

## QUESTIONS FOR THE EXPERT PLANNER

1. Should we implement item-level expense splitting in the MVP, or save that for v2?
2. Is the pluggable ReceiptEngine interface design solid, or would you suggest a different approach?
3. Should we add per-field confidence scores to guide users on which fields might have errors?
4. What's your recommendation on receipt image retention/cleanup policy?
5. Any security recommendations for serving receipt images from the API?
6. Should we implement a manual fallback UI (text entry form) if AI parsing fails?
7. What's the recommended approach for logging/debugging receipt parsing failures?

---

## HOW TO USE THIS REQUEST

1. **Send this document to the Expert Planner** requesting a complete markdown document with:
   - Detailed architecture & design
   - Complete, production-ready Python backend code (all files listed above)
   - Complete HTML/CSS/JavaScript frontend code (all files listed above)
   - Database schema SQL
   - Installation & configuration instructions
   - Testing strategy
   - Example API calls & responses

2. **Expert Planner will provide:**
   - ONE comprehensive markdown document
   - All source code ready to implement
   - Installation steps
   - Integration checklist
   - Testing validation steps

3. **Implementation Team will:**
   - Create all directories and files specified
   - Copy/implement code from expert's markdown document
   - Run tests to validate
   - Deploy to local MySQL instance
   - Test end-to-end workflow

---

## CONTACT & CLARIFICATION

If the Expert Planner needs clarification:

- **Database Host:** localhost:3306
- **Database Name:** nonprofit_finance
- **API Server Location:** http://localhost:8000
- **Frontend Location:** http://localhost:8000/ (served by FastAPI)
- **Main Backend Directory:** `/home/adamsl/planner/nonprofit_finance_db/`
- **Main Frontend Directory:** `/home/adamsl/planner/office-assistant/`
- **Current Python Version:** 3.9+
- **MySQL Version:** 8.0.43

---

**Status:** Ready for expert planning
**Next Step:** Wait for expert's comprehensive implementation document
**Estimated Completion:** [To be determined by expert planner]
