"""
WebSocket transport implementation using Strategy and Observer patterns.

Implements the MessageTransport interface for WebSocket-based
agent-to-agent communication.
"""

import asyncio
from typing import Dict, Callable, Awaitable, Optional

from .message_transport import MessageTransport
from .message_models import AgentMessage, ConnectionConfig


class WebSocketTransport(MessageTransport):
    """
    WebSocket implementation of MessageTransport (Strategy pattern).
    
    Features:
    - Async connect/disconnect
    - Topic-based subscriptions (Observer pattern)
    - Mock server support for testing
    """
    
    def __init__(
        self, 
        config: ConnectionConfig, 
        mock_server: Optional['MockWebSocketServer'] = None
    ):
        """
        Initialize WebSocket transport.
        
        Args:
            config: Connection configuration
            mock_server: Optional mock server for testing
        """
        self.config = config
        self._mock_server = mock_server
        self._connected = False
        self._subscriptions: Dict[str, Callable[[AgentMessage], Awaitable[None]]] = {}
        self.agent_id: Optional[str] = None
        
    async def connect(self) -> None:
        """Establish connection to WebSocket server"""
        if self.agent_id is None:
            raise ValueError("agent_id must be set before connecting")
            
        if self._mock_server:
            # Use mock server for testing
            await self._mock_server.connect_agent(self.agent_id)
            self._connected = True
        else:
            # Real WebSocket connection would go here
            raise NotImplementedError("Real WebSocket connection not yet implemented")
    
    async def disconnect(self) -> None:
        """Clean up connection and resources"""
        if not self._connected:
            return
            
        if self._mock_server:
            await self._mock_server.disconnect_agent(self.agent_id)
        
        self._connected = False
        self._subscriptions.clear()
    
    async def send(self, message: AgentMessage) -> bool:
        """
        Send message to target agent.
        
        Args:
            message: AgentMessage to deliver
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self._connected:
            return False
            
        if self._mock_server:
            return await self._mock_server.send_message(message)
        else:
            # Real WebSocket send would go here
            raise NotImplementedError("Real WebSocket send not yet implemented")
    
    async def subscribe(
        self, 
        topic: str, 
        callback: Callable[[AgentMessage], Awaitable[None]]
    ) -> None:
        """
        Subscribe to topic and register callback (Observer pattern).
        
        Args:
            topic: Topic name to subscribe to
            callback: Async function to call when messages arrive
        """
        if not self._connected:
            raise RuntimeError("Must connect before subscribing")
            
        self._subscriptions[topic] = callback
        
        if self._mock_server:
            await self._mock_server.subscribe(self.agent_id, topic)
    
    async def unsubscribe(self, topic: str) -> None:
        """
        Unsubscribe from topic.
        
        Args:
            topic: Topic to unsubscribe from
        """
        if topic in self._subscriptions:
            del self._subscriptions[topic]
            
        if self._mock_server and self.agent_id:
            await self._mock_server.unsubscribe(self.agent_id, topic)
    
    def is_connected(self) -> bool:
        """
        Check if transport is currently connected.
        
        Returns:
            True if connected, False otherwise
        """
        return self._connected
    
    async def _process_pending_messages(self) -> None:
        """
        Process pending messages from mock server and invoke callbacks.
        
        This is a helper method for testing. Real WebSocket would
        receive messages asynchronously via callbacks.
        """
        if not self._mock_server:
            return
            
        messages = await self._mock_server.get_messages(self.agent_id)
        
        for message in messages:
            # Find matching subscription callback
            if message.topic in self._subscriptions:
                callback = self._subscriptions[message.topic]
                await callback(message)
