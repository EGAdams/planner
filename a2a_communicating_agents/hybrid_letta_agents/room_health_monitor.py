#!/usr/bin/env python3
"""
LiveKit Room Health Monitor - Prevents stuck room states.

Runs in background and:
1. Monitors all rooms every 30 seconds
2. Detects stuck states (empty rooms, stale participants)
3. Automatically cleans up problematic rooms
4. Logs issues for debugging

This service prevents the "Waiting for agent to join..." loop by proactively
detecting and fixing stuck room states before they cause connection issues.
"""

import asyncio
import logging
import time
from livekit_room_manager import RoomManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RoomHealthMonitor:
    """
    Monitors LiveKit room health and automatically recovers stuck states.

    Key features:
    - Periodic health checks every 30 seconds
    - Detects empty stale rooms (>5 minutes old)
    - Detects stuck participants
    - Automatic cleanup and recovery
    - Detailed logging for debugging
    """

    def __init__(self, check_interval_seconds=30):
        """
        Initialize the health monitor.

        Args:
            check_interval_seconds: How often to check room health (default: 30s)
        """
        self.check_interval = check_interval_seconds
        self.manager = RoomManager()
        self.cleanup_count = 0
        self.check_count = 0

    async def monitor_loop(self):
        """Main monitoring loop - runs continuously."""
        logger.info(f"🏥 Room health monitor started (check interval: {self.check_interval}s)")
        logger.info("   Monitor will detect and fix:")
        logger.info("   • Empty rooms older than 5 minutes")
        logger.info("   • Stuck/stale participants")
        logger.info("   • Rooms with mismatched participant counts")

        while True:
            try:
                await self.check_room_health()
            except Exception as e:
                logger.error(f"Error in health check: {e}")
                import traceback
                traceback.print_exc()

            await asyncio.sleep(self.check_interval)

    async def check_room_health(self):
        """Check health of all rooms and clean up issues."""
        self.check_count += 1
        rooms = await self.manager.list_rooms()

        if not rooms:
            logger.debug(f"Health check #{self.check_count}: No active rooms")
            return

        logger.info(f"🔍 Health check #{self.check_count}: Checking {len(rooms)} room(s)...")

        for room in rooms:
            try:
                # Get room participants
                participants = await self.manager.list_participants(room.name)

                # Check for stuck states
                if len(participants) == 0 and room.num_participants > 0:
                    logger.warning(
                        f"⚠️  Room {room.name} shows {room.num_participants} participants "
                        f"but API returns 0 - stuck state detected"
                    )
                    await self.recover_stuck_room(room.name)
                    continue

                # Check for stale rooms (empty for >5 minutes)
                room_age = time.time() - room.creation_time
                if len(participants) == 0 and room_age > 300:
                    logger.info(
                        f"🧹 Cleaning up stale empty room: {room.name} "
                        f"(age: {room_age:.0f}s, threshold: 300s)"
                    )
                    await self.manager.delete_room(room.name)
                    self.cleanup_count += 1
                    continue

                # Check for stale participants (>10 minutes inactive)
                current_time = time.time()
                for participant in participants:
                    participant_age = current_time - participant.joined_at

                    # Only check agent participants, not humans
                    is_agent = (
                        'agent' in participant.identity.lower() or
                        'bot' in participant.identity.lower() or
                        participant.identity.startswith('AW_')
                    )

                    if is_agent and participant_age > 600:  # 10 minutes
                        logger.warning(
                            f"⚠️  Stale agent participant: {participant.identity} in {room.name} "
                            f"(age: {participant_age:.0f}s, threshold: 600s)"
                        )
                        await self.manager.remove_participant(room.name, participant.identity)
                        self.cleanup_count += 1

            except Exception as e:
                logger.error(f"Error checking room {room.name}: {e}")

        # Log summary every 10 checks
        if self.check_count % 10 == 0:
            logger.info(
                f"📊 Health monitor summary: {self.check_count} checks completed, "
                f"{self.cleanup_count} cleanups performed"
            )

    async def recover_stuck_room(self, room_name: str):
        """
        Attempt to recover a stuck room.

        A stuck room is one that shows participants in metadata but none via API.
        This typically happens when LiveKit server state is inconsistent.

        Recovery strategy:
        1. Try to clean the room (remove stale participants)
        2. If that fails, delete the room entirely
        """
        logger.info(f"🔧 Attempting to recover stuck room: {room_name}")

        try:
            # Try to clean the room first
            await self.manager.ensure_clean_room(room_name)
            logger.info(f"✅ Successfully recovered room: {room_name}")
            self.cleanup_count += 1
        except Exception as e:
            logger.error(f"Failed to clean room {room_name}: {e}")

            # Last resort: delete the room
            try:
                await self.manager.delete_room(room_name)
                logger.info(f"🗑️  Deleted problematic room: {room_name}")
                self.cleanup_count += 1
            except Exception as delete_error:
                logger.error(f"Failed to delete room {room_name}: {delete_error}")


async def main():
    """Main entry point - runs the health monitor continuously."""
    monitor = RoomHealthMonitor(check_interval_seconds=30)

    try:
        await monitor.monitor_loop()
    except KeyboardInterrupt:
        logger.info("Health monitor stopped by user")
    except Exception as e:
        logger.error(f"Health monitor crashed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up
        await monitor.manager.close()


if __name__ == "__main__":
    asyncio.run(main())
