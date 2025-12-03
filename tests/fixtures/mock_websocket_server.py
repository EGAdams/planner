"""
Mock WebSocket server for testing (Observer Pattern).

Simulates a real WebSocket server without network overhead.
"""

import asyncio
from typing import Dict, Set, Callable, Awaitable, List
from dataclasses import dataclass, field
from a2a_communicating_agents.agent_messaging.message_models import AgentMessage


@dataclass
class MockConnection:
    """Represents a mock WebSocket connection"""
    agent_id: str
    subscriptions: Set[str] = field(default_factory=set)
    message_queue: List[AgentMessage] = field(default_factory=list)
    
    
class MockWebSocketServer:
    """
    Mock WebSocket server implementing Observer pattern.
    
    Observers (agents) subscribe to topics and receive notifications
    when messages are published.
    """
    
    def __init__(self):
        self._connections: Dict[str, MockConnection] = {}
        self._topic_subscribers: Dict[str, Set[str]] = {}
        self._message_log: List[AgentMessage] = []
        
    async def connect_agent(self, agent_id: str) -> None:
        """Connect an agent to the mock server"""
        if agent_id in self._connections:
            raise ValueError(f"Agent {agent_id} already connected")
        self._connections[agent_id] = MockConnection(agent_id=agent_id)
        
    async def disconnect_agent(self, agent_id: str) -> None:
        """Disconnect an agent"""
        if agent_id in self._connections:
            conn = self._connections[agent_id]
            # Unsubscribe from all topics
            for topic in conn.subscriptions:
                self._topic_subscribers[topic].discard(agent_id)
            del self._connections[agent_id]
            
    async def subscribe(self, agent_id: str, topic: str) -> None:
        """
        Subscribe agent to topic (Observer pattern).
        
        Args:
            agent_id: Agent subscribing
            topic: Topic to subscribe to
        """
        if agent_id not in self._connections:
            raise ValueError(f"Agent {agent_id} not connected")
            
        conn = self._connections[agent_id]
        conn.subscriptions.add(topic)
        
        if topic not in self._topic_subscribers:
            self._topic_subscribers[topic] = set()
        self._topic_subscribers[topic].add(agent_id)
    
    async def unsubscribe(self, agent_id: str, topic: str) -> None:
        """
        Unsubscribe agent from topic.
        
        Args:
            agent_id: Agent to unsubscribe
            topic: Topic to unsubscribe from
        """
        if agent_id not in self._connections:
            return
            
        conn = self._connections[agent_id]
        conn.subscriptions.discard(topic)
        
        if topic in self._topic_subscribers:
            self._topic_subscribers[topic].discard(agent_id)
        
    async def send_message(self, message: AgentMessage) -> bool:
        """
        Send message to target agent or broadcast to topic.
        
        Args:
            message: AgentMessage to deliver
            
        Returns:
            True if delivered, False otherwise
        """
        self._message_log.append(message)
        
        # Direct message to specific agent
        if message.to_agent in self._connections:
            conn = self._connections[message.to_agent]
            conn.message_queue.append(message)
            return True
            
        # Broadcast to topic subscribers
        if message.topic in self._topic_subscribers:
            for agent_id in self._topic_subscribers[message.topic]:
                if agent_id in self._connections:
                    conn = self._connections[agent_id]
                    conn.message_queue.append(message)
            return True
            
        return False
        
    async def get_messages(self, agent_id: str) -> List[AgentMessage]:
        """Get pending messages for agent"""
        if agent_id not in self._connections:
            return []
        conn = self._connections[agent_id]
        messages = conn.message_queue.copy()
        conn.message_queue.clear()
        return messages
        
    def get_message_log(self) -> List[AgentMessage]:
        """Get all messages sent through server (for testing)"""
        return self._message_log.copy()
        
    def is_agent_connected(self, agent_id: str) -> bool:
        """Check if agent is connected"""
        return agent_id in self._connections
        
    def is_subscribed(self, agent_id: str, topic: str) -> bool:
        """Check if agent is subscribed to topic"""
        if agent_id not in self._connections:
            return False
        return topic in self._connections[agent_id].subscriptions
        
    def connection_count(self) -> int:
        """Get number of connected agents"""
        return len(self._connections)
