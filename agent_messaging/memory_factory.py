"""
Memory factory with smart fallback logic.

Automatically selects best available memory backend with priority:
1. Letta (shared, persistent, cloud-ready)
2. ChromaDB (local, semantic search, always available)
"""

import os
import asyncio
from typing import Optional, Tuple
from .memory_backend import MemoryBackend
from .letta_memory import LettaMemory, LettaMemoryConfig
from .chromadb_memory import ChromaDBMemory


class MemoryFactory:
    """
    Factory for creating memory backends with automatic fallback.
    
    Tries backends in priority order until one succeeds.
    Provides both async and sync interfaces for backward compatibility.
    """
    
    MEMORY_PRIORITY = [
        ("letta", LettaMemory),
        ("chromadb", ChromaDBMemory),
    ]
    
    @classmethod
    async def create_memory_async(
        cls,
        agent_id: str,
        letta_base_url: Optional[str] = None,
        letta_api_key: Optional[str] = None,
        doc_manager = None,
        forced_backend: Optional[str] = None
    ) -> Tuple[str, MemoryBackend]:
        """
        Create memory backend with automatic fallback (async version).
        
        Args:
            agent_id: ID of this agent (for potential future use)
            letta_base_url: Letta server URL (auto-detected if None)
            letta_api_key: Optional Letta API key for cloud
            doc_manager: DocumentManager instance for ChromaDB fallback
            forced_backend: Force specific backend (testing only)
            
        Returns:
            (backend_name, memory_instance)
        """
        errors = []
        
        # Auto-detect Letta URL from environment
        if letta_base_url is None:
            letta_base_url = os.getenv('LETTA_BASE_URL', 'http://localhost:8283')
        
        # Build configs
        letta_config = LettaMemoryConfig(
            base_url=letta_base_url,
            api_key=letta_api_key or os.getenv('LETTA_API_KEY')
        )
        
        # If forced, try only that backend
        if forced_backend:
            priority = [(forced_backend, dict(cls.MEMORY_PRIORITY)[forced_backend])]
        else:
            priority = cls.MEMORY_PRIORITY
        
        for name, memory_class in priority:
            try:
                if name == "letta":
                    memory = memory_class(letta_config)
                    await memory.connect()
                    print(f"  Using Letta memory ({letta_base_url})")
                    return (name, memory)
                
                elif name == "chromadb":
                    if doc_manager is None:
                        # Lazy import to avoid circular dependency
                        from rag_system.core.document_manager import DocumentManager
                        doc_manager = DocumentManager()
                    
                    memory = memory_class(doc_manager)
                    await memory.connect()
                    print(f"    Letta unavailable, using ChromaDB memory (fallback)")
                    return (name, memory)
                    
            except Exception as e:
                errors.append(f"{name}: {str(e)}")
                continue
        
        raise ConnectionError(f"All memory backends failed: {'; '.join(errors)}")
    
    @classmethod
    def create_memory(cls, agent_id: str, **kwargs) -> Tuple[str, MemoryBackend]:
        """
        Create memory backend with automatic fallback (sync wrapper).
        
        This is a synchronous wrapper around create_memory_async()
        for backward compatibility with existing code.
        
        Args:
            agent_id: ID of this agent
            **kwargs: Passed to create_memory_async()
            
        Returns:
            (backend_name, memory_instance)
        """
        try:
            # Try to get existing event loop
            loop = asyncio.get_running_loop()
            # We're in an async context, can't use asyncio.run()
            raise RuntimeError("Use create_memory_async() in async context")
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(cls.create_memory_async(agent_id, **kwargs))
