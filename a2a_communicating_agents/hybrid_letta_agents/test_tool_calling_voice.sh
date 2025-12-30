#!/bin/bash
#
# Test Tool Calling Voice Fix
#
# This script verifies that the voice agent can execute tools
# and speak the complete response including tool results.
#
# Usage: ./test_tool_calling_voice.sh
#

set -e

echo "🧪 Testing Voice Agent Tool Calling Fix"
echo "========================================"
echo ""

# Check if voice agent is running
if ! ps aux | grep "letta_voice_agent_optimized.py" | grep -v grep > /dev/null; then
    echo "❌ Voice agent is not running"
    echo "   Start it with: ./start_voice_agent_safe.sh"
    exit 1
fi

echo "✅ Voice agent is running"
echo ""

# Check .env configuration
echo "1️⃣  Checking .env configuration..."
if grep -q "^USE_HYBRID_STREAMING=false" .env; then
    echo "   ✅ HYBRID MODE DISABLED (tool calling enabled)"
else
    echo "   ❌ HYBRID MODE ENABLED (tool calling disabled)"
    echo "   Fix: Set USE_HYBRID_STREAMING=false in .env"
    exit 1
fi
echo ""

# Check voice agent logs for mode
echo "2️⃣  Checking voice agent mode in logs..."
if tail -100 /tmp/voice_agent.log | grep -q "HYBRID mode"; then
    echo "   ❌ Voice agent running in HYBRID mode"
    echo "   Restart needed: kill $(cat /tmp/letta_voice_agent.pid) && ./start_voice_agent_safe.sh"
    exit 1
elif tail -100 /tmp/voice_agent.log | grep -q "AsyncLetta mode" || tail -100 /tmp/voice_agent.log | grep -q "📞 Using AsyncLetta"; then
    echo "   ✅ Voice agent running in ASYNC LETTA mode (tool calling enabled)"
else
    echo "   ⚠️  Cannot determine mode from logs"
    echo "   Check manually: tail -f /tmp/voice_agent.log"
fi
echo ""

# Check Letta server
echo "3️⃣  Checking Letta server..."
if curl -s http://localhost:8283/admin/health > /dev/null 2>&1; then
    echo "   ✅ Letta server running on port 8283"
else
    echo "   ❌ Letta server not responding"
    exit 1
fi
echo ""

# Check LiveKit server
echo "4️⃣  Checking LiveKit server..."
if pgrep -f "livekit-server" > /dev/null; then
    echo "   ✅ LiveKit server running"
else
    echo "   ❌ LiveKit server not running"
    exit 1
fi
echo ""

# Check Agent_66
echo "5️⃣  Checking Agent_66 availability..."
AGENT_ID=$(cat .env | grep VOICE_PRIMARY_AGENT_ID | cut -d '=' -f2)
if [ -z "$AGENT_ID" ]; then
    echo "   ❌ VOICE_PRIMARY_AGENT_ID not set in .env"
    exit 1
fi

AGENT_CHECK=$(curl -s "http://localhost:8283/v1/agents/${AGENT_ID}" 2>/dev/null || echo "{}")
if echo "$AGENT_CHECK" | grep -q "Agent_66"; then
    echo "   ✅ Agent_66 (ID: ${AGENT_ID:0:8}...) is available"
else
    echo "   ❌ Agent_66 not found at ID: $AGENT_ID"
    exit 1
fi
echo ""

# Check if Agent_66 has tools
echo "6️⃣  Checking Agent_66 tools..."
TOOLS=$(curl -s "http://localhost:8283/v1/agents/${AGENT_ID}/tools" 2>/dev/null || echo "[]")
TOOL_COUNT=$(echo "$TOOLS" | grep -o '"name"' | wc -l)

if [ "$TOOL_COUNT" -gt 0 ]; then
    echo "   ✅ Agent_66 has $TOOL_COUNT tool(s)"
    echo "$TOOLS" | grep -o '"name":"[^"]*"' | sed 's/"name":"//g' | sed 's/"//g' | sed 's/^/      - /'
else
    echo "   ⚠️  Agent_66 has no tools configured"
    echo "      (This is OK if tools are base tools like send_message)"
fi
echo ""

echo "✨ All checks passed!"
echo ""
echo "🧪 Manual Testing Instructions:"
echo "================================"
echo ""
echo "1. Open browser to: http://localhost:9000"
echo "2. Click 'Connect'"
echo "3. Wait for 'Connected' status"
echo "4. Ask: 'What time is it?'"
echo ""
echo "Expected behavior:"
echo "  ✅ Agent says: 'I can retrieve the current time for you...'"
echo "  ✅ [Brief pause while tool executes]"
echo "  ✅ Agent says: 'The current time is [actual time]...'"
echo ""
echo "If you only hear the first part and NOT the actual time:"
echo "  ❌ Tool calling is still broken"
echo "  🔍 Check logs: tail -f /tmp/voice_agent.log | grep -E 'tool|HYBRID|mode'"
echo ""
echo "To monitor in real-time:"
echo "  Terminal 1: tail -f /tmp/voice_agent.log"
echo "  Terminal 2: tail -f /tmp/letta_server.log | grep tool"
echo ""
