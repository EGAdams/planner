#!/bin/bash
#
# Stop Voice System - Clean shutdown of all voice services
#
# Usage: ./stop_voice_system.sh
#

echo "🛑 Stopping Letta Voice System..."
echo ""

# Stop demo server
echo "1️⃣  Stopping demo server..."
pkill -f "http.server 8888" && echo "   ✅ Demo server stopped" || echo "   ℹ️  Not running"

# Stop voice agent
echo "2️⃣  Stopping voice agent..."
pkill -f "letta_voice_agent.py" && echo "   ✅ Voice agent stopped" || echo "   ℹ️  Not running"

# Stop LiveKit server
echo "3️⃣  Stopping LiveKit server..."
pkill -f "livekit-server" && echo "   ✅ LiveKit server stopped" || echo "   ℹ️  Not running"

# Optional: Stop Letta server (commented out - you might want to keep it running)
# echo "4️⃣  Stopping Letta server..."
# pkill -f "letta server" && echo "   ✅ Letta server stopped" || echo "   ℹ️  Not running"

# Optional: Stop PostgreSQL (commented out - usually keep database running)
# echo "5️⃣  Stopping PostgreSQL..."
# sudo service postgresql stop

echo ""
echo "✅ Voice system stopped"
echo ""
echo "ℹ️  Note: Letta server and PostgreSQL are still running"
echo "   To stop them manually:"
echo "   • Letta: pkill -f 'letta server'"
echo "   • PostgreSQL: sudo service postgresql stop"
