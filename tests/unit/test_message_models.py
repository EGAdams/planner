"""
Unit tests for Pydantic message models.

Test validation and serialization behavior.
"""

import pytest
from datetime import datetime
from pydantic import ValidationError
from agent_messaging.message_models import (
    AgentMessage, 
    MessagePriority, 
    ConnectionConfig
)


@pytest.mark.unit
class TestAgentMessage:
    """Test suite for AgentMessage Pydantic model"""
    
    def test_create_valid_message(self):
        """Should create message with valid data"""
        msg = AgentMessage(
            to_agent="agent-b",
            from_agent="agent-a",
            content="Test message"
        )
        assert msg.to_agent == "agent-b"
        assert msg.from_agent == "agent-a"
        assert msg.content == "Test message"
        assert msg.topic == "general"  # Default
        assert msg.priority == MessagePriority.NORMAL  # Default
        assert isinstance(msg.timestamp, datetime)
    
    def test_invalid_agent_id_raises_error(self):
        """Invalid agent IDs should raise ValidationError"""
        with pytest.raises(ValidationError):
            AgentMessage(
                to_agent="agent with spaces!",  # Invalid
                from_agent="agent-a",
                content="Test"
            )
    
    def test_empty_content_raises_error(self):
        """Empty content should raise ValidationError"""
        with pytest.raises(ValidationError):
            AgentMessage(
                to_agent="agent-b",
                from_agent="agent-a",
                content=""  # Invalid
            )
    
    def test_serialize_deserialize(self):
        """Should serialize and deserialize correctly"""
        original = AgentMessage(
            to_agent="agent-b",
            from_agent="agent-a",
            content="Test",
            priority=MessagePriority.HIGH
        )
        
        json_str = original.serialize()
        restored = AgentMessage.deserialize(json_str)
        
        assert restored.to_agent == original.to_agent
        assert restored.from_agent == original.from_agent
        assert restored.content == original.content
        assert restored.priority == original.priority
    
    def test_message_with_metadata(self):
        """Should support optional metadata"""
        msg = AgentMessage(
            to_agent="agent-b",
            from_agent="agent-a",
            content="Test",
            metadata={"request_id": "12345", "retry_count": 2}
        )
        assert msg.metadata["request_id"] == "12345"
        assert msg.metadata["retry_count"] == 2


@pytest.mark.unit
class TestConnectionConfig:
    """Test suite for ConnectionConfig Pydantic model"""
    
    def test_create_valid_config(self):
        """Should create config with valid WebSocket URL"""
        config = ConnectionConfig(url="ws://localhost:3030")
        assert config.url == "ws://localhost:3030"
        assert config.reconnect_attempts == 3  # Default
        assert config.timeout == 30.0  # Default
    
    def test_invalid_url_raises_error(self):
        """Non-WebSocket URLs should raise ValidationError"""
        with pytest.raises(ValidationError, match="must start with ws://"):
            ConnectionConfig(url="http://localhost:3030")
    
    def test_reconnect_attempts_validation(self):
        """Reconnect attempts should be in valid range"""
        with pytest.raises(ValidationError):
            ConnectionConfig(
                url="ws://localhost:3030",
                reconnect_attempts=15  # > 10, invalid
            )
    
    def test_secure_websocket_url(self):
        """Should accept wss:// URLs"""
        config = ConnectionConfig(url="wss://secure.example.com")
        assert config.url == "wss://secure.example.com"
