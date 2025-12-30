#!/usr/bin/env python3
"""
Fix for agent conflict detection bug.

The issue: _ROOM_TO_AGENT dictionary persists entries even when connections fail,
causing all subsequent connection attempts to be rejected as "duplicates".

Solution: Add smarter conflict detection that checks if the room actually has participants.
"""

import re

# Read the current file
with open('letta_voice_agent_optimized.py', 'r') as f:
    content = f.read()

# Find the conflict detection section
old_conflict_check = '''    # CRITICAL FIX: Check if this room already has an agent assigned
    async with _ROOM_ASSIGNMENT_LOCK:
        if room_name in _ROOM_TO_AGENT:
            existing_agent_id = _ROOM_TO_AGENT[room_name]
            logger.error(f"🚨 ========================================")
            logger.error(f"🚨 AGENT CONFLICT DETECTED!")
            logger.error(f"🚨 Room: {room_name}")
            logger.error(f"🚨 Already assigned to: {existing_agent_id}")
            logger.error(f"🚨 REJECTING duplicate job request")
            logger.error(f"🚨 ========================================")
            await job_request.reject()
            return'''

new_conflict_check = '''    # IMPROVED FIX: Check if this room already has an agent assigned AND has active participants
    async with _ROOM_ASSIGNMENT_LOCK:
        if room_name in _ROOM_TO_AGENT:
            existing_agent_id = _ROOM_TO_AGENT[room_name]

            # Check if room actually has participants (smarter conflict detection)
            try:
                from livekit_room_manager import RoomManager
                manager = RoomManager()
                participants = await manager.list_participants(room_name)
                participant_count = len(participants) if participants else 0
                await manager.close()

                if participant_count > 0:
                    # Room has actual participants - this is a real conflict
                    logger.error(f"🚨 ========================================")
                    logger.error(f"🚨 AGENT CONFLICT DETECTED!")
                    logger.error(f"🚨 Room: {room_name}")
                    logger.error(f"🚨 Already assigned to: {existing_agent_id}")
                    logger.error(f"🚨 Active participants: {participant_count}")
                    logger.error(f"🚨 REJECTING duplicate job request")
                    logger.error(f"🚨 ========================================")
                    await job_request.reject()
                    return
                else:
                    # Room is empty - stale assignment, clear it and continue
                    logger.warning(f"⚠️  Room {room_name} has stale assignment (no participants)")
                    logger.warning(f"⚠️  Clearing stale assignment and accepting new connection")
                    del _ROOM_TO_AGENT[room_name]
            except Exception as e:
                # Can't check participant count - be conservative and reject
                logger.error(f"🚨 Cannot verify room state: {e}")
                logger.error(f"🚨 REJECTING duplicate job request (safety)")
                await job_request.reject()
                return'''

# Apply the fix
if old_conflict_check in content:
    content = content.replace(old_conflict_check, new_conflict_check)

    # Backup original
    with open('letta_voice_agent_optimized.py.backup_conflict_fix', 'w') as f:
        with open('letta_voice_agent_optimized.py', 'r') as orig:
            f.write(orig.read())

    # Write fixed version
    with open('letta_voice_agent_optimized.py', 'w') as f:
        f.write(content)

    print("✅ Applied conflict detection fix")
    print("📁 Backup saved to: letta_voice_agent_optimized.py.backup_conflict_fix")
    print("")
    print("The fix adds smarter conflict detection that:")
    print("1. Checks if the room actually has participants")
    print("2. Clears stale assignments when room is empty")
    print("3. Only rejects if there's a real conflict")
    print("")
    print("Restart the voice agent to apply the fix:")
    print("  pkill -f letta_voice_agent_optimized")
    print("  /home/adamsl/planner/.venv/bin/python3 letta_voice_agent_optimized.py dev &")
else:
    print("❌ Could not find conflict detection code to fix")
    print("The code may have already been modified")
