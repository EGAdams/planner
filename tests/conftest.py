"""
Pytest configuration and shared fixtures.
"""

import pytest
import asyncio
from tests.fixtures.mock_websocket_server import MockWebSocketServer


@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mock_server():
    """Provide a fresh mock WebSocket server for each test"""
    server = MockWebSocketServer()
    yield server
    # Cleanup: disconnect all agents
    for agent_id in list(server._connections.keys()):
        await server.disconnect_agent(agent_id)


@pytest.fixture
def sample_message():
    """Provide a sample AgentMessage for testing"""
    from agent_messaging.message_models import AgentMessage, MessagePriority
    return AgentMessage(
        to_agent="agent-b",
        from_agent="agent-a",
        content="Test message",
        topic="general",
        priority=MessagePriority.NORMAL
    )
