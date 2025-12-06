#!/bin/bash
#
# Stop WebSocket Message Board Server
#

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/../logs"
PID_FILE="$LOG_DIR/websocket_server.pid"

if [ ! -f "$PID_FILE" ]; then
    echo "⚠️  WebSocket server PID file not found"
    exit 0
fi

PID=$(cat "$PID_FILE")

if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "⚠️  WebSocket server not running"
    rm "$PID_FILE"
    exit 0
fi

echo "🛑 Stopping WebSocket server (PID: $PID)..."
kill "$PID"

# Wait for graceful shutdown
for i in {1..5}; do
    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ WebSocket server stopped"
        rm "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# Force kill if still running
if ps -p "$PID" > /dev/null 2>&1; then
    echo "  Force stopping..."
    kill -9 "$PID"
    sleep 1
fi

if ! ps -p "$PID" > /dev/null 2>&1; then
    echo "✅ WebSocket server stopped"
    rm "$PID_FILE"
    exit 0
else
    echo "❌ Failed to stop WebSocket server"
    exit 1
fi
