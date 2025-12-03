"""
Abstract base class for memory backends (Strategy Pattern).

Defines the interface that all memory implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel


class MemoryEntry(BaseModel):
    """Represents a single memory entry"""
    id: str
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = {}
    tags: List[str] = []
    source: str = "unknown"
    memory_type: str = "general"  # general, error, fix, deployment, etc.


class MemoryQuery(BaseModel):
    """Query parameters for memory search"""
    query: str
    limit: int = 5
    memory_type: Optional[str] = None
    tags: Optional[List[str]] = None
    source: Optional[str] = None
    metadata_filter: Optional[Dict[str, Any]] = None


class MemoryBackend(ABC):
    """
    Abstract base for memory storage strategies.
    
    Implements the Strategy pattern - clients can swap memory
    implementations without changing their code.
    
    Inspired by Letta's memory model for runtime artifacts.
    """
    
    @abstractmethod
    async def connect(self) -> None:
        """
        Establish connection to memory backend.
        
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
    async def remember(
        self,
        content: str,
        memory_type: str = "general",
        source: str = "unknown",
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Store a memory entry.
        
        Args:
            content: The memory content to store
            memory_type: Type of memory (error, fix, deployment, note, etc.)
            source: Source identifier (agent name, file path, etc.)
            tags: Optional tags for categorization
            metadata: Optional additional metadata
            
        Returns:
            Memory entry ID
        """
        pass
    
    @abstractmethod
    async def recall(
        self,
        query: str,
        limit: int = 5,
        memory_type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata_filter: Optional[Dict[str, Any]] = None
    ) -> List[MemoryEntry]:
        """
        Search for relevant memories.
        
        Args:
            query: Search query
            limit: Maximum number of results
            memory_type: Filter by memory type
            tags: Filter by tags
            metadata_filter: Filter by metadata fields
            
        Returns:
            List of matching memory entries
        """
        pass
    
    @abstractmethod
    async def get_recent(
        self,
        limit: int = 10,
        memory_type: Optional[str] = None
    ) -> List[MemoryEntry]:
        """
        Get recent memories.
        
        Args:
            limit: Maximum number of results
            memory_type: Filter by memory type
            
        Returns:
            List of recent memory entries
        """
        pass
    
    @abstractmethod
    async def forget(self, memory_id: str) -> bool:
        """
        Delete a specific memory.
        
        Args:
            memory_id: ID of memory to delete
            
        Returns:
            True if deleted, False if not found
        """
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get memory system statistics.
        
        Returns:
            Dictionary with stats (total_memories, by_type, etc.)
        """
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if memory backend is connected.
        
        Returns:
            True if connected, False otherwise
        """
        pass
