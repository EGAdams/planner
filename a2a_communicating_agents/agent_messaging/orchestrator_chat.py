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
import os
import signal
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional, Sequence, Set

from rich.console import Console
from rich.prompt import Prompt

from a2a_communicating_agents.agent_messaging.agent_messaging_interface import (
    AgentMessage,
)
from rag_system.rag_tools import read_agent_messages, send_agent_message

console = Console()


def _default_orchestrator_path() -> Path:
    """Return the absolute path to the orchestrator agent directory."""
    return (
        Path(__file__)
        .resolve()
        .parents[1]
        / "a2a_communicating_agents"
        / "orchestrator_agent"
    )


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

    def __init__(
        self,
        *,
        agent_name: str,
        topic: str,
        poll_limit: int = 20,
        send_fn: Callable[..., AgentMessage] = send_agent_message,
        inbox_fn: Callable[..., Sequence[AgentMessage]] = read_agent_messages,
    ):
        self.agent_name = agent_name
        self.topic = topic
        self.poll_limit = poll_limit
        self.send_fn = send_fn
        self.inbox_fn = inbox_fn
        self._seen_ids: Set[str] = set()

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
        try:
            messages = self.inbox_fn(
                topic=self.topic, limit=self.poll_limit, render=False
            )
        except TypeError:
            # Some callers might not support keyword arguments (mainly tests)
            messages = self.inbox_fn(self.topic)  # type: ignore[arg-type]
        except Exception as exc:
            console.print(f"❌ Failed to read messages: {exc}", style="red")
            return []

        if not messages:
            return []

        new_messages: List[AgentMessage] = []
        sorted_messages = sorted(
            messages,
            key=lambda msg: getattr(msg, "timestamp", datetime.utcnow()),
        )
        for message in sorted_messages:
            key = self._message_key(message)
            if key in self._seen_ids:
                continue
            self._seen_ids.add(key)
            new_messages.append(message)
        return new_messages

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
        agent_message = self.send_fn(
            payload,
            topic=self.topic,
            from_agent=self.agent_name,
        )
        self._seen_ids.add(self._message_key(agent_message))
        return agent_message


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
