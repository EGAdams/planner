#!/bin/bash
# Stop Agent Communication Servers
# Gracefully shuts down A2A infrastructure services
# Usage: ./stop_agent_communication_servers.sh

set -e

# Resolve PLANNER_ROOT - go up one level from scripts/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLANNER_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PLANNER_ROOT/logs"
PID_FILE="$LOG_DIR/a2a_system.pids"

# Color output helpers
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Stopping Agent Communication Servers ===${NC}"
echo "PLANNER_ROOT: $PLANNER_ROOT"
echo "LOG_DIR: $LOG_DIR"
echo ""

# Function to stop process by PID with graceful shutdown
stop_process() {
    local pid=$1
    local name=$2
    local timeout=${3:-10}  # Default 10 second timeout

    if ! ps -p $pid > /dev/null 2>&1; then
        echo -e "  ${YELLOW}⚠${NC}  Process $pid ($name) not running"
        return 0
    fi

    echo -e "${YELLOW}[STOPPING]${NC} $name (PID: $pid)"

    # Try graceful SIGTERM first
    kill -TERM $pid 2>/dev/null || true

    # Wait for process to exit
    local count=0
    while ps -p $pid > /dev/null 2>&1 && [ $count -lt $timeout ]; do
        sleep 1
        count=$((count + 1))
    done

    # If still running, force kill
    if ps -p $pid > /dev/null 2>&1; then
        echo -e "  ${RED}⚠${NC}  Process did not stop gracefully, forcing kill..."
        kill -KILL $pid 2>/dev/null || true
        sleep 1
    fi

    # Final check
    if ps -p $pid > /dev/null 2>&1; then
        echo -e "  ${RED}✗${NC} Failed to stop process $pid"
        return 1
    else
        echo -e "  ${GREEN}✓${NC} Stopped successfully"
        return 0
    fi
}

# Function to stop process by port
stop_by_port() {
    local port=$1
    local name=$2

    echo -e "${YELLOW}[CHECKING]${NC} Looking for $name on port $port..."

    # Try lsof first (more reliable)
    local pid=$(lsof -ti:$port 2>/dev/null)

    # Fallback to ss if lsof didn't find anything
    if [ -z "$pid" ]; then
        pid=$(ss -lptn 2>/dev/null | grep ":$port " | awk '{print $6}' | cut -d'=' -f2 | cut -d',' -f1 | head -n1)
    fi

    if [ -n "$pid" ]; then
        stop_process "$pid" "$name on port $port" 10
    else
        echo -e "  ${YELLOW}⚠${NC}  No process found on port $port"
    fi
}

# 1. Stop processes from PID file
if [ -f "$PID_FILE" ]; then
    echo -e "${YELLOW}[PID FILE]${NC} Stopping processes from $PID_FILE..."
    echo ""

    while read -r pid; do
        # Skip empty lines
        if [ -z "$pid" ]; then
            continue
        fi

        # Get process name if possible
        if ps -p $pid > /dev/null 2>&1; then
            proc_name=$(ps -p $pid -o comm= 2>/dev/null || echo "unknown")
            stop_process "$pid" "$proc_name"
        else
            echo -e "  ${YELLOW}⚠${NC}  PID $pid no longer running"
        fi
    done < "$PID_FILE"

    # Remove PID file
    rm -f "$PID_FILE"
    echo -e "  ${GREEN}✓${NC} Removed PID file"
else
    echo -e "${YELLOW}⚠${NC}  PID file not found: $PID_FILE"
    echo "  Will attempt to stop services by port..."
fi

echo ""

# 2. Stop Letta server (by port as backup)
stop_by_port 8283 "Letta Server"

# 3. Stop WebSocket server if running
stop_by_port 8765 "WebSocket Server"

# 4. Stop any remaining A2A collective processes
echo -e "\n${YELLOW}[CLEANUP]${NC} Checking for remaining A2A processes..."

# Look for run_collective.py processes
COLLECTIVE_PIDS=$(pgrep -f "run_collective.py" 2>/dev/null || true)
if [ -n "$COLLECTIVE_PIDS" ]; then
    for pid in $COLLECTIVE_PIDS; do
        stop_process "$pid" "A2A Collective Hub"
    done
else
    echo -e "  ${GREEN}✓${NC} No A2A collective processes found"
fi

# Look for websocket_server.py processes
WS_PIDS=$(pgrep -f "websocket_server.py" 2>/dev/null || true)
if [ -n "$WS_PIDS" ]; then
    for pid in $WS_PIDS; do
        stop_process "$pid" "WebSocket Server"
    done
else
    echo -e "  ${GREEN}✓${NC} No WebSocket server processes found"
fi

# 5. Final verification
echo -e "\n${GREEN}=== Shutdown Complete ===${NC}"
echo ""
echo "Verification:"

# Check Letta port
if lsof -Pi :8283 -sTCP:LISTEN -t >/dev/null 2>&1 || ss -ltn | grep -q ":8283 " 2>/dev/null; then
    echo -e "  ${RED}✗${NC} Letta server (port 8283) still running"
else
    echo -e "  ${GREEN}✓${NC} Letta server stopped"
fi

# Check WebSocket port
if lsof -Pi :8765 -sTCP:LISTEN -t >/dev/null 2>&1 || ss -ltn | grep -q ":8765 " 2>/dev/null; then
    echo -e "  ${RED}✗${NC} WebSocket server (port 8765) still running"
else
    echo -e "  ${GREEN}✓${NC} WebSocket server stopped"
fi

# Check for any remaining Python agent processes
REMAINING=$(pgrep -f "agent_messaging.*\.py" 2>/dev/null | wc -l)
if [ "$REMAINING" -gt 0 ]; then
    echo -e "  ${YELLOW}⚠${NC}  $REMAINING agent messaging Python processes still running"
    echo "  Use 'pkill -f agent_messaging' to force stop if needed"
else
    echo -e "  ${GREEN}✓${NC} All agent messaging processes stopped"
fi

echo ""
echo -e "${GREEN}All agent communication services have been stopped.${NC}"
echo ""
echo "Logs preserved in: $LOG_DIR"
echo "To restart: ./scripts/start_agent_communication_servers.sh"
