from __future__ import annotations

import json
from datetime import datetime, timezone
from types import SimpleNamespace

from a2a_communicating_agents.orchestrator_agent.main import Orchestrator
from a2a_communicating_agents.agent_messaging.agent_messaging_interface import (
    AgentMessage,
)
from a2a_communicating_agents.agent_messaging.orchestrator_chat import (
    OrchestratorChatSession,
)


class DummyChatCompletions:
    def __init__(self, payload: dict):
        self.payload = payload
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        content = json.dumps(self.payload)
        message = SimpleNamespace(content=content)
        choice = SimpleNamespace(message=message)
        return SimpleNamespace(choices=[choice])


class DummyClient:
    def __init__(self, payload: dict):
        self.chat = SimpleNamespace(completions=DummyChatCompletions(payload))


def _sample_message(sender: str, document_id: str) -> AgentMessage:
    return AgentMessage(
        id=document_id,
        content=f"Message from {sender}",
        topic="orchestrator",
        sender=sender,
        priority="normal",
        timestamp=datetime.now(timezone.utc),
        metadata={"document_id": document_id},
    )


def test_orchestrator_decide_route_uses_openai_payload():
    payload = {
        "target_agent": "dashboard-agent",
        "reasoning": "Understands dashboards",
        "method": "agent.execute_task",
        "params": {"description": "Help fix dashboard"},
    }
    client = DummyClient(payload)
    orchestrator = Orchestrator(llm_client=client)
    orchestrator.known_agents = {
        "dashboard-agent": {"description": "Dashboard expert", "capabilities": ["dashboards"], "topics": ["ops"]}
    }

    decision = orchestrator.decide_route("Need help with dashboards")

    assert decision == payload
    assert client.chat.completions.last_kwargs["model"] == orchestrator.model_id


def test_orchestrator_chat_session_deduplicates_messages():
    messages = [
        _sample_message("orchestrator-agent", "doc-1"),
        _sample_message("tester", "doc-2"),
    ]

    def fake_inbox(**kwargs):
        return messages

    sent_payloads = []

    def fake_send(message, **kwargs):
        sent_payloads.append(message)
        return _sample_message("tester", f"doc-{len(sent_payloads)+2}")

    session = OrchestratorChatSession(
        agent_name="tester",
        topic="orchestrator",
        inbox_fn=fake_inbox,
        send_fn=fake_send,
    )

    first_batch = session.fetch_new_messages()
    assert len(first_batch) == 2
    assert session.fetch_new_messages() == []  # Deduped

    session.send_user_message("Ping orchestrator")
    assert sent_payloads == ["Ping orchestrator"]
