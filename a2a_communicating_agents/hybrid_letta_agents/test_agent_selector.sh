#!/bin/bash
#
# Test Agent Selector Feature
#
# This script verifies the agent selection functionality is working correctly.
#

set -e

echo "🧪 Testing Letta Voice Agent Selector"
echo "======================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Check Letta API is accessible
echo "Test 1: Checking Letta API..."
if curl -s http://localhost:8283/v1/agents > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Letta API is accessible${NC}"
else
    echo -e "${RED}✗ Letta API is not accessible${NC}"
    echo "   Start the voice system: ./start_voice_system.sh"
    exit 1
fi

# Test 2: Verify agents can be listed
echo ""
echo "Test 2: Fetching agent list..."
AGENT_COUNT=$(curl -s http://localhost:8283/v1/agents | python3 -c "import sys, json; print(len(json.load(sys.stdin)))" 2>/dev/null)
if [ "$AGENT_COUNT" -gt 0 ]; then
    echo -e "${GREEN}✓ Found $AGENT_COUNT agents${NC}"
else
    echo -e "${RED}✗ No agents found${NC}"
    exit 1
fi

# Test 3: Check voice_orchestrator exists
echo ""
echo "Test 3: Checking for voice_orchestrator agent..."
ORCHESTRATOR_EXISTS=$(curl -s http://localhost:8283/v1/agents | python3 -c "import sys, json; agents = json.load(sys.stdin); print('yes' if any(a.get('name') == 'voice_orchestrator' for a in agents) else 'no')" 2>/dev/null)
if [ "$ORCHESTRATOR_EXISTS" = "yes" ]; then
    echo -e "${GREEN}✓ voice_orchestrator agent found${NC}"
else
    echo -e "${YELLOW}⚠ voice_orchestrator agent not found (not critical)${NC}"
fi

# Test 4: Check voice agent selector HTML exists
echo ""
echo "Test 4: Checking voice agent selector file..."
if [ -f "/home/adamsl/ottomator-agents/livekit-agent/voice-agent-selector.html" ]; then
    FILE_SIZE=$(stat -f%z "/home/adamsl/ottomator-agents/livekit-agent/voice-agent-selector.html" 2>/dev/null || stat -c%s "/home/adamsl/ottomator-agents/livekit-agent/voice-agent-selector.html" 2>/dev/null)
    echo -e "${GREEN}✓ voice-agent-selector.html exists (${FILE_SIZE} bytes)${NC}"
else
    echo -e "${RED}✗ voice-agent-selector.html not found${NC}"
    exit 1
fi

# Test 5: Check web server is serving the file
echo ""
echo "Test 5: Checking web server access..."
if curl -s http://localhost:8888/voice-agent-selector.html | head -1 | grep -q "<!DOCTYPE html>"; then
    echo -e "${GREEN}✓ Web server is serving voice-agent-selector.html${NC}"
else
    echo -e "${RED}✗ Cannot access voice-agent-selector.html via web server${NC}"
    echo "   Check if demo server is running on port 8888"
    exit 1
fi

# Test 6: Check voice agent is running in DEV mode
echo ""
echo "Test 6: Checking voice agent mode..."
if ps aux | grep "letta_voice_agent.py dev" | grep -v grep > /dev/null; then
    VOICE_PID=$(ps aux | grep "letta_voice_agent.py dev" | grep -v grep | awk '{print $2}')
    echo -e "${GREEN}✓ Voice agent running in DEV mode (PID: $VOICE_PID)${NC}"
else
    echo -e "${RED}✗ Voice agent not running in DEV mode${NC}"
    echo "   Restart: ./restart_voice_system.sh"
    exit 1
fi

# Test 7: Check for duplicate agents
echo ""
echo "Test 7: Checking for duplicate voice agents..."
DUPLICATE_COUNT=$(ps aux | grep "letta_voice_agent" | grep -v grep | wc -l)
if [ "$DUPLICATE_COUNT" -eq 1 ]; then
    echo -e "${GREEN}✓ No duplicate agents detected${NC}"
else
    echo -e "${YELLOW}⚠ Found $DUPLICATE_COUNT voice agent processes (should be 1)${NC}"
    echo "   This may cause audio cutting. Restart: ./restart_voice_system.sh"
fi

# Test 8: Verify Livekit server is running
echo ""
echo "Test 8: Checking Livekit server..."
if ss -tlnp 2>/dev/null | grep -q ":7880"; then
    echo -e "${GREEN}✓ Livekit server is running on port 7880${NC}"
else
    echo -e "${RED}✗ Livekit server not running${NC}"
    exit 1
fi

# Test 9: Sample a few agents
echo ""
echo "Test 9: Sampling available agents..."
curl -s http://localhost:8283/v1/agents | python3 << 'EOF'
import sys
import json

agents = json.load(sys.stdin)
print(f"Sample of {min(5, len(agents))} agents:")
for agent in agents[:5]:
    name = agent.get('name', 'Unnamed')
    agent_id = agent.get('id', 'Unknown')
    print(f"  • {name[:30]:30} | {agent_id}")
EOF

# Summary
echo ""
echo "======================================"
echo -e "${GREEN}✅ All tests passed!${NC}"
echo ""
echo "🎙️  Open in browser:"
echo "   http://localhost:8888/voice-agent-selector.html"
echo ""
echo "📝 Alternative (simple UI):"
echo "   http://localhost:8888/test-simple.html"
echo ""
echo "🛑 To stop services:"
echo "   ./stop_voice_system.sh"
echo ""
