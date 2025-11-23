"""
Synchronous adapter between the orchestrator agent and the async A2A hub.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Dict, Optional

from agent_messaging.a2a_collective import A2ACollectiveHub, AgentSpoke


class A2ADispatcher:
    """Wrap A2ACollectiveHub with blocking helpers for the orchestrator."""

    def __init__(self, workspace_root: Path, memory_factory=None) -> None:
        self.hub = A2ACollectiveHub(workspace_root=workspace_root, memory_factory=memory_factory)
        self.registry: Dict[str, AgentSpoke] = {}

    def refresh_registry(self) -> Dict[str, AgentSpoke]:
        """Load all agent cards and remember them locally."""
        self.registry = asyncio.run(self.hub.discover_agents())
        return self.registry

    def routing_snapshot(self) -> Dict[str, Dict]:
        """Return a stable routing view of the current registry."""
        return self.hub.routing_snapshot(self.registry)

    def delegate(
        self,
        agent_name: str,
        description: str,
        context: Optional[Dict] = None,
        artifacts: Optional[list] = None,
    ) -> Dict[str, Dict]:
        """Generate the routing topic plus JSON-RPC payload for a delegation."""
        if not self.registry:
            self.refresh_registry()
        return asyncio.run(
            self.hub.prepare_delegation(
                registry=self.registry,
                agent_name=agent_name,
                description=description,
                context=context,
                artifacts=artifacts,
            )
        )
