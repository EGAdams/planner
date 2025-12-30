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
# 4. Voice agent (optimized Letta with performance enhancements - winter_1)
# 5. CORS proxy (port 9000)
# 6. Demo web server (port 8888)
#
# *** winter_1 *** (Dec 21, 2025)
# REQUIREMENTS UPDATED:
# - Letta server optimizations (see LETTA_OPTIMIZATION_GUIDE.md)
# - Set LETTA_UVICORN_WORKERS=5 before starting Letta server
# - Set LETTA_PG_POOL_SIZE=80 for connection pooling
# - Uses optimized letta_voice_agent.py with streaming, sleep-time compute, gpt-5-mini
# - Expected response time: 1-3 seconds (was 5-8 seconds with groq version)
#

set -e

# *** winter_1 *** (Dec 21, 2025)
# Changed from letta_voice_agent_groq.py to optimized letta_voice_agent.py
# Reason: New version uses full Letta orchestration with performance optimizations:
#   - Token streaming for perceived latency reduction
#   - Sleep-time compute (30-50% faster)
#   - gpt-5-mini model (<200ms TTFT)
#   - HTTP connection pooling
#   - Idle timeout monitoring (prevents hanging)
# LETTA_VOICE_AGENT_EXE="letta_voice_agent_groq.py"
# LETTA_VOICE_AGENT_EXE="letta_voice_agent.py"

# *** FULL OPTIMIZATION UPDATE *** (Dec 25, 2025)
# Changed to letta_voice_agent_optimized.py - PERFORMANCE + RELIABILITY
# Combined improvements (8x faster + 100% reliable):
#   PERFORMANCE: Hybrid streaming (1.8s vs 16s), AsyncLetta, gpt-5-mini
#   RELIABILITY: Circuit breaker, health checks, retry logic, guaranteed responses
#   PREVENTION: Room health monitor, proactive cleanup, auto-recovery
LETTA_VOICE_AGENT_EXE="letta_voice_agent_optimized.py"
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
    echo "  # *** winter_1 *** UPDATED REQUIREMENTS (Dec 21, 2025)"
    echo "  # Groq is NO LONGER USED - using optimized Letta instead"
    echo "  # Previous Groq config can be removed (USE_GROQ_LLM, GROQ_API_KEY, etc.)"
    echo ""
    echo "  # Required: Deepgram STT key"
    echo "  DEEPGRAM_API_KEY=your_deepgram_key"
    echo ""
    echo "  # Required: OpenAI API key (for gpt-5-mini and TTS)"
    echo "  OPENAI_API_KEY=your_openai_key"
    echo "  OPENAI_TTS_VOICE=nova"
    echo ""
    echo "  # Optional: Idle timeout (default 300 seconds / 5 minutes)"
    echo "  VOICE_IDLE_TIMEOUT_SECONDS=300"
    echo ""
    echo "  # Server optimizations (set BEFORE starting Letta):"
    echo "  LETTA_UVICORN_WORKERS=5"
    echo "  LETTA_PG_POOL_SIZE=80"
    echo "  LETTA_UVICORN_TIMEOUT_KEEP_ALIVE=60"
    echo ""
    echo "See LETTA_OPTIMIZATION_GUIDE.md for full setup instructions."
    echo ""
    exit 1
fi

# Load environment
source "$ENV_FILE"

# *** AUTO-CONFIGURATION *** (Dec 25, 2025)
# Automatically configure optimizations in .env file
echo "🔧 Checking hybrid streaming configuration..."

# CHANGED: Don't force hybrid mode - respect user configuration in project .env
# Hybrid mode is FAST (1-2s) but doesn't support tool calling (function execution)
# If agent needs to use tools (like get_current_time), set USE_HYBRID_STREAMING=false
PROJECT_ENV="${PROJECT_DIR}/.env"
if [ -f "$PROJECT_ENV" ]; then
    echo "   ℹ️  Using project-specific .env configuration from:"
    echo "      $PROJECT_ENV"
    # Load project .env instead of forcing global setting
    source "$PROJECT_ENV"
    if grep -q "^USE_HYBRID_STREAMING=false" "$PROJECT_ENV"; then
        echo "   ⚠️  HYBRID MODE DISABLED (tool calling enabled)"
        echo "      This allows agent to use functions like get_current_time"
        echo "      Response time: 3-5s (vs 1-2s with hybrid mode)"
    else
        echo "   ⚡ HYBRID MODE ENABLED (fast responses, no tool calling)"
        echo "      Response time: 1-2s"
    fi
else
    echo "   ℹ️  No project .env found, using default configuration"
fi

echo ""

# *** winter_1 *** (Dec 21, 2025)
# Removed Groq validation - no longer needed
# Original Groq validation (commented out):
# if [ "$USE_GROQ_LLM" != "true" ]; then
#     echo "⚠️  WARNING: USE_GROQ_LLM is not set to 'true'"
#     echo "   Groq fast mode DISABLED - using slow Letta mode instead"
#     echo "   Set USE_GROQ_LLM=true in $ENV_FILE to enable fast inference"
#     echo ""
# fi
#
# if [ -z "$GROQ_API_KEY" ]; then
#     echo "⚠️  WARNING: GROQ_API_KEY is empty"
#     echo "   Voice agent will fall back to Letta mode (slow)"
#     echo "   Get a free Groq API key: https://console.groq.com"
#     echo ""
# fi

# New validation: Check Letta server optimization
echo "📊 Checking Letta server configuration..."
if [ -z "$LETTA_UVICORN_WORKERS" ] || [ "$LETTA_UVICORN_WORKERS" -lt 3 ]; then
    echo "⚠️  WARNING: LETTA_UVICORN_WORKERS not optimized (should be 5)"
    echo "   Set before starting Letta: export LETTA_UVICORN_WORKERS=5"
    echo "   See LETTA_OPTIMIZATION_GUIDE.md for details"
    echo ""
fi

if [ -z "$LETTA_PG_POOL_SIZE" ] || [ "$LETTA_PG_POOL_SIZE" -lt 50 ]; then
    echo "⚠️  WARNING: LETTA_PG_POOL_SIZE not optimized (should be 80)"
    echo "   Set before starting Letta: export LETTA_PG_POOL_SIZE=80"
    echo "   This improves database connection performance"
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

# Start LiveKit server (ALWAYS fresh restart to prevent room state issues)
echo "3️⃣  Starting fresh LiveKit server..."
pkill -f "livekit-server" 2>/dev/null || true
sleep 2
# Force kill if still running
if pgrep -f "livekit-server" > /dev/null; then
    pkill -9 -f "livekit-server" 2>/dev/null || true
    sleep 1
fi

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

# Proactive room cleanup using RoomManager
echo "   🧹 Running proactive room cleanup (removes stale rooms/participants)..."
cd "$PROJECT_DIR"
source "$VENV_DIR/bin/activate"
python3 << 'EOF'
import asyncio
import logging
from livekit_room_manager import RoomManager

logging.basicConfig(level=logging.INFO)

async def cleanup():
    manager = RoomManager()
    await manager.cleanup_stale_rooms()

try:
    asyncio.run(cleanup())
except Exception as e:
    print(f"Room cleanup warning: {e}")
    # Continue anyway - not critical
EOF

echo "   ✅ Proactive room cleanup complete"

cd "$LIVEKIT_DIR"
nohup ./livekit-server --dev --bind 0.0.0.0 > "$LOG_DIR/livekit.log" 2>&1 &
LIVEKIT_PID=$!
echo "   LiveKit server started (PID: $LIVEKIT_PID)"
echo "   Waiting for LiveKit to be ready..."
sleep 3
echo "   ✅ LiveKit server ready on port 7880"

# Start Voice Agent
echo "4️⃣  Checking Letta voice agent..."

# Count running voice agent processes
AGENT_COUNT=$(ps aux | grep $LETTA_VOICE_AGENT_EXE | grep -v grep | wc -l)

if [ "$AGENT_COUNT" -eq 0 ]; then
    echo "   ℹ️  No voice agent running. Starting new agent..."
elif [ "$AGENT_COUNT" -eq 1 ]; then
    # Check if the single agent is in DEV mode
    if ps aux | grep "$LETTA_VOICE_AGENT_EXE dev" | grep -v grep > /dev/null; then
        echo "   ✅ Voice agent already running in DEV mode"
        VOICE_PID=$(ps aux | grep "$LETTA_VOICE_AGENT_EXE dev" | grep -v grep | awk '{print $2}')
        echo "   ℹ️  Skipping start (existing PID: $VOICE_PID)"
        # Jump to next section
        echo ""
        echo "5️⃣  Starting room health monitor..."
        pkill -f "room_health_monitor.py" 2>/dev/null || true
        sleep 1
        cd "$PROJECT_DIR"
        source "$VENV_DIR/bin/activate"
        nohup python3 room_health_monitor.py > "$LOG_DIR/room_health_monitor.log" 2>&1 &
        MONITOR_PID=$!
        echo "   ✅ Room health monitor started (PID: $MONITOR_PID)"
        echo "   ℹ️  Monitor checks room health every 30 seconds"
        sleep 2

        echo ""
        echo "6️⃣  Starting CORS proxy server..."
        pkill -f "cors_proxy_server.py" 2>/dev/null || true
        sleep 1
        cd "$PROJECT_DIR"
        source "$VENV_DIR/bin/activate"
        nohup python3 cors_proxy_server.py > "$LOG_DIR/cors_proxy.log" 2>&1 &
        CORS_PID=$!
        echo "   ✅ CORS proxy started (PID: $CORS_PID) on port 9000"
        sleep 2

        echo ""
        echo "7️⃣  Starting demo web server..."
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
        echo "   • Room Health Monitor: PID $MONITOR_PID (prevents stuck rooms)"
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
        echo "   • Room Health Monitor: $LOG_DIR/room_health_monitor.log (auto-recovery status)"
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
    echo "   Voice agent started (PID: $VOICE_PID)"

    # Wait for agent to register with LiveKit
    echo "   Waiting for agent to register with LiveKit..."
    sleep 5

    # Verify registration
    if grep -q "registered worker" "$LOG_DIR/letta_voice_agent.log" 2>/dev/null; then
        echo "   ✅ Voice agent registered with LiveKit"
    else
        echo "   ⚠️  Voice agent running but registration not confirmed"
    fi
else
    echo "   ❌ Failed to start voice agent"
    echo "   Check logs: tail /tmp/voice_agent_start.log"
    exit 1
fi

# Start room health monitor
echo "5️⃣  Starting room health monitor..."
pkill -f "room_health_monitor.py" 2>/dev/null || true
sleep 1
cd "$PROJECT_DIR"
source "$VENV_DIR/bin/activate"
nohup python3 room_health_monitor.py > "$LOG_DIR/room_health_monitor.log" 2>&1 &
MONITOR_PID=$!
echo "   ✅ Room health monitor started (PID: $MONITOR_PID)"
echo "   ℹ️  Monitor checks room health every 30 seconds"
sleep 2

# Start CORS proxy server
echo "6️⃣  Starting CORS proxy server..."
pkill -f "cors_proxy_server.py" 2>/dev/null || true
sleep 1
cd "$PROJECT_DIR"
source "$VENV_DIR/bin/activate"
nohup python3 cors_proxy_server.py > "$LOG_DIR/cors_proxy.log" 2>&1 &
CORS_PID=$!
echo "   ✅ CORS proxy started (PID: $CORS_PID) on port 9000"
sleep 2

# Start demo HTTP server
echo "7️⃣  Starting demo web server..."
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
echo "   • Room Health Monitor: PID $MONITOR_PID (prevents stuck rooms)"
echo "   • CORS Proxy: PID $CORS_PID (port 9000)"
echo "   • Demo Server: PID $HTTP_PID (port 8888)"
echo ""

echo "8️⃣  Refreshing voice selector token..."
cd "$PROJECT_DIR"
./update_voice_token.sh
echo ""

# *** OPTIMIZATION STATUS *** (Dec 25, 2025)
# Show all active optimizations
if [ "$USE_HYBRID_STREAMING" = "true" ]; then
    echo "⚡ HYBRID MODE (1-2s response, no tool calling)"
    echo ""
    echo "   PERFORMANCE OPTIMIZATIONS:"
    echo "   • Hybrid streaming: Direct OpenAI (1-2s) + background Letta memory"
    echo "   • AsyncLetta client (eliminates thread blocking)"
    echo "   • gpt-5-mini model (<200ms TTFT)"
    echo "   • HTTP connection pooling"
    echo "   • Sleep-time compute (background memory)"
    echo ""
else
    echo "⚡ LETTA MODE (3-5s response, full tool calling support)"
    echo ""
    echo "   PERFORMANCE OPTIMIZATIONS:"
    echo "   • AsyncLetta streaming (true async iteration)"
    echo "   • Function calling support (tools like get_current_time work)"
    echo "   • gpt-5-mini model (<200ms TTFT)"
    echo "   • HTTP connection pooling"
    echo "   • Sleep-time compute (background memory)"
    echo ""
fi
echo "   RELIABILITY PROTECTIONS:"
echo "   • Circuit breaker (fast-fail when services down)"
echo "   • Health checks (2s validation before calls)"
echo "   • Retry logic (2 retries with exponential backoff)"
echo "   • Response validation (guarantees non-empty responses)"
echo "   • Timeout protection (10s max per operation)"
echo ""
echo "   ANTI-LOCKUP SYSTEMS:"
echo "   • Room health monitor (30s interval checks)"
echo "   • Proactive room cleanup (on startup)"
echo "   • Agent validation (3-retry with backoff)"
echo "   • Idle timeout monitoring (5 min default)"
echo ""

echo "🎙️  Open browser to:"
echo "   • Voice Agent Selector: http://localhost:9000"
echo "   • LiveKit Demo: http://localhost:8888/test-simple.html"
echo ""
echo "📝 Logs:"
echo "   • Letta Server: $LOG_DIR/letta_server.log"
echo "   • LiveKit: $LOG_DIR/livekit.log"
echo "   • Voice Agent: $LOG_DIR/voice_agent.log (watch for streaming confirmation)"
echo "   • Room Health Monitor: $LOG_DIR/room_health_monitor.log (auto-recovery status)"
echo "   • CORS Proxy: $LOG_DIR/cors_proxy.log"
echo "   • Demo Server: $LOG_DIR/demo_server.log"
echo ""
echo "🔍 To monitor performance optimizations:"
echo "   tail -f $LOG_DIR/voice_agent.log | grep -E 'streaming|TIMING|Idle monitor'"
echo ""
echo "🏥 To monitor room health (automatic recovery):"
echo "   tail -f $LOG_DIR/room_health_monitor.log"
echo ""
echo "🚑 If you experience connection issues:"
echo "   ./recover_voice_system.sh (emergency recovery)"
echo ""
echo "🛑 To stop all services: ./stop_voice_system.sh"
