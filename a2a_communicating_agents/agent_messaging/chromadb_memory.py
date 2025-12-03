"""
ChromaDB memory backend implementation.

Wraps existing DocumentManager/RAGEngine for semantic vector search.
Best for: Code artifacts, historical knowledge, semantic similarity searches.
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime

from .memory_backend import MemoryBackend, MemoryEntry, MemoryQuery


class ChromaDBMemory(MemoryBackend):
    """
    ChromaDB-based memory backend.
    
    Wraps the existing DocumentManager/RAGEngine for vector search.
    Preserves artifact boosting (time decay + tag boosting).
    
    Note: This is always available as it uses local storage.
    """
    
    def __init__(self, doc_manager=None):
        """
        Initialize ChromaDB memory backend.
        
        Args:
            doc_manager: Optional DocumentManager instance (created if None)
        """
        self.doc_manager = doc_manager
        self._connected = False
        
    async def connect(self) -> None:
        """Establish connection to ChromaDB"""
        try:
            # Lazy import to avoid circular dependency
            if self.doc_manager is None:
                from rag_system.core.document_manager import DocumentManager
                # Run in thread to avoid blocking
                # This may raise PanicException if ChromaDB is corrupted
                self.doc_manager = await asyncio.to_thread(DocumentManager)
            
            self._connected = True
            
        except Exception as e:
            self._connected = False
            # Provide helpful error message
            error_msg = str(e)
            if "panic" in error_msg.lower() or "rust" in error_msg.lower():
                raise ConnectionError(
                    f"ChromaDB corrupted (rust panic). "
                    f"Delete ./storage/chromadb and try again, or use Letta. Error: {e}"
                )
            raise ConnectionError(f"Failed to initialize ChromaDB: {e}")
    
    async def disconnect(self) -> None:
        """Clean up connection"""
        self._connected = False
        # DocumentManager has no explicit cleanup needed
    
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
            Memory entry ID (document ID)
        """
        if not self._connected or not self.doc_manager:
            raise ConnectionError("Not connected to ChromaDB")
        
        try:
            # Use DocumentManager's add_runtime_artifact method
            # Map memory_type to artifact_type
            artifact_type = memory_type  # Direct mapping
            
            # Combine metadata
            full_metadata = metadata or {}
            full_metadata['tags'] = tags or []
            full_metadata['timestamp'] = datetime.now().isoformat()
            
            # Store via DocumentManager (run in thread)
            doc_id = await asyncio.to_thread(
                self.doc_manager.add_runtime_artifact,
                artifact_text=content,
                artifact_type=artifact_type,
                source=source,
                file_path=full_metadata.get('file_path'),
                project_name=full_metadata.get('project_name'),
                tags=tags
            )
            
            return doc_id
            
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
        Search for relevant memories using semantic vector search.
        
        Args:
            query: Search query (uses embeddings for semantic search)
            limit: Maximum number of results
            memory_type: Filter by memory type (artifact_type)
            tags: Filter by tags
            metadata_filter: Filter by metadata fields
            
        Returns:
            List of matching memory entries (sorted by relevance + time decay)
        """
        if not self._connected or not self.doc_manager:
            raise ConnectionError("Not connected to ChromaDB")
        
        try:
            # Use DocumentManager's search_artifacts method
            results = await asyncio.to_thread(
                self.doc_manager.search_artifacts,
                query=query,
                artifact_type=memory_type,
                file_path=metadata_filter.get('file_path') if metadata_filter else None,
                n_results=limit
            )
            
            # Convert QueryResult objects to MemoryEntry objects
            memories = []
            for result in results:
                # Extract metadata
                created_at_str = result.metadata.get('created_at', datetime.now().isoformat())
                try:
                    created_at = datetime.fromisoformat(created_at_str)
                except (ValueError, TypeError):
                    created_at = datetime.now()
                
                # Parse tags from metadata
                result_tags = []
                if 'tags' in result.metadata:
                    tags_str = result.metadata['tags']
                    if isinstance(tags_str, str):
                        result_tags = [t.strip() for t in tags_str.split(',') if t.strip()]
                    elif isinstance(tags_str, list):
                        result_tags = tags_str
                
                # Apply tag filter if specified
                if tags:
                    if not all(tag in result_tags for tag in tags):
                        continue
                
                memory = MemoryEntry(
                    id=result.chunk_id,
                    content=result.content,
                    timestamp=created_at,
                    metadata=result.metadata,
                    tags=result_tags,
                    source=result.metadata.get('source', 'unknown'),
                    memory_type=result.metadata.get('artifact_type', 'general')
                )
                memories.append(memory)
            
            return memories
            
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
        if not self._connected or not self.doc_manager:
            raise ConnectionError("Not connected to ChromaDB")
        
        try:
            # Use get_recent_activities with artifact filtering
            results = await asyncio.to_thread(
                self.doc_manager.get_recent_activities,
                n_results=limit
            )
            
            # Convert to MemoryEntry and filter by type if specified
            memories = []
            for result in results:
                artifact_type = result.metadata.get('artifact_type', '')
                
                # Filter by memory_type
                if memory_type and artifact_type != memory_type:
                    continue
                
                created_at_str = result.metadata.get('created_at', datetime.now().isoformat())
                try:
                    created_at = datetime.fromisoformat(created_at_str)
                except (ValueError, TypeError):
                    created_at = datetime.now()
                
                # Parse tags
                result_tags = []
                if 'tags' in result.metadata:
                    tags_str = result.metadata['tags']
                    if isinstance(tags_str, str):
                        result_tags = [t.strip() for t in tags_str.split(',') if t.strip()]
                    elif isinstance(tags_str, list):
                        result_tags = tags_str
                
                memory = MemoryEntry(
                    id=result.chunk_id,
                    content=result.content,
                    timestamp=created_at,
                    metadata=result.metadata,
                    tags=result_tags,
                    source=result.metadata.get('source', 'unknown'),
                    memory_type=artifact_type or 'general'
                )
                memories.append(memory)
            
            return memories
            
        except Exception as e:
            raise RuntimeError(f"Failed to get recent memories: {e}")
    
    async def forget(self, memory_id: str) -> bool:
        """
        Delete a specific memory.
        
        Args:
            memory_id: ID of memory to delete (document/chunk ID)
            
        Returns:
            True if deleted, False if not found
        """
        if not self._connected or not self.doc_manager:
            raise ConnectionError("Not connected to ChromaDB")
        
        try:
            # Extract document ID from chunk ID (format: doc_id_chunk_N)
            doc_id = memory_id.split('_chunk_')[0] if '_chunk_' in memory_id else memory_id
            
            # Delete document (deletes all chunks)
            success = await asyncio.to_thread(
                self.doc_manager.rag_engine.delete_document,
                document_id=doc_id
            )
            return success
            
        except Exception:
            return False
    
    async def get_stats(self) -> Dict[str, Any]:
        """
        Get memory system statistics.
        
        Returns:
            Dictionary with stats (total_memories, by_type, etc.)
        """
        if not self._connected or not self.doc_manager:
            raise ConnectionError("Not connected to ChromaDB")
        
        try:
            # Get system stats
            stats = await asyncio.to_thread(
                self.doc_manager.get_system_stats
            )
            
            # Add backend info
            stats['backend'] = 'chromadb'
            
            return stats
            
        except Exception as e:
            raise RuntimeError(f"Failed to get stats: {e}")
    
    def is_connected(self) -> bool:
        """
        Check if memory backend is connected.
        
        Returns:
            True if connected, False otherwise
        """
        return self._connected
