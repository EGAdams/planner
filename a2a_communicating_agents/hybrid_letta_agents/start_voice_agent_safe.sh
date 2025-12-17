#!/bin/bash
#
# Safe Voice Agent Starter - Prevents duplicate instances
#
# Features:
# - PID file locking
# - Lock file during startup
# - Automatic cleanup of stale locks
# - Prevents multiple simultaneous starts
#

set -e

PROJECT_DIR="/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents"
VENV_DIR="/home/adamsl/planner/.venv"
ENV_FILE="/home/adamsl/ottomator-agents/livekit-agent/.env"
PID_FILE="/tmp/letta_voice_agent.pid"
LOCK_FILE="/tmp/letta_voice_agent.lock"
LOG_FILE="/tmp/voice_agent.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🚀 Starting Letta Voice Agent (with duplicate prevention)..."
echo ""

# Check if already running
if ! "$PROJECT_DIR/check_agent_running.sh"; then
    echo -e "${RED}✗ Voice agent already running or locked${NC}"
    echo ""
    echo "Options:"
    echo "  1. Wait 30 seconds for current startup to complete"
    echo "  2. Force restart: ./restart_voice_system.sh"
    echo "  3. Check status: ps aux | grep letta_voice_agent"
    exit 1
fi

# Create lock file (prevents simultaneous starts)
echo $$ > "$LOCK_FILE"
trap "rm -f $LOCK_FILE" EXIT

echo -e "${GREEN}✓ No duplicates detected, proceeding with startup${NC}"
echo ""

# Load environment
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}✗ Environment file not found: $ENV_FILE${NC}"
    exit 1
fi

source "$ENV_FILE"

# Start voice agent
cd "$PROJECT_DIR"
echo "Starting voice agent in DEV mode..."
nohup "$VENV_DIR/bin/python3" letta_voice_agent.py dev > "$LOG_FILE" 2>&1 &
AGENT_PID=$!

# Save PID
echo "$AGENT_PID" > "$PID_FILE"
echo -e "${GREEN}✓ Voice agent started (PID: $AGENT_PID)${NC}"
echo "  PID file: $PID_FILE"
echo "  Log file: $LOG_FILE"

# Wait a moment to verify it's running
sleep 3

if ps -p "$AGENT_PID" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Voice agent is running successfully${NC}"
    echo ""
    echo "Monitor logs: tail -f $LOG_FILE"
    echo "Check status: ps -p $AGENT_PID"
    echo "Stop: kill $AGENT_PID && rm -f $PID_FILE"
else
    echo -e "${RED}✗ Voice agent failed to start${NC}"
    echo "Check logs: tail $LOG_FILE"
    rm -f "$PID_FILE"
    exit 1
fi

# Lock file will be automatically removed by trap on exit
