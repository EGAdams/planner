# Switch to Standalone Receipt Scanner

## Changes Made

### 1. Updated `api_server.py` (lines 30-35)

**Added standalone backend to Python path:**
```python
# Add standalone receipt scanner to path
RECEIPT_SCANNER_BACKEND = Path(__file__).parent / "receipt_scanning_tools" / "receipt_scanner" / "backend"
sys.path.insert(0, str(RECEIPT_SCANNER_BACKEND))

from api.receipt_endpoints import router as receipt_router  # Now from standalone copy
```

**Added standalone frontend directory (line 43):**
```python
RECEIPT_SCANNER_FRONTEND = (BASE_DIR / "receipt_scanning_tools" / "receipt_scanner" / "frontend").resolve()
```

**Added frontend mount point (lines 78-88):**
```python
# Mount standalone receipt scanner frontend
if RECEIPT_SCANNER_FRONTEND.is_dir():
    @app.get("/receipt-scanner", include_in_schema=False)
    async def get_receipt_scanner():
        return FileResponse(RECEIPT_SCANNER_FRONTEND / "receipt-scanner.html")

    app.mount(
        "/receipt-scanner-app",
        StaticFiles(directory=str(RECEIPT_SCANNER_FRONTEND), html=True),
        name="receipt-scanner",
    )
```

### 2. Updated `receipt_scanning_tools/receipt_scanner/backend/api/receipt_endpoints.py`

**Fixed imports to use standalone modules:**
```python
# Import from standalone backend
from config import settings
from services.receipt_parser import ReceiptParser
from services.receipt_engine import GeminiReceiptEngine
from models.receipt_models import ReceiptExtractionResult, ...

# Still use shared database repositories
from app.repositories.receipt_metadata import ReceiptMetadataRepository
from app.repositories.expenses import ExpenseRepository
```

## How to Apply Changes

### Step 1: Stop the Current API Server

In the terminal where `api_server.py` is running:
```bash
# Press Ctrl+C to stop
```

### Step 2: Restart the API Server

```bash
cd /home/adamsl/planner/nonprofit_finance_db
source venv/bin/activate  # If using venv
python3 api_server.py
```

### Step 3: Verify It's Working

The server should start and display:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8080
```

## New URLs

### Standalone Receipt Scanner
**Primary URL**: http://localhost:8080/receipt-scanner
**Alternative**: http://localhost:8080/receipt-scanner-app/receipt-scanner.html

### Original Receipt Scanner (still available)
**URL**: http://localhost:8080/office/receipt-scanner.html

## What Changed

### Before (Original)
```
Backend:  app/api/receipt_endpoints.py
          app/services/receipt_parser.py
          app/services/receipt_engine.py
Frontend: office-assistant/receipt-scanner.html
URL:      http://localhost:8080/office/receipt-scanner.html
```

### After (Standalone)
```
Backend:  receipt_scanning_tools/receipt_scanner/backend/api/receipt_endpoints.py
          receipt_scanning_tools/receipt_scanner/backend/services/receipt_parser.py
          receipt_scanning_tools/receipt_scanner/backend/services/receipt_engine.py
Frontend: receipt_scanning_tools/receipt_scanner/frontend/receipt-scanner.html
URL:      http://localhost:8080/receipt-scanner
```

## Verification

### Test Backend Import
```bash
cd /home/adamsl/planner/nonprofit_finance_db
python3 << 'EOF'
import sys
from pathlib import Path

backend = Path('receipt_scanning_tools/receipt_scanner/backend')
sys.path.insert(0, str(backend))

try:
    from api.receipt_endpoints import router
    print('✓ Backend imports working from standalone copy')
except Exception as e:
    print(f'✗ Import error: {e}')
EOF
```

### Test Frontend Path
```bash
ls -la receipt_scanning_tools/receipt_scanner/frontend/receipt-scanner.html
```

Should show:
```
-rw-r--r-- 1 adamsl adamsl 2695 Jan  3 19:07 receipt-scanner.html
```

### Test API Endpoint (after restart)
```bash
curl http://localhost:8080/api/categories | head -20
```

Should return JSON with categories.

### Test Frontend (after restart)
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/receipt-scanner
```

Should return `200`.

## Benefits

✅ **Working from receipt_scanning_tools**: All modifications now happen in the standalone copy
✅ **Original preserved**: Old files in `app/` and `office-assistant/` untouched
✅ **Dual access**: Both old and new URLs work during transition
✅ **Safe testing**: Can test changes without affecting production
✅ **Easy rollback**: Just remove the new imports to revert

## Rollback (if needed)

If something goes wrong, edit `api_server.py` and change line 35 back to:
```python
from app.api.receipt_endpoints import router as receipt_router
```

Then restart the server.

## Next Steps

After confirming it works:
1. ✅ Use the new URL: http://localhost:8080/receipt-scanner
2. ✅ Make changes in `receipt_scanning_tools/` directory
3. ✅ Test thoroughly
4. ✅ Eventually remove original files from `app/` when confident

---

**Status**: Ready to restart API server
**Date**: 2026-01-03
