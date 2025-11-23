"""
Pydantic models for agent messages with validation.

Uses Pydantic for type safety and automatic serialization.
"""

from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator


class MessagePriority(str, Enum):
    """Message priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class AgentMessage(BaseModel):
    """
    Agent-to-agent message with validation.
    
    Attributes:
        to_agent: Target agent ID
        from_agent: Sender agent ID
        content: Message content
        topic: Message topic/channel (default: 'general')
        priority: Message priority
        timestamp: Message creation time
        metadata: Optional additional data
    """
    to_agent: str = Field(..., min_length=1, description="Target agent identifier")
    from_agent: str = Field(..., min_length=1, description="Sender agent identifier")
    content: str = Field(..., min_length=1, description="Message content")
    topic: str = Field(default="general", description="Message topic/channel")
    priority: MessagePriority = Field(default=MessagePriority.NORMAL)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Optional[Dict[str, Any]] = Field(default=None)
    
    @field_validator('to_agent', 'from_agent')
    @classmethod
    def validate_agent_id(cls, v: str) -> str:
        """Ensure agent IDs are valid format"""
        # Allow "*" for broadcast messages
        if v == "*":
            return v
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError(f"Invalid agent ID format: {v}")
        return v
    
    def serialize(self) -> str:
        """Serialize to JSON string"""
        return self.model_dump_json()
    
    @classmethod
    def deserialize(cls, data: str) -> 'AgentMessage':
        """Deserialize from JSON string"""
        return cls.model_validate_json(data)


class ConnectionConfig(BaseModel):
    """WebSocket connection configuration"""
    url: str = Field(..., description="WebSocket server URL")
    reconnect_attempts: int = Field(default=3, ge=0, le=10)
    reconnect_delay: float = Field(default=1.0, ge=0.1, le=60.0)
    timeout: float = Field(default=30.0, ge=1.0, le=300.0)
    
    @field_validator('url')
    @classmethod
    def validate_websocket_url(cls, v: str) -> str:
        """Ensure URL is valid WebSocket format"""
        if not v.startswith(('ws://', 'wss://')):
            raise ValueError("URL must start with ws:// or wss://")
        return v
