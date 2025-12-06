#!/bin/bash
# Stop the Tester Agent

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f logs/tester_agent.pid ]; then
    echo "Tester Agent PID file not found"
    exit 1
fi

PID=$(cat logs/tester_agent.pid)

if ps -p $PID > /dev/null 2>&1; then
    echo "Stopping Tester Agent (PID: $PID)..."
    kill $PID
    rm logs/tester_agent.pid
    echo "Tester Agent stopped"
else
    echo "Tester Agent is not running (stale PID: $PID)"
    rm logs/tester_agent.pid
fi
