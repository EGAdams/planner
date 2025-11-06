#!/bin/bash

###############################################################################
# Daily Expense Categorizer - Connectivity Verification Script
#
# This script verifies that the API server is running and accessible,
# and provides troubleshooting information if issues are detected.
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

API_URL="http://localhost:8080"
PASS_COUNT=0
FAIL_COUNT=0

# Function to print section header
print_section() {
    echo -e "\n${BLUE}==== $1 ====${NC}"
}

# Function to print test result
print_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASS_COUNT++))
}

print_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAIL_COUNT++))
}

print_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

###############################################################################
# Test 1: API Server Running
###############################################################################
print_section "Test 1: API Server Availability"

if curl -s "${API_URL}/api" > /dev/null 2>&1; then
    print_pass "API server is running at ${API_URL}"

    # Get API status
    API_RESPONSE=$(curl -s "${API_URL}/api")
    if echo "$API_RESPONSE" | grep -q '"status":"running"'; then
        print_pass "API status: running"
    else
        print_warn "API status check inconclusive"
    fi
else
    print_fail "API server is NOT accessible at ${API_URL}"
    print_info "Please start the API server with: python3 api_server.py"
    exit 1
fi

###############################################################################
# Test 2: Database Connection
###############################################################################
print_section "Test 2: Database Connectivity"

# Check if we can query transactions
TX_RESPONSE=$(curl -s "${API_URL}/api/transactions")
if echo "$TX_RESPONSE" | grep -q '\['; then
    print_pass "Transactions endpoint accessible"

    # Count transactions (rough estimate)
    TX_COUNT=$(echo "$TX_RESPONSE" | grep -o '"id":' | wc -l)
    if [ "$TX_COUNT" -gt 0 ]; then
        print_pass "Database has $TX_COUNT transactions"
    else
        print_warn "Database has no transactions"
    fi
else
    print_fail "Cannot access transactions endpoint"
fi

# Check if we can query categories
CAT_RESPONSE=$(curl -s "${API_URL}/api/categories")
if echo "$CAT_RESPONSE" | grep -q '\['; then
    print_pass "Categories endpoint accessible"

    # Count categories (rough estimate)
    CAT_COUNT=$(echo "$CAT_RESPONSE" | grep -o '"id":' | wc -l)
    if [ "$CAT_COUNT" -gt 0 ]; then
        print_pass "Database has $CAT_COUNT categories"
    else
        print_warn "Database has no categories"
    fi
else
    print_fail "Cannot access categories endpoint"
fi

###############################################################################
# Test 3: CORS Configuration
###############################################################################
print_section "Test 3: CORS Configuration"

CORS_HEADER=$(curl -s -H "Origin: http://localhost:8081" -I "${API_URL}/api" | grep -i "access-control-allow-origin" || echo "")

if [ -n "$CORS_HEADER" ]; then
    print_pass "CORS headers present"
    print_info "$CORS_HEADER"
else
    print_fail "CORS headers missing"
    print_warn "Frontend may not be able to access API from different port"
fi

###############################################################################
# Test 4: Category Update Endpoint
###############################################################################
print_section "Test 4: Category Update Functionality"

# Get first transaction ID (extract from JSON manually)
FIRST_TX_ID=$(echo "$TX_RESPONSE" | grep -o '"id":[0-9]*' | head -1 | grep -o '[0-9]*')

if [ -n "$FIRST_TX_ID" ]; then
    # Try to update category (set to null, then restore if needed)
    UPDATE_RESPONSE=$(curl -s -X PUT -H "Content-Type: application/json" \
        -d '{"category_id": null}' \
        "${API_URL}/api/transactions/${FIRST_TX_ID}/category")

    if echo "$UPDATE_RESPONSE" | grep -q '"success":true'; then
        print_pass "Category update endpoint works correctly"
    else
        print_fail "Category update failed"
        print_info "Response: $UPDATE_RESPONSE"
    fi
else
    print_warn "No transactions to test category update"
fi

###############################################################################
# Test 5: Frontend HTML Serving
###############################################################################
print_section "Test 5: Frontend HTML Serving"

if curl -s "${API_URL}/" | grep -q "Daily Expense Categorizer"; then
    print_pass "Frontend HTML served at root URL"
else
    print_fail "Frontend HTML not found at root URL"
fi

if curl -s "${API_URL}/daily_expense_categorizer.html" | grep -q "Daily Expense Categorizer"; then
    print_pass "Frontend HTML accessible via direct path"
else
    print_warn "Frontend HTML not accessible via direct path"
fi

###############################################################################
# Test 6: API Response Time
###############################################################################
print_section "Test 6: Performance"

RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' "${API_URL}/api" 2>/dev/null || echo "0")

if [ -n "$RESPONSE_TIME" ] && [ "$RESPONSE_TIME" != "0" ]; then
    # Convert to milliseconds (multiply by 1000, use awk if bc not available)
    RESPONSE_TIME_MS=$(awk "BEGIN {printf \"%.0f\", $RESPONSE_TIME * 1000}")

    if awk "BEGIN {exit !($RESPONSE_TIME < 1.0)}"; then
        print_pass "API response time: ${RESPONSE_TIME_MS}ms (excellent)"
    elif awk "BEGIN {exit !($RESPONSE_TIME < 5.0)}"; then
        print_pass "API response time: ${RESPONSE_TIME_MS}ms (acceptable)"
    else
        print_warn "API response time: ${RESPONSE_TIME_MS}ms (slow)"
    fi
else
    print_warn "Could not measure response time"
fi

###############################################################################
# Summary
###############################################################################
print_section "Summary"

TOTAL_TESTS=$((PASS_COUNT + FAIL_COUNT))
echo ""
echo -e "Total Tests: $TOTAL_TESTS"
echo -e "${GREEN}Passed: $PASS_COUNT${NC}"
echo -e "${RED}Failed: $FAIL_COUNT${NC}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}✓ All connectivity tests passed!${NC}"
    echo ""
    echo -e "${BLUE}API Server is working correctly.${NC}"
    echo ""
    echo "Access the application at:"
    echo "  ${API_URL}/"
    echo ""
    echo "If you're seeing 'API unavailable' errors in the browser:"
    echo "  1. Make sure you're accessing http://localhost:8080 (not file://)"
    echo "  2. Clear your browser cache (Ctrl+Shift+R)"
    echo "  3. Open browser DevTools (F12) and check Console/Network tabs"
    echo "  4. Verify 'preferApi' flag is true in browser console"
    exit 0
else
    echo -e "${RED}✗ Some tests failed${NC}"
    echo ""
    echo "Troubleshooting steps:"
    echo "  1. Make sure API server is running: python3 api_server.py"
    echo "  2. Check database connection in .env file"
    echo "  3. Verify MySQL server is running"
    echo "  4. Review logs in api_server.log"
    exit 1
fi
