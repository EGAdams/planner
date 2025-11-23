"""
Red-phase tests for the A2A Collective hub.

These tests define the first slice of behavior for an orchestrator-centric
hub-and-spoke system that uses Google's A2A protocol plus per-agent Letta memory.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_messaging.a2a_collective import A2ACollectiveHub
from .a2a_test_utils import DummyMemoryBackend, StubMemoryFactory, write_agent_card


@pytest.mark.asyncio
async def test_discover_agents_assigns_dedicated_letta_memory(tmp_path: Path) -> None:
    """
    The orchestrator hub should load all agent cards and attach a unique Letta-backed
    memory instance to every spoke. This enforces hub-and-spoke isolation where each
    agent recalls only its own Letta namespace.
    """
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    write_agent_card(workspace, "planner-agent", ["general", "planner"])
    write_agent_card(workspace, "dashboard-ops-agent", ["ops"])

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
    write_agent_card(workspace, "planner-agent", ["general", "planner"])
    write_agent_card(workspace, "dashboard-ops-agent", ["ops"])

    memory_factory = StubMemoryFactory(created_for=[])
    hub = A2ACollectiveHub(workspace_root=workspace, memory_factory=memory_factory)

    registry = await hub.discover_agents()
    snapshot = hub.routing_snapshot(registry)

    assert snapshot["planner-agent"]["topics"] == ["general", "planner"]
    assert snapshot["dashboard-ops-agent"]["topics"] == ["ops"]
    assert snapshot["planner-agent"]["capabilities"] == ["execute_task"]


@pytest.mark.asyncio
async def test_prepare_delegation_returns_jsonrpc_payload(tmp_path: Path) -> None:
    """
    The hub should emit an A2A-compliant JSON-RPC payload (plus routing topic)
    when orchestrator assigns a task to a known agent.
    """
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    write_agent_card(workspace, "planner-agent", ["planning", "general"])

    hub = A2ACollectiveHub(workspace_root=workspace, memory_factory=StubMemoryFactory(created_for=[]))
    registry = await hub.discover_agents()

    routing = await hub.prepare_delegation(
        registry=registry,
        agent_name="planner-agent",
        description="Investigate failing dashboard tests",
        context={"priority": "high"},
    )

    assert routing["topic"] == "planning"
    payload = routing["payload"]
    assert payload["jsonrpc"] == "2.0"
    assert payload["method"] == "agent.execute_task"
    assert payload["params"]["description"] == "Investigate failing dashboard tests"
    assert payload["params"]["context"]["priority"] == "high"
    assert payload["params"]["target_agent"] == "planner-agent"
    assert isinstance(payload["params"]["task_id"], str) and payload["params"]["task_id"]


@pytest.mark.asyncio
async def test_delegation_is_logged_to_agent_memory(tmp_path: Path) -> None:
    """
    Preparing a delegation should write a memory entry for that agent so Letta
    histories capture every hub handoff.
    """
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    write_agent_card(workspace, "planner-agent", ["planner"])

    memory_factory = StubMemoryFactory(created_for=[])
    hub = A2ACollectiveHub(workspace_root=workspace, memory_factory=memory_factory)
    registry = await hub.discover_agents()

    await hub.prepare_delegation(
        registry=registry,
        agent_name="planner-agent",
        description="Draft CLAUDE collective charter",
        context={"phase": "research"},
    )

    backend = registry["planner-agent"].memory_backend
    assert isinstance(backend, DummyMemoryBackend)
    assert len(backend._entries) == 1
    entry = backend._entries[0]
    assert "Draft CLAUDE collective charter" in entry.content
    assert entry.metadata.get("kind") == "delegation"
