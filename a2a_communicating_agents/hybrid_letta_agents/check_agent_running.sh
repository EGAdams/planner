#!/bin/bash
#
# Check if voice agent is already running
# Returns: 0 if safe to start (no agent running), 1 if agent already running
#
# Usage: ./check_agent_running.sh || exit 1

PID_FILE="/tmp/letta_voice_agent.pid"
LOCK_FILE="/tmp/letta_voice_agent.lock"

# Check for running processes
RUNNING_COUNT=$(ps aux | grep "letta_voice_agent.py dev" | grep -v grep | grep -v bash | wc -l)

if [ "$RUNNING_COUNT" -gt 0 ]; then
    echo "❌ ERROR: $RUNNING_COUNT voice agent(s) already running!"
    ps aux | grep "letta_voice_agent.py dev" | grep -v grep | grep -v bash
    echo ""
    echo "To restart: ./restart_voice_system.sh"
    exit 1
fi

# Check for stale PID file
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "❌ ERROR: Voice agent already running (PID: $OLD_PID)"
        echo "PID file: $PID_FILE"
        exit 1
    else
        echo "⚠️  Removing stale PID file (process $OLD_PID not found)"
        rm -f "$PID_FILE"
    fi
fi

# Check for lock file
if [ -f "$LOCK_FILE" ]; then
    LOCK_AGE=$(($(date +%s) - $(stat -c %Y "$LOCK_FILE" 2>/dev/null || stat -f %m "$LOCK_FILE")))
    if [ "$LOCK_AGE" -lt 30 ]; then
        echo "❌ ERROR: Another voice agent is starting right now (lock file age: ${LOCK_AGE}s)"
        echo "Lock file: $LOCK_FILE"
        exit 1
    else
        echo "⚠️  Removing stale lock file (age: ${LOCK_AGE}s)"
        rm -f "$LOCK_FILE"
    fi
fi

echo "✅ Safe to start voice agent (no duplicates detected)"
exit 0
