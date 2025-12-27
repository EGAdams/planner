#!/bin/bash

echo "=== Voice Agent Diagnostics ==="
echo ""

echo "1. Checking if voice agent is running..."
ps aux | grep "letta_voice_agent.py" | grep -v grep && echo "   ✅ Running" || echo "   ❌ Not running"
echo ""

echo "2. Checking active rooms..."
python3 << 'EOF'
import asyncio
from livekit_room_manager import RoomManager

async def main():
    manager = RoomManager()
    try:
        rooms = await manager.list_rooms()
        if len(rooms) == 0:
            print("   ❌ No active rooms (user may not be connected)")
        else:
            print(f"   ✅ Found {len(rooms)} room(s)")
            for room in rooms:
                print(f"      Room: {room.name}")
                print(f"      Participants: {room.num_participants}")
                participants = await manager.list_participants(room.name)
                for p in participants:
                    print(f"        - {p.identity} (joined: {p.joined_at}, state: {p.state})")
    finally:
        await manager.close()

asyncio.run(main())
EOF
echo ""

echo "3. Checking recent logs for errors..."
tail -n 50 /tmp/letta_voice_agent.log | grep -E "(ERROR|Exception|Traceback|422|streaming)" || echo "   No errors found in last 50 lines"
echo ""

echo "4. Checking for voice activity (last 20 lines)..."
tail -n 20 /tmp/letta_voice_agent.log | grep -E "(🎤|🔊|transcription|speech)" || echo "   No voice activity detected"
echo ""

echo "=== End Diagnostics ==="
