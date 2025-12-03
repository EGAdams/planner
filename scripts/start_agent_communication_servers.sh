#!/bin/bash
# Start Agent Communication Servers
# Launches services needed for A2A agent communication infrastructure
# Usage: ./start_agent_communication_servers.sh

set -e

# Resolve PLANNER_ROOT - go up one level from scripts/
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLANNER_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="$PLANNER_ROOT/logs"
PID_FILE="$LOG_DIR/a2a_system.pids"

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR"

# Color output helpers
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Starting Agent Communication Servers ===${NC}"
echo "PLANNER_ROOT: $PLANNER_ROOT"
echo "LOG_DIR: $LOG_DIR"
echo ""

# Function to check if port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 || ss -ltn | grep -q ":$port " 2>/dev/null; then
        return 0  # Port is in use
    else
        return 1  # Port is free
    fi
}

# Function to start a background process and log its PID
start_service() {
    local name=$1
    local command=$2
    local log_file=$3
    local pid_var=$4

    echo -e "${GREEN}[STARTING]${NC} $name"
    echo "  Command: $command"
    echo "  Log: $log_file"

    # Start the process in background and capture PID
    eval "$command > '$log_file' 2>&1 &"
    local pid=$!

    # Store PID in variable if provided
    if [ -n "$pid_var" ]; then
        eval "$pid_var=$pid"
    fi

    # Give it a moment to start
    sleep 1

    # Check if process is still running
    if ps -p $pid > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Started (PID: $pid)"
        echo "$pid" >> "$PID_FILE"
        return 0
    else
        echo -e "  ${RED}✗${NC} Failed to start (check log: $log_file)"
        return 1
    fi
}

# Initialize PID file
> "$PID_FILE"

# 1. Check PostgreSQL connectivity (warn if unavailable, continue with SQLite fallback)
echo -e "\n${YELLOW}[DATABASE]${NC} Checking PostgreSQL connectivity..."

# Try to connect to PostgreSQL on default port
if nc -z localhost 5432 2>/dev/null; then
    echo -e "  ${GREEN}✓${NC} PostgreSQL is available on port 5432"
    DB_STATUS="postgresql"
else
    echo -e "  ${YELLOW}⚠${NC}  PostgreSQL not available - Letta will use SQLite fallback (~/.letta/letta.db)"
    DB_STATUS="sqlite"
fi

# 2. Start Letta Server (if not already running)
LETTA_PORT=8283
echo -e "\n${YELLOW}[LETTA]${NC} Checking Letta server on port $LETTA_PORT..."

if check_port $LETTA_PORT; then
    LETTA_PID=$(lsof -ti:$LETTA_PORT 2>/dev/null || ss -lptn | grep ":$LETTA_PORT " | awk '{print $6}' | cut -d'=' -f2 | cut -d',' -f1)
    echo -e "  ${YELLOW}⚠${NC}  Letta server already running on port $LETTA_PORT (PID: $LETTA_PID)"
    echo -e "  Skipping Letta startup"
else
    # Find letta executable or use python -m letta (prefer venv)
    if [ -f "$PLANNER_ROOT/.venv/bin/letta" ]; then
        LETTA_CMD="$PLANNER_ROOT/.venv/bin/letta server"
    elif command -v letta &> /dev/null; then
        LETTA_CMD="letta server"
    elif [ -f "$PLANNER_ROOT/.venv/bin/python" ]; then
        LETTA_CMD="$PLANNER_ROOT/.venv/bin/python -m letta server"
    else
        LETTA_CMD="python3 -m letta server"
    fi

    start_service \
        "Letta Server (Memory Backend)" \
        "cd '$PLANNER_ROOT' && $LETTA_CMD" \
        "$LOG_DIR/letta.log" \
        "LETTA_PID"

    # Wait a bit longer for Letta to initialize
    echo "  Waiting for Letta to initialize..."
    sleep 3

    # Verify Letta API is responding
    if curl -s http://localhost:$LETTA_PORT/health > /dev/null 2>&1 || curl -s http://localhost:$LETTA_PORT/v1/health > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} Letta API is responding"
    else
        echo -e "  ${YELLOW}⚠${NC}  Letta API not responding yet (may still be starting up)"
    fi
fi

# 3. Check for WebSocket server implementation
echo -e "\n${YELLOW}[WEBSOCKET]${NC} Checking WebSocket transport server..."

WS_SERVER_FILE="$PLANNER_ROOT/a2a_communicating_agents/agent_messaging/websocket_server.py"

if [ -f "$WS_SERVER_FILE" ]; then
    # WebSocket server exists - try to start it
    WS_PORT=8765  # Default WebSocket port

    if check_port $WS_PORT; then
        echo -e "  ${YELLOW}⚠${NC}  WebSocket server already running on port $WS_PORT"
    else
        start_service \
            "WebSocket Transport Server" \
            "cd '$PLANNER_ROOT/a2a_communicating_agents/agent_messaging' && python3 websocket_server.py" \
            "$LOG_DIR/websocket.log" \
            "WS_PID"
    fi
else
    echo -e "  ${YELLOW}⚠${NC}  WebSocket server not yet implemented (websocket_server.py not found)"
    echo -e "  Note: WebSocket transport currently uses mock server for testing"
    echo -e "  Real implementation planned for Phase 2 (see a2a_project_roadmap.md)"
fi

# 4. Start A2A Collective Hub (Python-based coordination)
echo -e "\n${YELLOW}[A2A HUB]${NC} Starting A2A Collective Hub..."

A2A_SCRIPT="$PLANNER_ROOT/a2a_communicating_agents/agent_messaging/run_collective.py"

if [ -f "$A2A_SCRIPT" ]; then
    start_service \
        "A2A Collective Hub" \
        "cd '$PLANNER_ROOT/a2a_communicating_agents/agent_messaging' && python3 run_collective.py" \
        "$LOG_DIR/a2a_collective.log" \
        "A2A_PID"
else
    echo -e "  ${YELLOW}⚠${NC}  A2A collective script not found: $A2A_SCRIPT"
    echo -e "  A2A hub may need to be started manually"
fi

# Summary
echo -e "\n${GREEN}=== Startup Complete ===${NC}"
echo ""
echo "Services Status:"
echo "  - Letta Server: http://localhost:$LETTA_PORT (${DB_STATUS})"
echo "  - WebSocket: Not yet implemented (mock mode)"
echo "  - A2A Hub: Running (see logs/a2a_collective.log)"
echo ""
echo "Process IDs saved to: $PID_FILE"
echo "Logs directory: $LOG_DIR"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  1. Verify services: ./scripts/verify_agent_services.sh"
echo "  2. View Letta logs: tail -f $LOG_DIR/letta.log"
echo "  3. Test A2A communication: cd a2a_communicating_agents/agent_messaging && python3 run_collective.py"
echo ""
echo -e "${GREEN}To stop all services: ./scripts/stop_agent_communication_servers.sh${NC}"
