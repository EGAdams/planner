#!/bin/bash
# Monitor voice agent debug logs with key information highlighted

echo "========================================="
echo "Voice Agent Real-Time Debug Monitor"
echo "========================================="
echo ""
echo "Watching for:"
echo "  - Agent initialization (🚀)"
echo "  - Agent selection messages (📨)"
echo "  - Agent switches (🔄)"
echo "  - Query processing (🎤)"
echo "  - Memory loading (🧠)"
echo "  - Response generation (✅)"
echo ""
echo "Press Ctrl+C to stop"
echo "========================================="
echo ""

tail -f voice_agent_debug.log | grep --line-buffered -E "🚀|📨|🔄|🎤|🧠|✅|❌|AGENT|Agent ID|Memory|DEBUG:"
