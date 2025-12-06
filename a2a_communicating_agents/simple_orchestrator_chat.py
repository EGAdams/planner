#!/usr/bin/env python3
"""
Simple async orchestrator chat - properly handles event loops.
"""
import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_messaging.message_models import AgentMessage, MessagePriority, ConnectionConfig
from agent_messaging.websocket_transport import WebSocketTransport

async def receive_messages(transport, topic):
    """Background task to print incoming messages"""
    async def handle_message(msg: AgentMessage):
        if msg.from_agent != 'user-chat-client':  # Don't echo our own messages
            print(f"\n[{msg.from_agent}]: {msg.content}")
            print(": ", end="", flush=True)

    await transport.subscribe(topic, handle_message)

async def chat_loop():
    """Main chat loop"""
    print("🤝 Orchestrator Chat (Async)")
    print("Type your message and press Enter. Ctrl+C to quit.\n")

    # Create transport
    config = ConnectionConfig(url='ws://localhost:3030')
    transport = WebSocketTransport(config)
    transport.agent_id = 'user-chat-client'

    # Connect
    print("Connecting to WebSocket server...")
    try:
        await transport.connect()
        print("✅ Connected!\n")
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        return

    # Subscribe to orchestrator topic
    await receive_messages(transport, 'orchestrator')
    print("📬 Subscribed to 'orchestrator' topic\n")

    try:
        # Chat loop
        while True:
            # Get user input (blocking, but in executor so async)
            user_input = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: input(": ")
            )

            if not user_input.strip():
                continue

            if user_input.lower() in ('/quit', '/exit', 'quit', 'exit'):
                break

            # Send message
            msg = AgentMessage(
                to_agent='board',
                from_agent='user-chat-client',
                content=user_input,
                topic='orchestrator',
                priority=MessagePriority.NORMAL
            )

            success = await transport.send(msg)
            if not success:
                print("❌ Failed to send message")

    except KeyboardInterrupt:
        print("\n\nGoodbye!")
    finally:
        await transport.disconnect()

if __name__ == '__main__':
    asyncio.run(chat_loop())
