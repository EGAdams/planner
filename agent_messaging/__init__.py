"""
Agent-to-Agent messaging system with pluggable transports.

Supports WebSocket, Letta, and RAG-based message delivery.
Also provides unified memory system with Letta and ChromaDB backends.
"""

from .message_transport import MessageTransport
from .websocket_transport import WebSocketTransport
from .letta_transport import LettaTransport, LettaConfig
from .rag_board_transport import RAGBoardTransport
from .transport_factory import TransportFactory
from .message_models import AgentMessage, MessagePriority
from .messenger import (
    AgentMessenger, 
    send_to_agent, 
    broadcast, 
    post_message, 
    read_messages, 
    list_agents, 
    list_groups,
    create_jsonrpc_request,
    create_jsonrpc_response,
    inbox,
    send
)

# Memory system imports
from .memory_backend import MemoryBackend, MemoryEntry, MemoryQuery
from .letta_memory import LettaMemory, LettaMemoryConfig
from .chromadb_memory import ChromaDBMemory
from .memory_factory import MemoryFactory

# Global memory instance cache
_memory_instance = None

async def get_memory(agent_id: str = "default", **kwargs):
    """
    Get or create global memory instance.
    
    Args:
        agent_id: Agent ID for memory context
        **kwargs: Additional config (letta_base_url, letta_api_key, etc.)
        
    Returns:
        MemoryBackend instance
    """
    global _memory_instance
    if _memory_instance is None:
        _, _memory_instance = await MemoryFactory.create_memory_async(agent_id, **kwargs)
    return _memory_instance

async def remember(
    content: str,
    memory_type: str = "general",
    source: str = "unknown",
    tags: list = None,
    metadata: dict = None,
    agent_id: str = "default"
) -> str:
    """
    Convenience function to store a memory.
    
    Uses MemoryFactory to automatically select backend (Letta   ChromaDB).
    
    Args:
        content: Memory content to store
        memory_type: Type of memory (error, fix, deployment, note, etc.)
        source: Source identifier (agent name, file path, etc.)
        tags: Optional tags for categorization
        metadata: Optional additional metadata
        agent_id: Agent ID for memory context
        
    Returns:
        Memory ID
        
    Example:
        await remember("Dashboard started on port 3000", memory_type="deployment", source="dashboard-agent")
    """
    memory = await get_memory(agent_id)
    return await memory.remember(content, memory_type, source, tags, metadata)

async def recall(
    query: str,
    limit: int = 5,
    memory_type: str = None,
    tags: list = None,
    metadata_filter: dict = None,
    agent_id: str = "default"
) -> list:
    """
    Convenience function to search memories.
    
    Uses MemoryFactory to automatically select backend (Letta   ChromaDB).
    
    Args:
        query: Search query
        limit: Maximum number of results
        memory_type: Filter by memory type
        tags: Filter by tags
        metadata_filter: Filter by metadata fields
        agent_id: Agent ID for memory context
        
    Returns:
        List of MemoryEntry objects
        
    Example:
        results = await recall("dashboard startup issues", memory_type="error")
    """
    memory = await get_memory(agent_id)
    return await memory.recall(query, limit, memory_type, tags, metadata_filter)

async def forget(memory_id: str, agent_id: str = "default") -> bool:
    """
    Convenience function to delete a memory.
    
    Args:
        memory_id: ID of memory to delete
        agent_id: Agent ID for memory context
        
    Returns:
        True if deleted, False if not found
    """
    memory = await get_memory(agent_id)
    return await memory.forget(memory_id)

async def get_recent_memories(limit: int = 10, memory_type: str = None, agent_id: str = "default") -> list:
    """
    Convenience function to get recent memories.
    
    Args:
        limit: Maximum number of results
        memory_type: Filter by memory type
        agent_id: Agent ID for memory context
        
    Returns:
        List of MemoryEntry objects
    """
    memory = await get_memory(agent_id)
    return await memory.get_recent(limit, memory_type)

__all__ = [
    # Transport system
    'MessageTransport',
    'WebSocketTransport',
    'LettaTransport',
    'LettaConfig',
    'RAGBoardTransport',
    'TransportFactory',
    'AgentMessage',
    'MessagePriority',
    'AgentMessenger',
    'send_to_agent',
    'broadcast',
    'post_message',
    'read_messages',
    'list_agents',
    'list_groups',
    'create_jsonrpc_request',
    'create_jsonrpc_response',
    'inbox',
    'send',
    # Memory system
    'MemoryBackend',
    'MemoryEntry',
    'MemoryQuery',
    'LettaMemory',
    'LettaMemoryConfig',
    'ChromaDBMemory',
    'MemoryFactory',
    'get_memory',
    'remember',
    'recall',
    'forget',
    'get_recent_memories',
]

