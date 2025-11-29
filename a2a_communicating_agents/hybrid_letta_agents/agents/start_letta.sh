#!/bin/bash
# A2A Agent System Startup Script
# Starts Letta Server, Orchestrator Agent, Dashboard Ops Agent, and System Admin Dashboard
# Uses Google's Agent-to-Agent (A2A) Protocol with Agent Cards

set -e  # Exit on error

PLANNER_ROOT="/home/adamsl/planner"
LOG_DIR="$PLANNER_ROOT/logs"
PIDS_FILE="$LOG_DIR/a2a_system.pids"

# Activate virtual environment
source "$PLANNER_ROOT/.venv/bin/activate"

# Create logs directory
mkdir -p "$LOG_DIR"

# Color output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[A2A System]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[A2A System]${NC} $1"
}

log_error() {
    echo -e "${RED}[A2A System]${NC} $1"
}

# Function to check if a process is running on a port
is_port_running() {
    local port=$1
    lsof -i :$port -t > /dev/null 2>&1
    return $?
}

# Function to check if a PID is running
is_pid_running() {
    local pid=$1
    kill -0 "$pid" 2>/dev/null
    return $?
}

# Clean up old PID file
rm -f "$PIDS_FILE"
touch "$PIDS_FILE"

log_info "Starting A2A Agent System..."
log_info "Agent Cards (agent.json) location: $PLANNER_ROOT/<agent>/"
echo ""

# ========================================
# 1. Start Letta Server (Unified Memory)
# ========================================
log_info "Step 1/4: Starting Letta Server (Unified Memory Backend)..."

if is_port_running 8283; then
    log_warn "Letta server already running on port 8283"
else
    cd "$PLANNER_ROOT"
    nohup letta server > "$LOG_DIR/letta.log" 2>&1 &
    LETTA_PID=$!
    echo "letta:$LETTA_PID" >> "$PIDS_FILE"
    log_info "Letta server started (PID: $LETTA_PID)"
    sleep 3
fi

# Verify Letta is running
if is_port_running 8283; then
    log_info "✓ Letta server is running on port 8283"
else
    log_error "✗ Letta server failed to start. Check $LOG_DIR/letta.log"
fi
echo ""

