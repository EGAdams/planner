"""
Letta memory blocks backend implementation.

Provides persistent memory storage using Letta's blocks API.
Best for: Conversational context, recent events, shared agent memory.
"""

import asyncio
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
try:
    from letta import Letta
except ImportError:
    Letta = None  # Letta not installed

from .memory_backend import MemoryBackend, MemoryEntry, MemoryQuery
from pydantic import BaseModel


class LettaMemoryConfig(BaseModel):
    """Configuration for Letta memory backend"""
    base_url: str = "http://localhost:8283"
    api_key: Optional[str] = None


class LettaMemory(MemoryBackend):
    """
    Letta blocks-based memory backend.
    
    Uses Letta's persistent memory blocks for storage.
    Memory is shared across all agents connected to the same Letta server.
    
    Note: Letta blocks use simple text search, not semantic/vector search.
    For semantic search, use ChromaDBMemory instead.
    """
    
    def __init__(self, config: LettaMemoryConfig):
        """
        Initialize Letta memory backend.
        
        Args:
            config: LettaMemoryConfig with base_url and optional api_key
        """
        self.config = config
        self.client: Optional[Letta] = None
        self._connected = False
        
    async def connect(self) -> None:
        """Establish connection to Letta server"""
        if Letta is None:
            raise ConnectionError("Letta package not installed. Install with: pip install letta")
        
        try:
            if self.config.api_key:
                self.client = Letta(api_key=self.config.api_key)
            else:
                self.client = Letta(base_url=self.config.base_url)
            
            # Test connection by listing blocks
            await asyncio.to_thread(self.client.blocks.list)
            self._connected = True
            
        except Exception as e:
            self._connected = False
            raise ConnectionError(f"Failed to connect to Letta: {e}")
    
    async def disconnect(self) -> None:
        """Clean up connection"""
        self._connected = False
        self.client = None
    
    def _encode_memory(self, content: str, memory_type: str, source: str, 
                       tags: Optional[List[str]], metadata: Optional[Dict[str, Any]]) -> str:
        """
        Encode memory data as JSON prefix + content.
        
        Format: {metadata_json}\n---\n{content}
        """
        memory_data = {
            "memory_type": memory_type,
            "source": source,
            "tags": tags or [],
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        }
        
        encoded = json.dumps(memory_data) + "\n---\n" + content
        return encoded
    
    def _decode_memory(self, block_id: str, block_value: str, block_label: str) -> MemoryEntry:
        """
        Decode memory block into MemoryEntry.
        
        Args:
            block_id: Block ID
            block_value: Block content (JSON prefix + content)
            block_label: Block label
            
        Returns:
            MemoryEntry
        """
        try:
            # Split metadata from content
            if "\n---\n" in block_value:
                json_part, content = block_value.split("\n---\n", 1)
                memory_data = json.loads(json_part)
            else:
                # Old format or simple block
                memory_data = {
                    "memory_type": "general",
                    "source": "unknown",
                    "tags": [],
                    "metadata": {},
                    "timestamp": datetime.now().isoformat()
                }
                content = block_value
            
            return MemoryEntry(
                id=block_id,
                content=content,
                timestamp=datetime.fromisoformat(memory_data["timestamp"]),
                metadata=memory_data.get("metadata", {}),
                tags=memory_data.get("tags", []),
                source=memory_data.get("source", "unknown"),
                memory_type=memory_data.get("memory_type", "general")
            )
        except Exception:
            # Fallback for malformed blocks
            return MemoryEntry(
                id=block_id,
                content=block_value,
                timestamp=datetime.now(),
                metadata={},
                tags=[],
                source="unknown",
                memory_type="general"
            )
    
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
            Memory entry ID (block ID)
        """
        if not self._connected or not self.client:
            raise ConnectionError("Not connected to Letta server")
        
        try:
            # Create label from type and source
            label = f"{memory_type}:{source}"
            
            # Encode memory with metadata
            value = self._encode_memory(content, memory_type, source, tags, metadata)
            
            # Create block
            block = await asyncio.to_thread(
                self.client.blocks.create,
                label=label,
                value=value,
                template=False
            )
            
            return block.id
            
        except Exception as e:
            raise RuntimeError(f"Failed to store memory: {e}")
    
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
        
        Note: Letta blocks don't support semantic search.
        This does simple text matching and filtering.
        
        Args:
            query: Search query (simple text match)
            limit: Maximum number of results
            memory_type: Filter by memory type
            tags: Filter by tags (must contain all specified tags)
            metadata_filter: Filter by metadata fields
            
        Returns:
            List of matching memory entries
        """
        if not self._connected or not self.client:
            raise ConnectionError("Not connected to Letta server")
        
        try:
            # Get all blocks
            response = await asyncio.to_thread(self.client.blocks.list)
            blocks = response.blocks if hasattr(response, 'blocks') else []
            
            results = []
            query_lower = query.lower()
            
            for block in blocks:
                # Decode memory
                entry = self._decode_memory(block.id, block.value, block.label)
                
                # Apply filters
                if memory_type and entry.memory_type != memory_type:
                    continue
                
                if tags:
                    if not all(tag in entry.tags for tag in tags):
                        continue
                
                if metadata_filter:
                    matches = all(
                        entry.metadata.get(k) == v 
                        for k, v in metadata_filter.items()
                    )
                    if not matches:
                        continue
                
                # Text search in content
                if query and query_lower not in entry.content.lower():
                    continue
                
                results.append(entry)
            
            # Sort by timestamp (most recent first)
            results.sort(key=lambda e: e.timestamp, reverse=True)
            
            return results[:limit]
            
        except Exception as e:
            raise RuntimeError(f"Failed to recall memories: {e}")
    
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
        # Use recall with empty query to get all, then filter
        return await self.recall(
            query="",
            limit=limit,
            memory_type=memory_type
        )
    
    async def forget(self, memory_id: str) -> bool:
        """
        Delete a specific memory.
        
        Args:
            memory_id: ID of memory to delete (block ID)
            
        Returns:
            True if deleted, False if not found
        """
        if not self._connected or not self.client:
            raise ConnectionError("Not connected to Letta server")
        
        try:
            await asyncio.to_thread(
                self.client.blocks.delete,
                block_id=memory_id
            )
            return True
        except Exception:
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get memory system statistics.
        
        Returns:
            Dictionary with stats (total_memories, by_type, etc.)
        """
        if not self._connected or not self.client:
            raise ConnectionError("Not connected to Letta server")
        
        try:
            response = await asyncio.to_thread(self.client.blocks.list)
            blocks = response.blocks if hasattr(response, 'blocks') else []
            
            # Decode all and categorize
            type_counts = {}
            source_counts = {}
            
            for block in blocks:
                entry = self._decode_memory(block.id, block.value, block.label)
                type_counts[entry.memory_type] = type_counts.get(entry.memory_type, 0) + 1
                source_counts[entry.source] = source_counts.get(entry.source, 0) + 1
            
            return {
                "total_memories": len(blocks),
                "by_type": type_counts,
                "by_source": source_counts,
                "backend": "letta",
                "server_url": self.config.base_url
            }
            
        except Exception as e:
            raise RuntimeError(f"Failed to get stats: {e}")
    
    def is_connected(self) -> bool:
        """
        Check if memory backend is connected.
        
        Returns:
            True if connected, False otherwise
        """
        return self._connected
