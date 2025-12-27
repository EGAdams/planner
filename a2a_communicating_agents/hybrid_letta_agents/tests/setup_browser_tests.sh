#!/bin/bash
# Browser Test Setup Script
# This script installs dependencies and prepares the environment for browser testing

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "Browser Test Setup"
echo "========================================"
echo ""

# Check Python version
echo "[1/5] Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "    Python version: $python_version"

# Install Python dependencies
echo ""
echo "[2/5] Installing Python dependencies..."
pip install -r "$SCRIPT_DIR/requirements-browser-testing.txt"

# Install Playwright browsers
echo ""
echo "[3/5] Installing Playwright browsers..."
playwright install chromium

# Verify installation
echo ""
echo "[4/5] Verifying installation..."
python3 -c "from playwright.sync_api import sync_playwright; print('    ✅ Playwright installed correctly')"
python3 -c "import pytest; print('    ✅ Pytest installed correctly')"

# Create run script
echo ""
echo "[5/5] Creating run script..."
cat > "$SCRIPT_DIR/run_browser_tests.sh" << 'RUNSCRIPT'
#!/bin/bash
# Quick test runner script

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo "Running Browser Tests"
echo "========================================"
echo ""

# Check if HTTP server is running
if ! curl -s http://localhost:9000 > /dev/null 2>&1; then
    echo "⚠️  WARNING: No HTTP server detected on port 9000"
    echo ""
    echo "Starting HTTP server in background..."
    cd "$PROJECT_DIR"
    python3 -m http.server 9000 > /tmp/browser_test_server.log 2>&1 &
    SERVER_PID=$!
    echo "    HTTP server started (PID: $SERVER_PID)"
    sleep 2
else
    echo "✅ HTTP server already running on port 9000"
    SERVER_PID=""
fi

# Check Letta server
echo ""
if curl -s http://localhost:8283/api/v1/agents/ > /dev/null 2>&1; then
    agent_count=$(curl -s http://localhost:8283/api/v1/agents/ | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "?")
    echo "✅ Letta server running on port 8283 ($agent_count agents)"
else
    echo "⚠️  WARNING: Letta server not responding on port 8283"
    echo "    Tests may fail if no agents available"
fi

echo ""
echo "========================================"
echo "Running Tests"
echo "========================================"
echo ""

# Run tests
cd "$SCRIPT_DIR"
pytest test_voice_agent_switching_browser.py -v -s "$@"

TEST_EXIT_CODE=$?

# Cleanup HTTP server if we started it
if [ -n "$SERVER_PID" ]; then
    echo ""
    echo "Stopping HTTP server (PID: $SERVER_PID)..."
    kill $SERVER_PID 2>/dev/null || true
fi

exit $TEST_EXIT_CODE
RUNSCRIPT

chmod +x "$SCRIPT_DIR/run_browser_tests.sh"

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "To run tests:"
echo "  cd $SCRIPT_DIR"
echo "  ./run_browser_tests.sh"
echo ""
echo "Or run specific tests:"
echo "  pytest test_voice_agent_switching_browser.py::test_voice_agent_selection_ui -v -s"
echo ""
echo "For more information, see:"
echo "  $SCRIPT_DIR/BROWSER_TESTING_README.md"
echo ""
