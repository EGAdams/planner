"""
RAG message board transport implementation.

Provides MessageTransport interface for RAG-based message persistence.
Always available as fallback when WebSocket and Letta are offline.
"""

import asyncio
from typing import Optional, Callable, Awaitable, Dict
from datetime import datetime

from .message_transport import MessageTransport
from .message_models import AgentMessage


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
            # Search for messages addressed to this agent
            query = f"to:{agent_id}"
            if topic:
                query += f" topic:{topic}"
            
            print(f"[RAGBoardTransport] Polling with query: {query}")
            
            results = await asyncio.to_thread(
                self.doc_manager.search_artifacts,
                query=query,
                n_results=10
            )
            
            print(f"[RAGBoardTransport] Found {len(results)} results")
            
            # Parse results back into AgentMessage objects
            # (This is simplified - real implementation would parse the stored format)
            messages = []
            for result in results:
                # Extract metadata from tags
                # This is a placeholder - real parsing needed
                messages.append(result)
            
            return messages
            
        except Exception as e:
            print(f"[RAGBoardTransport] Error polling messages: {e}")
            import traceback
            traceback.print_exc()
            return []
