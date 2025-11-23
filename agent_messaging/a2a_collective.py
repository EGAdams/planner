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

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Protocol, Tuple
from uuid import uuid4

from .memory_backend import MemoryBackend
from .memory_factory import MemoryFactory


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
    memory_namespace: Optional[str] = None


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
        self.memory_factory = memory_factory or MemoryFactory

    async def _create_memory_for_agent(self, agent_id: str) -> Tuple[str, MemoryBackend]:
        """
        Allocate a dedicated memory backend for a given agent.

        Uses the injected memory factory when provided, otherwise falls back to the
        production MemoryFactory implementation (Letta ƒƒ Chroma fallback chain).
        """
        factory = self.memory_factory
        if not factory or not hasattr(factory, "create_memory_async"):
            raise RuntimeError("No valid memory factory configured for the collective hub")
        return await factory.create_memory_async(agent_id=agent_id)

    async def discover_agents(self) -> Dict[str, AgentSpoke]:
        """
        Scan the workspace for agent cards and register each agent as a spoke.

        Discovers every `agent.json` file under the workspace root and provisions a
        unique memory backend per agent so that the orchestrator can enforce
        hub-and-spoke isolation with Letta memory as the canonical backing store.
        """
        registry: Dict[str, AgentSpoke] = {}

        if not self.workspace_root.exists():
            return registry

        for card_path in sorted(self.workspace_root.rglob("agent.json")):
            try:
                card_data = json.loads(card_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue

            agent_name = card_data.get("name")
            if not agent_name or agent_name in registry:
                continue

            capabilities = card_data.get("capabilities") or []
            topics = card_data.get("topics") or []

            agent_card = AgentCard(
                name=agent_name,
                version=card_data.get("version", "0.0.0"),
                description=card_data.get("description", ""),
                capabilities=capabilities,
                topics=topics,
            )

            memory_backend_name, memory_backend = await self._create_memory_for_agent(agent_name)

            memory_namespace = getattr(memory_backend, "namespace", None)

            registry[agent_name] = AgentSpoke(
                card=agent_card,
                memory_backend=memory_backend,
                memory_backend_name=memory_backend_name,
                topics=topics,
                memory_namespace=memory_namespace,
            )

        return registry

    def routing_snapshot(self, registry: Dict[str, AgentSpoke]) -> Dict[str, Dict[str, Any]]:
        """
        Produce a normalized routing table similar to CLAUDE's collective routing matrix.

        Each entry includes topics, capability names, and descriptive metadata so the
        orchestrator can reason about delegations without re-reading every agent card.
        """
        snapshot: Dict[str, Dict[str, Any]] = {}
        for agent_name, spoke in registry.items():
            capability_names = [
                cap.get("name")
                for cap in (spoke.card.capabilities or [])
                if isinstance(cap, dict) and isinstance(cap.get("name"), str)
            ]
            memory_backend = spoke.memory_backend
            backend_connected: Optional[bool] = None
            if memory_backend and hasattr(memory_backend, "is_connected"):
                try:
                    backend_connected = bool(memory_backend.is_connected())
                except Exception:
                    backend_connected = None

            memory_info: Dict[str, Any] = {
                "backend": spoke.memory_backend_name,
                "connected": backend_connected,
            }
            if spoke.memory_namespace:
                memory_info["namespace"] = spoke.memory_namespace

            snapshot[agent_name] = {
                "topics": spoke.topics or spoke.card.topics,
                "capabilities": capability_names,
                "description": spoke.card.description,
                "version": spoke.card.version,
                "memory": memory_info,
            }
        return snapshot

    async def prepare_delegation(
        self,
        registry: Dict[str, AgentSpoke],
        agent_name: str,
        description: str,
        context: Optional[Dict] = None,
        artifacts: Optional[List[str]] = None,
    ) -> Dict[str, Dict]:
        """
        Build the JSON-RPC payload and routing topic for an agent delegation.

        Returns a dict containing:
            {
                "topic": <topic string>,
                "payload": <json-rpc dict>
            }
        """
        if agent_name not in registry:
            raise ValueError(f"Unknown agent '{agent_name}' in registry")

        spoke = registry[agent_name]
        topics = spoke.topics or spoke.card.topics
        topic = topics[0] if topics else "general"

        payload = {
            "jsonrpc": "2.0",
            "method": "agent.execute_task",
            "params": {
                "task_id": str(uuid4()),
                "target_agent": agent_name,
                "description": description,
                "context": context or {},
                "artifacts": artifacts or [],
            },
            "id": 1,
        }

        await self._log_delegation(spoke, payload["params"])

        return {"topic": topic, "payload": payload}

    async def _log_delegation(self, spoke: AgentSpoke, params: Dict) -> None:
        """Record delegation metadata in the agent's memory backend."""
        memory = spoke.memory_backend
        if not memory:
            return

        content = (
            f"Task {params['task_id']} delegated to {spoke.card.name}: "
            f"{params['description']}"
        )
        metadata = {
            "kind": "delegation",
            "target_agent": spoke.card.name,
        }

        try:
            await memory.remember(
                content=content,
                memory_type="task",
                source="a2a-collective-hub",
                metadata=metadata,
            )
        except Exception:
            # Memory logging failures should not block orchestration
            pass
