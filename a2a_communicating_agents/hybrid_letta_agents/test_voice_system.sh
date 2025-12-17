#!/bin/bash
#
# Test Voice System - Verify all services are running correctly
#
# Usage: ./test_voice_system.sh
#

echo "🧪 Testing Letta Voice System..."
echo ""

FAILED=0

# Test PostgreSQL
echo -n "1️⃣  PostgreSQL... "
if pg_isready -q 2>/dev/null; then
    echo "✅ Running"
else
    echo "❌ Not running"
    FAILED=$((FAILED + 1))
fi

# Test Letta Server
echo -n "2️⃣  Letta Server (port 8283)... "
if curl -s http://localhost:8283/ > /dev/null 2>&1; then
    echo "✅ Responding"
else
    echo "❌ Not responding"
    FAILED=$((FAILED + 1))
fi

# Test LiveKit Server
echo -n "3️⃣  LiveKit Server (port 7880)... "
if ss -tlnp 2>/dev/null | grep -q ":7880"; then
    echo "✅ Listening"
else
    echo "❌ Not listening"
    FAILED=$((FAILED + 1))
fi

# Test Voice Agent
echo -n "4️⃣  Voice Agent... "
if pgrep -f "letta_voice_agent.py" > /dev/null 2>&1; then
    echo "✅ Running (PID: $(pgrep -f 'letta_voice_agent.py'))"
else
    echo "❌ Not running"
    FAILED=$((FAILED + 1))
fi

# Test Demo Server
echo -n "5️⃣  Demo Server (port 8888)... "
if ss -tlnp 2>/dev/null | grep -q ":8888"; then
    echo "✅ Listening"
else
    echo "❌ Not listening"
    FAILED=$((FAILED + 1))
fi

echo ""

if [ $FAILED -eq 0 ]; then
    echo "✨ All services are running!"
    echo ""
    echo "🎙️  Open browser to: http://localhost:8888/test-simple.html"
    echo ""
    echo "📝 View logs:"
    echo "   tail -f /tmp/voice_agent.log"
    exit 0
else
    echo "⚠️  $FAILED service(s) failed"
    echo ""
    echo "🔧 To start all services:"
    echo "   ./start_voice_system.sh"
    exit 1
fi
