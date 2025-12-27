#!/bin/bash
#
# Emergency recovery script for stuck voice system
# Run this if you experience "Waiting for agent to join..." or connection issues
#
# Usage: ./recover_voice_system.sh
#

set -e

PROJECT_DIR="/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents"
VENV_DIR="/home/adamsl/planner/.venv"

echo "🚑 Emergency Voice System Recovery"
echo ""
echo "This script will:"
echo "  1. Clean up all LiveKit rooms"
echo "  2. Restart the voice agent"
echo "  3. Restart all services"
echo ""

# 1. Clean up rooms
echo "1️⃣  Cleaning up LiveKit rooms..."
cd "$PROJECT_DIR"
source "$VENV_DIR/bin/activate"
python3 << 'EOF'
import asyncio
from livekit_room_manager import RoomManager

async def emergency_cleanup():
    manager = RoomManager()
    print("   🧹 Deleting all rooms...")
    try:
        rooms = await manager.list_rooms()
        if not rooms:
            print("   ℹ️  No rooms to clean up")
        else:
            for room in rooms:
                try:
                    await manager.delete_room(room.name)
                    print(f"   ✅ Deleted room: {room.name}")
                except Exception as e:
                    print(f"   ⚠️  Failed to delete {room.name}: {e}")
            print(f"   ✅ Room cleanup complete ({len(rooms)} rooms processed)")
    except Exception as e:
        print(f"   ⚠️  Error during cleanup: {e}")
    finally:
        await manager.close()

asyncio.run(emergency_cleanup())
EOF

# 2. Restart voice agent
echo ""
echo "2️⃣  Restarting voice agent..."
echo "   🛑 Stopping voice agent..."
pkill -9 -f letta_voice_agent 2>/dev/null || true
sleep 2
echo "   ✅ Voice agent stopped"

# 3. Full system restart
echo ""
echo "3️⃣  Restarting all services..."
echo "   🛑 Stopping all services..."
./stop_voice_system.sh
sleep 2

echo ""
echo "   ▶️  Starting all services..."
./start_voice_system.sh

echo ""
echo "✅ Recovery complete!"
echo ""
echo "🎙️  Try connecting again in your browser:"
echo "   • Voice Agent Selector: http://localhost:9000"
echo "   • LiveKit Demo: http://localhost:8888/test-simple.html"
echo ""
echo "📊 To check if recovery worked:"
echo "   tail -f /tmp/room_health_monitor.log"
echo "   tail -f /tmp/voice_agent.log"
echo ""
