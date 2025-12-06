#!/usr/bin/env python3
"""
TransportManager - Singleton pattern for shared transport instance.

Implements GoF Singleton Pattern to ensure all agents use the same
WebSocket connection, eliminating duplicate connections and RAG fallbacks.

Key Features:
- Thread-safe via asyncio.Lock
- Lazy initialization
- Lifecycle management (connect/disconnect)
- Single source of truth for transport state
"""

import asyncio
import logging
from typing import Optional, Tuple

from .message_transport import MessageTransport
from .transport_factory import TransportFactory

logger = logging.getLogger(__name__)


class TransportManager:
    """
    Singleton managing the global shared transport instance.

    This ensures all agents and messaging functions use the same
    WebSocket connection, preventing duplicate connections and
    eliminating fallback to RAG transport for message passing.

    Thread-Safety:
        Uses asyncio.Lock to protect initialization and state changes
        in async environments.

    Usage:
        # In any agent or messaging function
        transport_name, transport = await TransportManager.get_transport("my-agent")

        # Use transport for messaging
        await transport.send(message)
        await transport.subscribe("topic", callback)

    Example:
        >>> manager = TransportManager()  # Always returns same instance
        >>> name, transport = await manager.get_transport("agent-1")
        >>> print(name)  # "websocket"
        >>> # All subsequent calls return the SAME transport
        >>> name2, transport2 = await manager.get_transport("agent-2")
        >>> assert transport is transport2  # Same object!
    """

    # Class-level state (shared across all instances)
    _instance: Optional['TransportManager'] = None
    _transport: Optional[MessageTransport] = None
    _transport_name: Optional[str] = None
    _lock: Optional[asyncio.Lock] = None
    _initialized: bool = False
    _agent_id: Optional[str] = None

    def __new__(cls):
        """
        Override __new__ to implement Singleton pattern.
        Always returns the same instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            # Initialize lock at first instance creation
            # Note: Lock must be created in async context, so we defer this
        return cls._instance

    @classmethod
    async def _ensure_lock(cls):
        """Ensure lock exists (must be called from async context)."""
        if cls._lock is None:
            cls._lock = asyncio.Lock()

    @classmethod
    async def get_transport(
        cls,
        agent_id: str,
        force_reconnect: bool = False,
        **kwargs
    ) -> Tuple[str, MessageTransport]:
        """
        Get or create the shared transport instance.

        Thread-safe via asyncio.Lock. First call initializes transport,
        subsequent calls return the same instance.

        Args:
            agent_id: ID of the requesting agent (used for first initialization)
            force_reconnect: If True, disconnect and reconnect transport
            **kwargs: Additional args passed to TransportFactory

        Returns:
            Tuple of (transport_name, transport_instance)
            - transport_name: "websocket", "letta", or "rag"
            - transport_instance: The shared MessageTransport object

        Raises:
            ConnectionError: If all transports fail to connect

        Example:
            >>> name, transport = await TransportManager.get_transport("orchestrator")
            >>> await transport.send(message)
        """
        # Ensure lock exists
        await cls._ensure_lock()

        async with cls._lock:
            # If already initialized and not forcing reconnect, return existing
            if cls._initialized and not force_reconnect:
                logger.debug(
                    f"Returning existing {cls._transport_name} transport "
                    f"(initialized by {cls._agent_id}, requested by {agent_id})"
                )
                return cls._transport_name, cls._transport

            # Need to initialize or reconnect
            if force_reconnect and cls._transport:
                logger.info(f"Force reconnecting transport (requested by {agent_id})")
                try:
                    await cls._transport.disconnect()
                except Exception as e:
                    logger.warning(f"Error disconnecting during reconnect: {e}")

            # Create new transport
            logger.info(f"Initializing shared transport for agent: {agent_id}")

            try:
                cls._transport_name, cls._transport = \
                    await TransportFactory.create_transport_async(
                        agent_id=agent_id,
                        **kwargs
                    )

                cls._agent_id = agent_id
                cls._initialized = True

                logger.info(
                    f"✅ Shared transport initialized: {cls._transport_name} "
                    f"(by {agent_id})"
                )

                return cls._transport_name, cls._transport

            except Exception as e:
                logger.error(f"Failed to initialize transport: {e}")
                raise

    @classmethod
    async def disconnect(cls):
        """
        Disconnect the shared transport and reset state.

        Call this during application shutdown to cleanly close
        the WebSocket connection.

        Example:
            >>> await TransportManager.disconnect()
        """
        await cls._ensure_lock()

        async with cls._lock:
            if cls._transport:
                logger.info(f"Disconnecting shared {cls._transport_name} transport")
                try:
                    await cls._transport.disconnect()
                except Exception as e:
                    logger.warning(f"Error during disconnect: {e}")
                finally:
                    cls._transport = None
                    cls._transport_name = None
                    cls._initialized = False
                    cls._agent_id = None
            else:
                logger.debug("Disconnect called but no transport was initialized")

    @classmethod
    def is_initialized(cls) -> bool:
        """
        Check if shared transport is initialized.

        Returns:
            True if transport is ready to use, False otherwise

        Example:
            >>> if TransportManager.is_initialized():
            ...     print("Transport ready!")
        """
        return cls._initialized and cls._transport is not None

    @classmethod
    def get_transport_name(cls) -> Optional[str]:
        """
        Get the name of the current transport without async.

        Returns:
            "websocket", "letta", "rag", or None if not initialized

        Example:
            >>> print(TransportManager.get_transport_name())
            'websocket'
        """
        return cls._transport_name

    @classmethod
    def get_agent_id(cls) -> Optional[str]:
        """
        Get the agent ID that initialized the transport.

        Returns:
            Agent ID string or None if not initialized

        Example:
            >>> print(TransportManager.get_agent_id())
            'orchestrator-agent'
        """
        return cls._agent_id

    @classmethod
    async def reset(cls):
        """
        Reset singleton state (primarily for testing).

        WARNING: This will disconnect all agents! Only use during
        testing or controlled shutdown.

        Example:
            >>> # In test cleanup
            >>> await TransportManager.reset()
        """
        await cls.disconnect()
        cls._instance = None
        cls._lock = None
