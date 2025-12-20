#!/bin/bash
echo "Quick Agent Selector Test"
echo "========================="
echo ""
echo "1. Checking services..."
ss -tlnp 2>/dev/null | grep -E ":(8283|7880|8888)" | awk '{print $4}' | sed 's/.*:/  Port /' | sort -u
echo ""
echo "2. Checking voice agent..."
ps aux | grep "letta_voice_agent.py dev" | grep -v grep | awk '{print "  PID: " $2 " Mode: DEV"}'
echo ""
echo "3. Checking agent count..."
curl -s http://localhost:8283/v1/agents | python3 -c "import sys,json; print('  Agents available: ' + str(len(json.load(sys.stdin))))"
echo ""
echo "✅ Ready to test!"
echo ""
echo "Open browser: http://localhost:8888/voice-agent-selector.html"
