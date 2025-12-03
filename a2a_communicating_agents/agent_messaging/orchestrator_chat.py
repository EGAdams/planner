#!/usr/bin/env python3
"""
Interactive orchestrator chat utility.

Bridges the agent messaging system with the orchestrator topic so we can talk
to the OpenAI-backed orchestrator agent from any terminal session. The script
optionally auto-starts the orchestrator process and keeps a rolling view of the
conversation topic to reduce duplicate implementations across directories.
"""

from __future__ import annotations

import argparse
import asyncio
import os
import re
import signal
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Sequence, Set, Tuple

from rich.console import Console
from rich.prompt import Prompt

CURRENT_FILE = Path(__file__).resolve()
REPO_ROOT = CURRENT_FILE.parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

PACKAGE_ROOT = REPO_ROOT / "a2a_communicating_agents"

from a2a_communicating_agents.agent_messaging.agent_messaging_interface import (
    AgentMessage,
)
from a2a_communicating_agents.agent_messaging.message_models import (
    AgentMessage as TransportAgentMessage,
    MessagePriority as TransportMessagePriority,
)
from a2a_communicating_agents.agent_messaging.message_transport import MessageTransport
from a2a_communicating_agents.agent_messaging.transport_factory import TransportFactory
from rag_system.core.document_manager import DocumentManager

console = Console()


def _default_orchestrator_path() -> Path:
    """Return the absolute path to the orchestrator agent directory."""
    return PACKAGE_ROOT / "orchestrator_agent"


class OrchestratorProcessManager:
    """Simple helper to optionally start/stop the orchestrator process."""

    def __init__(self, orchestrator_path: Path):
        self.orchestrator_path = orchestrator_path
        self.process: Optional[subprocess.Popen] = None

    def start(self) -> None:
        if self.process:
            return
        if not self.orchestrator_path.exists():
            raise FileNotFoundError(
                f"Orchestrator path '{self.orchestrator_path}' does not exist"
            )
        console.print(
            f"🚀 Starting orchestrator agent from {self.orchestrator_path}", style="cyan"
        )
        env = os.environ.copy()
        self.process = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd=str(self.orchestrator_path),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    def stop(self) -> None:
        if not self.process:
            return
        console.print("🛑 Stopping orchestrator agent...", style="yellow")
        self.process.terminate()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()
        self.process = None


class OrchestratorChatSession:
    """Stateful helper that polls the orchestrator topic and sends messages."""

    _HEADER_PATTERN = re.compile(r"^\*\*(?P<label>[^*]+)\*\*\s*(?P<value>.*)$")

    def __init__(
        self,
        *,
        agent_name: str,
        topic: str,
        poll_limit: int = 20,
        transport_name: Optional[str] = None,
        transport: Optional[MessageTransport] = None,
        doc_manager: Optional[DocumentManager] = None,
        transport_factory=TransportFactory,
    ):
        self.agent_name = agent_name
        self.topic = topic
        self.poll_limit = poll_limit
        self._seen_ids: Set[str] = set()
        self._doc_manager = doc_manager or DocumentManager()
        self._transport_factory = transport_factory
        self.transport_name, self.transport = self._initialize_transport(
            transport_name=transport_name,
            transport=transport,
        )
        console.print(
            f"  Using '{self.transport_name}' transport for orchestrator chat",
            style="dim",
        )

    def _initialize_transport(
        self,
        *,
        transport_name: Optional[str],
        transport: Optional[MessageTransport],
    ) -> Tuple[str, MessageTransport]:
        """Set up the backing transport via the shared factory."""
        if transport_name and transport:
            return transport_name, transport

        try:
            name, transport_instance = self._transport_factory.create_transport(
                agent_id=self.agent_name,
                doc_manager=self._doc_manager,
            )
            return name, transport_instance
        except Exception as exc:  # pragma: no cover - defensive logging
            console.print(
                f"❌ Failed to initialize transport: {exc}", style="red"
            )
            raise

    def _message_key(self, message: AgentMessage) -> str:
        """Generate a stable key for deduplication."""
        if isinstance(message.metadata, dict):
            metadata_id = message.metadata.get("document_id")
            if metadata_id:
                return metadata_id
        if getattr(message, "document_id", None):
            return str(message.document_id)
        timestamp = getattr(message, "timestamp", None)
        sender = getattr(message, "sender", "unknown")
        return f"{sender}:{timestamp}:{hash(message.content)}"

    def fetch_new_messages(self) -> List[AgentMessage]:
        """Fetch new messages for this topic, skipping ones we've already shown."""
        raw_messages = self._poll_transport_messages()
        if not raw_messages:
            return []

        normalized: List[AgentMessage] = []
        for raw in raw_messages[: self.poll_limit]:
            message = self._convert_raw_message(raw)
            if not message:
                continue
            key = self._message_key(message)
            if key in self._seen_ids:
                continue
            self._seen_ids.add(key)
            normalized.append(message)

        normalized.sort(key=lambda msg: getattr(msg, "timestamp", datetime.utcnow()))
        return normalized

    def render_messages(self, messages: Sequence[AgentMessage]) -> None:
        """Render a collection of messages with simple color coding."""
        for msg in messages:
            timestamp = getattr(msg, "timestamp", None)
            time_str = (
                timestamp.strftime("%H:%M:%S") if isinstance(timestamp, datetime) else "--:--"
            )
            sender = getattr(msg, "sender", "unknown") or "unknown"
            content = (msg.content or "").strip()
            if sender == self.agent_name:
                style = "green"
            elif "orchestrator" in sender.lower():
                style = "cyan"
            else:
                style = "white"
            console.print(f"[dim]{time_str}[/dim] [{style}]{sender}[/]: {content}")

    def send_user_message(self, message: str) -> Optional[AgentMessage]:
        """Send a user-authored message to the orchestrator topic."""
        payload = message.strip()
        if not payload:
            return None
        transport_message = TransportAgentMessage(
            to_agent="board",
            from_agent=self.agent_name,
            content=payload,
            topic=self.topic,
            priority=TransportMessagePriority.NORMAL,
        )
        try:
            success = asyncio.run(self.transport.send(transport_message))
        except Exception as exc:
            console.print(f"❌ Failed to send message: {exc}", style="red")
            return None

        if not success:
            console.print("❌ Transport rejected the message.", style="red")
            return None

        local_msg = self._build_local_agent_message(
            payload=payload,
            timestamp=self._normalize_timestamp(transport_message.timestamp),
        )
        self._seen_ids.add(self._message_key(local_msg))
        return local_msg

    def _poll_transport_messages(self) -> Sequence:
        """Poll the backing transport for orchestrator messages."""
        poller = getattr(self.transport, "poll_messages", None)
        if not callable(poller):
            console.print(
                "⚠️ Active transport does not support polling yet.",
                style="yellow",
            )
            return []
        try:
            return asyncio.run(poller("board", topic=self.topic))
        except Exception as exc:
            console.print(f"❌ Failed to read messages: {exc}", style="red")
            return []

    def _convert_raw_message(self, raw) -> Optional[AgentMessage]:
        """Normalize transport-specific results into AgentMessage objects."""
        if isinstance(raw, AgentMessage):
            return raw

        content = getattr(raw, "content", None)
        metadata = dict(getattr(raw, "metadata", {}) or {})
        if content is None:
            return None

        text = str(content).strip()
        header, body = self._split_header_and_body(text)
        header_fields = self._parse_header_lines(header)

        sender = (
            header_fields.get("from")
            or metadata.get("sender")
            or metadata.get("source")
            or "unknown"
        )
        sender = sender.replace("agent:", "", 1) if sender.startswith("agent:") else sender

        topic = (
            header_fields.get("topic")
            or metadata.get("topic")
            or metadata.get("project_name")
            or self.topic
        )
        priority = (
            header_fields.get("priority")
            or metadata.get("priority")
            or TransportMessagePriority.NORMAL.value
        )
        timestamp_value = (
            header_fields.get("time")
            or metadata.get("timestamp")
            or metadata.get("created_at")
        )
        timestamp = self._parse_timestamp(timestamp_value)

        document_id = (
            metadata.get("document_id")
            or getattr(raw, "document_id", None)
            or getattr(raw, "id", None)
        )
        if document_id is None:
            document_id = f"{sender}:{timestamp.isoformat()}:{hash(body or text)}"

        normalized_metadata = {
            **metadata,
            "document_id": document_id,
            "topic": topic,
            "priority": priority,
        }
        normalized_metadata.setdefault("transport_source", self.transport_name)

        final_content = body.strip() if body.strip() else text

        return AgentMessage(
            id=document_id,
            document_id=document_id,
            content=final_content,
            topic=topic,
            sender=sender or "unknown",
            priority=priority,
            timestamp=timestamp,
            metadata=normalized_metadata,
            score=getattr(raw, "score", 1.0),
            raw=raw,
        )

    def _split_header_and_body(self, text: str) -> Tuple[str, str]:
        """Split stored transport payloads into header/body segments."""
        normalized = text.strip()
        if not normalized:
            return "", ""
        parts = normalized.split("\n\n", 1)
        if len(parts) == 2:
            return parts[0], parts[1]
        return normalized, ""

    def _parse_header_lines(self, header_block: str) -> dict:
        """Extract structured fields from the serialized header."""
        fields = {}
        for raw_line in header_block.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            match = self._HEADER_PATTERN.match(line)
            if not match:
                continue
            label = match.group("label").strip().rstrip(":").lower()
            value = match.group("value").strip()
            fields[label] = value
        return fields

    @staticmethod
    def _parse_timestamp(value: Optional[str]) -> datetime:
        """Parse ISO timestamps coming from transport metadata."""
        if not value:
            return datetime.utcnow()
        sanitized = value.strip().replace("Z", "+00:00")
        try:
            parsed = datetime.fromisoformat(sanitized)
        except ValueError:
            return datetime.utcnow()
        return OrchestratorChatSession._normalize_timestamp(parsed)

    @staticmethod
    def _normalize_timestamp(timestamp: datetime) -> datetime:
        """Convert timezone-aware timestamps to naive UTC for display."""
        if timestamp.tzinfo:
            return timestamp.astimezone(timezone.utc).replace(tzinfo=None)
        return timestamp

    def _build_local_agent_message(
        self,
        *,
        payload: str,
        timestamp: datetime,
    ) -> AgentMessage:
        """Create a lightweight AgentMessage for locally sent payloads."""
        metadata = {
            "transport_source": self.transport_name,
            "local_echo": True,
        }
        message_id = f"local-{hash((timestamp.isoformat(), payload))}"
        return AgentMessage(
            id=message_id,
            document_id=message_id,
            content=payload,
            topic=self.topic,
            sender=self.agent_name,
            priority=TransportMessagePriority.NORMAL.value,
            timestamp=timestamp,
            metadata=metadata,
            score=1.0,
            raw=None,
        )


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Chat with the orchestrator agent over the shared message board.",
    )
    parser.add_argument(
        "--agent-name",
        default=os.getenv("ORCHESTRATOR_CHAT_AGENT", "dashboard-ui"),
        help="Name to use when posting messages.",
    )
    parser.add_argument(
        "--topic",
        default="orchestrator",
        help="Message topic to monitor.",
    )
    parser.add_argument(
        "--poll-limit",
        type=int,
        default=25,
        help="Maximum messages to fetch per refresh.",
    )
    parser.add_argument(
        "--auto-start",
        action="store_true",
        help="Automatically launch the orchestrator agent before chatting.",
    )
    parser.add_argument(
        "--orchestrator-path",
        type=Path,
        default=_default_orchestrator_path(),
        help="Location of the orchestrator agent (used with --auto-start).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    manager: Optional[OrchestratorProcessManager] = None
    if args.auto_start:
        manager = OrchestratorProcessManager(args.orchestrator_path)

    session = OrchestratorChatSession(
        agent_name=args.agent_name,
        topic=args.topic,
        poll_limit=args.poll_limit,
    )

    console.print("\n🤝 Orchestrator Chat")
    console.print(" Type message and press Enter to send.")
    console.print(" Commands: /refresh, /quit, /help\n", style="dim")

    def cleanup(*_):
        if manager:
            manager.stop()
        console.print("\n👋 Goodbye!\n", style="yellow")
        raise SystemExit(0)

    signal.signal(signal.SIGINT, cleanup)

    if manager:
        try:
            manager.start()
        except Exception as exc:
            console.print(f"❌ Failed to auto-start orchestrator: {exc}", style="red")
            manager = None

    # Initial refresh so we can see existing context.
    initial_messages = session.fetch_new_messages()
    if initial_messages:
        session.render_messages(initial_messages)
    else:
        console.print("📭 No orchestrator messages yet. Start the conversation!", style="yellow")

    while True:
        try:
            user_input = Prompt.ask(f"[{args.agent_name}]").strip()
        except (EOFError, KeyboardInterrupt):
            cleanup()

        normalized = user_input.lower()
        if normalized in {"", "/refresh", "/r"}:
            new_msgs = session.fetch_new_messages()
            if new_msgs:
                session.render_messages(new_msgs)
            else:
                console.print("📭 No new messages.", style="dim")
            continue
        if normalized in {"/quit", "/exit", "/q"}:
            cleanup()
        if normalized in {"/help", "help"}:
            console.print("Commands: /refresh, /quit, /help", style="dim")
            continue

        session.send_user_message(user_input)
        console.print("✅ Message sent.", style="green")
        new_msgs = session.fetch_new_messages()
        if new_msgs:
            session.render_messages(new_msgs)


if __name__ == "__main__":
    main()
