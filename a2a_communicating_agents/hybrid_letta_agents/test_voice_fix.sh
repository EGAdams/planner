#!/bin/bash
# Quick test to verify the voice agent fix

echo "=========================================="
echo "Voice Agent Fix Verification"
echo "=========================================="
echo ""

# Check services
echo "1. Checking services..."
LIVEKIT_RUNNING=$(ps aux | grep "livekit-server" | grep -v grep | wc -l)
VOICE_AGENT_RUNNING=$(ps aux | grep "letta_voice_agent" | grep -v grep | wc -l)
CORS_PROXY_RUNNING=$(ps aux | grep "cors_proxy_server" | grep -v grep | wc -l)

if [ "$LIVEKIT_RUNNING" -gt 0 ]; then
    echo "   ✅ LiveKit server running"
else
    echo "   ❌ LiveKit server NOT running"
    echo "      Start with: ./livekit-server --dev --bind 0.0.0.0"
fi

if [ "$VOICE_AGENT_RUNNING" -gt 0 ]; then
    echo "   ✅ Voice agent running"
else
    echo "   ❌ Voice agent NOT running"
    echo "      Start with: python3 letta_voice_agent_optimized.py dev"
fi

if [ "$CORS_PROXY_RUNNING" -gt 0 ]; then
    echo "   ✅ CORS proxy running"
else
    echo "   ❌ CORS proxy NOT running"
    echo "      Start with: python3 cors_proxy_server.py"
fi

echo ""
echo "2. Checking HTML files..."
if [ -f "voice-agent-selector.html" ]; then
    if grep -q 'test-room' voice-agent-selector.html; then
        echo "   ✅ voice-agent-selector.html has room fix"
    else
        echo "   ❌ voice-agent-selector.html missing room fix"
    fi
else
    echo "   ❌ voice-agent-selector.html not found"
fi

if [ -f "voice-agent-selector-debug.html" ]; then
    if grep -q 'test-room' voice-agent-selector-debug.html; then
        echo "   ✅ voice-agent-selector-debug.html has room fix"
    else
        echo "   ❌ voice-agent-selector-debug.html missing room fix"
    fi
else
    echo "   ❌ voice-agent-selector-debug.html not found"
fi

echo ""
echo "3. Testing HTTP endpoints..."
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/)
if [ "$HTTP_STATUS" = "200" ]; then
    echo "   ✅ http://localhost:9000/ accessible"
else
    echo "   ❌ http://localhost:9000/ returned $HTTP_STATUS"
fi

DEBUG_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/debug)
if [ "$DEBUG_STATUS" = "200" ]; then
    echo "   ✅ http://localhost:9000/debug accessible"
else
    echo "   ❌ http://localhost:9000/debug returned $DEBUG_STATUS"
fi

API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/api/v1/agents/)
if [ "$API_STATUS" = "200" ]; then
    echo "   ✅ Letta API proxy working"
else
    echo "   ❌ Letta API proxy returned $API_STATUS"
fi

echo ""
echo "4. Checking JWT token room name..."
TOKEN='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiVXNlciIsInZpZGVvIjp7InJvb21Kb2luIjp0cnVlLCJyb29tIjoidGVzdC1yb29tIiwiY2FuUHVibGlzaCI6dHJ1ZSwiY2FuU3Vic2NyaWJlIjp0cnVlLCJjYW5QdWJsaXNoRGF0YSI6dHJ1ZX0sInN1YiI6InVzZXIxIiwiaXNzIjoiZGV2a2V5IiwibmJmIjoxNzY2ODAxOTM3LCJleHAiOjE3NjY4ODgzMzd9.0LlIcOjqsMVbifgGaY5cxA5Uz-YVTYhXXC4asJvw8vI'
PAYLOAD=$(echo $TOKEN | cut -d'.' -f2 | base64 -d 2>/dev/null)
ROOM_NAME=$(echo $PAYLOAD | grep -o '"room":"[^"]*"' | cut -d'"' -f4)

if [ "$ROOM_NAME" = "test-room" ]; then
    echo "   ✅ JWT token allows: $ROOM_NAME"
else
    echo "   ⚠️  JWT token allows: $ROOM_NAME (expected: test-room)"
fi

echo ""
echo "=========================================="
echo "TESTING INSTRUCTIONS"
echo "=========================================="
echo ""
echo "1. Open Windows browser to:"
echo "   http://localhost:9000/debug"
echo ""
echo "2. Expected behavior:"
echo "   - Select an agent"
echo "   - Click Connect"
echo "   - Allow microphone access"
echo "   - Watch debug console for:"
echo "     ✅ 'Using fixed room name \"test-room\" to match JWT token'"
echo "     ✅ 'Room connected successfully'"
echo "     ✅ 'AUDIO TRACK IS NOW PUBLISHING TO LIVEKIT!'"
echo "     ✅ 'Participant connected: voice-agent'"
echo ""
echo "3. Speak into microphone:"
echo "   - You should see transcription in debug console"
echo "   - You should HEAR voice response from agent"
echo ""
echo "4. Check voice agent logs (in WSL terminal):"
echo "   tail -f /tmp/letta_voice_agent.log | grep 'User message'"
echo ""
echo "If you don't see the agent join within 15 seconds:"
echo "   - Check that voice agent is running in 'dev' mode"
echo "   - Check LiveKit server logs for room creation"
echo "   - Verify both browser and agent are joining 'test-room'"
echo ""
echo "=========================================="
