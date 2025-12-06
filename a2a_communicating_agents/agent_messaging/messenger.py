#!/usr/bin/env python3
"""
Agent-to-Agent Messaging System (Async Refactored)

Implements GoF Facade Pattern to provide simple interface for agent communication.
Uses TransportManager Singleton to ensure all agents share the same WebSocket connection.

Key Changes:
- All methods converted to async/await
- Uses TransportManager singleton (no duplicate connections)
- Observer pattern support via subscribe()
- Backward compatibility wrappers for sync code
- Eliminates RAG fallback for messaging (WebSocket-first)

GoF Patterns:
- Facade Pattern: AgentMessenger simplifies transport complexity
- Singleton Pattern: TransportManager ensures one connection
- Observer Pattern: subscribe() for real-time message delivery
"""

import os
import asyncio
import json
import uuid
import logging
from typing import Optional, List, Dict, Callable, Awaitable
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table

# Import transport system
from .transport_manager import TransportManager  # NEW: Use singleton
from .message_models import AgentMessage, MessagePriority
try:
    from .rag_board_transport import RAGBoardTransport
except ImportError:
    RAGBoardTransport = None  # Optional dependency

# Try to import Letta for backward compatibility methods
try:
    from letta_client import Letta
except ImportError:
    Letta = None

console = Console()
logger = logging.getLogger(__name__)


# ============================================================================
# JSON-RPC HELPERS
# ============================================================================

def create_jsonrpc_request(method: str, params: Dict, request_id: int = 1) -> str:
    """Create a JSON-RPC 2.0 request string"""
    return json.dumps({
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": request_id
    })


def create_jsonrpc_response(result: Dict, request_id: int = 1) -> str:
    """Create a JSON-RPC 2.0 response string"""
    return json.dumps({
        "jsonrpc": "2.0",
        "result": result,
        "id": request_id
    })


# ============================================================================
# AGENT MESSENGER (FACADE PATTERN)
# ============================================================================

class AgentMessenger:
    """
    Facade for agent communication using shared TransportManager.

    This class provides a simple interface for agents to send/receive messages
    while using the shared TransportManager singleton underneath. This eliminates
    duplicate WebSocket connections and RAG transport fallbacks.

    GoF Patterns:
        - Facade Pattern: Simplifies transport interface
        - Uses Singleton (TransportManager) internally

    Example:
        >>> messenger = AgentMessenger("my-agent")
        >>> await messenger.send_to_agent("coder-agent", "write hello world")
        >>> await messenger.subscribe("responses", my_callback)
    """

    def __init__(self, agent_id: Optional[str] = None):
        """
        Initialize messenger (uses shared transport via TransportManager).

        Args:
            agent_id: ID of this agent (optional, auto-generated if None)

        Note:
            Multiple AgentMessenger instances with different agent_ids
            will still use the SAME underlying WebSocket connection.
        """
        self.agent_id = agent_id or f"agent-{uuid.uuid4().hex[:8]}"
        self._transport_initialized = False
        self.transport = None
        self.transport_name = None

        # Keep direct Letta client for backward compatibility
        self.base_url = os.getenv('LETTA_BASE_URL', 'http://localhost:8283')
        self.api_key = os.getenv('LETTA_API_KEY')

        try:
            if Letta:
                if self.api_key:
                    self.client = Letta(api_key=self.api_key)
                else:
                    self.client = Letta(base_url=self.base_url)
            else:
                self.client = None
        except Exception:
            self.client = None

    async def _ensure_transport(self):
        """
        Lazy initialization of transport via TransportManager singleton.

        First call initializes shared transport, subsequent calls reuse it.
        """
        if not self._transport_initialized:
            logger.debug(f"Agent '{self.agent_id}' getting shared transport")
            self.transport_name, self.transport = \
                await TransportManager.get_transport(self.agent_id)
            self._transport_initialized = True
            logger.info(
                f"✅ Agent '{self.agent_id}' using shared {self.transport_name} transport"
            )

    # ========================================================================
    # ASYNC MESSAGING METHODS
    # ========================================================================

    async def send_to_agent(
        self,
        agent_id: str,
        message: str,
        topic: Optional[str] = None,
        priority: MessagePriority = MessagePriority.NORMAL,
        role: str = "user"
    ) -> bool:
        """
        Send message to specific agent (async).

        Args:
            agent_id: Target agent ID or "board" for broadcast
            message: Message content
            topic: Topic/channel (defaults to agent_id)
            priority: Message priority
            role: Message role (user, assistant, system)

        Returns:
            True if sent successfully, False otherwise

        Example:
            >>> await messenger.send_to_agent("coder-agent", "write code", topic="code")
        """
        await self._ensure_transport()

        try:
            msg = AgentMessage(
                to_agent=agent_id,
                from_agent=self.agent_id,
                content=message,
                topic=topic or agent_id,
                priority=priority,
                metadata={"role": role}
            )

            success = await self.transport.send(msg)

            if success:
                logger.debug(f"✅ {self.agent_id} → {agent_id} ({len(message)} chars)")
                return True
            else:
                logger.warning(f"❌ Failed to send from {self.agent_id} to {agent_id}")
                return False

        except Exception as e:
            logger.error(f"Error sending message from {self.agent_id} to {agent_id}: {e}")
            return False

    async def subscribe(
        self,
        topic: str,
        callback: Callable[[AgentMessage], Awaitable[None]]
    ) -> bool:
        """
        Subscribe to topic using Observer Pattern (WebSocket only).

        Your callback will be invoked automatically when messages arrive.

        Args:
            topic: Topic to subscribe to
            callback: Async function(message: AgentMessage) -> None

        Returns:
            True if subscribed successfully

        Example:
            >>> async def handle_message(msg: AgentMessage):
            ...     print(f"Got message: {msg.content}")
            >>>
            >>> await messenger.subscribe("code", handle_message)
        """
        await self._ensure_transport()

        try:
            if self.transport_name == "websocket":
                await self.transport.subscribe(topic, callback)
                logger.info(f"✅ Agent '{self.agent_id}' subscribed to topic '{topic}'")
                return True
            else:
                logger.warning(
                    f"Subscribe not supported on {self.transport_name} transport. "
                    "Use read_messages() polling instead."
                )
                return False

        except Exception as e:
            logger.error(f"Error subscribing to topic '{topic}': {e}")
            return False

    async def read_messages(
        self,
        topic: str,
        limit: int = 10
    ) -> List[AgentMessage]:
        """
        Poll for messages on topic (fallback for non-WebSocket transports).

        For WebSocket, prefer subscribe() instead.

        Args:
            topic: Topic to read from
            limit: Maximum messages to return

        Returns:
            List of AgentMessage objects

        Example:
            >>> messages = await messenger.read_messages("code", limit=5)
        """
        await self._ensure_transport()

        try:
            if hasattr(self.transport, 'poll_messages'):
                messages = await self.transport.poll_messages("board", topic=topic)
                return messages[:limit]
            else:
                logger.warning(f"Polling not supported on {self.transport_name}")
                return []

        except Exception as e:
            logger.error(f"Error reading messages from topic '{topic}': {e}")
            return []

    # ========================================================================
    # LETTA COMPATIBILITY METHODS (unchanged, for backward compat)
    # ========================================================================

    def list_agents(self) -> List:
        """List all agents (via Letta if available)"""
        if not self.client:
            console.print("  Letta client not available", style="yellow")
            return []

        try:
            agents_list = self.client.list_agents()
            if agents_list:
                table = Table(title=f"Agents ({len(agents_list)} found)")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="green")
                table.add_column("Description", style="yellow")

                for agent in agents_list:
                    agent_id = agent.id[:12] + "..." if len(agent.id) > 12 else agent.id
                    name = getattr(agent, 'name', 'Unknown')
                    desc = (getattr(agent, 'description', '') or '')[:50]
                    table.add_row(agent_id, name, desc)

                console.print(table)
            return agents_list

        except Exception as e:
            console.print(f"  Error listing agents: {e}", style="red")
            return []

    def list_groups(self) -> List:
        """List all agent groups (via Letta if available)"""
        if not self.client:
            console.print("  Letta client not available", style="yellow")
            return []

        try:
            groups_list = self.client.list_groups()
            if groups_list:
                table = Table(title=f"Groups ({len(groups_list)} found)")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="green")
                table.add_column("Description", style="yellow")

                for group in groups_list:
                    group_id = group.id[:12] + "..." if len(group.id) > 12 else group.id
                    name = getattr(group, 'name', 'Unknown')
                    desc = getattr(group, 'description', '')[:50]
                    table.add_row(group_id, name, desc)

                console.print(table)
            return groups_list

        except Exception as e:
            console.print(f"  Error listing groups: {e}", style="red")
            return []


# ============================================================================
# ASYNC CONVENIENCE FUNCTIONS (PRIMARY INTERFACE)
# ============================================================================

async def send_to_agent_async(
    agent_id: str,
    message: str,
    from_agent: str = "sender",
    topic: Optional[str] = None,
    priority: MessagePriority = MessagePriority.NORMAL
) -> bool:
    """
    Send message to agent (async convenience function).

    Uses shared TransportManager singleton.

    Example:
        >>> await send_to_agent_async("coder-agent", "write hello world")
    """
    messenger = AgentMessenger(agent_id=from_agent)
    return await messenger.send_to_agent(agent_id, message, topic=topic, priority=priority)


async def post_message_async(
    message: str,
    topic: str = "general",
    from_agent: str = "sender",
    to_agent: str = "board",
    priority: MessagePriority = MessagePriority.NORMAL
) -> bool:
    """
    Post message to topic (async convenience function).

    Uses shared TransportManager singleton.

    Example:
        >>> await post_message_async("Hello world", topic="orchestrator")
    """
    messenger = AgentMessenger(agent_id=from_agent)
    return await messenger.send_to_agent(to_agent, message, topic=topic, priority=priority)


async def inbox_async(
    topic: str,
    limit: int = 10,
    agent_id: str = "inbox-reader"
) -> List[AgentMessage]:
    """
    Read messages from topic (async convenience function).

    Uses shared TransportManager singleton.

    Example:
        >>> messages = await inbox_async("orchestrator", limit=5)
    """
    messenger = AgentMessenger(agent_id=agent_id)
    return await messenger.read_messages(topic, limit=limit)


async def subscribe_async(
    topic: str,
    callback: Callable[[AgentMessage], Awaitable[None]],
    agent_id: str = "subscriber"
) -> bool:
    """
    Subscribe to topic with callback (async convenience function).

    Uses shared TransportManager singleton.

    Example:
        >>> async def my_handler(msg):
        ...     print(msg.content)
        >>>
        >>> await subscribe_async("code", my_handler)
    """
    messenger = AgentMessenger(agent_id=agent_id)
    return await messenger.subscribe(topic, callback)


# ============================================================================
# BACKWARD COMPATIBILITY (SYNC WRAPPERS)
# ============================================================================
# These wrap async functions for old code that expects sync interface.
# NEW CODE SHOULD USE ASYNC VERSIONS ABOVE.
# ============================================================================

def send_to_agent(agent_id: str, message: str, from_agent: str = "sender") -> bool:
    """
    Sync wrapper for send_to_agent_async().

    DEPRECATED: Use send_to_agent_async() in new code.
    """
    return asyncio.run(send_to_agent_async(agent_id, message, from_agent=from_agent))


def post_message(
    message: str,
    topic: str = "general",
    from_agent: str = "sender",
    to_agent: str = "board"
) -> bool:
    """
    Sync wrapper for post_message_async().

    DEPRECATED: Use post_message_async() in new code.
    """
    return asyncio.run(post_message_async(message, topic, from_agent, to_agent))


def read_messages(
    topic: str,
    limit: int = 10,
    render: bool = False
) -> List[AgentMessage]:
    """
    Sync wrapper for inbox_async().

    DEPRECATED: Use inbox_async() in new code.

    Args:
        topic: Topic to read from
        limit: Max messages
        render: Ignored (kept for compatibility)

    Returns:
        List of messages
    """
    return asyncio.run(inbox_async(topic, limit=limit))


def list_agents():
    """List all agents via Letta"""
    messenger = AgentMessenger()
    return messenger.list_agents()


def list_groups():
    """List all agent groups via Letta"""
    messenger = AgentMessenger()
    return messenger.list_groups()


# Aliases
inbox = read_messages  # Backward compat
send = send_to_agent   # Backward compat
broadcast = send_to_agent  # Simplified


# ============================================================================
# DEPRECATED BACKWARD COMPATIBILITY - DO NOT USE IN NEW CODE
# ============================================================================
# These exist only to avoid breaking old code.
# Use async versions (send_to_agent_async, post_message_async, etc) instead.
# ============================================================================
