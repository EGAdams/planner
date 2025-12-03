"""
End-to-end tests for agent-to-agent messaging.

Tests realistic scenarios with multiple agents communicating.
"""

import pytest
import asyncio
from a2a_communicating_agents.agent_messaging.message_models import AgentMessage, ConnectionConfig, MessagePriority
from a2a_communicating_agents.agent_messaging.websocket_transport import WebSocketTransport


@pytest.mark.e2e
class TestAgentToAgentMessaging:
    """E2E tests for complete A2A communication workflows"""
    
    @pytest.mark.asyncio
    async def test_two_agents_direct_communication(self, mock_server):
        """
        Scenario: Agent A sends a direct message to Agent B.
        Agent B receives it via callback.
        """
        config = ConnectionConfig(url="ws://localhost:3030")
        
        # Create two agent transports
        agent_a = WebSocketTransport(config, mock_server=mock_server)
        agent_a.agent_id = "planner-agent"
        
        agent_b = WebSocketTransport(config, mock_server=mock_server)
        agent_b.agent_id = "orchestrator-agent"
        
        # Connect both
        await agent_a.connect()
        await agent_b.connect()
        
        # Agent B sets up message handler
        received_messages = []
        
        async def message_handler(msg: AgentMessage):
            received_messages.append(msg)
        
        await agent_b.subscribe("planner-responses", message_handler)
        
        # Agent A sends message to Agent B
        message = AgentMessage(
            to_agent="orchestrator-agent",
            from_agent="planner-agent",
            content="Task completed: Database migration successful",
            topic="planner-responses",
            priority=MessagePriority.HIGH
        )
        
        result = await agent_a.send(message)
        assert result == True
        
        # Process pending messages
        await agent_b._process_pending_messages()
        
        # Verify receipt
        assert len(received_messages) == 1
        msg = received_messages[0]
        assert msg.from_agent == "planner-agent"
        assert msg.content == "Task completed: Database migration successful"
        assert msg.priority == MessagePriority.HIGH
        
        # Cleanup
        await agent_a.disconnect()
        await agent_b.disconnect()
    
    @pytest.mark.asyncio
    async def test_broadcast_to_multiple_agents(self, mock_server):
        """
        Scenario: Orchestrator broadcasts announcement to all agents.
        All subscribed agents receive the message.
        """
        config = ConnectionConfig(url="ws://localhost:3030")
        
        # Create orchestrator
        orchestrator = WebSocketTransport(config, mock_server=mock_server)
        orchestrator.agent_id = "orchestrator-agent"
        await orchestrator.connect()
        
        # Create multiple worker agents
        agents = []
        message_logs = {}
        
        for agent_id in ["planner-agent", "dashboard-agent", "task-agent"]:
            transport = WebSocketTransport(config, mock_server=mock_server)
            transport.agent_id = agent_id
            await transport.connect()
            
            # Each agent subscribes to announcements
            messages = []
            message_logs[agent_id] = messages
            
            async def make_handler(messages_list):
                async def handler(msg: AgentMessage):
                    messages_list.append(msg)
                return handler
            
            await transport.subscribe("system-announcements", await make_handler(messages))
            agents.append(transport)
        
        # Orchestrator broadcasts
        broadcast = AgentMessage(
            to_agent="*",
            from_agent="orchestrator-agent",
            content="SYSTEM MAINTENANCE: Scheduled downtime in 5 minutes",
            topic="system-announcements",
            priority=MessagePriority.URGENT
        )
        
        await orchestrator.send(broadcast)
        
        # All agents process messages
        for agent in agents:
            await agent._process_pending_messages()
        
        # Verify all agents received broadcast
        for agent_id, messages in message_logs.items():
            assert len(messages) == 1, f"{agent_id} should receive broadcast"
            assert messages[0].content == "SYSTEM MAINTENANCE: Scheduled downtime in 5 minutes"
            assert messages[0].priority == MessagePriority.URGENT
        
        # Cleanup
        await orchestrator.disconnect()
        for agent in agents:
            await agent.disconnect()
    
    @pytest.mark.asyncio
    async def test_request_response_pattern(self, mock_server):
        """
        Scenario: Agent A sends request to Agent B, Agent B responds.
        Tests bidirectional communication.
        """
        config = ConnectionConfig(url="ws://localhost:3030")
        
        agent_a = WebSocketTransport(config, mock_server=mock_server)
        agent_a.agent_id = "client-agent"
        await agent_a.connect()
        
        agent_b = WebSocketTransport(config, mock_server=mock_server)
        agent_b.agent_id = "service-agent"
        await agent_b.connect()
        
        # Setup handlers
        agent_a_messages = []
        agent_b_messages = []
        
        async def agent_a_handler(msg: AgentMessage):
            agent_a_messages.append(msg)
        
        async def agent_b_handler(msg: AgentMessage):
            agent_b_messages.append(msg)
            # Auto-respond
            response = AgentMessage(
                to_agent=msg.from_agent,
                from_agent="service-agent",
                content=f"Response to: {msg.content}",
                topic="responses"
            )
            await agent_b.send(response)
        
        await agent_a.subscribe("responses", agent_a_handler)
        await agent_b.subscribe("requests", agent_b_handler)
        
        # Agent A sends request
        request = AgentMessage(
            to_agent="service-agent",
            from_agent="client-agent",
            content="Get user list",
            topic="requests"
        )
        
        await agent_a.send(request)
        await agent_b._process_pending_messages()
        
        # Verify request received
        assert len(agent_b_messages) == 1
        assert agent_b_messages[0].content == "Get user list"
        
        # Process response
        await agent_a._process_pending_messages()
        
        # Verify response received
        assert len(agent_a_messages) == 1
        assert agent_a_messages[0].content == "Response to: Get user list"
        
        # Cleanup
        await agent_a.disconnect()
        await agent_b.disconnect()
    
    @pytest.mark.asyncio
    async def test_unsubscribe_stops_receiving_messages(self, mock_server):
        """
        Scenario: Agent unsubscribes from topic and stops receiving messages.
        """
        config = ConnectionConfig(url="ws://localhost:3030")
        
        agent_a = WebSocketTransport(config, mock_server=mock_server)
        agent_a.agent_id = "sender"
        await agent_a.connect()
        
        agent_b = WebSocketTransport(config, mock_server=mock_server)
        agent_b.agent_id = "receiver"
        await agent_b.connect()
        
        messages = []
        
        async def handler(msg: AgentMessage):
            messages.append(msg)
        
        await agent_b.subscribe("notifications", handler)
        
        # Send first message
        msg1 = AgentMessage(
            to_agent="*",
            from_agent="sender",
            content="Message 1",
            topic="notifications"
        )
        await agent_a.send(msg1)
        await agent_b._process_pending_messages()
        assert len(messages) == 1
        
        # Unsubscribe
        await agent_b.unsubscribe("notifications")
        
        # Send second message
        msg2 = AgentMessage(
            to_agent="*",
            from_agent="sender",
            content="Message 2",
            topic="notifications"
        )
        await agent_a.send(msg2)
        await agent_b._process_pending_messages()
        
        # Should still have only 1 message (didn't receive second)
        assert len(messages) == 1
        
        # Cleanup
        await agent_a.disconnect()
        await agent_b.disconnect()
