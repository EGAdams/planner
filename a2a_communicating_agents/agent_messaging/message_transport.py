"""
Abstract base class for message transports (Strategy Pattern).

Defines the interface that all transport implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Callable, Awaitable, Optional

from .message_models import AgentMessage


class MessageTransport(ABC):
    """
    Abstract base for message delivery strategies.
    
    Implements the Strategy pattern - clients can swap transport
    implementations without changing their code.
    """
    
    @abstractmethod
    async def connect(self) -> None:
        """
        Establish connection to message broker.
        
        Raises:
            ConnectionError: If connection fails
        """
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """
        Clean up connection and resources.
        """
        pass
    
    @abstractmethod
    async def send(self, message: AgentMessage) -> bool:
        """
        Send message to target agent.
        
        Args:
            message: AgentMessage to deliver
            
        Returns:
            True if sent successfully, False otherwise
        """
        pass
    
    @abstractmethod
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
        pass
    
    @abstractmethod
    async def unsubscribe(self, topic: str) -> None:
        """
        Unsubscribe from topic.
        
        Args:
            topic: Topic to unsubscribe from
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if transport is currently connected.
        
        Returns:
            True if connected, False otherwise
        """
        pass
