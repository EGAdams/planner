#!/bin/bash
# A2A Agent System Shutdown Script
# Gracefully stops all A2A agents and services

PLANNER_ROOT="/home/adamsl/planner"
LOG_DIR="$PLANNER_ROOT/logs"
PIDS_FILE="$LOG_DIR/a2a_system.pids"

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

log_info "Stopping A2A Agent System..."

# Check if PID file exists
if [ ! -f "$PIDS_FILE" ]; then
    log_warn "No PID file found at $PIDS_FILE"
    log_info "Attempting to stop services by port..."
    
    # Stop dashboard (port 3000)
    if lsof -i :3000 -t > /dev/null 2>&1; then
        log_info "Stopping dashboard (port 3000)..."
        kill $(lsof -i :3000 -t) 2>/dev/null
    fi
    
    # Stop Letta (port 8283)
    if lsof -i :8283 -t > /dev/null 2>&1; then
        log_info "Stopping Letta server (port 8283)..."
        kill $(lsof -i :8283 -t) 2>/dev/null
    fi
    
    log_info "Done."
    exit 0
fi

# Read PIDs and stop processes
while IFS=: read -r name pid; do
    if [ -n "$pid" ]; then
        if kill -0 "$pid" 2>/dev/null; then
            log_info "Stopping $name (PID: $pid)..."
            kill "$pid" 2>/dev/null
            
            # Wait for graceful shutdown (max 5 seconds)
            for i in {1..5}; do
                if ! kill -0 "$pid" 2>/dev/null; then
                    log_info "✓ $name stopped"
                    break
                fi
                sleep 1
            done
            
            # Force kill if still running
            if kill -0 "$pid" 2>/dev/null; then
                log_warn "Force stopping $name..."
                kill -9 "$pid" 2>/dev/null
            fi
        else
            log_warn "$name (PID: $pid) not running"
        fi
    fi
done < "$PIDS_FILE"

# Clean up PID file
rm -f "$PIDS_FILE"

log_info "All A2A services stopped."
