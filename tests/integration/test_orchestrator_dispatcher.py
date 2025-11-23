"""
Integration-flavored tests verifying the orchestrator cooperates with the
dispatcher/hub stack and records delegations into agent memory.
"""

from __future__ import annotations

import asyncio
import shutil
import socket
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

import pytest

from orchestrator_agent import main as orchestrator_main
from orchestrator_agent.a2a_dispatcher import A2ADispatcher
from tests.unit.a2a_test_utils import DummyMemoryBackend, StubMemoryFactory, write_agent_card


def _get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_for_server(base_url: str, timeout: float = 20.0) -> None:
    parsed = urlparse(base_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 8283
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError(f"Letta server at {base_url} did not become ready in time")


def test_orchestrator_delegation_records_memory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Smoke test: orchestrator routing should log the delegation into Letta memory."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    write_agent_card(workspace, "planner-agent", ["planning"])

    memory_factory = StubMemoryFactory(created_for=[])
    dispatcher = A2ADispatcher(workspace_root=workspace, memory_factory=memory_factory)

    monkeypatch.setattr(orchestrator_main, "WORKSPACE_ROOT", workspace)
    monkeypatch.setattr(orchestrator_main, "A2ADispatcher", lambda *_, **__: dispatcher)
    monkeypatch.setattr(orchestrator_main, "DocumentManager", lambda: object())

    orchestrator = orchestrator_main.Orchestrator()
    orchestrator.discover_agents()

    decision = orchestrator._fallback_route("planner-agent please plan the sprint")
    assert decision is not None
    assert decision["target_agent"] == "planner-agent"

    delegation = orchestrator.dispatcher.delegate(
        agent_name=decision["target_agent"],
        description=decision["params"]["description"],
        context=decision["params"].get("context", {}),
    )
    assert delegation["topic"] == "planning"

    backend = dispatcher.registry["planner-agent"].memory_backend
    assert isinstance(backend, DummyMemoryBackend)
    assert len(backend._entries) == 1
    assert backend._entries[0].metadata["kind"] == "delegation"

    agent_metadata = orchestrator.known_agents["planner-agent"]
    memory_info = agent_metadata["memory"]
    assert memory_info["backend"] == "letta"
    assert memory_info["connected"] is True
    assert memory_info["namespace"] == "letta://planner-agent"


@pytest.mark.skipif(shutil.which("letta") is None, reason="letta CLI is not installed")
def test_orchestrator_logs_to_real_letta(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Boot a real Letta server and verify delegations persist via the true backend."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    write_agent_card(workspace, "planner-agent", ["planning"])

    port = _get_free_port()
    base_url = f"http://127.0.0.1:{port}"

    server = subprocess.Popen(
        ["letta", "server", "--port", str(port), "--host", "127.0.0.1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        try:
            _wait_for_server(base_url)
        except RuntimeError as exc:
            server.terminate()
            output = ""
            try:
                output = server.communicate(timeout=10)[0]
            except Exception:
                pass
            pytest.skip(f"Letta server unavailable ({exc}); output: {output[-400:]}")
        monkeypatch.setenv("LETTA_BASE_URL", base_url)
        monkeypatch.setattr(orchestrator_main, "WORKSPACE_ROOT", workspace)
        monkeypatch.setattr(orchestrator_main, "DocumentManager", lambda: object())

        orchestrator = orchestrator_main.Orchestrator()
        orchestrator.discover_agents()

        decision = orchestrator._fallback_route("planner-agent draft staffing plan")
        assert decision is not None

        orchestrator.dispatcher.delegate(
            agent_name=decision["target_agent"],
            description=decision["params"]["description"],
            context=decision["params"].get("context", {}),
        )

        backend = orchestrator.dispatcher.registry["planner-agent"].memory_backend
        entries = asyncio.run(backend.get_recent(limit=1))
        assert entries
        assert entries[0].metadata["kind"] == "delegation"
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
        if server.stdout:
            server.stdout.close()
