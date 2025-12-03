"""
Unit tests for mock WebSocket server (RED phase - should PASS).

These tests verify the mock server works correctly before
testing the client against it.
"""

import pytest
from a2a_communicating_agents.agent_messaging.message_models import AgentMessage, MessagePriority


@pytest.mark.unit
class TestMockWebSocketServer:
    """Test suite for MockWebSocketServer"""
    
    @pytest.mark.asyncio
    async def test_agent_can_connect(self, mock_server):
        """Agent should be able to connect to server"""
        await mock_server.connect_agent('agent-a')
        assert mock_server.is_agent_connected('agent-a') == True
        assert mock_server.connection_count() == 1
    
    @pytest.mark.asyncio
    async def test_duplicate_connection_raises_error(self, mock_server):
        """Connecting twice should raise ValueError"""
        await mock_server.connect_agent('agent-a')
        with pytest.raises(ValueError, match="already connected"):
            await mock_server.connect_agent('agent-a')
    
    @pytest.mark.asyncio
    async def test_agent_can_disconnect(self, mock_server):
        """Agent should be able to disconnect"""
        await mock_server.connect_agent('agent-a')
        await mock_server.disconnect_agent('agent-a')
        assert mock_server.is_agent_connected('agent-a') == False
        assert mock_server.connection_count() == 0
    
    @pytest.mark.asyncio
    async def test_subscribe_to_topic(self, mock_server):
        """Agent should be able to subscribe to topics"""
        await mock_server.connect_agent('agent-a')
        await mock_server.subscribe('agent-a', 'test-topic')
        assert mock_server.is_subscribed('agent-a', 'test-topic') == True
    
    @pytest.mark.asyncio
    async def test_send_direct_message(self, mock_server, sample_message):
        """Server should deliver direct messages to target agent"""
        await mock_server.connect_agent('agent-a')
        await mock_server.connect_agent('agent-b')
        
        result = await mock_server.send_message(sample_message)
        assert result == True
        
        messages = await mock_server.get_messages('agent-b')
        assert len(messages) == 1
        assert messages[0].content == "Test message"
        assert messages[0].from_agent == "agent-a"
    
    @pytest.mark.asyncio
    async def test_broadcast_to_topic(self, mock_server):
        """Server should broadcast messages to all topic subscribers"""
        await mock_server.connect_agent('agent-a')
        await mock_server.connect_agent('agent-b')
        await mock_server.connect_agent('agent-c')
        
        await mock_server.subscribe('agent-b', 'announcements')
        await mock_server.subscribe('agent-c', 'announcements')
        
        message = AgentMessage(
            to_agent="*",  # Broadcast
            from_agent="agent-a",
            content="Important announcement",
            topic="announcements"
        )
        
        await mock_server.send_message(message)
        
        # Agent B should receive
        messages_b = await mock_server.get_messages('agent-b')
        assert len(messages_b) == 1
        
        # Agent C should receive
        messages_c = await mock_server.get_messages('agent-c')
        assert len(messages_c) == 1
        
        # Agent A should NOT receive (sender doesn't get own broadcast)
        messages_a = await mock_server.get_messages('agent-a')
        assert len(messages_a) == 0
    
    @pytest.mark.asyncio
    async def test_message_log(self, mock_server, sample_message):
        """Server should keep log of all messages"""
        await mock_server.connect_agent('agent-b')
        await mock_server.send_message(sample_message)
        
        log = mock_server.get_message_log()
        assert len(log) == 1
        assert log[0].content == "Test message"
