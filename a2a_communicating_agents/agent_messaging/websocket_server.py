#!/usr/bin/env python3
"""
WebSocket Message Board Server

Real-time message routing server for agent-to-agent communication.
Supports topic-based pub/sub with instant message delivery.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Set, Optional
from pathlib import Path
import sys

try:
    import websockets
    from websockets.server import WebSocketServerProtocol
except ImportError:
    print("ERROR: websockets package not installed. Install with: pip install websockets")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Store connected clients by agent_id
clients: Dict[str, WebSocketServerProtocol] = {}

# Store topic subscriptions: topic -> set of agent_ids
subscriptions: Dict[str, Set[str]] = {}

# Message history for new subscribers (last 100 messages per topic)
message_history: Dict[str, list] = {}
MAX_HISTORY = 100


async def register_client(websocket: WebSocketServerProtocol, agent_id: str):
    """Register a new client connection."""
    if agent_id in clients:
        logger.warning(f"Agent {agent_id} reconnecting, closing old connection")
        old_socket = clients[agent_id]
        await old_socket.close()

    clients[agent_id] = websocket
    logger.info(f"✅ Agent '{agent_id}' connected (total: {len(clients)})")


async def unregister_client(agent_id: str):
    """Unregister a client and clean up subscriptions."""
    if agent_id in clients:
        del clients[agent_id]

    # Remove from all topic subscriptions
    for topic, subscribers in subscriptions.items():
        subscribers.discard(agent_id)

    logger.info(f"❌ Agent '{agent_id}' disconnected (total: {len(clients)})")


async def subscribe_to_topic(agent_id: str, topic: str):
    """Subscribe an agent to a topic."""
    if topic not in subscriptions:
        subscriptions[topic] = set()

    subscriptions[topic].add(agent_id)
    logger.info(f"📬 Agent '{agent_id}' subscribed to topic '{topic}'")

    # Send message history for this topic
    if topic in message_history and message_history[topic]:
        websocket = clients.get(agent_id)
        if websocket:
            history_msg = {
                "type": "history",
                "topic": topic,
                "messages": message_history[topic][-10:]  # Last 10 messages
            }
            try:
                await websocket.send(json.dumps(history_msg))
                logger.debug(f"📜 Sent {len(history_msg['messages'])} history messages to '{agent_id}'")
            except Exception as e:
                logger.error(f"Failed to send history to '{agent_id}': {e}")


async def unsubscribe_from_topic(agent_id: str, topic: str):
    """Unsubscribe an agent from a topic."""
    if topic in subscriptions:
        subscriptions[topic].discard(agent_id)
        logger.info(f"📭 Agent '{agent_id}' unsubscribed from topic '{topic}'")


async def broadcast_message(message: dict, topic: str, from_agent: str):
    """Broadcast a message to all subscribers of a topic."""
    # Add to message history
    if topic not in message_history:
        message_history[topic] = []

    message_history[topic].append({
        **message,
        "timestamp": datetime.utcnow().isoformat(),
        "from_agent": from_agent
    })

    # Trim history
    if len(message_history[topic]) > MAX_HISTORY:
        message_history[topic] = message_history[topic][-MAX_HISTORY:]

    # Get subscribers for this topic
    subscribers = subscriptions.get(topic, set())

    if not subscribers:
        logger.debug(f"📢 No subscribers for topic '{topic}'")
        return

    # Prepare message envelope
    envelope = {
        "type": "message",
        "topic": topic,
        "from_agent": from_agent,
        "timestamp": datetime.utcnow().isoformat(),
        "content": message.get("content", ""),
        "to_agent": message.get("to_agent", "board"),
        "priority": message.get("priority", "normal"),
        "metadata": message.get("metadata", {})
    }

    # Send to all subscribers
    disconnected = []
    sent_count = 0

    for agent_id in subscribers:
        websocket = clients.get(agent_id)
        if websocket:
            try:
                # Check if connection is still open (handles different websockets library versions)
                if hasattr(websocket, 'closed') and websocket.closed:
                    disconnected.append(agent_id)
                    continue

                await websocket.send(json.dumps(envelope))
                sent_count += 1
            except Exception as e:
                logger.error(f"Failed to send to '{agent_id}': {e}")
                disconnected.append(agent_id)
        else:
            disconnected.append(agent_id)

    # Clean up disconnected clients
    for agent_id in disconnected:
        await unregister_client(agent_id)

    logger.info(f"📤 Sent message on topic '{topic}' to {sent_count}/{len(subscribers)} subscribers")


async def handle_message(websocket: WebSocketServerProtocol, message: str, agent_id: str):
    """Handle incoming message from a client."""
    try:
        data = json.loads(message)
        msg_type = data.get("type")

        if msg_type == "subscribe":
            topic = data.get("topic", "general")
            await subscribe_to_topic(agent_id, topic)

            # Send acknowledgment
            ack = {"type": "subscribed", "topic": topic}
            await websocket.send(json.dumps(ack))

        elif msg_type == "unsubscribe":
            topic = data.get("topic", "general")
            await unsubscribe_from_topic(agent_id, topic)

            # Send acknowledgment
            ack = {"type": "unsubscribed", "topic": topic}
            await websocket.send(json.dumps(ack))

        elif msg_type == "send":
            topic = data.get("topic", "general")
            logger.info(f"📨 Agent '{agent_id}' sending to topic '{topic}'")
            await broadcast_message(data, topic, agent_id)

            # Send acknowledgment
            ack = {"type": "sent", "topic": topic}
            logger.info(f"✉️  Sending ACK to '{agent_id}' for topic '{topic}'")
            await websocket.send(json.dumps(ack))
            logger.info(f"✅ ACK sent to '{agent_id}'")

        elif msg_type == "ping":
            # Respond to ping with pong
            pong = {"type": "pong"}
            await websocket.send(json.dumps(pong))

        else:
            logger.warning(f"Unknown message type '{msg_type}' from '{agent_id}'")
            error = {"type": "error", "message": f"Unknown message type: {msg_type}"}
            await websocket.send(json.dumps(error))

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON from '{agent_id}': {e}")
        error = {"type": "error", "message": "Invalid JSON"}
        await websocket.send(json.dumps(error))

    except Exception as e:
        logger.error(f"Error handling message from '{agent_id}': {e}")
        error = {"type": "error", "message": str(e)}
        try:
            await websocket.send(json.dumps(error))
        except:
            pass


async def handler(websocket: WebSocketServerProtocol):
    """Main WebSocket connection handler."""
    agent_id = None

    try:
        # First message should be registration
        registration = await websocket.recv()
        reg_data = json.loads(registration)

        if reg_data.get("type") != "register":
            error = {"type": "error", "message": "First message must be registration"}
            await websocket.send(json.dumps(error))
            return

        agent_id = reg_data.get("agent_id")
        if not agent_id:
            error = {"type": "error", "message": "agent_id required"}
            await websocket.send(json.dumps(error))
            return

        # Register the client
        await register_client(websocket, agent_id)

        # Send registration confirmation
        confirm = {"type": "registered", "agent_id": agent_id}
        await websocket.send(json.dumps(confirm))

        # Handle messages
        async for message in websocket:
            await handle_message(websocket, message, agent_id)

    except websockets.exceptions.ConnectionClosed:
        logger.debug(f"Connection closed for '{agent_id or 'unknown'}'")

    except Exception as e:
        logger.error(f"Error in handler for '{agent_id or 'unknown'}': {e}")

    finally:
        if agent_id:
            await unregister_client(agent_id)


async def main():
    """Start the WebSocket server."""
    host = "0.0.0.0"  # Listen on all interfaces for cross-machine access
    port = 3030

    logger.info("🚀 Starting WebSocket Message Board Server")
    logger.info(f"   Listening on {host}:{port}")
    logger.info(f"   Connect with: ws://localhost:{port}")
    logger.info(f"   Remote access: ws://<your-ip>:{port}")
    logger.info("")

    async with websockets.serve(handler, host, port):
        logger.info("✅ WebSocket server is running!")
        logger.info("   Press Ctrl+C to stop")
        logger.info("")

        # Run forever
        await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n👋 Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
