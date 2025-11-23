#!/bin/bash
# A2A Agent System Startup Script
# Starts Letta Server, Orchestrator Agent, Dashboard Ops Agent, and System Admin Dashboard
# Uses Google's Agent-to-Agent (A2A) Protocol with Agent Cards

set -e  # Exit on error

PLANNER_ROOT="/home/adamsl/planner"
LOG_DIR="$PLANNER_ROOT/logs"
PIDS_FILE="$LOG_DIR/a2a_system.pids"

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

# ========================================
# 2. Start Orchestrator Agent
# ========================================
log_info "Step 2/4: Starting Orchestrator Agent..."
log_info "Agent Card: $PLANNER_ROOT/orchestrator_agent/agent.json"

cd "$PLANNER_ROOT/orchestrator_agent"
nohup python main.py > "$LOG_DIR/orchestrator.log" 2>&1 &
ORCHESTRATOR_PID=$!
echo "orchestrator:$ORCHESTRATOR_PID" >> "$PIDS_FILE"
log_info "Orchestrator agent started (PID: $ORCHESTRATOR_PID)"
log_info "  - Capabilities: route_request, discover_agents"
log_info "  - Topics: orchestrator, general"
sleep 2
echo ""

# ========================================
# 3. Start Dashboard Ops Agent
# ========================================
log_info "Step 3/4: Starting Dashboard Ops Agent..."
log_info "Agent Card: $PLANNER_ROOT/dashboard_ops_agent/agent.json"

cd "$PLANNER_ROOT/dashboard_ops_agent"
nohup python main.py > "$LOG_DIR/dashboard_ops.log" 2>&1 &
DASHBOARD_OPS_PID=$!
echo "dashboard_ops:$DASHBOARD_OPS_PID" >> "$PIDS_FILE"
log_info "Dashboard Ops agent started (PID: $DASHBOARD_OPS_PID)"
log_info "  - Capabilities: check_status, start_server, start_test_browser"
log_info "  - Topics: ops, dashboard, maintenance"
sleep 2
echo ""

# ========================================
# 4. Start System Admin Dashboard
# ========================================
log_info "Step 4/4: Starting System Admin Dashboard..."

if is_port_running 3000; then
    log_warn "Dashboard already running on port 3000"
else
    cd "$PLANNER_ROOT/dashboard"
    env ADMIN_PORT=3000 nohup npm start > "$LOG_DIR/dashboard.log" 2>&1 &
    DASHBOARD_PID=$!
    echo "dashboard:$DASHBOARD_PID" >> "$PIDS_FILE"
    log_info "Dashboard started (PID: $DASHBOARD_PID)"
    sleep 5
fi

# Verify Dashboard is running
if is_port_running 3000; then
    log_info "✓ Dashboard is running on port 3000"
else
    log_error "✗ Dashboard failed to start. Check $LOG_DIR/dashboard.log"
fi
echo ""

# ========================================
# Summary
# ========================================
log_info "========================================="
log_info "A2A Agent System Status:"
log_info "========================================="
log_info "Letta Server:       http://localhost:8283"
log_info "System Dashboard:   http://localhost:3000"
log_info ""
log_info "Active A2A Agents:"
log_info "  - orchestrator-agent    (PID: $ORCHESTRATOR_PID)"
log_info "  - dashboard-ops-agent   (PID: $DASHBOARD_OPS_PID)"
log_info ""
log_info "Logs: $LOG_DIR/"
log_info "PIDs: $PIDS_FILE"
log_info ""
log_info "To stop all services, run: ./stop_a2a_system.sh"
log_info "========================================="
echo ""
log_info "Opening dashboard in browser..."
sleep 2

# Open browser (if available)
if command -v xdg-open > /dev/null; then
    xdg-open http://localhost:3000 2>/dev/null &
elif command -v google-chrome > /dev/null; then
    google-chrome http://localhost:3000 2>/dev/null &
fi

log_info "A2A Agent System startup complete!"
