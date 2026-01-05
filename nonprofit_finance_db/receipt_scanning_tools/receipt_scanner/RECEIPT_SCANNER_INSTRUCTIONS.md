# Receipt Scanner

This is a **standalone, verified copy** of the receipt scanning system. It can be moved to any location and used independently.

## 📁 Directory Structure

```
receipt_scanner/
├── backend/                    # Python backend components
│   ├── services/
│   │   ├── receipt_parser.py   # Image processing and validation
│   │   └── receipt_engine.py   # Gemini AI integration
│   ├── api/
│   │   └── receipt_endpoints.py # FastAPI endpoints
│   ├── models/
│   │   └── receipt_models.py   # Pydantic data models
│   └── repositories/
│       └── receipt_metadata.py # Database operations
├── frontend/                   # Web interface
│   ├── receipt-scanner.html    # Main UI
│   └── js/
│       ├── components/
│       │   └── receipt-scanner.js # Receipt scanner component
│       ├── category-picker.js  # Category selection
│       └── event-bus.js        # Event system
├── tests/                      # Test suite
│   ├── test_receipt_processing.py
│   ├── test_receipt_api.py
│   └── test_receipt_items_api.py
├── data/                       # Storage
│   └── receipts/
│       ├── temp/              # Temporary uploads
│       ├── 2024/              # Archived by year
│       ├── 2025/
│       └── 2026/
├── docs/                       # Documentation
│   ├── RECEIPT_SCANNING_STATUS.md
│   └── create_receipt_metadata_table.sql
├── test_standalone.py          # Verification script
└── README.md                   # This file
```

## ✅ Verification

Run the standalone test to verify everything is working:

```bash
cd /home/adamsl/planner/nonprofit_finance_db/receipt_scanning_tools/receipt_scanner
python3 test_standalone.py
```

This test verifies:
- ✓ Environment variables loaded correctly
- ✓ All backend modules importable
- ✓ Gemini API connection works
- ✓ Directory structure complete
- ✓ All required files present
- ✓ Pydantic models functional
- ✓ Receipt engine initializes

## 🚀 How to Use

### 1. Prerequisites

**Environment Variables** (in `/home/adamsl/planner/.env`):
```bash
GEMINI_API_KEY=your_gemini_api_key
RECEIPT_MAX_SIZE_MB=10
RECEIPT_IMAGE_MAX_WIDTH_PX=2048
RECEIPT_IMAGE_MAX_HEIGHT_PX=2048
RECEIPT_PARSE_TIMEOUT_SECONDS=30
```

**Python Dependencies**:
```bash
pip install google-generativeai pydantic pillow fastapi uvicorn python-dotenv
```

**Database**: MySQL with `nonprofit_finance` database

### 2. Database Setup

Create the receipt_metadata table:
```bash
mysql -u adamsl -pTinman@2 nonprofit_finance < docs/create_receipt_metadata_table.sql
```

### 3. Integration with API Server

To use this standalone copy, integrate it into your API server:

**Option A: Import from this location**
```python
# In your api_server.py
import sys
from pathlib import Path

receipt_scanner_path = Path("receipt_scanning_tools/receipt_scanner/backend")
sys.path.insert(0, str(receipt_scanner_path))

from api.receipt_endpoints import router as receipt_router
app.include_router(receipt_router, prefix="/api")
```

**Option B: Copy to main app directory**
```bash
# Copy backend components to main app
cp -r receipt_scanner/backend/* /path/to/main/app/

# Copy frontend to office-assistant
cp -r receipt_scanner/frontend/* /path/to/office-assistant/
```

### 4. Start Services

```bash
# Start MySQL (if not running)
sudo service mysql start

# Start API server (from main directory)
python3 api_server.py
```

### 5. Access Web Interface

Open in browser:
```
http://localhost:8080/receipt-scanner.html
```

## 📊 How It Works

### Receipt Scanning Flow

1. **Upload** receipt image → Frontend sends to `/api/parse-receipt`
2. **Parser** validates and preprocesses image
3. **Gemini AI** extracts structured data:
   - Merchant info
   - Transaction date
   - Line items (description, quantity, price)
   - Totals (subtotal, tax, tip, discount)
4. **Frontend** displays parsed data in table
5. **User** selects category for each item
6. **Auto-save** when category selected → Creates expense entry
7. **Storage** receipt file saved in `data/receipts/YYYY/MM/`
8. **Metadata** AI model info saved in `receipt_metadata` table

### Model Fallback Strategy

The engine tries models in this order (flash models first to avoid quota):
1. `gemini-2.5-flash` (primary)
2. `gemini-2.0-flash`
3. `gemini-2.5-pro`
4. `gemini-pro-latest`

### Per-Item Categorization

**IMPORTANT**: Items do NOT auto-save when receipt is scanned.

- Items with categories selected → Save to database
- Items without categories → Ignored
- Each categorized item → Separate expense entry

## 🧪 Testing

### Run Verification Test
```bash
python3 test_standalone.py
```

### Run Unit Tests
```bash
pytest tests/test_receipt_processing.py -v
pytest tests/test_receipt_api.py -v
pytest tests/test_receipt_items_api.py -v
```

### Test with Sample Receipt
```bash
# Use one of the PDFs in /pdfs directory
curl -X POST "http://localhost:8080/api/parse-receipt" \
  -F "file=@/path/to/receipt.jpg"
```

## 📝 API Endpoints

- `POST /api/parse-receipt` - Parse receipt (doesn't save to DB)
- `POST /api/receipt-items` - Save individual categorized item
- `POST /api/save-receipt` - Batch save operation
- `GET /api/receipts/{expense_id}` - Get receipt metadata
- `GET /api/receipts/file/{year}/{month}/{filename}` - Serve receipt file

## 🔒 Security Notes

- API key stored in parent `.env` file (not in this directory)
- Receipt files stored with timestamp to prevent overwrites
- File uploads validated for type and size
- No direct SQL queries (uses repository pattern)

## 📦 Moving This Copy

To move this standalone copy to another location:

1. **Copy entire directory**:
   ```bash
   cp -r receipt_scanner /new/location/
   ```

2. **Update environment paths** (if needed):
   - `.env` file location in `test_standalone.py`
   - Database connection settings
   - Storage directory paths

3. **Verify with test**:
   ```bash
   cd /new/location/receipt_scanner
   python3 test_standalone.py
   ```

4. **Update API server imports** to point to new location

## 📚 Documentation

See `docs/RECEIPT_SCANNING_STATUS.md` for complete system documentation including:
- Detailed architecture
- Configuration guide
- Troubleshooting
- Integration with Letta agents

## ✅ Verification Checklist

Before using in production:

- [ ] `test_standalone.py` passes all tests
- [ ] Gemini API key valid and has quota
- [ ] MySQL running and `receipt_metadata` table created
- [ ] Storage directories have write permissions
- [ ] API server includes receipt endpoints
- [ ] Frontend accessible at correct URL
- [ ] Test upload with sample receipt successful
- [ ] Database entries created correctly
- [ ] Files stored in correct directory structure

## 🆘 Troubleshooting

### "GEMINI_API_KEY not set"
- Check `.env` file in `/home/adamsl/planner/.env`
- Verify key is valid at https://aistudio.google.com/app/apikey

### "Cannot import receipt_models"
- Run `test_standalone.py` to check imports
- Verify all files copied correctly
- Check Python path includes `backend` directory

### "Failed to connect to MySQL"
- Start MySQL: `sudo service mysql start`
- Verify database exists: `mysql -u adamsl -p -e "SHOW DATABASES;"`
- Check credentials in `.env`

### "Receipt files not saving"
- Check directory permissions on `data/receipts/`
- Verify `RECEIPT_UPLOAD_DIR` setting
- Check disk space

---

**Created**: 2026-01-03
**Status**: Verified and Ready
**Original Location**: `/home/adamsl/planner/nonprofit_finance_db/app/`
**Standalone Copy**: Safe to move anywhere
