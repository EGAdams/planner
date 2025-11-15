#!/bin/bash
# Server Administration Dashboard Stop Script

LOG_FILE="/home/adamsl/planner/dashboard-startup.log"
echo "=== Dashboard Stop: $(date) ===" >> "$LOG_FILE"

# Function to check if service is already running and get PID
get_pid() {
    lsof -i :3000 -t
}

PID=$(get_pid)

if [ -n "$PID" ]; then
    echo "Stopping Admin Dashboard Server (PID: $PID)..." >> "$LOG_FILE"
    kill $PID
    sleep 2
    if ! kill -0 $PID > /dev/null 2>&1; then
        echo "✓ Admin Dashboard Server stopped successfully." >> "$LOG_FILE"
        echo "Server stopped."
    else
        echo "✗ Failed to stop server. Trying with kill -9." >> "$LOG_FILE"
        kill -9 $PID
        sleep 2
        if ! kill -0 $PID > /dev/null 2>&1; then
            echo "✓ Admin Dashboard Server stopped successfully with kill -9." >> "$LOG_FILE"
            echo "Server stopped."
        else
            echo "✗ Failed to stop server with kill -9." >> "$LOG_FILE"
            echo "Failed to stop server."
        fi
    fi
else
    echo "Admin Dashboard Server is not running." >> "$LOG_FILE"
    echo "Server is not running."
fi

echo "Dashboard stop script complete. Check $LOG_FILE for details."
