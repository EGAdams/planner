from pathlib import Path

import pytest

from orchestrator_agent.a2a_dispatcher import A2ADispatcher
from .a2a_test_utils import StubMemoryFactory, DummyMemoryBackend, write_agent_card


def test_dispatcher_refresh_and_delegate(tmp_path: Path) -> None:
    """Dispatcher should expose registry snapshots and Letta-backed delegations."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    write_agent_card(workspace, "planner-agent", ["planning"])

    dispatcher = A2ADispatcher(workspace_root=workspace, memory_factory=StubMemoryFactory(created_for=[]))
    registry = dispatcher.refresh_registry()

    assert "planner-agent" in registry
    snapshot = dispatcher.routing_snapshot()
    assert snapshot["planner-agent"]["topics"] == ["planning"]

    routing = dispatcher.delegate(
        agent_name="planner-agent",
        description="Plan weekly sprint",
        context={"sprint": "47"},
    )

    assert routing["topic"] == "planning"
    payload = routing["payload"]
    assert payload["params"]["target_agent"] == "planner-agent"

    backend = registry["planner-agent"].memory_backend
    assert isinstance(backend, DummyMemoryBackend)
    assert len(backend._entries) == 1
