#!/bin/bash
# Interactive Voice Test Runner
# This script runs the interactive voice test with manual microphone control

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Determine the correct Python to use
# Priority: 1) Virtual env at /home/adamsl/planner/.venv, 2) System python3
if [ -f "/home/adamsl/planner/.venv/bin/python3" ]; then
    PYTHON="/home/adamsl/planner/.venv/bin/python3"
    echo "ℹ️  Using virtual environment: /home/adamsl/planner/.venv"
else
    PYTHON="python3"
    echo "⚠️  Virtual environment not found, using system python3"
fi

echo "========================================"
echo "Interactive Voice Test - Manual Control"
echo "========================================"
echo ""

# Check if HTTP server is running
echo "[1/4] Checking HTTP server..."
if ! curl -s http://localhost:9000 > /dev/null 2>&1; then
    echo "⚠️  WARNING: No HTTP server detected on port 9000"
    echo ""
    echo "Starting HTTP server in background..."
    cd "$PROJECT_DIR"
    $PYTHON -m http.server 9000 > /tmp/voice_test_http_server.log 2>&1 &
    SERVER_PID=$!
    echo "    HTTP server started (PID: $SERVER_PID)"
    sleep 2
else
    echo "✅ HTTP server running on port 9000"
    SERVER_PID=""
fi

# Check Letta server
echo ""
echo "[2/4] Checking Letta server..."
if curl -s http://localhost:8283/api/v1/agents/ > /dev/null 2>&1; then
    agent_count=$(curl -s http://localhost:8283/api/v1/agents/ | $PYTHON -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null || echo "?")
    echo "✅ Letta server running on port 8283 ($agent_count agents)"
else
    echo "⚠️  WARNING: Letta server not responding on port 8283"
    echo "    Tests may fail if no agents available"
fi

# Check LiveKit server
echo ""
echo "[3/4] Checking LiveKit server..."
if curl -s http://localhost:7880 > /dev/null 2>&1; then
    echo "✅ LiveKit server running on port 7880"
else
    echo "⚠️  WARNING: LiveKit server not responding on port 7880"
    echo "    Voice connections will fail"
fi

# Check voice agent backend
echo ""
echo "[4/4] Checking voice agent backend..."
if ps aux | grep -v grep | grep letta_voice_agent > /dev/null 2>&1; then
    echo "✅ Voice agent backend running"
else
    echo "⚠️  WARNING: Voice agent backend not running"
    echo "    Agent will not join the room (expected if testing UI only)"
fi

echo ""
echo "========================================"
echo "Starting Interactive Test"
echo "========================================"
echo ""

# Determine which device mode to use
# Default to fake device (safer for headless/CI)
DEVICE_ARG="--fake-device"
MODE_ARG="--non-interactive"

# Check arguments
for arg in "$@"; do
    if [ "$arg" = "--real-device" ]; then
        DEVICE_ARG="--real-device"
        echo "⚠️  Using REAL microphone device (make sure it's connected)"
    elif [ "$arg" = "--interactive" ]; then
        MODE_ARG=""
        echo "ℹ️  Running in INTERACTIVE mode (will wait for user input)"
    fi
done

# Default messages
if [ "$DEVICE_ARG" = "--fake-device" ]; then
    echo "ℹ️  Using FAKE audio device (pass --real-device to use real mic)"
fi

if [ "$MODE_ARG" = "--non-interactive" ]; then
    echo "ℹ️  Running in NON-INTERACTIVE mode (auto-continue, pass --interactive to wait for input)"
fi

echo ""

# Run the test
cd "$SCRIPT_DIR"
$PYTHON test_interactive_voice_manual.py $DEVICE_ARG $MODE_ARG

TEST_EXIT_CODE=$?

# Cleanup HTTP server if we started it
if [ -n "$SERVER_PID" ]; then
    echo ""
    echo "Stopping HTTP server (PID: $SERVER_PID)..."
    kill $SERVER_PID 2>/dev/null || true
fi

exit $TEST_EXIT_CODE
