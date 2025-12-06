#!/bin/bash
# Start the Orchestrator Agent

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLANNER_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PLANNER_ROOT"

echo "Starting Orchestrator Agent..."

# Check if already running
if [ -f logs/orchestrator.pid ]; then
    PID=$(cat logs/orchestrator.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "Orchestrator Agent is already running (PID: $PID)"
        exit 1
    fi
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Start the agent in the background
cd a2a_communicating_agents/orchestrator_agent
nohup "$PLANNER_ROOT/.venv/bin/python" main.py >> "$PLANNER_ROOT/logs/orchestrator.log" 2>&1 &
PID=$!

# Save PID
echo $PID > "$PLANNER_ROOT/logs/orchestrator.pid"

echo "Orchestrator Agent started (PID: $PID)"
echo "Logs: $PLANNER_ROOT/logs/orchestrator.log"
