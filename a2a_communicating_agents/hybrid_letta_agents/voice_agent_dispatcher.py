#!/usr/bin/env python3
"""
Shared helper for dispatching the Letta voice agent to a LiveKit room.

Encapsulates the aiohttp + LiveKit API plumbing so both the CORS proxy and
room health monitor can trigger dispatches without duplicating code.
"""

from __future__ import annotations

import asyncio
import logging
import os
from typing import Any, Dict

import aiohttp
from livekit.api import agent_dispatch_service, room_service

from livekit_room_manager import RoomManager

logger = logging.getLogger(__name__)

LIVEKIT_URL = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
LIVEKIT_HTTP_URL = LIVEKIT_URL.replace("ws://", "http://").replace("wss://", "https://")
LIVEKIT_API_KEY = os.getenv("LIVEKIT_API_KEY")
LIVEKIT_API_SECRET = os.getenv("LIVEKIT_API_SECRET")
DEFAULT_AGENT_NAME = os.getenv("VOICE_AGENT_DISPATCH_NAME", "letta-voice-agent")


async def dispatch_agent_async(room_name: str, agent_name: str | None = None) -> Dict[str, Any]:
    """
    Dispatch the configured voice agent to a LiveKit room.

    Returns a dict containing success status, dispatch_id, and whether the room existed.
    """
    if not room_name:
        raise ValueError("room_name is required for agent dispatch")

    if not LIVEKIT_API_KEY or not LIVEKIT_API_SECRET:
        raise RuntimeError("LIVEKIT_API_KEY and LIVEKIT_API_SECRET must be set")

    agent_label = agent_name or DEFAULT_AGENT_NAME

    # Proactively clear previous agent participants before dispatching again
    manager = RoomManager()
    try:
        await manager.ensure_clean_room(room_name)
    except Exception as cleanup_err:
        logger.warning("Pre-dispatch cleanup for %s failed: %s", room_name, cleanup_err)
    finally:
        await manager.close()

    async with aiohttp.ClientSession() as session:
        # RoomService is only used to emit helpful logs (room existence)
        room_svc = room_service.RoomService(
            session, LIVEKIT_HTTP_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET
        )
        dispatch_svc = agent_dispatch_service.AgentDispatchService(
            session, LIVEKIT_HTTP_URL, LIVEKIT_API_KEY, LIVEKIT_API_SECRET
        )

        room_exists = False
        try:
            rooms = await room_svc.list_rooms(room_service.ListRoomsRequest())
            room_exists = any(r.name == room_name for r in rooms.rooms)
            logger.info("Room check: '%s' exists=%s", room_name, room_exists)
        except Exception as err:
            logger.warning("Could not check room existence for %s: %s", room_name, err)

        dispatch_req = agent_dispatch_service.CreateAgentDispatchRequest(
            room=room_name,
            agent_name=agent_label,
        )

        dispatch_result = await dispatch_svc.create_dispatch(dispatch_req)
        dispatch_id = getattr(dispatch_result, "id", "unknown")

    logger.info(
        "Agent dispatch created for %s (agent=%s, dispatch_id=%s)",
        room_name,
        agent_label,
        dispatch_id,
    )

    return {
        "success": True,
        "room": room_name,
        "agent_name": agent_label,
        "dispatch_id": dispatch_id,
        "room_existed": room_exists,
        "message": f"Agent dispatched to room {room_name}",
    }


def dispatch_agent(room_name: str, agent_name: str | None = None) -> Dict[str, Any]:
    """
    Synchronous helper for contexts (like HTTP handlers) that are not async.
    """
    return asyncio.run(dispatch_agent_async(room_name, agent_name=agent_name))
