#!/usr/bin/env python3
"""
Helper script to send messages to agents via the dashboard.

Adds a lightweight response watcher so menu-driven checks can confirm
the orchestrator is alive without opening the chat session.
"""

import os
import sys
import time
from pathlib import Path
from typing import Optional, Set, Tuple

# Ensure the package root is importable when executed as a standalone script
CURRENT_DIR = Path(__file__).resolve().parent
WORKSPACE_ROOT = CURRENT_DIR.parent.parent
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.append(str(WORKSPACE_ROOT))

from a2a_communicating_agents.agent_messaging import (
    post_message,
    create_jsonrpc_request,
    read_messages,
)

TOPIC_MAPPING = {
    "dashboard-agent": "ops",
    "orchestrator-agent": "orchestrator",
}

RESPONSE_HINTS = {
    "dashboard-agent": "dashboard",
    "orchestrator-agent": "orchestrator",
}

DEFAULT_WAIT_SECONDS = float(os.getenv("AGENT_MESSAGE_WAIT_SECONDS", "6"))


def _message_identifier(msg) -> str:
    """Build a stable identifier for RAG board entries."""
    document_id = getattr(msg, "document_id", None)
    if document_id:
        return str(document_id)

    sender = getattr(msg, "from_agent", None) or getattr(msg, "sender", "unknown")
    content = getattr(msg, "content", "")
    return f"{sender}:{hash(content)}"


def _snapshot_topic(topic: str, limit: int = 10) -> Set[str]:
    """Capture recent message IDs so we can filter old entries."""
    try:
        messages = read_messages(topic=topic, limit=limit, render=False) or []
    except Exception as exc:  # pragma: no cover - defensive
        print(f"Warning: unable to read message board snapshot: {exc}", file=sys.stderr)
        return set()
    return {_message_identifier(msg) for msg in messages}


def wait_for_response(
    topic: str,
    *,
    expected_sender: Optional[str] = None,
    timeout: float = DEFAULT_WAIT_SECONDS,
    poll_interval: float = 1.0,
    ignore_ids: Optional[Set[str]] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Poll the message board for a reply on the given topic."""
    deadline = time.time() + timeout
    seen = set(ignore_ids or [])

    while time.time() < deadline:
        try:
            messages = read_messages(topic=topic, limit=5, render=False) or []
        except Exception as exc:
            print(f"Warning: unable to read responses: {exc}", file=sys.stderr)
            break

        for msg in messages:
            identifier = _message_identifier(msg)
            if identifier in seen:
                continue
            seen.add(identifier)

            sender = getattr(msg, "from_agent", None) or getattr(msg, "sender", "unknown")
            if expected_sender and expected_sender.lower() not in sender.lower():
                continue

            content = getattr(msg, "content", str(msg))
            return sender, content

        time.sleep(poll_interval)

    return None, None


def send_to_agent(agent_id: str, message: str) -> Tuple[str, str]:
    """Send a message to an agent and return a status string plus topic name."""
    topic = TOPIC_MAPPING.get(agent_id, "general")

    request = create_jsonrpc_request(
        method="agent.execute_task",
        params={
            "description": message,
            "from": "dashboard-ui",
        },
    )

    post_message(
        message=request,
        topic=topic,
        from_agent="dashboard-ui",
    )

    return f"Message sent to {agent_id} on topic '{topic}'", topic


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python send_agent_message.py <agent_id> <message>", file=sys.stderr)
        sys.exit(1)

    agent_id = sys.argv[1]
    message = sys.argv[2]

    topic = TOPIC_MAPPING.get(agent_id, "general")
    baseline_ids = _snapshot_topic(topic)

    result, topic_name = send_to_agent(agent_id, message)
    print(result)

    expected_sender = RESPONSE_HINTS.get(agent_id)
    sender, response = wait_for_response(
        topic_name,
        expected_sender=expected_sender,
        ignore_ids=baseline_ids,
    )

    if response:
        print(f"\nLatest response from {sender} on topic '{topic_name}':\n{response}")
    else:
        print(f"\nNo response detected on topic '{topic_name}' within {DEFAULT_WAIT_SECONDS:.0f}s. "
              "Check orchestrator logs if this persists.")
