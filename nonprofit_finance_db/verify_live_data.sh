#!/bin/bash
# End-to-end verification that Daily Expense Categorizer shows live data

echo "============================================================"
echo "Daily Expense Categorizer - Live Data Verification"
echo "============================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Test 1: Check API server is running
echo "1. Checking API server (port 8080)..."
if curl -s http://localhost:8080/api > /dev/null 2>&1; then
    echo -e "   ${GREEN}✓${NC} API server is running"
else
    echo -e "   ${RED}✗${NC} API server is NOT running"
    echo "   Run: python3 api_server.py"
    exit 1
fi

# Test 2: Check frontend server is running
echo ""
echo "2. Checking frontend server (port 8081)..."
if curl -s http://localhost:8081/office/daily_expense_categorizer.html > /dev/null 2>&1; then
    echo -e "   ${GREEN}✓${NC} Frontend server is running"
else
    echo -e "   ${RED}✗${NC} Frontend server is NOT running"
    echo "   Run: npx http-server -p 8081"
    exit 1
fi

# Test 3: Verify API returns data
echo ""
echo "3. Verifying API returns live data..."
TRANSACTION_COUNT=$(curl -s http://localhost:8080/api/transactions | grep -o '"id"' | wc -l)
CATEGORY_COUNT=$(curl -s http://localhost:8080/api/categories | grep -o '"id"' | wc -l)

if [ "$TRANSACTION_COUNT" -gt 0 ]; then
    echo -e "   ${GREEN}✓${NC} API returns $TRANSACTION_COUNT transactions"
else
    echo -e "   ${RED}✗${NC} API returned 0 transactions"
    exit 1
fi

if [ "$CATEGORY_COUNT" -gt 0 ]; then
    echo -e "   ${GREEN}✓${NC} API returns $CATEGORY_COUNT categories"
else
    echo -e "   ${RED}✗${NC} API returned 0 categories"
    exit 1
fi

# Test 4: Verify frontend configuration
echo ""
echo "4. Verifying frontend configuration..."
if curl -s http://localhost:8081/office/daily_expense_categorizer.html | grep -q 'window.location.port === "8081"'; then
    echo -e "   ${GREEN}✓${NC} Frontend configured to use API on port 8080"
else
    echo -e "   ${RED}✗${NC} Frontend configuration not updated"
    exit 1
fi

if curl -s http://localhost:8081/office/daily_expense_categorizer.html | grep -q 'const STATIC_PORTS = new Set(\[\])'; then
    echo -e "   ${GREEN}✓${NC} STATIC_PORTS cleared - live API enabled by default"
else
    echo -e "   ${RED}✗${NC} STATIC_PORTS still includes port 8081"
    exit 1
fi

# Test 5: Database connection
echo ""
echo "5. Testing database connection..."
cd /home/adamsl/planner/nonprofit_finance_db
DB_TEST_RESULT=$(./venv/bin/python test_db_connection.py 2>&1)
if echo "$DB_TEST_RESULT" | grep -q "All database tests passed"; then
    echo -e "   ${GREEN}✓${NC} Database connection working"
    echo -e "   ${GREEN}✓${NC} nonprofit_finance database accessible"
else
    echo -e "   ${RED}✗${NC} Database connection failed"
    echo "$DB_TEST_RESULT"
    exit 1
fi

# Summary
echo ""
echo "============================================================"
echo -e "${GREEN}✅ ALL CHECKS PASSED${NC}"
echo "============================================================"
echo ""
echo "The Daily Expense Categorizer is now showing LIVE DATA from"
echo "the nonprofit_finance database."
echo ""
echo "🌐 Access the application at:"
echo "   http://localhost:8081/office/daily_expense_categorizer.html"
echo ""
echo "📊 Current Database Stats:"
echo "   - Transactions: $TRANSACTION_COUNT"
echo "   - Categories: $CATEGORY_COUNT"
echo ""
echo "Database Credentials (from .env):"
echo "   - Host: 127.0.0.1:3306"
echo "   - Database: nonprofit_finance"
echo "   - User: root"
echo "============================================================"
