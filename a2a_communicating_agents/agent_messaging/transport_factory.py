"""
Transport factory with smart fallback logic.

Automatically selects best available transport with priority:
1. WebSocket (fastest)
2. Letta (medium speed)
3. RAG Board (always available)
"""

import os
import asyncio
from typing import Optional, Tuple

from .message_transport import MessageTransport
from .websocket_transport import WebSocketTransport
from .letta_transport import LettaTransport, LettaConfig
from .rag_board_transport import RAGBoardTransport
from .message_models import ConnectionConfig


class TransportFactory:
    """
    Factory for creating transports with automatic fallback.
    
    Tries transports in priority order until one succeeds.
    Provides both async and sync interfaces for backward compatibility.
    """
    
    TRANSPORT_PRIORITY = [
        ("websocket", WebSocketTransport),
        ("letta", LettaTransport),
        ("rag", RAGBoardTransport),
    ]
    
    @classmethod
    async def create_transport_async(
        cls,
        agent_id: str,
        websocket_url: Optional[str] = None,
        letta_base_url: Optional[str] = None,
        letta_api_key: Optional[str] = None,
        doc_manager = None,
        forced_transport: Optional[str] = None
    ) -> Tuple[str, MessageTransport]:
        """
        Create transport with automatic fallback (async version).
        
        Args:
            agent_id: ID of this agent
            websocket_url: WebSocket URL (auto-detected if None)
            letta_base_url: Letta server URL
            letta_api_key: Optional Letta API key
            doc_manager: DocumentManager instance for RAG fallback
            forced_transport: Force specific transport (testing only)
            
        Returns:
            (transport_name, transport_instance)
        """
        errors = []
        
        # Auto-detect WebSocket URL from environment
        if websocket_url is None:
            websocket_url = os.getenv('WEBSOCKET_URL', 'ws://localhost:3030')
        
        # Build configs
        ws_config = ConnectionConfig(url=websocket_url)
        letta_config = LettaConfig(
            base_url=letta_base_url or os.getenv('LETTA_BASE_URL', 'http://localhost:8283'),
            api_key=letta_api_key or os.getenv('LETTA_API_KEY')
        )
        
        # If forced, try only that transport
        if forced_transport:
            priority = [(forced_transport, dict(cls.TRANSPORT_PRIORITY)[forced_transport])]
        else:
            priority = cls.TRANSPORT_PRIORITY
        
        for name, transport_class in priority:
            try:
                if name == "websocket":
                    transport = transport_class(ws_config)
                    transport.agent_id = agent_id
                    await transport.connect()
                    print(f"  Using WebSocket transport ({websocket_url})")
                    return (name, transport)
                
                elif name == "letta":
                    transport = transport_class(letta_config)
                    await transport.connect()
                    print(f"    WebSocket unavailable, using Letta transport ({letta_config.base_url})")
                    return (name, transport)
                
                elif name == "rag":
                    if doc_manager is None:
                        # Lazy import to avoid circular dependency
                        from rag_system.core.document_manager import DocumentManager
                        doc_manager = DocumentManager()
                    
                    transport = transport_class(doc_manager)
                    await transport.connect()
                    print(f"    Letta unavailable, using RAG message board (fallback)")
                    return (name, transport)
                    
            except Exception as e:
                errors.append(f"{name}: {str(e)}")
                continue
        
        raise ConnectionError(f"All transports failed: {'; '.join(errors)}")
    
    @classmethod
    def create_transport(cls, agent_id: str, **kwargs) -> Tuple[str, MessageTransport]:
        """
        Create transport with automatic fallback (sync wrapper).
        
        This is a synchronous wrapper around create_transport_async()
        for backward compatibility with existing code.
        
        Args:
            agent_id: ID of this agent
            **kwargs: Passed to create_transport_async()
            
        Returns:
            (transport_name, transport_instance)
        """
        try:
            # Try to get existing event loop
            loop = asyncio.get_running_loop()
            # We're in an async context, can't use asyncio.run()
            raise RuntimeError("Use create_transport_async() in async context")
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(cls.create_transport_async(agent_id, **kwargs))
