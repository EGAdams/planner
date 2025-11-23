"""
Letta transport implementation wrapping existing Letta client.

Provides MessageTransport interface for Letta-based agent communication.
"""

import asyncio
from typing import Optional, Callable, Awaitable
try:
    from letta import Letta
except ImportError:
    Letta = None  # Letta not installed
from .message_transport import MessageTransport
from .message_models import AgentMessage
from pydantic import BaseModel


class LettaConfig(BaseModel):
    """Configuration for Letta transport"""
    base_url: str = "http://localhost:8283"
    api_key: Optional[str] = None


class LettaTransport(MessageTransport):
    """
    Letta-based transport (Strategy pattern).
    
    Wraps the existing Letta client to provide MessageTransport interface.
    """
    
    def __init__(self, config: LettaConfig):
        """
        Initialize Letta transport.
        
        Args:
            config: LettaConfig with base_url and optional api_key
        """
        self.config = config
        self.client: Optional[Letta] = None
        self._connected = False
        self._subscriptions = {}
        
    async def connect(self) -> None:
        """Establish connection to Letta server"""
        if Letta is None:
            raise ConnectionError("Letta package not installed. Install with: pip install letta")
        
        try:
            if self.config.api_key:
                self.client = Letta(api_key=self.config.api_key)
            else:
                self.client = Letta(base_url=self.config.base_url)
            
            # Test connection by listing agents
            await asyncio.to_thread(self.client.agents.list)
            self._connected = True
            
        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to Letta: {e}")
    
    async def disconnect(self) -> None:
        """Clean up connection"""
        self._connected = False
        self.client = None
        self._subscriptions.clear()
    
    async def send(self, message: AgentMessage) -> bool:
        """
        Send message to target agent via Letta.
        
        Args:
            message: AgentMessage to send
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not self._connected or not self.client:
            return False
        
        try:
            response = await asyncio.to_thread(
                self.client.agents.messages.create,
                agent_id=message.to_agent,
                messages=[{
                    "role": "user",
                    "content": message.content
                }]
            )
            return bool(response)
            
        except Exception:
            return False
    
    async def subscribe(
        self, 
        topic: str, 
        callback: Callable[[AgentMessage], Awaitable[None]]
    ) -> None:
        """
        Subscribe to topic (limited support in Letta).
        
        Note: Letta doesn't have native pub/sub, so this is a no-op.
        Messages are delivered directly via send().
        """
        self._subscriptions[topic] = callback
    
    async def unsubscribe(self, topic: str) -> None:
        """Unsubscribe from topic"""
        if topic in self._subscriptions:
            del self._subscriptions[topic]
    
    def is_connected(self) -> bool:
        """Check if connected to Letta"""
        return self._connected
