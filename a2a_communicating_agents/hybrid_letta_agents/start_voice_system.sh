#!/bin/bash
#
# Start Voice System - Complete startup for Letta voice agent
#
# Usage: ./start_voice_system.sh
#
# This script starts all required services:
# 1. PostgreSQL database
# 2. Letta server (port 8283)
# 3. LiveKit server (port 7880)
# 4. Voice agent (uses Groq for fast inference)
# 5. CORS proxy (port 9000)
# 6. Demo web server (port 8888)
#
# REQUIREMENTS:
# - GROQ_API_KEY must be set in /home/adamsl/ottomator-agents/livekit-agent/.env
# - USE_GROQ_LLM=true must be set to enable fast mode
# - See .env configuration below
#

set -e

LETTA_VOICE_AGENT_EXE="letta_voice_agent_groq.py"
PROJECT_DIR="/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents"
VENV_DIR="/home/adamsl/planner/.venv"
LIVEKIT_DIR="/home/adamsl/ottomator-agents/livekit-agent"
LOG_DIR="/tmp"
ENV_FILE="/home/adamsl/ottomator-agents/livekit-agent/.env"

echo "🚀 Starting Letta Voice System..."
echo ""

# Check for required environment file
if [ ! -f "$ENV_FILE" ]; then
    echo "❌ ERROR: Environment file not found: $ENV_FILE"
    echo ""
    echo "Please create $ENV_FILE with:"
    echo ""
    echo "  LIVEKIT_URL=ws://localhost:7880"
    echo "  LIVEKIT_API_KEY=devkey"
    echo "  LIVEKIT_API_SECRET=secret"
    echo ""
    echo "  # REQUIRED FOR GROQ FAST MODE (5-10x faster LLM)"
    echo "  USE_GROQ_LLM=true"
    echo "  GROQ_API_KEY=your_groq_key_from_https://console.groq.com"
    echo "  GROQ_MODEL=llama-3.1-70b-versatile"
    echo ""
    echo "  # Optional: Deepgram STT key"
    echo "  DEEPGRAM_API_KEY=your_deepgram_key"
    echo ""
    echo "  # Optional: OpenAI (fallback TTS, cheaper than Cartesia)"
    echo "  OPENAI_API_KEY=your_openai_key"
    echo "  OPENAI_TTS_VOICE=nova"
    echo ""
    exit 1
fi

# Load environment
source "$ENV_FILE"

# Validate Groq configuration
if [ "$USE_GROQ_LLM" != "true" ]; then
    echo "⚠️  WARNING: USE_GROQ_LLM is not set to 'true'"
    echo "   Groq fast mode DISABLED - using slow Letta mode instead"
    echo "   Set USE_GROQ_LLM=true in $ENV_FILE to enable fast inference"
    echo ""
fi

if [ -z "$GROQ_API_KEY" ]; then
    echo "⚠️  WARNING: GROQ_API_KEY is empty"
    echo "   Voice agent will fall back to Letta mode (slow)"
    echo "   Get a free Groq API key: https://console.groq.com"
    echo ""
fi

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

# Clean up stale LiveKit rooms and state
echo "   🧹 Cleaning LiveKit stale rooms..."
LIVEKIT_DATA_DIR="/tmp/livekit"
if [ -d "$LIVEKIT_DATA_DIR" ]; then
    rm -rf "$LIVEKIT_DATA_DIR" 2>/dev/null || true
fi
# Truncate old log to start fresh
if [ -f "$LOG_DIR/livekit.log" ]; then
    > "$LOG_DIR/livekit.log"
fi

cd "$LIVEKIT_DIR"
nohup ./livekit-server --dev --bind 0.0.0.0 > "$LOG_DIR/livekit.log" 2>&1 &
LIVEKIT_PID=$!
echo "   ✅ LiveKit server started (PID: $LIVEKIT_PID) on port 7880"
sleep 2

# Start Voice Agent
echo "4️⃣  Checking Letta voice agent..."

# Count running voice agent processes
AGENT_COUNT=$(ps aux | grep $LETTA_VOICE_AGENT_EXE | grep -v grep | wc -l)

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
        echo "5️⃣  Starting CORS proxy server..."
        pkill -f "cors_proxy_server.py" 2>/dev/null || true
        sleep 1
        cd "$PROJECT_DIR"
        source "$VENV_DIR/bin/activate"
        nohup python3 cors_proxy_server.py > "$LOG_DIR/cors_proxy.log" 2>&1 &
        CORS_PID=$!
        echo "   ✅ CORS proxy started (PID: $CORS_PID) on port 9000"
        sleep 2

        echo ""
        echo "6️⃣  Starting demo web server..."
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
        echo "   • CORS Proxy: PID $CORS_PID (port 9000)"
        echo "   • Demo Server: PID $HTTP_PID (port 8888)"
        echo ""
        echo "🎙️  Open browser to:"
        echo "   • Voice Agent Selector: http://localhost:9000"
        echo "   • LiveKit Demo: http://localhost:8888/test-simple.html"
        echo ""
        echo "📝 Logs:"
        echo "   • Letta Server: $LOG_DIR/letta_server.log"
        echo "   • LiveKit: $LOG_DIR/livekit.log"
        echo "   • Voice Agent: $LOG_DIR/voice_agent.log"
        echo "   • CORS Proxy: $LOG_DIR/cors_proxy.log"
        echo "   • Demo Server: $LOG_DIR/demo_server.log"
        echo ""
        echo "🛑 To stop all services: ./stop_voice_system.sh"
        exit 0
    else
        echo "   ⚠️  Voice agent running in wrong mode (START instead of DEV). Killing..."
        pkill -f $LETTA_VOICE_AGENT_EXE 2>/dev/null || true
        sleep 1
    fi
else
    echo "   🚨 WARNING: $AGENT_COUNT duplicate voice agents detected!"
    echo "   ℹ️  This causes audio cutting and conflicts. Killing all duplicates..."
    pkill -f $LETTA_VOICE_AGENT_EXE 2>/dev/null || true
    sleep 2
    # Verify all killed
    REMAINING=$(ps aux | grep $LETTA_VOICE_AGENT_EXE | grep -v grep | wc -l)
    if [ "$REMAINING" -gt 0 ]; then
        echo "   ⚠️  Some processes didn't stop gracefully. Force killing..."
        pkill -9 -f $LETTA_VOICE_AGENT_EXE 2>/dev/null || true
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

# Start CORS proxy server
echo "5️⃣  Starting CORS proxy server..."
pkill -f "cors_proxy_server.py" 2>/dev/null || true
sleep 1
cd "$PROJECT_DIR"
source "$VENV_DIR/bin/activate"
nohup python3 cors_proxy_server.py > "$LOG_DIR/cors_proxy.log" 2>&1 &
CORS_PID=$!
echo "   ✅ CORS proxy started (PID: $CORS_PID) on port 9000"
sleep 2

# Start demo HTTP server
echo "6️⃣  Starting demo web server..."
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
echo "   • CORS Proxy: PID $CORS_PID (port 9000)"
echo "   • Demo Server: PID $HTTP_PID (port 8888)"
echo ""

# Show Groq mode status
if [ "$USE_GROQ_LLM" = "true" ] && [ -n "$GROQ_API_KEY" ]; then
    echo "⚡ LLM Mode: GROQ (Fast - 5-10x faster)"
else
    echo "🐌 LLM Mode: LETTA (Slow - full orchestration)"
fi
echo ""

echo "🎙️  Open browser to:"
echo "   • Voice Agent Selector: http://localhost:9000"
echo "   • LiveKit Demo: http://localhost:8888/test-simple.html"
echo ""
echo "📝 Logs:"
echo "   • Letta Server: $LOG_DIR/letta_server.log"
echo "   • LiveKit: $LOG_DIR/livekit.log"
echo "   • Voice Agent: $LOG_DIR/voice_agent.log (watch this for mode confirmation)"
echo "   • CORS Proxy: $LOG_DIR/cors_proxy.log"
echo "   • Demo Server: $LOG_DIR/demo_server.log"
echo ""
echo "🔍 To verify Groq mode is active, watch logs:"
echo "   tail -f $LOG_DIR/voice_agent.log | grep -E 'Groq mode|Letta mode'"
echo ""
echo "🛑 To stop all services: ./stop_voice_system.sh"
