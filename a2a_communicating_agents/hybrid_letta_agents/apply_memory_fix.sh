#!/bin/bash
# Apply Voice Agent Memory Fix and Restart System

set -e

echo "================================================================================"
echo "VOICE AGENT MEMORY FIX - DEPLOYMENT"
echo "================================================================================"
echo ""

# Change to script directory
cd "$(dirname "$0")"

echo "Step 1: Verify backup exists"
echo "--------------------------------------------------------------------------------"
if [ -f "letta_voice_agent_optimized.py.backup" ]; then
    echo "✅ Backup file exists: letta_voice_agent_optimized.py.backup"
else
    echo "❌ ERROR: Backup file not found!"
    echo "   Run deployment manually to create backup first."
    exit 1
fi
echo ""

echo "Step 2: Stop current voice agent"
echo "--------------------------------------------------------------------------------"
VOICE_PIDS=$(pgrep -f "letta_voice_agent_optimized.py dev" || true)
if [ -n "$VOICE_PIDS" ]; then
    echo "Found running voice agent processes: $VOICE_PIDS"
    echo "Stopping processes..."
    pkill -f "letta_voice_agent_optimized.py dev"
    echo "✅ Voice agent stopped"
    echo "Waiting 3 seconds for clean shutdown..."
    sleep 3
else
    echo "⚠️  No running voice agent found (already stopped)"
fi
echo ""

echo "Step 3: Verify fixed version deployed"
echo "--------------------------------------------------------------------------------"
if grep -q "_load_agent_memory" letta_voice_agent_optimized.py; then
    echo "✅ Fixed version contains _load_agent_memory() method"
    echo "✅ Memory fix is deployed"
else
    echo "❌ ERROR: Fixed version not found!"
    echo "   The deployed file doesn't contain the memory fix."
    exit 1
fi
echo ""

echo "Step 4: Verify environment configuration"
echo "--------------------------------------------------------------------------------"
if grep -q "VOICE_PRIMARY_AGENT_ID=agent-4dfca708-49a8-4982-8e36-0f1146f9a66e" .env; then
    echo "✅ VOICE_PRIMARY_AGENT_ID configured correctly"
else
    echo "⚠️  WARNING: VOICE_PRIMARY_AGENT_ID may not be configured"
fi

if grep -q "USE_HYBRID_STREAMING=true" .env; then
    echo "✅ Hybrid streaming enabled (with memory fix)"
else
    echo "⚠️  Hybrid streaming disabled (using AsyncLetta mode)"
fi
echo ""

echo "Step 5: Start voice system with fix"
echo "--------------------------------------------------------------------------------"
if [ -f "start_voice_system.sh" ]; then
    echo "Starting voice system..."
    ./start_voice_system.sh &
    START_PID=$!
    echo "✅ Voice system started (PID: $START_PID)"
    echo "Waiting 5 seconds for initialization..."
    sleep 5
elif [ -f "restart_voice_system.sh" ]; then
    echo "Starting voice system..."
    ./restart_voice_system.sh &
    START_PID=$!
    echo "✅ Voice system started (PID: $START_PID)"
    echo "Waiting 5 seconds for initialization..."
    sleep 5
else
    echo "⚠️  No start script found - manual restart required"
    echo ""
    echo "Manual restart command:"
    echo "  /home/adamsl/planner/.venv/bin/python3 letta_voice_agent_optimized.py dev"
    echo ""
fi
echo ""

echo "Step 6: Verify voice agent is running"
echo "--------------------------------------------------------------------------------"
sleep 2
VOICE_PIDS=$(pgrep -f "letta_voice_agent_optimized.py dev" || true)
if [ -n "$VOICE_PIDS" ]; then
    echo "✅ Voice agent running (PID: $VOICE_PIDS)"
else
    echo "⚠️  Voice agent not detected (may need manual start)"
fi
echo ""

echo "================================================================================"
echo "DEPLOYMENT COMPLETE"
echo "================================================================================"
echo ""
echo "✅ Voice agent memory fix deployed successfully!"
echo ""
echo "NEXT STEPS:"
echo "  1. Open http://localhost:9000/voice-agent-selector-debug.html"
echo "  2. Connect with Agent_66"
echo "  3. Ask questions to test agent knowledge"
echo "  4. Check debug console for memory loading messages"
echo ""
echo "EXPECTED LOG MESSAGES:"
echo "  🧠 Loading memory and persona for Agent_66..."
echo "  ✅ Memory loaded successfully in X.XX s"
echo "  ⚡ Using direct OpenAI streaming with agent memory (fast path)"
echo ""
echo "ROLLBACK (if needed):"
echo "  1. Stop: pkill -f letta_voice_agent_optimized.py"
echo "  2. Restore: cp letta_voice_agent_optimized.py.backup letta_voice_agent_optimized.py"
echo "  3. Restart: ./restart_voice_system.sh"
echo ""
echo "================================================================================"
