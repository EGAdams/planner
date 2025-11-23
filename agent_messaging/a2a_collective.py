"""
Agent Collective scaffolding for Google's A2A protocol.

Provides the high-level hub-and-spoke orchestration primitives required to mirror
the CLAUDE collective workflow inside this codebase. The orchestrator behaves as
the GoF Mediator, while the pluggable memory factory acts as an Abstract Factory
that provisions agent-specific Letta backends.

This module intentionally contains just enough scaffolding for the first TDD
cycle. Functional logic will be implemented after the red test is in place.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Protocol, Tuple

from .memory_backend import MemoryBackend


@dataclass
class AgentCard:
    """Represents the minimal metadata parsed from an agent.json file."""

    name: str
    version: str
    description: str
    capabilities: List[Dict]
    topics: List[str]


@dataclass
class AgentSpoke:
    """
    Container for a registered agent inside the collective.

    Holds the parsed card plus references to an allocated memory backend.
    """

    card: AgentCard
    memory_backend: MemoryBackend
    memory_backend_name: str
    topics: List[str] = field(default_factory=list)


class MemoryFactoryProtocol(Protocol):
    """Thin protocol so we can inject fake factories during tests."""

    async def create_memory_async(self, agent_id: str, **kwargs) -> Tuple[str, MemoryBackend]:
        ...


class A2ACollectiveHub:
    """
    Central coordinator for the A2A collective.

    Discovers agent cards, provisions memory per spoke, and exposes helper
    accessors so the orchestrator can enforce hub-and-spoke routing rules.
    """

    def __init__(
        self,
        workspace_root: Path,
        memory_factory: Optional[MemoryFactoryProtocol] = None,
    ) -> None:
        self.workspace_root = workspace_root
        self.memory_factory = memory_factory

    async def discover_agents(self) -> Dict[str, AgentSpoke]:
        """
        Scan the workspace for agent cards and register each agent as a spoke.

        TDD placeholder: actual implementation arrives in the next (green) phase.
        """
        raise NotImplementedError("discover_agents is not implemented yet")
