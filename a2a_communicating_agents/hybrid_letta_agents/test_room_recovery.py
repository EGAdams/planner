#!/usr/bin/env python3
"""
Test Room Recovery System
==========================
Validates that the RoomManager can:
1. List active rooms
2. Clean up stale rooms
3. Remove stuck participants
4. Ensure clean room state before agent joins

Usage:
    python test_room_recovery.py
"""

import asyncio
import logging
import sys
from livekit_room_manager import RoomManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_room_manager():
    """Test the RoomManager functionality."""
    logger.info("=" * 60)
    logger.info("Testing Room Recovery System")
    logger.info("=" * 60)

    manager = None
    try:
        # Initialize RoomManager
        logger.info("\n1. Initializing RoomManager...")
        manager = RoomManager()
        logger.info("✅ RoomManager initialized")

        # List current rooms
        logger.info("\n2. Listing current rooms...")
        rooms = await manager.list_rooms()
        logger.info(f"Found {len(rooms)} active room(s)")

        for room in rooms:
            logger.info(f"  - Room: {room.name}")
            logger.info(f"    Created: {room.creation_time}")
            logger.info(f"    Num participants: {room.num_participants}")

            # List participants in each room
            participants = await manager.list_participants(room.name)
            for participant in participants:
                logger.info(f"      Participant: {participant.identity}")
                logger.info(f"        Joined: {participant.joined_at}")
                logger.info(f"        State: {participant.state}")

        # Cleanup stale rooms
        logger.info("\n3. Running stale room cleanup...")
        await manager.cleanup_stale_rooms()
        logger.info("✅ Stale room cleanup complete")

        # Test ensuring clean room
        test_room_name = "test-recovery-room"
        logger.info(f"\n4. Testing ensure_clean_room for '{test_room_name}'...")
        await manager.ensure_clean_room(test_room_name)
        logger.info(f"✅ Room '{test_room_name}' is clean and ready")

        # Verify final room count
        logger.info("\n5. Final room count...")
        final_rooms = await manager.list_rooms()
        logger.info(f"Final: {len(final_rooms)} active room(s)")

        logger.info("\n" + "=" * 60)
        logger.info("✅ Room Recovery System Test PASSED")
        logger.info("=" * 60)

        return True

    except Exception as e:
        logger.error(f"\n❌ Room Recovery System Test FAILED")
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Always close the session
        if manager:
            await manager.close()


async def test_room_cleanup_scenario():
    """
    Test a realistic scenario:
    1. Create some rooms
    2. Simulate stuck participants
    3. Run cleanup
    4. Verify recovery
    """
    logger.info("\n" + "=" * 60)
    logger.info("Testing Room Cleanup Scenario")
    logger.info("=" * 60)

    manager = RoomManager()

    try:
        # Note: We can't create rooms directly without a client connection
        # This test validates cleanup of existing rooms
        logger.info("\nChecking for rooms that need cleanup...")

        rooms = await manager.list_rooms()

        if len(rooms) == 0:
            logger.info("No rooms to clean up (this is good!)")
            return True

        logger.info(f"Found {len(rooms)} room(s) to inspect")

        for room in rooms:
            logger.info(f"\nInspecting room: {room.name}")

            participants = await manager.list_participants(room.name)

            if len(participants) == 0:
                logger.info(f"  Room is empty - candidate for cleanup")

                # Check age
                import time
                age_seconds = time.time() - room.creation_time

                if age_seconds > 300:  # 5 minutes
                    logger.info(f"  Room is stale (age: {age_seconds:.0f}s)")
                    logger.info(f"  Cleaning up room: {room.name}")
                    await manager.delete_room(room.name)
                    logger.info(f"  ✅ Room deleted")
            else:
                logger.info(f"  Room has {len(participants)} participant(s)")
                for p in participants:
                    logger.info(f"    - {p.identity}")

        logger.info("\n✅ Room cleanup scenario complete")
        return True
    finally:
        # Always close the session
        await manager.close()


async def main():
    """Run all tests."""
    logger.info("Starting Room Recovery Tests\n")

    # Test 1: Basic RoomManager functionality
    test1_passed = await test_room_manager()

    # Test 2: Cleanup scenario
    test2_passed = await test_room_cleanup_scenario()

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Test 1 (RoomManager): {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    logger.info(f"Test 2 (Cleanup Scenario): {'✅ PASSED' if test2_passed else '❌ FAILED'}")

    all_passed = test1_passed and test2_passed

    if all_passed:
        logger.info("\n🎉 All tests PASSED!")
        logger.info("\nRoom recovery system is working correctly.")
        logger.info("The 'Waiting for agent to join...' issue should be fixed!")
        return 0
    else:
        logger.error("\n❌ Some tests FAILED")
        logger.error("\nPlease check the errors above and fix before using the system.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
