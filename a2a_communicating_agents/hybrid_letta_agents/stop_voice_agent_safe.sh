#!/bin/bash
#
# Safe Voice Agent Stopper - Cleans up PID and lock files
#

PID_FILE="/tmp/letta_voice_agent.pid"
LOCK_FILE="/tmp/letta_voice_agent.lock"

echo "🛑 Stopping Letta Voice Agent..."
echo ""

# Check PID file first
if [ -f "$PID_FILE" ]; then
    AGENT_PID=$(cat "$PID_FILE")
    echo "Found PID file: $AGENT_PID"

    if ps -p "$AGENT_PID" > /dev/null 2>&1; then
        echo "Killing process $AGENT_PID..."
        kill "$AGENT_PID"

        # Wait for graceful shutdown
        sleep 2

        if ps -p "$AGENT_PID" > /dev/null 2>&1; then
            echo "⚠️  Graceful shutdown failed, force killing..."
            kill -9 "$AGENT_PID"
            sleep 1
        fi

        echo "✅ Process $AGENT_PID stopped"
    else
        echo "⚠️  Process $AGENT_PID not found (already stopped)"
    fi

    # Remove PID file
    rm -f "$PID_FILE"
    echo "✅ Removed PID file"
else
    echo "No PID file found, checking for running processes..."
fi

# Kill any remaining voice agent processes
REMAINING=$(ps aux | grep "letta_voice_agent.py dev" | grep -v grep | grep -v bash | wc -l)
if [ "$REMAINING" -gt 0 ]; then
    echo "⚠️  Found $REMAINING running voice agent(s), killing..."
    pkill -f "letta_voice_agent.py"
    sleep 1

    # Force kill if still running
    if ps aux | grep "letta_voice_agent.py dev" | grep -v grep > /dev/null; then
        echo "Force killing remaining processes..."
        pkill -9 -f "letta_voice_agent.py"
    fi
    echo "✅ All voice agents stopped"
fi

# Clean up lock file
if [ -f "$LOCK_FILE" ]; then
    rm -f "$LOCK_FILE"
    echo "✅ Removed lock file"
fi

echo ""
echo "✅ Voice agent stopped and cleaned up"
echo "   • PID file removed"
echo "   • Lock file removed"
echo "   • All processes terminated"
