#!/bin/bash
set -e

echo "=========================================="
echo "  LETTA VOICE SYSTEM RESTART"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Demo HTTP server defaults
HTTP_SERVER_DIR="/home/adamsl/ottomator-agents/livekit-agent"
HTTP_SERVER_LOG="/tmp/livekit_http_server.log"
HTTP_PRIMARY_PORT=8888
HTTP_FALLBACK_PORT=8899
HTTP_ACTIVE_PORT=""

is_port_listening() {
    local port="$1"
    ss -tln | awk 'NR>1 {print $4}' | grep -Eq "[:.]${port}\$"
}

start_http_server_on_port() {
    local port="$1"
    echo -e "${BLUE}→ Starting LiveKit demo server on port ${port}...${NC}"
    (cd "$HTTP_SERVER_DIR" && nohup python3 -m http.server "$port" > "$HTTP_SERVER_LOG" 2>&1 &)
    sleep 2
    if is_port_listening "$port"; then
        HTTP_ACTIVE_PORT="$port"
        echo -e "${GREEN}✓ LiveKit demo server running on http://localhost:${port}${NC}"
        return 0
    fi
    echo -e "${RED}✗ Failed to start server on port ${port}${NC}"
    return 1
}

ensure_http_server() {
    echo -e "${YELLOW}[7/7] Checking LiveKit demo server...${NC}"
    if is_port_listening "$HTTP_PRIMARY_PORT"; then
        HTTP_ACTIVE_PORT="$HTTP_PRIMARY_PORT"
        echo -e "${GREEN}✓ Demo server already listening on http://localhost:${HTTP_PRIMARY_PORT}${NC}"
        return
    fi
    if start_http_server_on_port "$HTTP_PRIMARY_PORT"; then
        return
    fi
    echo -e "${YELLOW}Primary port unavailable, trying fallback ${HTTP_FALLBACK_PORT}...${NC}"
    if start_http_server_on_port "$HTTP_FALLBACK_PORT"; then
        return
    fi
    echo -e "${RED}✗ Unable to start demo HTTP server on ports ${HTTP_PRIMARY_PORT} or ${HTTP_FALLBACK_PORT}${NC}"
    echo "  Check $HTTP_SERVER_LOG for details."
    exit 1
}

echo -e "${YELLOW}[1/7] Stopping existing processes...${NC}"

# Use safe stopper to clean up PID/lock files
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/stop_voice_agent_safe.sh" ]; then
    echo "  Using safe stopper (cleans up PID and lock files)..."
    "$SCRIPT_DIR/stop_voice_agent_safe.sh" 2>&1 | sed 's/^/  /'
else
    # Fallback to manual cleanup
    AGENT_COUNT=$(ps aux | grep "letta_voice_agent.py" | grep -v grep | wc -l)

    if [ "$AGENT_COUNT" -eq 0 ]; then
        echo "  No voice agents running"
    elif [ "$AGENT_COUNT" -eq 1 ]; then
        echo "  Stopping 1 voice agent..."
        pkill -f "letta_voice_agent.py" || true
        sleep 1
    else
        echo -e "  ${RED}🚨 WARNING: $AGENT_COUNT duplicate voice agents detected!${NC}"
        echo "  This causes audio cutting and conflicts. Killing all..."
        pkill -f "letta_voice_agent.py" || true
        sleep 2
        REMAINING=$(ps aux | grep "letta_voice_agent.py" | grep -v grep | wc -l)
        if [ "$REMAINING" -gt 0 ]; then
            echo "  Force killing remaining processes..."
            pkill -9 -f "letta_voice_agent.py" || true
            sleep 1
        fi
        echo -e "  ${GREEN}✓ All $AGENT_COUNT duplicate agents removed${NC}"
    fi

    # Manual cleanup of PID and lock files
    rm -f /tmp/letta_voice_agent.pid /tmp/letta_voice_agent.lock 2>/dev/null || true
fi

# Kill Livekit server (force kill if stuck with stale rooms)
if pgrep -f "livekit-server" > /dev/null; then
    # Check if Livekit is stuck with stale rooms
    if grep -q "waiting for participants to exit" /tmp/livekit.log 2>/dev/null; then
        echo -e "  ${YELLOW}⚠️  Livekit stuck with stale rooms - force killing...${NC}"
        pkill -9 -f "livekit-server" || true
        sleep 1
    else
        echo "  Stopping Livekit server..."
        pkill -f "livekit-server" || true
        sleep 2
        # Verify it stopped
        if pgrep -f "livekit-server" > /dev/null; then
            echo "  Force killing Livekit..."
            pkill -9 -f "livekit-server" || true
            sleep 1
        fi
    fi
else
    echo "  No Livekit server running"
fi

echo -e "${GREEN}✓ Cleanup complete${NC}"
echo ""

echo -e "${YELLOW}[2/7] Checking PostgreSQL...${NC}"
if ! pg_isready -q 2>/dev/null; then
    echo "  ⚠️  PostgreSQL not running. Starting..."
    sudo service postgresql start
    sleep 2

    # Verify PostgreSQL is ready
    if ! pg_isready -q 2>/dev/null; then
        echo -e "${RED}✗ PostgreSQL failed to start!${NC}"
        echo "  Please start it manually: sudo service postgresql start"
        exit 1
    fi
fi
echo -e "${GREEN}✓ PostgreSQL is running${NC}"
echo ""

echo -e "${YELLOW}[3/7] Checking Letta server...${NC}"
if curl -s http://localhost:8283/ > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Letta server is running on port 8283${NC}"
else
    echo "  ⚠️  Letta server NOT running. Starting..."
    cd /home/adamsl/planner
    nohup ./start_letta_dec_09_2025.sh > /tmp/letta_startup.log 2>&1 &
    echo "  ⏳ Waiting for Letta server to start..."
    sleep 5

    # Wait up to 60 seconds for Letta to be ready
    for i in {1..60}; do
        if curl -s http://localhost:8283/ > /dev/null 2>&1; then
            break
        fi
        echo "  ⏳ Still waiting... ($i/60)"
        sleep 1
    done

    # Final check
    if ! curl -s http://localhost:8283/ > /dev/null 2>&1; then
        echo -e "${RED}✗ Letta server failed to start!${NC}"
        echo "  Check logs: tail /tmp/letta_startup.log"
        exit 1
    fi
    echo -e "${GREEN}✓ Letta server started on port 8283${NC}"
fi
echo ""

echo -e "${YELLOW}[4/7] Starting Livekit server...${NC}"
LIVEKIT_BIN="/home/adamsl/ottomator-agents/livekit-agent/livekit-server"
if [ ! -x "$LIVEKIT_BIN" ]; then
    echo -e "${RED}✗ livekit-server binary not found at $LIVEKIT_BIN${NC}"
    exit 1
fi
nohup "$LIVEKIT_BIN" --dev --bind 0.0.0.0 > /tmp/livekit.log 2>&1 &
LIVEKIT_PID=$!
echo "  Started Livekit server (PID: $LIVEKIT_PID)"
sleep 2

# Verify it started
if ps -p $LIVEKIT_PID > /dev/null; then
    echo -e "${GREEN}✓ Livekit server is running${NC}"
else
    echo -e "${RED}✗ Livekit server failed to start!${NC}"
    echo "  Check logs: tail /tmp/livekit.log"
    exit 1
fi
echo ""

echo -e "${YELLOW}[5/7] Starting voice agent in DEV mode...${NC}"

# Load environment variables
ENV_FILE="/home/adamsl/ottomator-agents/livekit-agent/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}✗ Environment file not found: $ENV_FILE${NC}"
    exit 1
fi

export $(grep -v '^#' "$ENV_FILE" | xargs)

# Also load planner env for Letta credentials
PLANNER_ENV="/home/adamsl/planner/.env"
if [ -f "$PLANNER_ENV" ]; then
    export $(grep -v '^#' "$PLANNER_ENV" | xargs)
fi

# Change to voice agent directory
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents

# Start voice agent
/home/adamsl/planner/.venv/bin/python3 letta_voice_agent.py dev > /tmp/letta_voice_agent.log 2>&1 &
VOICE_AGENT_PID=$!
echo "  Started voice agent (PID: $VOICE_AGENT_PID)"
sleep 3

# Verify it started
if ps -p $VOICE_AGENT_PID > /dev/null; then
    echo -e "${GREEN}✓ Voice agent is running in DEV mode${NC}"
else
    echo -e "${RED}✗ Voice agent failed to start!${NC}"
    echo "  Check logs: tail /tmp/letta_voice_agent.log"
    exit 1
fi
echo ""

echo -e "${YELLOW}[6/7] Generating connection token...${NC}"

# Generate token and capture it
NEW_TOKEN=$(/home/adamsl/planner/.venv/bin/python3 << 'EOF'
from livekit import api
import os

token = api.AccessToken(os.environ['LIVEKIT_API_KEY'], os.environ['LIVEKIT_API_SECRET']) \
    .with_identity('user1') \
    .with_name('User') \
    .with_grants(api.VideoGrants(
        room_join=True,
        room='test-room',
    ))

print(token.to_jwt())
EOF
)

echo "  Token generated for room: test-room"
echo ""
echo "=" * 60
echo "CONNECTION TOKEN (valid for ~6 hours)"
echo "=" * 60
echo "$NEW_TOKEN"
echo "=" * 60
echo ""

# Update test-simple.html with the new token
TEST_HTML="/home/adamsl/ottomator-agents/livekit-agent/test-simple.html"
if [ -f "$TEST_HTML" ]; then
    echo -e "${BLUE}→ Updating token in test-simple.html...${NC}"

    # Use sed to replace the TOKEN line
    sed -i "s|const TOKEN = '.*';|const TOKEN = '$NEW_TOKEN';|" "$TEST_HTML"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Token updated in $TEST_HTML${NC}"
    else
        echo -e "${RED}✗ Failed to update token in HTML file${NC}"
        echo "  Please manually update the TOKEN constant in $TEST_HTML"
    fi
else
    echo -e "${YELLOW}⚠ test-simple.html not found at $TEST_HTML${NC}"
    echo "  Token generated but not automatically inserted into HTML"
fi
echo ""

ensure_http_server

echo -e "${GREEN}=========================================="
echo "  SYSTEM READY!"
echo "==========================================${NC}"
echo ""
echo "Next steps:"
if [ -n "$HTTP_ACTIVE_PORT" ] && [ "$HTTP_ACTIVE_PORT" != "$HTTP_PRIMARY_PORT" ]; then
echo "  1. Open: http://localhost:${HTTP_ACTIVE_PORT}/test-simple.html (fallback port)"
else
echo "  1. Open: http://localhost:${HTTP_PRIMARY_PORT}/test-simple.html"
fi
echo "     (or run: cd /home/adamsl/ottomator-agents/livekit-agent && python3 -m http.server ${HTTP_PRIMARY_PORT})"
echo "  2. Click 'Connect'"
echo "  3. Allow microphone access"
echo "  4. Say 'Hello!'"
echo ""
echo "Watch logs:"
echo "  Voice agent: tail -f /tmp/letta_voice_agent.log"
echo "  Livekit:     tail -f /tmp/livekit.log"
echo ""
echo "PIDs:"
echo "  Livekit:     $LIVEKIT_PID"
echo "  Voice agent: $VOICE_AGENT_PID"
echo ""
