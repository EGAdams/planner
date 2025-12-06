"""
RAG message board transport implementation.

Provides MessageTransport interface for RAG-based message persistence.
Always available as fallback when WebSocket and Letta are offline.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Callable, Awaitable, Dict, List, Set
from uuid import uuid4

from .message_transport import MessageTransport
from .message_models import AgentMessage
from rag_system.models.document import QueryResult


class LocalBoardMessage:
    """Lightweight message container backed by the JSONL cache."""

    __slots__ = ("content", "from_agent", "topic", "document_id", "metadata", "sender")

    def __init__(
        self,
        *,
        content: str,
        from_agent: str,
        topic: str,
        document_id: str,
        created_at: datetime,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.content = content
        self.from_agent = from_agent
        self.sender = from_agent
        self.topic = topic
        self.document_id = document_id
        self.metadata = metadata or {}
        self.metadata.setdefault("created_at", created_at.isoformat())


class RAGBoardTransport(MessageTransport):
    """
    RAG message board transport (always-available fallback).
    
    Uses DocumentManager to persist messages in ChromaDB.
    Slower than WebSocket/Letta but always available.
    """
    
    def __init__(self, doc_manager):
        """
        Initialize RAG board transport.
        
        Args:
            doc_manager: DocumentManager instance for persistence
        """
        self.doc_manager = doc_manager
        self._connected = True  # Always "connected" (no server needed)
        self._subscriptions: Dict[str, Callable] = {}
        root = Path(__file__).resolve().parents[2]
        self._local_board_path = root / "storage" / "message_board.jsonl"
        self._local_board_path.parent.mkdir(parents=True, exist_ok=True)
        self._local_cache_limit = 200
        
    async def connect(self) -> None:
        """No connection needed for RAG board"""
        self._connected = True
    
    async def disconnect(self) -> None:
        """Clean up subscriptions"""
        self._subscriptions.clear()
        self._connected = False
    
    async def send(self, message: AgentMessage) -> bool:
        """
        Send message by persisting to RAG board.
        
        Args:
            message: AgentMessage to persist
            
        Returns:
            True if persisted successfully, False otherwise
        """
        if not self._connected:
            return False
        
        try:
            # Format message for RAG storage
            content = f"""
**From:** {message.from_agent}
**To:** {message.to_agent}
**Topic:** {message.topic}
**Priority:** {message.priority.value}
**Time:** {message.timestamp.isoformat()}

{message.content}
"""
            
            # Persist to RAG with tags for filtering
            artifact_id = await asyncio.to_thread(
                self.doc_manager.add_runtime_artifact,
                artifact_text=content,
                artifact_type="message",
                source=f"agent:{message.from_agent}",
                tags=[
                    message.topic,
                    f"to:{message.to_agent}",
                    f"from:{message.from_agent}",
                    f"priority:{message.priority.value}"
                ]
            )
            
            return artifact_id is not None
            
        except Exception:
            return False
        finally:
            self._append_local_board(
                content=content,
                from_agent=message.from_agent,
                to_agent=message.to_agent,
                topic=message.topic or "general",
                priority=message.priority.value,
                timestamp=message.timestamp,
            )
    
    async def subscribe(
        self, 
        topic: str, 
        callback: Callable[[AgentMessage], Awaitable[None]]
    ) -> None:
        """
        Subscribe to topic (polling-based).
        
        Note: RAG doesn't support push notifications, so this just
        registers the callback. A background poller would be needed
        for real-time delivery.
        """
        self._subscriptions[topic] = callback
    
    async def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from topic"""
        if topic in self._subscriptions:
            del self._subscriptions[topic]
    
    def is_connected(self) -> bool:
        """RAG board is always "connected" """
        return self._connected
    
    async def poll_messages(self, agent_id: str, topic: Optional[str] = None) -> list:
        """
        Poll for new messages (RAG-specific method).
        
        Args:
            agent_id: Agent to get messages for
            topic: Optional topic filter
            
        Returns:
            List of AgentMessage objects
        """
        combined: List[Any] = []
        local_messages = self._read_local_board(agent_id, topic, limit=25)
        combined.extend(local_messages)

        seen_ids = {
            getattr(msg, "document_id", None)
            for msg in combined
            if getattr(msg, "document_id", None)
        }

        try:
            metadata_results = await asyncio.to_thread(
                self._fetch_by_metadata,
                agent_id,
                topic,
                25,
            )
            if metadata_results:
                print(f"[RAGBoardTransport] Found {len(metadata_results)} results (metadata scan)")
                for result in metadata_results:
                    document_id = getattr(result, "document_id", None)
                    if document_id and document_id in seen_ids:
                        continue
                    combined.append(result)
                    if document_id:
                        seen_ids.add(document_id)
        except Exception as exc:
            print(f"[RAGBoardTransport] Metadata scan failed: {exc}")
        
        # Fallback to semantic search if metadata scan returns nothing
        fallback_needed = not combined
        if fallback_needed:
            try:
                query = f"to:{agent_id}"
                if topic:
                    query += f" topic:{topic}"
                
                print(f"[RAGBoardTransport] Polling with query fallback: {query}")
                results = await asyncio.to_thread(
                    self.doc_manager.search_artifacts,
                    query=query,
                    artifact_type="message",
                    n_results=10
                )
                print(f"[RAGBoardTransport] Fallback found {len(results)} results")
                for result in results:
                    wrapped = self._wrap_query_result(result, topic)
                    document_id = getattr(wrapped, "document_id", None)
                    if document_id and document_id in seen_ids:
                        continue
                    combined.append(wrapped)
                    if document_id:
                        seen_ids.add(document_id)
            except Exception as e:
                print(f"[RAGBoardTransport] Error polling messages: {e}")
                import traceback
                traceback.print_exc()
                return combined

        combined.sort(key=lambda msg: self._metadata_timestamp(getattr(msg, "metadata", {})), reverse=True)
        return combined[:25]

    def _append_local_board(
        self,
        *,
        content: str,
        from_agent: str,
        to_agent: str,
        topic: str,
        priority: str,
        timestamp: datetime,
    ) -> None:
        """Persist a small JSONL log so we can read the latest messages without scanning Chroma."""
        record = {
            "id": f"local-{uuid4()}",
            "from_agent": from_agent,
            "to_agent": to_agent,
            "topic": topic,
            "priority": priority,
            "timestamp": timestamp.isoformat(),
            "content": content,
        }
        try:
            existing: List[str] = []
            if self._local_board_path.exists():
                existing = [
                    line.strip()
                    for line in self._local_board_path.read_text(encoding="utf-8").splitlines()
                    if line.strip()
                ]
            existing.append(json.dumps(record))
            if len(existing) > self._local_cache_limit:
                existing = existing[-self._local_cache_limit :]
            data = "\n".join(existing) + ("\n" if existing else "")
            self._local_board_path.write_text(data, encoding="utf-8")
        except Exception:
            # Cache failures should never break the main transport flow
            pass

    def _read_local_board(
        self,
        agent_id: str,
        topic: Optional[str],
        *,
        limit: int,
    ) -> List[LocalBoardMessage]:
        """Load cached entries for the requested recipient/topic."""
        if not self._local_board_path.exists():
            return []

        agent = (agent_id or "").lower()
        topic_filter = (topic or "").lower()
        items: List[LocalBoardMessage] = []

        try:
            with self._local_board_path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if agent and payload.get("to_agent", "").lower() != agent:
                        continue
                    if topic_filter and payload.get("topic", "").lower() != topic_filter:
                        continue

                    try:
                        created_at = datetime.fromisoformat(payload["timestamp"])
                    except Exception:
                        created_at = datetime.utcnow()

                    items.append(
                        LocalBoardMessage(
                            content=payload.get("content", ""),
                            from_agent=payload.get("from_agent", "unknown"),
                            topic=payload.get("topic", "general"),
                            document_id=payload.get("id", f"local-{uuid4()}"),
                            created_at=created_at,
                        )
                    )
        except Exception:
            return []

        items.sort(key=lambda item: self._metadata_timestamp(item.metadata), reverse=True)
        return items[:limit]
    def _fetch_by_metadata(
        self,
        agent_id: str,
        topic: Optional[str],
        limit: int = 25,
    ) -> List[QueryResult]:
        """Pull the latest message artifacts by scanning metadata instead of embeddings."""
        collection = self.doc_manager.rag_engine.collection
        filters = {
            "$and": [
                {"doc_type": "runtime_artifact"},
                {"artifact_type": "message"},
            ]
        }
        response = collection.get(
            where=filters,
            include=["metadatas", "documents"],
            limit=max(limit * 4, 20),
        )
        ids = response.get("ids") or []
        documents = response.get("documents") or []
        metadatas = response.get("metadatas") or []

        agent_tag = f"to:{agent_id.lower()}" if agent_id else None
        topic_tag = topic.lower() if topic else None

        items: List[LocalBoardMessage] = []
        for idx, chunk_id in enumerate(ids):
            metadata = metadatas[idx] or {}
            tag_set = self._normalize_tags(metadata.get("tags"))

            if agent_tag and agent_tag not in tag_set:
                continue
            if topic_tag and topic_tag not in tag_set:
                continue

            document_id = metadata.get("document_id", chunk_id)
            content = documents[idx] or ""
            from_agent = self._extract_tag_value(tag_set, "from:") or "unknown"
            topic_name = topic or self._extract_topic_from_tags(tag_set) or metadata.get("topic", "general")
            created_at = self._parse_timestamp(metadata.get("created_at"))

            items.append(
                LocalBoardMessage(
                    content=content,
                    from_agent=from_agent,
                    topic=topic_name,
                    document_id=document_id,
                    created_at=created_at,
                    metadata=metadata,
                )
            )

        items.sort(
            key=lambda result: self._metadata_timestamp(result.metadata),
            reverse=True,
        )
        return items[:limit]

    @staticmethod
    def _normalize_tags(tag_blob: Optional[str]) -> Set[str]:
        if not tag_blob:
            return set()
        tokens = [token.strip().lower() for token in tag_blob.split(",") if token.strip()]
        return set(tokens)

    def _wrap_query_result(self, result: QueryResult, topic: Optional[str]) -> LocalBoardMessage:
        metadata = result.metadata or {}
        tag_set = self._normalize_tags(metadata.get("tags"))
        document_id = metadata.get("document_id", result.document_id)
        created_at = self._parse_timestamp(metadata.get("created_at"))
        from_agent = self._extract_tag_value(tag_set, "from:") or metadata.get("source") or "unknown"
        topic_name = topic or self._extract_topic_from_tags(tag_set) or metadata.get("topic", "general")
        return LocalBoardMessage(
            content=result.content,
            from_agent=from_agent,
            topic=topic_name,
            document_id=document_id,
            created_at=created_at,
            metadata=metadata,
        )

    @staticmethod
    def _extract_tag_value(tag_set: Set[str], prefix: str) -> Optional[str]:
        normalized = prefix.lower()
        for token in tag_set:
            if token.startswith(normalized):
                return token[len(normalized) :]
        return None

    @staticmethod
    def _extract_topic_from_tags(tag_set: Set[str]) -> Optional[str]:
        for token in tag_set:
            if ":" in token:
                continue
            if token == "message":
                continue
            return token
        return None

    @staticmethod
    def _parse_timestamp(value: Optional[str]) -> datetime:
        if not value:
            return datetime.utcnow()
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return datetime.utcnow()

    @staticmethod
    def _metadata_timestamp(metadata: Dict) -> float:
        value = metadata.get("created_at")
        if not value:
            return 0.0
        try:
            timestamp = datetime.fromisoformat(value).timestamp()
        except ValueError:
            return 0.0

        now = datetime.utcnow().timestamp()
        # Some historic entries were written with far-future timestamps.
        # Clamp anything ahead of "now" so those artifacts don't hide new chats.
        if timestamp > now:
            return now
        return timestamp
