#!/bin/bash
# Health check script for JWT token validity
# Automatically regenerates token if expired or expiring soon

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if verify_token.py exists
if [ ! -f "./verify_token.py" ]; then
    echo "ERROR: verify_token.py not found"
    exit 2
fi

# Run token verification
echo "Checking token validity..."
if ./verify_token.py 2>&1 | grep -q "EXPIRED"; then
    echo "❌ Token is EXPIRED! Regenerating..."
    ./update_voice_token.sh

    # Restart CORS proxy if running
    if pgrep -f cors_proxy_server > /dev/null; then
        echo "Restarting CORS proxy server..."
        pkill -f cors_proxy_server
        sleep 1
        /home/adamsl/planner/.venv/bin/python3 cors_proxy_server.py > /tmp/cors_proxy.log 2>&1 &
        echo "CORS proxy restarted"
    fi

    echo "✓ Token regenerated successfully"
    exit 0
elif ./verify_token.py 2>&1 | grep -q "VALID"; then
    # Extract hours remaining - look for pattern "expires in X.X hours"
    HOURS=$(./verify_token.py 2>&1 | grep "expires in" | sed -n 's/.*expires in \([0-9.]*\) hours.*/\1/p')

    # Check if less than 2 hours remaining (using awk for float comparison)
    if [ -n "$HOURS" ] && awk "BEGIN {exit !($HOURS < 2)}"; then
        echo "⚠️  Token expires in less than 2 hours! Regenerating..."
        ./update_voice_token.sh

        # Restart CORS proxy if running
        if pgrep -f cors_proxy_server > /dev/null; then
            echo "Restarting CORS proxy server..."
            pkill -f cors_proxy_server
            sleep 1
            /home/adamsl/planner/.venv/bin/python3 cors_proxy_server.py > /tmp/cors_proxy.log 2>&1 &
            echo "CORS proxy restarted"
        fi

        echo "✓ Token regenerated proactively"
    else
        echo "✓ Token is valid ($HOURS hours remaining)"
    fi
    exit 0
else
    echo "⚠️  Unknown token status"
    exit 1
fi
