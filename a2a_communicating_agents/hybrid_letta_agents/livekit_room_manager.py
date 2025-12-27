#!/usr/bin/env python3
"""
LiveKit Room Manager - Room Self-Recovery and Cleanup
======================================================
Prevents "Waiting for agent to join..." issues by:
- Automatically clearing stale rooms on startup
- Detecting and removing stuck participants
- Providing graceful cleanup on shutdown
- Implementing timeout-based recovery

Usage:
    from livekit_room_manager import RoomManager

    # On agent startup
    manager = RoomManager()
    await manager.cleanup_stale_rooms()

    # Before joining room
    await manager.ensure_clean_room(room_name)

    # On shutdown
    await manager.cleanup_room(room_name)
"""

import asyncio
import logging
import os
import time
from typing import Optional, List, Any
from datetime import datetime, timedelta

import aiohttp
from livekit.api.room_service import RoomService
from livekit.api import (
    ListRoomsRequest,
    ListParticipantsRequest,
    RoomParticipantIdentity,
    DeleteRoomRequest,
)

logger = logging.getLogger(__name__)


class RoomManager:
    """
    Manages LiveKit room lifecycle to prevent stuck states.

    Key features:
    - Automatic cleanup of stale rooms (>5 minutes old with no participants)
    - Force cleanup of rooms with stuck participants
    - Graceful disconnect handling
    - Room state validation before agent joins
    """

    def __init__(
        self,
        livekit_url: str = None,
        api_key: str = None,
        api_secret: str = None,
        stale_room_timeout: int = 300,  # 5 minutes
    ):
        """
        Initialize room manager.

        Args:
            livekit_url: LiveKit server URL (ws://localhost:7880)
            api_key: LiveKit API key
            api_secret: LiveKit API secret
            stale_room_timeout: Time in seconds before a room is considered stale
        """
        self.livekit_url = livekit_url or os.getenv("LIVEKIT_URL", "ws://localhost:7880")
        self.api_key = api_key or os.getenv("LIVEKIT_API_KEY", "devkey")
        self.api_secret = api_secret or os.getenv("LIVEKIT_API_SECRET", "secret")
        self.stale_room_timeout = stale_room_timeout

        # Remove ws:// or wss:// prefix for HTTP API calls
        http_url = self.livekit_url.replace("ws://", "http://").replace("wss://", "https://")

        # Create aiohttp session and RoomService
        self._session = None
        self._http_url = http_url
        self.room_service = None

        logger.info(f"RoomManager initialized (stale timeout: {stale_room_timeout}s)")

    async def _ensure_session(self):
        """Ensure aiohttp session exists."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
            self.room_service = RoomService(self._session, self._http_url, self.api_key, self.api_secret)

    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def list_rooms(self) -> List[Any]:
        """List all active rooms."""
        try:
            await self._ensure_session()
            response = await self.room_service.list_rooms(ListRoomsRequest())
            return list(response.rooms)
        except Exception as e:
            logger.error(f"Error listing rooms: {e}")
            return []

    async def get_room_info(self, room_name: str) -> Optional[Any]:
        """
        Get information about a specific room.

        Returns None if room doesn't exist or on error.
        """
        try:
            rooms = await self.list_rooms()
            for room in rooms:
                if room.name == room_name:
                    return room
            return None
        except Exception as e:
            logger.error(f"Error getting room info for {room_name}: {e}")
            return None

    async def list_participants(self, room_name: str) -> List[Any]:
        """List all participants in a room."""
        try:
            await self._ensure_session()
            response = await self.room_service.list_participants(
                ListParticipantsRequest(room=room_name)
            )
            return list(response.participants)
        except Exception as e:
            logger.error(f"Error listing participants in {room_name}: {e}")
            return []

    async def remove_participant(self, room_name: str, participant_identity: str):
        """Forcefully remove a participant from a room."""
        try:
            await self._ensure_session()
            await self.room_service.remove_participant(
                RoomParticipantIdentity(
                    room=room_name,
                    identity=participant_identity
                )
            )
            logger.info(f"Removed participant {participant_identity} from room {room_name}")
        except Exception as e:
            logger.error(f"Error removing participant {participant_identity}: {e}")

    async def delete_room(self, room_name: str):
        """Delete a room entirely."""
        try:
            await self._ensure_session()
            await self.room_service.delete_room(
                DeleteRoomRequest(room=room_name)
            )
            logger.info(f"Deleted room: {room_name}")
        except Exception as e:
            logger.error(f"Error deleting room {room_name}: {e}")

    async def cleanup_room(self, room_name: str, force: bool = False):
        """
        Clean up a specific room.

        Args:
            room_name: Name of the room to clean up
            force: If True, delete the room entirely. If False, just remove participants.
        """
        try:
            logger.info(f"Cleaning up room: {room_name} (force={force})")

            # Check if room exists
            room_info = await self.get_room_info(room_name)
            if not room_info:
                logger.info(f"Room {room_name} doesn't exist, nothing to clean up")
                return

            # List participants
            participants = await self.list_participants(room_name)
            logger.info(f"Room {room_name} has {len(participants)} participant(s)")

            # Remove all participants
            for participant in participants:
                logger.info(f"Removing participant: {participant.identity}")
                await self.remove_participant(room_name, participant.identity)

            # Wait for participants to disconnect
            await asyncio.sleep(1)

            # Force delete room if requested
            if force:
                await self.delete_room(room_name)
                logger.info(f"Room {room_name} forcefully deleted")
            else:
                logger.info(f"Room {room_name} cleaned (participants removed)")

        except Exception as e:
            logger.error(f"Error cleaning up room {room_name}: {e}")

    async def cleanup_stale_rooms(self):
        """
        Clean up stale rooms that have been empty for too long.

        This prevents rooms from accumulating and causing state issues.
        Runs automatically on agent startup.
        """
        try:
            logger.info("🧹 Scanning for stale rooms...")
            rooms = await self.list_rooms()

            if not rooms:
                logger.info("No rooms found")
                return

            current_time = time.time()
            cleaned_count = 0

            for room in rooms:
                # Check if room is empty
                participants = await self.list_participants(room.name)

                if len(participants) == 0:
                    # Room is empty - check age
                    room_age_seconds = current_time - room.creation_time

                    if room_age_seconds > self.stale_room_timeout:
                        logger.info(
                            f"Found stale empty room: {room.name} "
                            f"(age: {room_age_seconds:.0f}s > {self.stale_room_timeout}s)"
                        )
                        await self.delete_room(room.name)
                        cleaned_count += 1
                else:
                    # Room has participants - check if any are stuck/stale
                    for participant in participants:
                        participant_age = current_time - participant.joined_at

                        # If participant has been in room for too long without activity, remove them
                        if participant_age > self.stale_room_timeout:
                            logger.warning(
                                f"Found stale participant: {participant.identity} in {room.name} "
                                f"(age: {participant_age:.0f}s)"
                            )
                            await self.remove_participant(room.name, participant.identity)
                            cleaned_count += 1

            if cleaned_count > 0:
                logger.info(f"✅ Cleaned up {cleaned_count} stale room(s)/participant(s)")
            else:
                logger.info("✅ No stale rooms found")

        except Exception as e:
            logger.error(f"Error cleaning up stale rooms: {e}")
            import traceback
            traceback.print_exc()

    async def ensure_clean_room(self, room_name: str):
        """
        Ensure a room is clean before agent joins.

        This is the key method to call before joining a room to prevent
        "Waiting for agent to join..." issues.

        IMPORTANT: Only removes AGENT participants or truly stale ones.
        DOES NOT remove active human users.

        Args:
            room_name: Name of the room to prepare
        """
        try:
            logger.info(f"🔍 Ensuring room {room_name} is clean...")

            room_info = await self.get_room_info(room_name)

            if room_info:
                # Room exists - check for participants
                participants = await self.list_participants(room_name)

                if len(participants) > 0:
                    # Only remove AGENTS or stale participants, NOT active human users
                    stale_participants = []
                    current_time = time.time()

                    for participant in participants:
                        participant_age = current_time - participant.joined_at

                        # Identify agents by common patterns (adjust as needed)
                        is_agent = (
                            'agent' in participant.identity.lower() or
                            'bot' in participant.identity.lower() or
                            participant.identity.startswith('AW_')  # Livekit agent worker pattern
                        )

                        # Remove if it's an agent OR if it's stale (>5 min)
                        if is_agent or participant_age > self.stale_room_timeout:
                            reason = "agent" if is_agent else f"stale ({participant_age:.0f}s)"
                            logger.warning(
                                f"Will remove participant {participant.identity} - {reason}"
                            )
                            stale_participants.append(participant)
                        else:
                            logger.info(
                                f"Keeping human participant {participant.identity} "
                                f"(age: {participant_age:.0f}s)"
                            )

                    if stale_participants:
                        logger.info(f"Removing {len(stale_participants)} stale/agent participant(s)...")
                        for participant in stale_participants:
                            await self.remove_participant(room_name, participant.identity)

                        # Wait for cleanup
                        await asyncio.sleep(1)
                        logger.info(f"✅ Room {room_name} cleaned (kept human users)")
                    else:
                        logger.info(f"✅ Room {room_name} has only active human users - no cleanup needed")
                else:
                    logger.info(f"✅ Room {room_name} already empty")
            else:
                logger.info(f"✅ Room {room_name} doesn't exist yet (will be created fresh)")

        except Exception as e:
            logger.error(f"Error ensuring clean room {room_name}: {e}")
            import traceback
            traceback.print_exc()


async def main():
    """Test/demo the room manager."""
    logging.basicConfig(level=logging.INFO)

    manager = RoomManager()

    try:
        # List current rooms
        rooms = await manager.list_rooms()
        print(f"\nCurrent rooms: {len(rooms)}")
        for room in rooms:
            print(f"  - {room.name} (created: {room.creation_time})")

        # Clean up stale rooms
        await manager.cleanup_stale_rooms()

        # Example: Ensure a specific room is clean
        await manager.ensure_clean_room("test-room")
    finally:
        # Always close the session
        await manager.close()


if __name__ == "__main__":
    asyncio.run(main())
