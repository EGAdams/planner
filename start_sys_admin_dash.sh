#!/bin/bash
# Server Administration Dashboard Auto-Start Script
# Consolidated single-server architecture on port 3000
# Optimized for WSL2 environment

LOG_FILE="/home/adamsl/planner/dashboard-startup.log"
echo "=== Dashboard Startup: $(date) ===" >> "$LOG_FILE"

# Function to check if service is already running
is_running() {
    local port=$1
    lsof -i :$port -t > /dev/null 2>&1
    return $?
}

# Start Admin Dashboard Server (consolidated on port 3000)
if is_running 3000; then
    echo "Admin Dashboard Server already running on port 3000" >> "$LOG_FILE"
else
    echo "Starting Admin Dashboard Server on port 3000..." >> "$LOG_FILE"
    cd /home/adamsl/planner/dashboard
    # Explicitly set ADMIN_PORT=3000 to override any system environment variable
    env ADMIN_PORT=3000 nohup npm start >> "$LOG_FILE" 2>&1 &
    sleep 3
fi

# Verify service is running
echo "Verification:" >> "$LOG_FILE"
if is_running 3000; then
    echo "✓ Admin Dashboard Server is running on port 3000" >> "$LOG_FILE"
else
    echo "✗ Admin Dashboard Server failed to start" >> "$LOG_FILE"
fi

echo "Dashboard startup complete. Check $LOG_FILE for details."
