#!/bin/bash
# Stop the Coder Agent

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f logs/coder_agent.pid ]; then
    echo "Coder Agent PID file not found"
    exit 1
fi

PID=$(cat logs/coder_agent.pid)

if ps -p $PID > /dev/null 2>&1; then
    echo "Stopping Coder Agent (PID: $PID)..."
    kill $PID
    rm logs/coder_agent.pid
    echo "Coder Agent stopped"
else
    echo "Coder Agent is not running (stale PID: $PID)"
    rm logs/coder_agent.pid
fi
