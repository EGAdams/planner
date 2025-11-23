"""
Red-phase tests for the A2A Collective hub.

These tests define the first slice of behavior for an orchestrator-centric
hub-and-spoke system that uses Google's A2A protocol plus per-agent Letta memory.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytest

from agent_messaging.memory_backend import MemoryBackend, MemoryEntry
from agent_messaging.a2a_collective import A2ACollectiveHub


class DummyMemoryBackend(MemoryBackend):
    """
    Minimal in-memory backend so the hub can attach a unique memory to each agent.

    Implements the MemoryBackend Strategy interface so we preserve the API surface
    while keeping assertions focused on per-agent isolation.
    """

    def __init__(self, namespace: str) -> None:
        self.namespace = namespace
        self._connected = True
        self._entries: List[MemoryEntry] = []

    async def connect(self) -> None:
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False

    async def remember(
        self,
        content: str,
        memory_type: str = "general",
        source: str = "unknown",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict] = None,
    ) -> str:
        entry_id = f"{self.namespace}:{len(self._entries)}"
        entry = MemoryEntry(
            id=entry_id,
            content=content,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
            tags=tags or [],
            source=source,
            memory_type=memory_type,
        )
        self._entries.append(entry)
        return entry_id

    async def recall(
        self,
        query: str,
        limit: int = 5,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata_filter: Optional[Dict] = None,
    ) -> List[MemoryEntry]:
        return self._entries[:limit]

    async def get_recent(
        self, limit: int = 10, memory_type: Optional[str] = None
    ) -> List[MemoryEntry]:
        return list(reversed(self._entries[-limit:]))

    async def forget(self, memory_id: str) -> bool:
        for index, entry in enumerate(self._entries):
            if entry.id == memory_id:
                self._entries.pop(index)
                return True
        return False

    async def get_stats(self) -> Dict:
        return {"entries": len(self._entries)}

    def is_connected(self) -> bool:
        return self._connected


@dataclass
class StubMemoryFactory:
    """Records each agent that requests a memory backend."""

    created_for: List[str]

    async def create_memory_async(self, agent_id: str, **_: Dict) -> Tuple[str, MemoryBackend]:
        self.created_for.append(agent_id)
        return ("letta", DummyMemoryBackend(namespace=f"letta://{agent_id}"))


def _write_agent_card(root: Path, name: str, topics: List[str]) -> None:
    agent_dir = root / name
    agent_dir.mkdir(parents=True)
    card = {
        "name": name,
        "version": "1.0.0",
        "description": f"{name} test agent",
        "capabilities": [
            {
                "name": "execute_task",
                "description": "Run assigned work items",
                "input_schema": {"type": "object"},
                "output_schema": {"type": "object"},
            }
        ],
        "topics": topics,
    }
    (agent_dir / "agent.json").write_text(json.dumps(card), encoding="utf-8")


@pytest.mark.asyncio
async def test_discover_agents_assigns_dedicated_letta_memory(tmp_path: Path) -> None:
    """
    The orchestrator hub should load all agent cards and attach a unique Letta-backed
    memory instance to every spoke. This enforces hub-and-spoke isolation where each
    agent recalls only its own Letta namespace.
    """
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _write_agent_card(workspace, "planner-agent", ["general", "planner"])
    _write_agent_card(workspace, "dashboard-ops-agent", ["ops"])

    memory_factory = StubMemoryFactory(created_for=[])
    hub = A2ACollectiveHub(workspace_root=workspace, memory_factory=memory_factory)

    registry = await hub.discover_agents()

    assert set(registry.keys()) == {"planner-agent", "dashboard-ops-agent"}
    for agent_name, spoke in registry.items():
        assert spoke.card.name == agent_name
        assert spoke.memory_backend is not None
        assert isinstance(spoke.memory_backend, DummyMemoryBackend)
        assert spoke.memory_backend.namespace == f"letta://{agent_name}"

    # Each agent must have a dedicated backend instance (no shared references)
    backend_ids = {id(spoke.memory_backend) for spoke in registry.values()}
    assert len(backend_ids) == 2
    assert sorted(memory_factory.created_for) == ["dashboard-ops-agent", "planner-agent"]


@pytest.mark.asyncio
async def test_routing_metadata_exposes_topics_and_capabilities(tmp_path: Path) -> None:
    """
    After discovery, the hub should produce a routing snapshot that mirrors the
    Claude collective routing matrix—topics and capability names per agent.
    """
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _write_agent_card(workspace, "planner-agent", ["general", "planner"])
    _write_agent_card(workspace, "dashboard-ops-agent", ["ops"])

    memory_factory = StubMemoryFactory(created_for=[])
    hub = A2ACollectiveHub(workspace_root=workspace, memory_factory=memory_factory)

    registry = await hub.discover_agents()
    snapshot = hub.routing_snapshot(registry)

    assert snapshot["planner-agent"]["topics"] == ["general", "planner"]
    assert snapshot["dashboard-ops-agent"]["topics"] == ["ops"]
    assert snapshot["planner-agent"]["capabilities"] == ["execute_task"]
