#!/usr/bin/env python3
"""
LiveKit Room Cleanup Script for Agent_66 Voice Connection
==========================================================
This script cleans out stuck LiveKit rooms to fix voice connection issues.

Steps:
1. Lists all active LiveKit rooms
2. Shows all participants in each room
3. Removes stuck agent participants
4. Optionally deletes empty rooms
5. Verifies the room is ready for fresh connection

Usage:
    python3 cleanup_livekit_room.py [--force-delete]
"""

import asyncio
import logging
import sys
import argparse
from livekit_room_manager import RoomManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def cleanup_all_rooms(force_delete: bool = False):
    """
    Clean up all LiveKit rooms and prepare for fresh connections.

    Args:
        force_delete: If True, delete all rooms entirely. If False, just remove agents/stale participants.
    """
    manager = RoomManager()

    try:
        logger.info("=" * 60)
        logger.info("LIVEKIT ROOM CLEANUP - STARTING")
        logger.info("=" * 60)

        # Step 1: List all rooms
        logger.info("\n1️⃣  Listing all active rooms...")
        rooms = await manager.list_rooms()

        if not rooms:
            logger.info("✅ No rooms found - system is clean!")
            return

        logger.info(f"Found {len(rooms)} room(s):")
        for room in rooms:
            logger.info(f"  📦 Room: {room.name}")
            logger.info(f"     Created: {room.creation_time}")
            logger.info(f"     Participants: {room.num_participants}")

        # Step 2: Examine each room's participants
        logger.info("\n2️⃣  Examining participants in each room...")
        for room in rooms:
            logger.info(f"\n  📦 Room: {room.name}")
            participants = await manager.list_participants(room.name)

            if not participants:
                logger.info("     No participants")
            else:
                logger.info(f"     Found {len(participants)} participant(s):")
                for p in participants:
                    logger.info(f"       - Identity: {p.identity}")
                    logger.info(f"         State: {p.state}")
                    logger.info(f"         Joined: {p.joined_at}")
                    logger.info(f"         Is publisher: {p.is_publisher}")

                    # Identify if it's an agent
                    is_agent = (
                        'agent' in p.identity.lower() or
                        'bot' in p.identity.lower() or
                        p.identity.startswith('AW_')
                    )
                    if is_agent:
                        logger.warning(f"         ⚠️  This is an AGENT participant")

        # Step 3: Clean up rooms
        logger.info("\n3️⃣  Cleaning up rooms...")
        for room in rooms:
            if force_delete:
                logger.info(f"  🗑️  Deleting room: {room.name}")
                await manager.cleanup_room(room.name, force=True)
            else:
                logger.info(f"  🧹 Cleaning room (removing agents/stale participants): {room.name}")
                await manager.ensure_clean_room(room.name)

        # Step 4: Verify cleanup
        logger.info("\n4️⃣  Verifying cleanup...")
        await asyncio.sleep(1)
        rooms_after = await manager.list_rooms()

        if not rooms_after:
            logger.info("✅ All rooms cleaned/deleted successfully!")
        else:
            logger.info(f"Remaining rooms: {len(rooms_after)}")
            for room in rooms_after:
                participants = await manager.list_participants(room.name)
                logger.info(f"  📦 {room.name}: {len(participants)} participant(s)")
                for p in participants:
                    logger.info(f"     - {p.identity}")

        logger.info("\n" + "=" * 60)
        logger.info("LIVEKIT ROOM CLEANUP - COMPLETE")
        logger.info("=" * 60)
        logger.info("\n✅ Voice system is ready for Agent_66 connection")
        logger.info("   Next steps:")
        logger.info("   1. Refresh your browser page (voice-agent-selector.html)")
        logger.info("   2. Select Agent_66 from the dropdown")
        logger.info("   3. Click 'Connect Voice Agent'")
        logger.info("   4. Test voice connection")

    except Exception as e:
        logger.error(f"❌ Error during cleanup: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await manager.close()


async def verify_agent_exists():
    """Verify that Agent_66 exists in Letta."""
    import httpx
    import os
    from dotenv import load_dotenv

    load_dotenv("/home/adamsl/planner/.env", override=True)

    letta_url = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")

    logger.info("\n5️⃣  Verifying Agent_66 exists in Letta...")

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(f"{letta_url}/v1/agents/")  # CRITICAL: Trailing slash required
            response.raise_for_status()
            agents = response.json()

            logger.info(f"Found {len(agents)} agent(s) in Letta:")

            agent_66 = None
            for agent in agents:
                agent_name = agent.get('name', 'unknown')
                agent_id = agent.get('id', 'unknown')
                logger.info(f"  - {agent_name} (ID: {agent_id})")

                if agent_name == "Agent_66":
                    agent_66 = agent

            if agent_66:
                logger.info(f"\n✅ Agent_66 FOUND!")
                logger.info(f"   Name: {agent_66['name']}")
                logger.info(f"   ID: {agent_66['id']}")
                logger.info(f"\n   Set this in your .env file:")
                logger.info(f"   VOICE_PRIMARY_AGENT_ID={agent_66['id']}")
                return agent_66
            else:
                logger.error("\n❌ Agent_66 NOT FOUND in Letta!")
                logger.error("   Please verify the agent exists before connecting voice")
                return None

    except Exception as e:
        logger.error(f"❌ Error verifying agent: {e}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    parser = argparse.ArgumentParser(description='Clean up LiveKit rooms for voice agent')
    parser.add_argument(
        '--force-delete',
        action='store_true',
        help='Delete all rooms entirely (not just participants)'
    )
    parser.add_argument(
        '--verify-agent',
        action='store_true',
        help='Verify Agent_66 exists in Letta'
    )

    args = parser.parse_args()

    # Always verify agent first
    agent_66 = await verify_agent_exists()

    if args.verify_agent:
        # Just verify, don't clean
        return

    # Clean up rooms
    await cleanup_all_rooms(force_delete=args.force_delete)


if __name__ == "__main__":
    asyncio.run(main())
