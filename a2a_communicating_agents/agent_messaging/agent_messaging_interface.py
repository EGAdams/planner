"""Agent messaging interface with pluggable backends.

This module provides a small abstraction layer so callers can talk to
"messaging" without caring whether the message ultimately goes to the shared
memory board or a direct Letta channel.  We only ship the always-on message
board implementation today, but the shape of the interface makes it easy to
swap in a Letta-backed transport later.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from rag_system.core.document_manager import DocumentManager
from rag_system.models.document import Document, DocumentType


@dataclass
class AgentMessage:
    """Represents a normalized agent message.

    The attributes intentionally mirror what existing call sites expect from
    `rag_tools.inbox`, while adding richer metadata so we can evolve toward
    structured messaging without breaking compatibility.
    """

    id: str
    content: str
    topic: str
    sender: str
    priority: str
    timestamp: datetime
    metadata: Dict[str, Any]
    score: float = 1.0
    document_id: Optional[str] = None
    raw: Any = None


class AgentMessenger:
    """Base interface for agent messaging backends."""

    def send(
        self,
        message: str,
        *,
        topic: str = "general",
        sender: str = "unknown",
        priority: str = "normal",
    ) -> AgentMessage:
        raise NotImplementedError

    def receive(
        self,
        *,
        topic: Optional[str] = None,
        limit: int = 10,
    ) -> List[AgentMessage]:
        raise NotImplementedError


@dataclass
class AgentMessagingConfig:
    """Runtime configuration for selecting a transport backend."""

    transport: str = "message_board"
    base_url: Optional[str] = None
    api_key: Optional[str] = None


class MessageBoardMessenger(AgentMessenger):
    """Always-on shared message board using the local RAG memory."""

    def __init__(self, doc_manager: DocumentManager):
        self._doc_manager = doc_manager

    # ------------------------------------------------------------------
    # AgentMessenger interface
    # ------------------------------------------------------------------
    def send(
        self,
        message: str,
        *,
        topic: str = "general",
        sender: str = "unknown",
        priority: str = "normal",
    ) -> AgentMessage:
        timestamp = datetime.utcnow()
        normalized_topic = topic or "general"
        sender_name = sender or "unknown"
        priority_level = priority or "normal"
        message_body = message.strip()

        metadata = {
            "runtime_capture": True,
            "artifact_category": "agent_message",
            "topic": normalized_topic,
            "priority": priority_level,
            "sender": sender_name,
            "source": sender_name,
            "project_name": normalized_topic,
            "message_body": message_body,
            "timestamp": timestamp.isoformat(),
        }

        document = Document(
            title=f"[Agent Message] {normalized_topic} • {sender_name}",
            content=self._format_persistent_content(
                sender_name, normalized_topic, priority_level, timestamp, message_body
            ),
            doc_type=DocumentType.RUNTIME_ARTIFACT,
            metadata=metadata,
            tags=[
                "agent-message",
                normalized_topic,
                priority_level,
                sender_name,
            ],
            artifact_type="agent_message",
            source=sender_name,
            project_name=normalized_topic,
            priority=priority_level,
        )

        document_id = self._doc_manager.rag_engine.add_document(document)

        metadata.update(
            {
                "document_id": document_id,
                "created_at": timestamp.isoformat(),
            }
        )

        return AgentMessage(
            id=document_id,
            document_id=document_id,
            content=message_body,
            topic=normalized_topic,
            sender=sender_name,
            priority=priority_level,
            timestamp=timestamp,
            metadata=metadata,
            score=1.0,
            raw=None,
        )

    def receive(
        self,
        *,
        topic: Optional[str] = None,
        limit: int = 10,
    ) -> List[AgentMessage]:
        filters = [
            {"doc_type": DocumentType.RUNTIME_ARTIFACT.value},
            {"artifact_type": "agent_message"},
        ]
        if topic:
            filters.append({"project_name": topic})

        filter_dict = {"$and": filters} if filters else None
        query_text = topic or "agent message"

        results = self._doc_manager.rag_engine.query(
            query_text=query_text,
            n_results=limit,
            filter_dict=filter_dict,
            apply_artifact_boosting=True,
        )

        messages: List[AgentMessage] = []
        for result in results:
            metadata = dict(result.metadata)
            message_body = metadata.get("message_body")
            if not message_body:
                message_body = self._strip_headers(result.content)

            timestamp_value = metadata.get("timestamp") or metadata.get("created_at")
            timestamp_dt = self._parse_timestamp(timestamp_value) or datetime.utcnow()

            sender_name = metadata.get("sender") or metadata.get("source") or "unknown"
            topic_name = metadata.get("topic") or metadata.get("project_name") or topic or "general"
            priority_level = metadata.get("priority") or "normal"

            normalized_metadata = {
                **metadata,
                "sender": sender_name,
                "topic": topic_name,
                "priority": priority_level,
                "timestamp": timestamp_dt.isoformat(),
            }
            normalized_metadata.setdefault("document_id", result.document_id)

            messages.append(
                AgentMessage(
                    id=normalized_metadata["document_id"],
                    document_id=result.document_id,
                    content=message_body,
                    topic=topic_name,
                    sender=sender_name,
                    priority=priority_level,
                    timestamp=timestamp_dt,
                    metadata=normalized_metadata,
                    score=getattr(result, "score", 1.0),
                    raw=result,
                )
            )

        messages.sort(key=lambda m: m.timestamp)
        return messages

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _format_persistent_content(
        sender: str,
        topic: str,
        priority: str,
        timestamp: datetime,
        message_body: str,
    ) -> str:
        header = (
            f"**From**: {sender}\n"
            f"**Topic**: {topic}\n"
            f"**Priority**: {priority}\n"
            f"**Time**: {timestamp.isoformat()}\n\n"
        )
        return f"{header}{message_body}"

    @staticmethod
    def _strip_headers(content: str) -> str:
        if not content:
            return ""
        if content.startswith("**From**:"):
            parts = content.split("\n\n", 1)
            if len(parts) == 2:
                return parts[1].strip()
        return content.strip()

    @staticmethod
    def _parse_timestamp(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None


def get_agent_messenger(
    config: Optional[AgentMessagingConfig] = None,
    *,
    doc_manager: Optional[DocumentManager] = None,
) -> AgentMessenger:
    """Factory that returns the appropriate messenger implementation."""

    resolved_config = config or AgentMessagingConfig()
    resolved_doc_manager = doc_manager or DocumentManager()

    transport = (resolved_config.transport or "").lower()
    if transport in ("message_board", "board", "memory", "default"):
        return MessageBoardMessenger(resolved_doc_manager)

    raise NotImplementedError(
        f"Transport '{resolved_config.transport}' is not implemented yet."
    )
