"""
Agent-to-Agent messaging system with pluggable transports.

Supports WebSocket, Letta, and RAG-based message delivery.
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

__all__ = [
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
    'send'
]
