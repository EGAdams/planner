#!/bin/bash

# Simple Receipt Scanner Startup Script
# Starts the API server for the receipt scanning system

set -e

# Configuration
PARENT_DIR="/home/adamsl/planner/nonprofit_finance_db"
PYTHON="$PARENT_DIR/venv/bin/python"
API_SERVER="receipt_scanning_tools/server_tools/api_server.py"
PORT=${PORT:-8080}

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Starting Receipt Scanner...${NC}"
echo ""

# Check if Python exists
if [ ! -f "$PYTHON" ]; then
    echo -e "${YELLOW}Virtual environment not found at $PYTHON${NC}"
    echo "Using system Python instead..."
    PYTHON="python3"
fi

# Change to parent directory and start server
cd "$PARENT_DIR"

echo -e "${GREEN}API Server starting on port $PORT${NC}"
echo -e "${GREEN}Receipt Scanner: http://localhost:$PORT/receipt-scanner${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

# Start the server
exec "$PYTHON" "$API_SERVER"
