#!/bin/bash
# Stop the Orchestrator Agent

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLANNER_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$PLANNER_ROOT"

# Check for PID file in logs directory
if [ -f logs/orchestrator.pid ]; then
    PID=$(cat logs/orchestrator.pid)

    if ps -p $PID > /dev/null 2>&1; then
        echo "Stopping Orchestrator Agent (PID: $PID)..."
        kill $PID
        rm logs/orchestrator.pid
        echo "Orchestrator Agent stopped"
    else
        echo "Orchestrator Agent is not running (stale PID: $PID)"
        rm logs/orchestrator.pid
    fi
elif [ -f logs/a2a_system.pids ]; then
    # Check system-wide PIDs file
    if grep -q "ORCHESTRATOR_PID" logs/a2a_system.pids; then
        PID=$(grep "ORCHESTRATOR_PID" logs/a2a_system.pids | cut -d'=' -f2)
        if ps -p $PID > /dev/null 2>&1; then
            echo "Stopping Orchestrator Agent (PID: $PID from system PIDs)..."
            kill $PID
            echo "Orchestrator Agent stopped"
        else
            echo "Orchestrator Agent is not running (stale PID: $PID)"
        fi
    else
        echo "Orchestrator PID not found in system PIDs file"
    fi
else
    # Fallback: try to kill by process name
    echo "No PID file found, attempting to stop by process name..."
    pkill -f "orchestrator_agent/main.py"
    if [ $? -eq 0 ]; then
        echo "Orchestrator Agent stopped (by process name)"
    else
        echo "No orchestrator agent process found"
    fi
fi
