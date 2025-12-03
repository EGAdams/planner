"""
RAG message board transport implementation.

Provides MessageTransport interface for RAG-based message persistence.
Always available as fallback when WebSocket and Letta are offline.
"""

import asyncio
from datetime import datetime
from typing import Optional, Callable, Awaitable, Dict, List, Set

from .message_transport import MessageTransport
from .message_models import AgentMessage
from rag_system.models.document import QueryResult


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
        try:
            metadata_results = await asyncio.to_thread(
                self._fetch_by_metadata,
                agent_id,
                topic,
                25,
            )
            if metadata_results:
                print(f"[RAGBoardTransport] Found {len(metadata_results)} results (metadata scan)")
                return metadata_results
        except Exception as exc:
            print(f"[RAGBoardTransport] Metadata scan failed: {exc}")
        
        # Fallback to semantic search if metadata scan returns nothing
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
            return results
        except Exception as e:
            print(f"[RAGBoardTransport] Error polling messages: {e}")
            import traceback
            traceback.print_exc()
            return []

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

        items: List[QueryResult] = []
        for idx, chunk_id in enumerate(ids):
            metadata = metadatas[idx] or {}
            tag_set = self._normalize_tags(metadata.get("tags"))

            if agent_tag and agent_tag not in tag_set:
                continue
            if topic_tag and topic_tag not in tag_set:
                continue

            document_id = metadata.get("document_id", chunk_id)
            content = documents[idx] or ""

            items.append(
                QueryResult(
                    content=content,
                    score=1.0,
                    document_id=document_id,
                    chunk_id=chunk_id,
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
        tokens = [
            token.strip().lower()
            for token in tag_blob.split(",")
            if token.strip()
        ]
        return set(tokens)

    @staticmethod
    def _metadata_timestamp(metadata: Dict) -> float:
        value = metadata.get("created_at")
        if not value:
            return 0.0
        try:
            return datetime.fromisoformat(value).timestamp()
        except ValueError:
            return 0.0
