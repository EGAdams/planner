"""
Unit tests for LettaTransport.

Tests Letta client wrapping and MessageTransport interface.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from a2a_communicating_agents.agent_messaging.letta_transport import LettaTransport, LettaConfig
from a2a_communicating_agents.agent_messaging.message_models import AgentMessage


@pytest.mark.unit
class TestLettaTransport:
    """Test suite for LettaTransport"""
    
    @pytest.mark.asyncio
    async def test_create_letta_transport(self):
        """Should create transport with config"""
        config = LettaConfig(base_url="http://localhost:8283")
        transport = LettaTransport(config)
        
        assert transport is not None
        assert transport.config.base_url == "http://localhost:8283"
        assert transport.is_connected() == False
    
    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Should connect to Letta server successfully"""
        config = LettaConfig(base_url="http://localhost:8283")
        transport = LettaTransport(config)
        
        # Mock Letta client
        with patch('agent_messaging.letta_transport.Letta') as mock_letta_class:
            mock_client = Mock()
            mock_client.agents.list = Mock(return_value=[])
            mock_letta_class.return_value = mock_client
            
            await transport.connect()
            
            assert transport.is_connected() == True
            assert transport.client is not None
    
    @pytest.mark.asyncio
    async def test_connect_failure(self):
        """Should raise ConnectionError on connect failure"""
        config = LettaConfig(base_url="http://localhost:8283")
        transport = LettaTransport(config)
        
        with patch('agent_messaging.letta_transport.Letta') as mock_letta_class:
            mock_letta_class.side_effect = Exception("Connection refused")
            
            with pytest.raises(ConnectionError, match="Failed to connect"):
                await transport.connect()
            
            assert transport.is_connected() == False
    
    @pytest.mark.asyncio
    async def test_send_message_success(self):
        """Should send message via Letta client"""
        config = LettaConfig(base_url="http://localhost:8283")
        transport = LettaTransport(config)
        
        # Mock connected client
        mock_client = Mock()
        mock_client.agents.messages.create = Mock(return_value={"id": "msg-123"})
        transport.client = mock_client
        transport._connected = True
        
        message = AgentMessage(
            to_agent="agent-b",
            from_agent="agent-a",
            content="Test message"
        )
        
        result = await transport.send(message)
        
        assert result == True
        mock_client.agents.messages.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_message_while_disconnected(self):
        """Should return False when sending while disconnected"""
        config = LettaConfig(base_url="http://localhost:8283")
        transport = LettaTransport(config)
        
        message = AgentMessage(
            to_agent="agent-b",
            from_agent="agent-a",
            content="Test"
        )
        
        result = await transport.send(message)
        assert result == False
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Should disconnect and clean up"""
        config = LettaConfig(base_url="http://localhost:8283")
        transport = LettaTransport(config)
        transport._connected = True
        transport.client = Mock()
        
        await transport.disconnect()
        
        assert transport.is_connected() == False
        assert transport.client is None
    
    @pytest.mark.asyncio
    async def test_subscribe_unsubscribe(self):
        """Should handle subscriptions (no-op for Letta)"""
        config = LettaConfig(base_url="http://localhost:8283")
        transport = LettaTransport(config)
        
        async def callback(msg):
            pass
        
        await transport.subscribe("test-topic", callback)
        assert "test-topic" in transport._subscriptions
        
        await transport.unsubscribe("test-topic")
        assert "test-topic" not in transport._subscriptions
