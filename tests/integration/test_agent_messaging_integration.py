"""
Integration tests for AgentMessenger with TransportFactory.

Verifies that AgentMessenger correctly initializes and uses the appropriate
transport based on availability.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from a2a_communicating_agents.agent_messaging import AgentMessenger
from a2a_communicating_agents.agent_messaging.transport_factory import TransportFactory
from a2a_communicating_agents.agent_messaging.message_models import AgentMessage

TRANSPORT_FACTORY_IMPORT = (
    "a2a_communicating_agents.agent_messaging.transport_factory.TransportFactory"
)

@pytest.mark.integration
class TestAgentMessengerIntegration:
    """Integration tests for AgentMessenger"""

    @pytest.fixture
    def mock_transport_factory(self):
        """Mock TransportFactory to control transport selection"""
        with patch(TRANSPORT_FACTORY_IMPORT) as mock_factory:
            yield mock_factory

    def test_initialization_defaults(self):
        """Should initialize with default transport (WebSocket)"""
        # We need to mock the factory's create_transport method
        with patch(f"{TRANSPORT_FACTORY_IMPORT}.create_transport") as mock_create:
            mock_transport = AsyncMock()
            mock_create.return_value = ("websocket", mock_transport)
            
            messenger = AgentMessenger(agent_id="test-agent")
            
            assert messenger.transport_name == "websocket"
            assert messenger.transport == mock_transport
            mock_create.assert_called_once()

    def test_send_message_delegates_to_transport(self):
        """send_message should use the active transport"""
        with patch(f"{TRANSPORT_FACTORY_IMPORT}.create_transport") as mock_create:
            mock_transport = AsyncMock()
            mock_transport.send.return_value = True
            mock_create.return_value = ("websocket", mock_transport)
            
            messenger = AgentMessenger(agent_id="test-agent")
            
            result = messenger.send_message("target-agent", "Hello")
            
            assert result["status"] == "sent"
            assert result["transport"] == "websocket"
            mock_transport.send.assert_called_once()
            
            # Verify message content
            call_args = mock_transport.send.call_args[0][0]
            assert isinstance(call_args, AgentMessage)
            assert call_args.content == "Hello"
            assert call_args.to_agent == "target-agent"
            assert call_args.from_agent == "test-agent"

    def test_send_message_failure(self):
        """Should handle transport failure gracefully"""
        with patch(f"{TRANSPORT_FACTORY_IMPORT}.create_transport") as mock_create:
            mock_transport = AsyncMock()
            mock_transport.send.return_value = False
            mock_create.return_value = ("websocket", mock_transport)
            
            messenger = AgentMessenger(agent_id="test-agent")
            
            result = messenger.send_message("target-agent", "Hello")
            
            assert "error" in result
            assert result["error"] == "Send failed"

    def test_post_to_board_with_rag_transport(self):
        """post_to_board should work when messenger already has RAG transport"""
        with patch(f"{TRANSPORT_FACTORY_IMPORT}.create_transport") as mock_create:
            # Initialize messenger with RAG transport
            from a2a_communicating_agents.agent_messaging.rag_board_transport import RAGBoardTransport
            mock_transport = AsyncMock(spec=RAGBoardTransport)
            mock_transport.send.return_value = True
            mock_create.return_value = ("rag", mock_transport)
            
            messenger = AgentMessenger(agent_id="test-agent")
            
            # Since messenger has RAG transport, post_to_board should use it directly
            result = messenger.post_to_board("Test message")
            
            # Should have used existing RAG transport
            assert result is not None
            mock_transport.send.assert_called_once()

    def test_read_messages_rag_fallback(self):
        """read_messages should poll RAG if transport is RAG"""
        with patch(f"{TRANSPORT_FACTORY_IMPORT}.create_transport") as mock_create:
            mock_transport = AsyncMock()
            mock_transport.poll_messages.return_value = [
                AgentMessage(to_agent="me", from_agent="other", content="Hi")
            ]
            mock_create.return_value = ("rag", mock_transport)
            
            messenger = AgentMessenger(agent_id="test-agent")
            
            messages = messenger.read_messages("test-agent")
            
            assert len(messages) == 1
            assert messages[0].content == "Hi"
            mock_transport.poll_messages.assert_called_once()
