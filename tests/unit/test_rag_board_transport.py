"""
Unit tests for RAGBoardTransport.

Tests RAG-based message persistence and MessageTransport interface.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from agent_messaging.rag_board_transport import RAGBoardTransport
from agent_messaging.message_models import AgentMessage, MessagePriority


@pytest.mark.unit
class TestRAGBoardTransport:
    """Test suite for RAGBoardTransport"""
    
    @pytest.mark.asyncio
    async def test_create_rag_transport(self):
        """Should create transport with DocumentManager"""
        mock_doc_manager = Mock()
        transport = RAGBoardTransport(mock_doc_manager)
        
        assert transport is not None
        assert transport.is_connected() == True  # Always connected
    
    @pytest.mark.asyncio
    async def test_connect_always_succeeds(self):
        """RAG board should always connect successfully"""
        mock_doc_manager = Mock()
        transport = RAGBoardTransport(mock_doc_manager)
        
        await transport.connect()
        assert transport.is_connected() == True
    
    @pytest.mark.asyncio
    async def test_send_message_persists_to_rag(self):
        """Should persist message to RAG with tags"""
        mock_doc_manager = Mock()
        mock_doc_manager.add_runtime_artifact = Mock(return_value="artifact-123")
        
        transport = RAGBoardTransport(mock_doc_manager)
        
        message = AgentMessage(
            to_agent="agent-b",
            from_agent="agent-a",
            content="Test message",
            topic="general",
            priority=MessagePriority.HIGH
        )
        
        result = await transport.send(message)
        
        assert result == True
        mock_doc_manager.add_runtime_artifact.assert_called_once()
        
        # Verify tags were included
        call_kwargs = mock_doc_manager.add_runtime_artifact.call_args[1]
        assert "general" in call_kwargs['tags']
        assert "to:agent-b" in call_kwargs['tags']
        assert "from:agent-a" in call_kwargs['tags']
    
    @pytest.mark.asyncio
    async def test_send_message_failure(self):
        """Should return False on persistence failure"""
        mock_doc_manager = Mock()
        mock_doc_manager.add_runtime_artifact = Mock(side_effect=Exception("DB error"))
        
        transport = RAGBoardTransport(mock_doc_manager)
        
        message = AgentMessage(
            to_agent="agent-b",
            from_agent="agent-a",
            content="Test"
        )
        
        result = await transport.send(message)
        assert result == False
    
    @pytest.mark.asyncio
    async def test_subscribe_registers_callback(self):
        """Should register callback for topic"""
        mock_doc_manager = Mock()
        transport = RAGBoardTransport(mock_doc_manager)
        
        async def callback(msg):
            pass
        
        await transport.subscribe("test-topic", callback)
        assert "test-topic" in transport._subscriptions
    
    @pytest.mark.asyncio
    async def test_unsubscribe_removes_callback(self):
        """Should remove callback on unsubscribe"""
        mock_doc_manager = Mock()
        transport = RAGBoardTransport(mock_doc_manager)
        
        async def callback(msg):
            pass
        
        await transport.subscribe("test-topic", callback)
        await transport.unsubscribe("test-topic")
        
        assert "test-topic" not in transport._subscriptions
    
    @pytest.mark.asyncio
    async def test_disconnect_cleans_up(self):
        """Should clean up subscriptions on disconnect"""
        mock_doc_manager = Mock()
        transport = RAGBoardTransport(mock_doc_manager)
        
        async def callback(msg):
            pass
        
        await transport.subscribe("topic1", callback)
        await transport.subscribe("topic2", callback)
        
        await transport.disconnect()
        
        assert len(transport._subscriptions) == 0
        assert transport.is_connected() == False
    
    @pytest.mark.asyncio
    async def test_poll_messages(self):
        """Should poll for messages from RAG"""
        mock_doc_manager = Mock()
        mock_doc_manager.search_artifacts = Mock(return_value=[
            {"content": "Message 1"},
            {"content": "Message 2"}
        ])
        
        transport = RAGBoardTransport(mock_doc_manager)
        
        messages = await transport.poll_messages("agent-b", topic="general")
        
        assert len(messages) == 2
        mock_doc_manager.search_artifacts.assert_called_once()
