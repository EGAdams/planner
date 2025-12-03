"""
Unit tests for WebSocket transport (RED phase - should FAIL).

These tests define the expected behavior of WebSocketTransport.
They will fail until we implement the class.
"""

import pytest
from a2a_communicating_agents.agent_messaging.message_models import AgentMessage, MessagePriority, ConnectionConfig
from a2a_communicating_agents.agent_messaging.websocket_transport import WebSocketTransport


@pytest.mark.unit
class TestWebSocketTransport:
    """Test suite for WebSocketTransport (TDD - RED phase)"""
    
    @pytest.mark.asyncio
    async def test_transport_creation(self):
        """Should be able to create transport with config"""
        config = ConnectionConfig(url="ws://localhost:3030")
        transport = WebSocketTransport(config)
        assert transport is not None
        assert transport.is_connected() == False
    
    @pytest.mark.asyncio
    async def test_connect_to_server(self, mock_server):
        """Transport should connect to WebSocket server"""
        config = ConnectionConfig(url="ws://localhost:3030")
        transport = WebSocketTransport(config, mock_server=mock_server)
        transport.agent_id = "test-agent"
        
        await transport.connect()
        assert transport.is_connected() == True
        assert mock_server.is_agent_connected("test-agent") == True
    
    @pytest.mark.asyncio
    async def test_disconnect_from_server(self, mock_server):
        """Transport should cleanly disconnect"""
        config = ConnectionConfig(url="ws://localhost:3030")
        transport = WebSocketTransport(config, mock_server=mock_server)
        transport.agent_id = "test-agent"
        
        await transport.connect()
        await transport.disconnect()
        
        assert transport.is_connected() == False
        assert mock_server.is_agent_connected("test-agent") == False
    
    @pytest.mark.asyncio
    async def test_send_message(self, mock_server):
        """Transport should send messages through server"""
        # Setup
        config = ConnectionConfig(url="ws://localhost:3030")
        transport_a = WebSocketTransport(config, mock_server=mock_server)
        transport_a.agent_id = "agent-a"
        transport_b = WebSocketTransport(config, mock_server=mock_server)
        transport_b.agent_id = "agent-b"
        
        await transport_a.connect()
        await transport_b.connect()
        
        # Send message
        message = AgentMessage(
            to_agent="agent-b",
            from_agent="agent-a",
            content="Hello from A"
        )
        
        result = await transport_a.send(message)
        assert result == True
        
        # Verify delivery
        messages = await mock_server.get_messages("agent-b")
        assert len(messages) == 1
        assert messages[0].content == "Hello from A"
    
    @pytest.mark.asyncio
    async def test_subscribe_to_topic(self, mock_server):
        """Transport should subscribe to topics"""
        config = ConnectionConfig(url="ws://localhost:3030")
        transport = WebSocketTransport(config, mock_server=mock_server)
        transport.agent_id = "test-agent"
        
        await transport.connect()
        
        received_messages = []
        
        async def callback(msg: AgentMessage):
            received_messages.append(msg)
        
        await transport.subscribe("test-topic", callback)
        assert mock_server.is_subscribed("test-agent", "test-topic") == True
    
    @pytest.mark.asyncio
    async def test_receive_subscribed_message(self, mock_server):
        """Transport should invoke callback when subscribed message arrives"""
        config = ConnectionConfig(url="ws://localhost:3030")
        transport_a = WebSocketTransport(config, mock_server=mock_server)
        transport_a.agent_id = "agent-a"
        transport_b = WebSocketTransport(config, mock_server=mock_server)
        transport_b.agent_id = "agent-b"
        
        await transport_a.connect()
        await transport_b.connect()
        
        received_messages = []
        
        async def callback(msg: AgentMessage):
            received_messages.append(msg)
        
        # Agent B subscribes to topic
        await transport_b.subscribe("announcements", callback)
        
        # Agent A broadcasts to topic
        message = AgentMessage(
            to_agent="*",
            from_agent="agent-a",
            content="Broadcast message",
            topic="announcements"
        )
        
        await transport_a.send(message)
        
        # Manually trigger message processing (mock doesn't auto-deliver)
        await transport_b._process_pending_messages()
        
        assert len(received_messages) == 1
        assert received_messages[0].content == "Broadcast message"
    
    @pytest.mark.asyncio
    async def test_unsubscribe_from_topic(self, mock_server):
        """Transport should unsubscribe from topics"""
        config = ConnectionConfig(url="ws://localhost:3030")
        transport = WebSocketTransport(config, mock_server=mock_server)
        transport.agent_id = "test-agent"
        
        await transport.connect()
        
        async def callback(msg: AgentMessage):
            pass
        
        await transport.subscribe("test-topic", callback)
        await transport.unsubscribe("test-topic")
        
        assert mock_server.is_subscribed("test-agent", "test-topic") == False
    
    @pytest.mark.asyncio
    async def test_send_without_connection_fails(self):
        """Sending while disconnected should return False"""
        config = ConnectionConfig(url="ws://localhost:3030")
        transport = WebSocketTransport(config)
        
        message = AgentMessage(
            to_agent="agent-b",
            from_agent="agent-a",
            content="Test"
        )
        
        result = await transport.send(message)
        assert result == False
