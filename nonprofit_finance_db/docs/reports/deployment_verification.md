# Daily Expense Categorizer - Deployment Verification

## Overview
This document verifies that the Daily Expense Categorizer is correctly connected to the nonprofit_finance database.

## Database Configuration
**Location**: `/home/adamsl/planner/nonprofit_finance_db/.env`

```
DB_HOST=127.0.0.1
DB_PORT=3306
NON_PROFIT_USER=root
NON_PROFIT_PASSWORD=tinman
NON_PROFIT_DB_NAME=nonprofit_finance
POOL_SIZE=5
```

## Architecture

### Components:
1. **Database**: MySQL `nonprofit_finance` database on `localhost:3306`
2. **API Server**: FastAPI server running on `http://localhost:8080`
3. **Frontend**: Static file server on `http://localhost:8081`

### Data Flow:
```
Browser (port 8081)
  --> API Server (port 8080)
    --> MySQL Database (port 3306)
```

## Changes Made

### 1. Updated HTML Configuration
**Files Modified**:
- `/home/adamsl/planner/office-assistant/daily_expense_categorizer.html`
- `/home/adamsl/planner/category-picker/public/office/daily_expense_categorizer.html`

**Changes**:
```javascript
// OLD: Used sample data on port 8081
const STATIC_PORTS = new Set(["8081"]);

// NEW: Points to API server on port 8080
const API_BASE = window.location.port === "8081"
  ? "http://localhost:8080/api"
  : `${window.location.protocol}//${window.location.host}/api`;
const STATIC_PORTS = new Set([]);  // Use live API by default
```

### 2. Database Connection
**Module**: `/home/adamsl/planner/nonprofit_finance_db/app/db/pool.py`
- Uses `mysql.connector` with connection pooling
- Loads credentials from `.env` file via `app/config.py`
- Provides helper functions: `query_one()`, `query_all()`, `execute()`

### 3. API Endpoints
**Server**: `/home/adamsl/planner/nonprofit_finance_db/api_server.py`

Active endpoints:
- `GET /api` - API status check
- `GET /api/transactions` - Fetch all transactions (with optional date filtering)
- `GET /api/categories` - Fetch hierarchical categories
- `PUT /api/transactions/{id}/category` - Update transaction category
- `GET /api/recent-downloads` - List recent PDF downloads
- `POST /api/import-pdf` - Import bank statement PDF

## Test Results

### Database Connection Test
```bash
$ ./venv/bin/python test_db_connection.py
✓ Connected to database: nonprofit_finance
✓ Found 192 transactions in database
✓ Found 115 active categories in database
✓ Sample transaction: ID=56, Date=2025-06-17, Description=Checks #3921, #9343, #9344, Amount=25.00

✅ All database tests passed!
```

### API Integration Test
```bash
$ ./venv/bin/python test_api_integration.py
✓ API is running: Daily Expense Categorizer API
✓ Loaded 192 transactions
✓ Loaded 115 categories
✓ Root categories: 2
✓ Subcategories: 113
✓ Found 182 uncategorized transactions
✓ Categorized: 10 transactions
✓ Found 53 transactions in June 2025

✅ ALL TESTS PASSED - API is working correctly!
```

## Verification Steps

### 1. Check API Server is Running
```bash
ps aux | grep api_server
# Should show: python3 api_server.py
```

### 2. Test API Endpoints
```bash
# Test API root
curl http://localhost:8080/api

# Test transactions endpoint
curl http://localhost:8080/api/transactions | head -20

# Test categories endpoint
curl http://localhost:8080/api/categories | head -20
```

### 3. Access Frontend
Open browser and navigate to:
```
http://localhost:8081/office/daily_expense_categorizer.html
```

**Expected Behavior**:
- Page loads transaction data from database
- Shows actual transaction count (not sample data)
- Displays real vendor names and amounts
- Category picker shows hierarchical categories from database
- Can categorize transactions and save to database

### 4. Verify Live Data
Check the page footer banner:
- Should NOT show "Showing sample data" message
- Data should reflect current database state

## Database Schema

### Transactions Table
```sql
CREATE TABLE transactions (
  id INT PRIMARY KEY AUTO_INCREMENT,
  transaction_date DATE NOT NULL,
  description VARCHAR(255),
  amount DECIMAL(10,2),
  transaction_type VARCHAR(50),  -- 'CREDIT' for expenses
  category_id INT,
  FOREIGN KEY (category_id) REFERENCES categories(id)
);
```

### Categories Table
```sql
CREATE TABLE categories (
  id INT PRIMARY KEY AUTO_INCREMENT,
  name VARCHAR(255) NOT NULL,
  parent_id INT NULL,
  kind VARCHAR(50),  -- 'EXPENSE' or 'INCOME'
  is_active BOOLEAN DEFAULT 1,
  FOREIGN KEY (parent_id) REFERENCES categories(id)
);
```

## Current Data Statistics
- **Total Transactions**: 192
- **Categorized**: 10 (5.2%)
- **Uncategorized**: 182 (94.8%)
- **Active Categories**: 115
- **Root Categories**: 2 (Church, Housing)
- **Transactions in June 2025**: 53

## Troubleshooting

### Issue: Page shows "Showing sample data"
**Solution**: The configuration has been updated. Refresh the page hard (Ctrl+Shift+R)

### Issue: API connection failed
**Check**:
1. API server is running: `ps aux | grep api_server`
2. Port 8080 is accessible: `curl http://localhost:8080/api`
3. Database credentials are correct in `.env`

### Issue: Database connection error
**Check**:
1. MySQL is running: `systemctl status mysql`
2. Credentials are correct: `mysql -uroot -ptinman nonprofit_finance`
3. Database exists: `SHOW DATABASES;`

### Issue: CORS errors in browser console
**Solution**: CORS is already configured in `api_server.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: ERR_EMPTY_RESPONSE in Windows Browser (WSL2 Networking)
**Symptoms**:
- Windows browser shows "This page isn't working - localhost didn't send any data"
- ERR_EMPTY_RESPONSE error
- Server works fine from within WSL (curl, Playwright tests pass)
- Page completely blank in Windows browser

**Root Cause**: WSL2 uses a separate network namespace. Windows `localhost:8080` doesn't automatically reach WSL2's `localhost:8080`.

**Solutions**:

#### Option 1: Use WSL2 IP Address Directly (IMMEDIATE FIX)
1. Get WSL2 IP address:
   ```bash
   hostname -I
   # Example output: 172.30.171.179 172.18.0.1 172.17.0.1
   # Use the first IP (172.30.171.179)
   ```

2. Access from Windows browser using WSL2 IP:
   ```
   http://172.30.171.179:8080/office/daily_expense_categorizer.html
   ```

#### Option 2: Configure Windows Port Forwarding (For localhost access)
Run these commands in **PowerShell as Administrator**:

```powershell
# Get current WSL2 IP address
wsl hostname -I

# Delete any existing proxy for port 8080
netsh interface portproxy delete v4tov4 listenport=8080 listenaddress=0.0.0.0

# Add new proxy to forward Windows localhost:8080 to WSL2
netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0 connectport=8080 connectaddress=172.30.171.179

# Verify configuration
netsh interface portproxy show all
```

Replace `172.30.171.179` with your actual WSL2 IP from step 1.

After this, `http://localhost:8080` will work in Windows browser.

#### Option 3: Automatic Script for Dynamic WSL2 IPs
WSL2 IP addresses can change on restart. Create a script to automatically update:

**File**: `fix-wsl-port.ps1` (Run as Administrator)
```powershell
# Get current WSL2 IP
$wslIP = (wsl hostname -I).Trim().Split()[0]
Write-Host "WSL2 IP: $wslIP"

# Remove old proxy
netsh interface portproxy delete v4tov4 listenport=8080 listenaddress=0.0.0.0

# Add new proxy
netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0 connectport=8080 connectaddress=$wslIP

# Show current configuration
netsh interface portproxy show all
Write-Host "`nPort forwarding updated! Access at http://localhost:8080"
```

**Verification**:
```bash
# From WSL - should work
curl http://localhost:8080/api

# From Windows PowerShell - should also work after port forwarding
curl http://localhost:8080/api
```

**Important Notes**:
- WSL2 IP addresses change on Windows restart
- Re-run port forwarding script after Windows restarts
- Windows Firewall may block the connection - allow port 8080 if needed
- Server must bind to `0.0.0.0` not `127.0.0.1` (already configured in api_server.py)

## Success Criteria ✅

- [x] Database connection configured with correct credentials
- [x] API server connects to database successfully
- [x] Frontend points to API server (not sample data)
- [x] Transactions load from database
- [x] Categories load from database
- [x] Category updates save to database
- [x] Live data displays on page at http://localhost:8081/office/daily_expense_categorizer.html

## Maintenance

### Starting the API Server
```bash
cd /home/adamsl/planner/nonprofit_finance_db
python3 api_server.py
```

### Starting the Frontend Server
```bash
cd /home/adamsl/planner/category-picker
npx http-server -p 8081
```

### Updating Database Credentials
Edit `/home/adamsl/planner/nonprofit_finance_db/.env` and restart API server.

---

**Status**: ✅ DEPLOYMENT VERIFIED
**Last Updated**: 2025-11-06
**Verified By**: Claude Code (TDD Feature Implementation Agent)
