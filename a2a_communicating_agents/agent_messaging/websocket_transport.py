"""
WebSocket transport implementation using Strategy and Observer patterns.

Implements the MessageTransport interface for WebSocket-based
agent-to-agent communication.
"""

import asyncio
import json
from typing import Dict, Callable, Awaitable, Optional
from datetime import datetime

try:
    import websockets
except ImportError:
    websockets = None

from .message_transport import MessageTransport
from .message_models import AgentMessage, ConnectionConfig, MessagePriority


class WebSocketTransport(MessageTransport):
    """
    WebSocket implementation of MessageTransport (Strategy pattern).

    Features:
    - Real-time bidirectional communication
    - Topic-based subscriptions (Observer pattern)
    - Automatic reconnection
    - Message queuing during disconnections
    """

    def __init__(
        self,
        config: ConnectionConfig,
        mock_server: Optional['MockWebSocketServer'] = None
    ):
        """
        Initialize WebSocket transport.

        Args:
            config: Connection configuration
            mock_server: Optional mock server for testing
        """
        self.config = config
        self._mock_server = mock_server
        self._connected = False
        self._subscriptions: Dict[str, Callable[[AgentMessage], Awaitable[None]]] = {}
        self.agent_id: Optional[str] = None
        self._websocket = None
        self._receiver_task = None
        self._message_queue = asyncio.Queue()

    async def connect(self) -> None:
        """Establish connection to WebSocket server"""
        if self.agent_id is None:
            raise ValueError("agent_id must be set before connecting")

        if self._mock_server:
            # Use mock server for testing
            await self._mock_server.connect_agent(self.agent_id)
            self._connected = True
            return

        # Real WebSocket connection
        if websockets is None:
            raise ConnectionError("websockets package not installed. Install with: pip install websockets")

        try:
            # Connect to WebSocket server
            self._websocket = await websockets.connect(self.config.url)

            # Register with server
            registration = {
                "type": "register",
                "agent_id": self.agent_id
            }
            await self._websocket.send(json.dumps(registration))

            # Wait for confirmation
            response = await asyncio.wait_for(self._websocket.recv(), timeout=5.0)
            data = json.loads(response)

            if data.get("type") != "registered":
                raise ConnectionError(f"Registration failed: {data}")

            self._connected = True

            # Start receiver task
            self._receiver_task = asyncio.create_task(self._receive_messages())

        except Exception as e:
            self._connected = False
            if self._websocket:
                await self._websocket.close()
                self._websocket = None
            raise ConnectionError(f"Failed to connect to WebSocket server: {e}")

    async def disconnect(self) -> None:
        """Clean up connection and resources"""
        if not self._connected:
            return

        if self._mock_server:
            await self._mock_server.disconnect_agent(self.agent_id)
        elif self._websocket:
            # Cancel receiver task
            if self._receiver_task:
                self._receiver_task.cancel()
                try:
                    await self._receiver_task
                except asyncio.CancelledError:
                    pass

            # Close WebSocket
            await self._websocket.close()
            self._websocket = None

        self._connected = False
        self._subscriptions.clear()

    async def send(self, message: AgentMessage) -> bool:
        """
        Send message via WebSocket.

        Args:
            message: AgentMessage to deliver

        Returns:
            True if sent successfully, False otherwise
        """
        if not self._connected:
            print(f"WebSocket send error: Not connected")
            return False

        if self._mock_server:
            return await self._mock_server.send_message(message)

        # Real WebSocket send
        try:
            payload = {
                "type": "send",
                "topic": message.topic,
                "to_agent": message.to_agent,
                "from_agent": message.from_agent,
                "content": message.content,
                "priority": message.priority.value if hasattr(message.priority, 'value') else message.priority,
                "metadata": getattr(message, 'metadata', {})
            }

            await self._websocket.send(json.dumps(payload))

            # Wait for "sent" acknowledgment with timeout (skip other acks)
            deadline = asyncio.get_event_loop().time() + 5.0
            while asyncio.get_event_loop().time() < deadline:
                remaining = deadline - asyncio.get_event_loop().time()
                if remaining <= 0:
                    raise asyncio.TimeoutError()

                ack = await asyncio.wait_for(self._message_queue.get(), timeout=remaining)
                if ack.get("type") == "sent":
                    return True
                # Got a different ack (subscribed, unsubscribed), discard and keep waiting
                print(f"[WebSocketTransport] Skipping {ack.get('type')} ack, waiting for 'sent'...")

            raise asyncio.TimeoutError()

        except asyncio.TimeoutError:
            print(f"WebSocket send error: Timeout waiting for acknowledgment")
            print(f"  - Receiver task running: {self._receiver_task and not self._receiver_task.done()}")
            print(f"  - WebSocket open: {self._websocket and not self._websocket.closed if hasattr(self._websocket, 'closed') else 'unknown'}")
            print(f"  - Queue size: {self._message_queue.qsize()}")
            print(f"  - Connected: {self._connected}")
            # Try to see what's in the queue without blocking
            temp_items = []
            try:
                while not self._message_queue.empty():
                    item = self._message_queue.get_nowait()
                    temp_items.append(item)
                    print(f"  - Queue had: {item}")
                # Put them back
                for item in temp_items:
                    self._message_queue.put_nowait(item)
            except:
                pass
            return False
        except Exception as e:
            print(f"WebSocket send error: {e}")
            import traceback
            traceback.print_exc()
            return False

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
        if not self._connected:
            raise RuntimeError("Must connect before subscribing")

        self._subscriptions[topic] = callback

        if self._mock_server:
            await self._mock_server.subscribe(self.agent_id, topic)
        else:
            # Send subscription request to server
            request = {
                "type": "subscribe",
                "topic": topic
            }
            await self._websocket.send(json.dumps(request))

    async def unsubscribe(self, topic: str) -> None:
        """
        Unsubscribe from topic.

        Args:
            topic: Topic to unsubscribe from
        """
        if topic in self._subscriptions:
            del self._subscriptions[topic]

        if self._mock_server and self.agent_id:
            await self._mock_server.unsubscribe(self.agent_id, topic)
        elif self._websocket:
            # Send unsubscription request to server
            request = {
                "type": "unsubscribe",
                "topic": topic
            }
            await self._websocket.send(json.dumps(request))

    def is_connected(self) -> bool:
        """
        Check if transport is currently connected.

        Returns:
            True if connected, False otherwise
        """
        return self._connected

    async def _receive_messages(self) -> None:
        """
        Background task to receive and dispatch messages.
        Runs continuously while connected.
        """
        try:
            async for raw_message in self._websocket:
                try:
                    data = json.loads(raw_message)
                    msg_type = data.get("type")

                    if msg_type == "message":
                        # Incoming message from server
                        await self._handle_incoming_message(data)

                    elif msg_type in ("sent", "subscribed", "unsubscribed"):
                        # Acknowledgment - put in queue for send() to process
                        print(f"[WebSocketTransport-{self.agent_id}] Received ACK: {msg_type} for topic {data.get('topic')}")
                        await self._message_queue.put(data)
                        print(f"[WebSocketTransport-{self.agent_id}] ACK queued, queue size now: {self._message_queue.qsize()}")

                    elif msg_type == "error":
                        print(f"WebSocket error: {data.get('message')}")

                    elif msg_type == "history":
                        # Message history for newly subscribed topic
                        for historical_msg in data.get("messages", []):
                            await self._handle_incoming_message(historical_msg)

                except json.JSONDecodeError as e:
                    print(f"Invalid JSON received: {e}")
                except Exception as e:
                    print(f"Error processing message: {e}")

        except asyncio.CancelledError:
            # Task was cancelled, clean shutdown
            pass
        except Exception as e:
            print(f"Receiver error: {e}")
            self._connected = False

    async def _handle_incoming_message(self, data: dict) -> None:
        """
        Handle an incoming message and dispatch to callbacks.

        Args:
            data: Message data from server
        """
        topic = data.get("topic")

        if topic not in self._subscriptions:
            print(f"[WebSocketTransport] Topic '{topic}' not in subscriptions, ignoring")
            return

        # Convert to AgentMessage
        message = AgentMessage(
            to_agent=data.get("to_agent", "board"),
            from_agent=data.get("from_agent", "unknown"),
            content=data.get("content", ""),
            topic=topic,
            priority=MessagePriority(data.get("priority", "normal")),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat()))
        )

        # Invoke callback (fire and forget to not block ack processing)
        callback = self._subscriptions[topic]
        async def safe_callback():
            try:
                await callback(message)
            except Exception as e:
                print(f"Error in subscription callback for topic '{topic}': {e}")
                import traceback
                traceback.print_exc()

        # Don't await - let it run in background so we can process acks quickly
        asyncio.create_task(safe_callback())

    async def poll_messages(self, agent_id: str, topic: Optional[str] = None) -> list:
        """
        Poll for messages (compatibility method for existing code).

        Note: With WebSocket, messages are pushed automatically via subscriptions.
        This method is provided for backward compatibility but is not needed
        with real-time WebSocket communication.

        Returns empty list as messages are delivered via callbacks.
        """
        return []
