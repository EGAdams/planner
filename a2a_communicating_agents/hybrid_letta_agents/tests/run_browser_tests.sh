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
