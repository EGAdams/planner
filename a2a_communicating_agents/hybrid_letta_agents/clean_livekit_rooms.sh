#!/bin/bash
#
# Clean Livekit Stale Rooms
# Forces Livekit restart when rooms get stuck
#
# Usage: ./clean_livekit_rooms.sh

echo "🧹 Cleaning Livekit stale rooms..."
echo ""

# Check if Livekit is running
LIVEKIT_PID=$(ps aux | grep "livekit-server" | grep -v grep | awk '{print $2}')

if [ -z "$LIVEKIT_PID" ]; then
    echo "❌ Livekit is not running!"
    exit 1
fi

echo "Found Livekit process: PID $LIVEKIT_PID"

# Check if it's stuck waiting for participants
if grep -q "waiting for participants to exit" /tmp/livekit.log 2>/dev/null; then
    echo "⚠️  Livekit is stuck waiting for participants to exit"
    echo "   This happens when rooms have stale connections"
    echo ""
    echo "🔨 Force killing Livekit (bypassing graceful shutdown)..."
    kill -9 "$LIVEKIT_PID"
    sleep 2
else
    echo "✅ No stale rooms detected"
    echo "   Performing clean restart..."
    kill "$LIVEKIT_PID"
    sleep 3
fi

# Verify it stopped
if ps -p "$LIVEKIT_PID" > /dev/null 2>&1; then
    echo "❌ Livekit didn't stop. Force killing..."
    kill -9 "$LIVEKIT_PID"
    sleep 1
fi

echo "✅ Livekit stopped"
echo ""

# Start fresh Livekit
echo "🚀 Starting fresh Livekit server..."
nohup /home/adamsl/ottomator-agents/livekit-agent/livekit-server --dev --bind 0.0.0.0 > /tmp/livekit.log 2>&1 &
NEW_PID=$!

sleep 3

# Verify it started
if ps -p "$NEW_PID" > /dev/null 2>&1; then
    echo "✅ Livekit started successfully (PID: $NEW_PID)"
    echo ""
    echo "📊 Status:"
    echo "   • Livekit: http://localhost:7880 (PID $NEW_PID)"
    echo "   • Logs: tail -f /tmp/livekit.log"
    echo ""
    echo "🎯 All stale rooms cleared!"
else
    echo "❌ Failed to start Livekit"
    echo "   Check logs: tail /tmp/livekit.log"
    exit 1
fi
