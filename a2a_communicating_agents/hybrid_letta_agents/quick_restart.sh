#!/bin/bash
# Quick restart script for voice agent after code changes

echo "🔄 Quick Voice Agent Restart"
echo "=============================="

# Kill all voice agent processes
echo "→ Stopping voice agent..."
pkill -9 -f letta_voice_agent
sleep 2

# Verify all killed
if pgrep -f letta_voice_agent > /dev/null; then
    echo "⚠️  Warning: Some processes still running, force killing..."
    killall -9 python3
    sleep 1
fi

# Clear old log
> /tmp/letta_voice_agent.log

# Start fresh agent
echo "→ Starting voice agent..."
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents

export $(grep -v '^#' /home/adamsl/ottomator-agents/livekit-agent/.env | xargs)
export $(grep -v '^#' /home/adamsl/planner/.env | xargs)

/home/adamsl/planner/.venv/bin/python3 letta_voice_agent.py dev > /tmp/letta_voice_agent.log 2>&1 &
AGENT_PID=$!

sleep 5

# Check if started successfully
if ps -p $AGENT_PID > /dev/null; then
    echo "✅ Voice agent running (PID: $AGENT_PID)"

    # Check for registration
    if grep -q "registered worker" /tmp/letta_voice_agent.log; then
        echo "✅ Agent registered with LiveKit"
    else
        echo "⚠️  Agent started but not registered yet, check logs"
    fi
else
    echo "❌ Agent failed to start"
    echo "Last 20 lines of log:"
    tail -20 /tmp/letta_voice_agent.log
    exit 1
fi

echo ""
echo "📋 Next Steps:"
echo "  1. Close browser tab COMPLETELY (don't just disconnect)"
echo "  2. Wait 5 seconds"
echo "  3. Open fresh tab: http://localhost:8888/test-simple.html"
echo "  4. Click 'Connect'"
echo "  5. Speak!"
echo ""
echo "Monitor: tail -f /tmp/letta_voice_agent.log | grep '🎤'"
