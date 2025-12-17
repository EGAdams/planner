#!/bin/bash
#
# Start Voice System - Complete startup for Letta voice agent
#
# Usage: ./start_voice_system.sh
#

set -e

PROJECT_DIR="/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents"
VENV_DIR="/home/adamsl/planner/.venv"
LIVEKIT_DIR="/home/adamsl/ottomator-agents/livekit-agent"
LOG_DIR="/tmp"

echo "🚀 Starting Letta Voice System..."
echo ""

# Check if PostgreSQL is running
echo "1️⃣  Checking PostgreSQL..."
if ! pg_isready -q 2>/dev/null; then
    echo "   ⚠️  PostgreSQL not running. Starting..."
    sudo service postgresql start
    sleep 2
fi
echo "   ✅ PostgreSQL ready"

# Check if Letta server is running
echo "2️⃣  Checking Letta server..."
if ! curl -s http://localhost:8283/ > /dev/null 2>&1; then
    echo "   ⚠️  Letta server not running. Starting..."
    cd /home/adamsl/planner
    source "$VENV_DIR/bin/activate"
    nohup ./start_letta_dec_09_2025.sh > "$LOG_DIR/letta_server.log" 2>&1 &
    echo "   ⏳ Waiting for Letta server to start..."
    sleep 5

    # Wait up to 60 seconds for Letta to be ready
    for i in {1..60}; do
        if curl -s http://localhost:8283/ > /dev/null 2>&1; then
            break
        fi
        echo "   ⏳ Still waiting... ($i/60)"
        sleep 1
    done

    # Final check
    if ! curl -s http://localhost:8283/ > /dev/null 2>&1; then
        echo "   ❌ Letta server failed to start!"
        echo "   Check logs: tail $LOG_DIR/letta_server.log"
        exit 1
    fi
fi
echo "   ✅ Letta server ready on port 8283"

# Start LiveKit server
echo "3️⃣  Starting LiveKit server..."
pkill -f "livekit-server" 2>/dev/null || true
sleep 1
cd "$LIVEKIT_DIR"
nohup ./livekit-server --dev --bind 0.0.0.0 > "$LOG_DIR/livekit.log" 2>&1 &
LIVEKIT_PID=$!
echo "   ✅ LiveKit server started (PID: $LIVEKIT_PID) on port 7880"
sleep 2

# Start Voice Agent
echo "4️⃣  Checking Letta voice agent..."

# Count running voice agent processes
AGENT_COUNT=$(ps aux | grep "letta_voice_agent.py" | grep -v grep | wc -l)

if [ "$AGENT_COUNT" -eq 0 ]; then
    echo "   ℹ️  No voice agent running. Starting new agent..."
elif [ "$AGENT_COUNT" -eq 1 ]; then
    # Check if the single agent is in DEV mode
    if ps aux | grep "letta_voice_agent.py dev" | grep -v grep > /dev/null; then
        echo "   ✅ Voice agent already running in DEV mode"
        VOICE_PID=$(ps aux | grep "letta_voice_agent.py dev" | grep -v grep | awk '{print $2}')
        echo "   ℹ️  Skipping start (existing PID: $VOICE_PID)"
        # Jump to next section
        echo ""
        echo "5️⃣  Starting demo web server..."
        pkill -f "http.server 8888" 2>/dev/null || true
        sleep 1
        cd "$LIVEKIT_DIR"
        nohup python3 -m http.server 8888 > "$LOG_DIR/demo_server.log" 2>&1 &
        HTTP_PID=$!
        echo "   ✅ Demo server started (PID: $HTTP_PID) on port 8888"

        echo ""
        echo "✨ All services started!"
        echo ""
        echo "📊 Status:"
        echo "   • PostgreSQL: $(pg_isready 2>/dev/null && echo '✅ Running' || echo '❌ Down')"
        echo "   • Letta Server: $(curl -s http://localhost:8283/ >/dev/null 2>&1 && echo '✅ Port 8283' || echo '❌ Down')"
        echo "   • LiveKit Server: PID $LIVEKIT_PID (port 7880)"
        echo "   • Voice Agent: PID $VOICE_PID"
        echo "   • Demo Server: PID $HTTP_PID (port 8888)"
        echo ""
        echo "🎙️  Open browser to: http://localhost:8888/test-simple.html"
        echo ""
        echo "📝 Logs:"
        echo "   • Letta Server: $LOG_DIR/letta_server.log"
        echo "   • LiveKit: $LOG_DIR/livekit.log"
        echo "   • Voice Agent: $LOG_DIR/voice_agent.log"
        echo "   • Demo Server: $LOG_DIR/demo_server.log"
        echo ""
        echo "🛑 To stop all services: ./stop_voice_system.sh"
        exit 0
    else
        echo "   ⚠️  Voice agent running in wrong mode (START instead of DEV). Killing..."
        pkill -f "letta_voice_agent.py" 2>/dev/null || true
        sleep 1
    fi
else
    echo "   🚨 WARNING: $AGENT_COUNT duplicate voice agents detected!"
    echo "   ℹ️  This causes audio cutting and conflicts. Killing all duplicates..."
    pkill -f "letta_voice_agent.py" 2>/dev/null || true
    sleep 2
    # Verify all killed
    REMAINING=$(ps aux | grep "letta_voice_agent.py" | grep -v grep | wc -l)
    if [ "$REMAINING" -gt 0 ]; then
        echo "   ⚠️  Some processes didn't stop gracefully. Force killing..."
        pkill -9 -f "letta_voice_agent.py" 2>/dev/null || true
        sleep 1
    fi
    echo "   ✅ All duplicates removed. Starting fresh agent..."
fi

# Use safe starter with PID file locking
echo "   ℹ️  Using safe starter (prevents race conditions)..."
if "$PROJECT_DIR/start_voice_agent_safe.sh" > /tmp/voice_agent_start.log 2>&1; then
    # Get PID from PID file
    VOICE_PID=$(cat /tmp/letta_voice_agent.pid 2>/dev/null || echo "unknown")
    echo "   ✅ Voice agent started (PID: $VOICE_PID)"
else
    echo "   ❌ Failed to start voice agent"
    echo "   Check logs: tail /tmp/voice_agent_start.log"
    exit 1
fi
sleep 3

# Start demo HTTP server
echo "5️⃣  Starting demo web server..."
pkill -f "http.server 8888" 2>/dev/null || true
sleep 1
cd "$LIVEKIT_DIR"
nohup python3 -m http.server 8888 > "$LOG_DIR/demo_server.log" 2>&1 &
HTTP_PID=$!
echo "   ✅ Demo server started (PID: $HTTP_PID) on port 8888"

echo ""
echo "✨ All services started!"
echo ""
echo "📊 Status:"
echo "   • PostgreSQL: $(pg_isready 2>/dev/null && echo '✅ Running' || echo '❌ Down')"
echo "   • Letta Server: $(curl -s http://localhost:8283/ >/dev/null 2>&1 && echo '✅ Port 8283' || echo '❌ Down')"
echo "   • LiveKit Server: PID $LIVEKIT_PID (port 7880)"
echo "   • Voice Agent: PID $VOICE_PID"
echo "   • Demo Server: PID $HTTP_PID (port 8888)"
echo ""
echo "🎙️  Open browser to: http://localhost:8888/test-simple.html"
echo ""
echo "📝 Logs:"
echo "   • Letta Server: $LOG_DIR/letta_server.log"
echo "   • LiveKit: $LOG_DIR/livekit.log"
echo "   • Voice Agent: $LOG_DIR/voice_agent.log"
echo "   • Demo Server: $LOG_DIR/demo_server.log"
echo ""
echo "🛑 To stop all services: ./stop_voice_system.sh"
