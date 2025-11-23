"""
Unit tests for TransportFactory.

Tests smart fallback logic and transport selection.
"""

import pytest
import os
from unittest.mock import Mock, patch, AsyncMock
from agent_messaging.transport_factory import TransportFactory
from agent_messaging.message_models import ConnectionConfig


@pytest.mark.unit
class TestTransportFactory:
    """Test suite for TransportFactory fallback logic"""
    
    @pytest.mark.asyncio
    async def test_websocket_selected_when_available(self):
        """Should use WebSocket as first priority"""
        mock_ws_cls = Mock()
        mock_transport = AsyncMock()
        mock_transport.connect = AsyncMock()
        mock_ws_cls.return_value = mock_transport
        
        # Patch the priority list to use our mock class
        with patch.object(TransportFactory, 'TRANSPORT_PRIORITY', [("websocket", mock_ws_cls)]):
            name, transport = await TransportFactory.create_transport_async(
                agent_id="test-agent"
            )
            
            assert name == "websocket"
            assert transport is mock_transport
    
    @pytest.mark.asyncio
    async def test_fallback_to_letta_when_websocket_fails(self):
        """Should fall back to Letta when WebSocket fails"""
        # Mock WebSocket to fail
        mock_ws_cls = Mock()
        mock_ws_instance = AsyncMock()
        mock_ws_instance.connect.side_effect = ConnectionError("WebSocket unavailable")
        mock_ws_cls.return_value = mock_ws_instance
        
        # Mock Letta to succeed
        mock_letta_cls = Mock()
        mock_letta_instance = AsyncMock()
        mock_letta_instance.connect = AsyncMock()
        mock_letta_cls.return_value = mock_letta_instance
        
        priority = [
            ("websocket", mock_ws_cls),
            ("letta", mock_letta_cls)
        ]
        
        with patch.object(TransportFactory, 'TRANSPORT_PRIORITY', priority):
            name, transport = await TransportFactory.create_transport_async(
                agent_id="test-agent"
            )
            
            assert name == "letta"
            assert transport is mock_letta_instance
    
    @pytest.mark.asyncio
    async def test_fallback_to_rag_when_all_fail(self):
        """Should fall back to RAG when WebSocket and Letta fail"""
        mock_doc_manager = Mock()
        
        # Mock all to fail except RAG
        mock_ws_cls = Mock()
        mock_ws_cls.return_value.connect.side_effect = ConnectionError("WS fail")
        
        mock_letta_cls = Mock()
        mock_letta_cls.return_value.connect.side_effect = ConnectionError("Letta fail")
        
        mock_rag_cls = Mock()
        mock_rag_instance = AsyncMock()
        mock_rag_instance.connect = AsyncMock()
        mock_rag_cls.return_value = mock_rag_instance
        
        priority = [
            ("websocket", mock_ws_cls),
            ("letta", mock_letta_cls),
            ("rag", mock_rag_cls)
        ]
        
        with patch.object(TransportFactory, 'TRANSPORT_PRIORITY', priority):
            name, transport = await TransportFactory.create_transport_async(
                agent_id="test-agent",
                doc_manager=mock_doc_manager
            )
            
            assert name == "rag"
            assert transport is mock_rag_instance
    
    @pytest.mark.asyncio
    async def test_autodetect_websocket_url_from_env(self):
        """Should auto-detect WebSocket URL from environment"""
        mock_ws_cls = Mock()
        mock_transport = AsyncMock()
        mock_transport.connect = AsyncMock()
        mock_ws_cls.return_value = mock_transport
        
        with patch.dict(os.environ, {'WEBSOCKET_URL': 'ws://custom:9999'}), \
             patch.object(TransportFactory, 'TRANSPORT_PRIORITY', [("websocket", mock_ws_cls)]):
            
            name, transport = await TransportFactory.create_transport_async(
                agent_id="test-agent"
            )
            
            # Verify custom URL was used
            call_args = mock_ws_cls.call_args[0][0]
            assert call_args.url == 'ws://custom:9999'
    
    @pytest.mark.asyncio
    async def test_forced_transport(self):
        """Should use forced transport when specified"""
        mock_doc_manager = Mock()
        mock_rag_cls = Mock()
        mock_rag_instance = AsyncMock()
        mock_rag_instance.connect = AsyncMock()
        mock_rag_cls.return_value = mock_rag_instance
        
        # We need to patch the dict lookup in create_transport_async
        # But create_transport_async uses dict(cls.TRANSPORT_PRIORITY)
        # So we need TRANSPORT_PRIORITY to contain the forced transport
        
        with patch.object(TransportFactory, 'TRANSPORT_PRIORITY', [("rag", mock_rag_cls)]):
            name, transport = await TransportFactory.create_transport_async(
                agent_id="test-agent",
                forced_transport="rag",
                doc_manager=mock_doc_manager
            )
            
            assert name == "rag"
            assert transport is mock_rag_instance
    
    @pytest.mark.asyncio
    async def test_all_transports_fail_raises_error(self):
        """Should raise ConnectionError when all transports fail"""
        mock_ws_cls = Mock()
        mock_ws_cls.return_value.connect.side_effect = Exception("Fail")
        
        with patch.object(TransportFactory, 'TRANSPORT_PRIORITY', [("websocket", mock_ws_cls)]):
            with pytest.raises(ConnectionError, match="All transports failed"):
                await TransportFactory.create_transport_async(
                    agent_id="test-agent"
                )
    
    def test_sync_wrapper(self):
        """Should provide sync wrapper for backward compatibility"""
        mock_ws_cls = Mock()
        mock_transport = AsyncMock()
        mock_transport.connect = AsyncMock()
        mock_ws_cls.return_value = mock_transport
        
        with patch.object(TransportFactory, 'TRANSPORT_PRIORITY', [("websocket", mock_ws_cls)]):
            # Call sync version
            name, transport = TransportFactory.create_transport(agent_id="test-agent")
            
            assert name == "websocket"
            assert transport is mock_transport
