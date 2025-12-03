"""
Shared stubs for exercising the A2A collective hub without real Letta services.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from a2a_communicating_agents.agent_messaging.memory_backend import MemoryBackend, MemoryEntry


class DummyMemoryBackend(MemoryBackend):
    """
    Minimal in-memory backend so tests can assert Letta logging without a server.
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
            timestamp=datetime.now(timezone.utc),
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


def write_agent_card(root: Path, name: str, topics: List[str]) -> None:
    """Create a minimal agent.json file for tests."""
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
