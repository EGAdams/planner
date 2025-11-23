#!/usr/bin/env python3
"""
Agent-to-Agent Messaging System

Enable AI agents to communicate with each other through:
1. Direct messages via WebSocket (Primary)
2. Letta Server (Fallback)
3. Shared memory message boards (Final Fallback)
"""

import os
import asyncio
import json
import uuid
from typing import Optional, List, Dict
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table

# Import new transport system
from agent_messaging.transport_factory import TransportFactory
from agent_messaging.message_models import AgentMessage, MessagePriority
from agent_messaging.rag_board_transport import RAGBoardTransport

# Try to import Letta for backward compatibility methods
try:
    from letta_client import Letta
except ImportError:
    Letta = None

console = Console()

def create_jsonrpc_request(method: str, params: Dict, request_id: int = 1) -> str:
    """Create a JSON-RPC 2.0 request string"""
    return json.dumps({
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": request_id
    })

def create_jsonrpc_response(result: Dict, request_id: int = 1) -> str:
    """Create a JSON-RPC 2.0 response string"""
    return json.dumps({
        "jsonrpc": "2.0",
        "result": result,
        "id": request_id
    })

class AgentMessenger:
    """Handle agent-to-agent communication with smart transport fallback"""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, agent_id: Optional[str] = None):
        """
        Initialize messenger with automatic transport selection.
        
        Args:
            base_url: Letta server URL (optional)
            api_key: Letta API key (optional)
            agent_id: ID of the current agent (optional but recommended)
        """
        self.agent_id = agent_id or f"agent-{uuid.uuid4().hex[:8]}"
        
        # Initialize transport using factory
        try:
            self.transport_name, self.transport = TransportFactory.create_transport(
                agent_id=self.agent_id,
                letta_base_url=base_url,
                letta_api_key=api_key
            )
            console.print(f"✅ Messenger initialized using: {self.transport_name}", style="green")
        except Exception as e:
            console.print(f"⚠️  Failed to initialize transport: {e}", style="yellow")
            console.print("⚠️  Messaging may be limited to RAG board.", style="yellow")
            self.transport = None
            self.transport_name = "none"

        # Keep direct Letta client for group management (not yet in transport interface)
        self.base_url = base_url or os.getenv('LETTA_BASE_URL', 'http://localhost:8283')
        self.api_key = api_key or os.getenv('LETTA_API_KEY')
        
        try:
            if Letta:
                if self.api_key:
                    self.client = Letta(api_key=self.api_key)
                else:
                    self.client = Letta(base_url=self.base_url)
            else:
                self.client = None
        except Exception:
            self.client = None

    # ========================================================================
    # DIRECT AGENT MESSAGING
    # ========================================================================

    def send_message(self, agent_id: str, message: str, role: str = "user") -> Dict:
        """
        Send a direct message to another agent using active transport
        
        Args:
            agent_id: Target agent ID
            message: Message content
            role: Message role (user, assistant, system)

        Returns:
            Response dict (simulated for async transports)
        """
        if not self.transport:
            console.print("❌ No active transport", style="red")
            return {"error": "No transport"}

        try:
            msg = AgentMessage(
                to_agent=agent_id,
                from_agent=self.agent_id,
                content=message,
                metadata={"role": role}
            )
            
            # Use async run for the transport send
            success = asyncio.run(self.transport.send(msg))
            
            if success:
                console.print(f"✅ Message sent to {agent_id[:8]} via {self.transport_name}", style="green")
                return {"status": "sent", "transport": self.transport_name}
            else:
                console.print(f"❌ Failed to send message via {self.transport_name}", style="red")
                return {"error": "Send failed"}

        except Exception as e:
            console.print(f"❌ Error sending message: {e}", style="red")
            raise

    def read_messages(self, agent_id: str, limit: int = 10) -> List[Dict]:
        """
        Read messages for an agent
        
        Note: This currently relies on Letta or RAG polling depending on transport.
        """
        # If using RAG transport or fallback, poll RAG
        if self.transport_name == "rag" or isinstance(self.transport, RAGBoardTransport):
            try:
                messages = asyncio.run(self.transport.poll_messages(agent_id))
                if messages:
                    console.print(f"📬 Found {len(messages)} messages (RAG)", style="cyan")
                    return messages
            except Exception as e:
                console.print(f"❌ Error reading RAG messages: {e}", style="red")
        
        # Fallback to Letta client if available
        if self.client:
            try:
                messages = self.client.agents.messages.list(
                    agent_id=agent_id,
                    limit=limit
                )
                if messages:
                    console.print(f"📬 Found {len(messages)} messages (Letta)", style="cyan")
                    return messages
            except Exception:
                pass
                
        return []

    def list_agents(self) -> List[Dict]:
        """List all available agents"""
        if self.client:
            try:
                agents = self.client.agents.list()
                if hasattr(agents, 'agents'):
                    agents_list = agents.agents
                else:
                    agents_list = agents if isinstance(agents, list) else []

                if agents_list:
                    table = Table(title="Available Agents")
                    table.add_column("ID", style="cyan")
                    table.add_column("Name", style="green")
                    table.add_column("Description", style="white")

                    for agent in agents_list:
                        agent_id = agent.id[:12] + "..." if len(agent.id) > 12 else agent.id
                        name = getattr(agent, 'name', 'Unknown')
                        desc = getattr(agent, 'description', '')[:50]
                        table.add_row(agent_id, name, desc)

                    console.print(table)
                return agents_list
            except Exception as e:
                console.print(f"❌ Error listing agents: {e}", style="red")
        return []

    # ========================================================================
    # GROUP MESSAGING (Multi-Agent Collaboration)
    # ========================================================================

    def create_group(self, name: str, description: str = "") -> Optional[str]:
        """Create an agent group (Letta only for now)"""
        if not self.client:
            console.print("❌ Group management requires Letta connection", style="red")
            return None
            
        try:
            group = self.client.groups.create(name=name, description=description)
            console.print(f"✅ Created group: {name} (ID: {group.id})", style="green")
            return group.id
        except Exception as e:
            console.print(f"❌ Error creating group: {e}", style="red")
            return None

    def send_to_group(self, group_id: str, message: str) -> Dict:
        """Send a message to all agents in a group"""
        if not self.client:
            console.print("❌ Group messaging requires Letta connection", style="red")
            return {"error": "No Letta connection"}

        try:
            response = self.client.groups.messages.create(
                group_id=group_id,
                messages=[{"role": "user", "content": message}]
            )
            console.print(f"✅ Broadcast to group {group_id[:8]}...", style="green")
            return response
        except Exception as e:
            console.print(f"❌ Failed to broadcast: {e}", style="red")
            raise

    def list_groups(self) -> List[Dict]:
        """List all agent groups"""
        if not self.client:
            return []
            
        try:
            groups = self.client.groups.list()
            if hasattr(groups, 'groups'):
                groups_list = groups.groups
            else:
                groups_list = groups if isinstance(groups, list) else []

            if groups_list:
                table = Table(title="Agent Groups")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="green")
                table.add_column("Description", style="white")

                for group in groups_list:
                    group_id = group.id[:12] + "..." if len(group.id) > 12 else group.id
                    name = getattr(group, 'name', 'Unknown')
                    desc = getattr(group, 'description', '')[:50]
                    table.add_row(group_id, name, desc)

                console.print(table)
            return groups_list
        except Exception as e:
            console.print(f"❌ Error listing groups: {e}", style="red")
            return []

    # ========================================================================
    # MEMORY-BASED MESSAGE BOARD (Fallback/Complement)
    # ========================================================================

    def post_to_board(self, message: str, topic: str = "general",
                      from_agent: str = "unknown", priority: str = "normal"):
        """
        Post a message to shared memory board using RAG transport
        """
        try:
            # Use RAG transport directly if available, or create temporary one
            if isinstance(self.transport, RAGBoardTransport):
                transport = self.transport
            else:
                from rag_system.core.document_manager import DocumentManager
                from agent_messaging.rag_board_transport import RAGBoardTransport
                transport= RAGBoardTransport(DocumentManager())
                asyncio.run(transport.connect())

            msg = AgentMessage(
                to_agent="board",
                from_agent=from_agent,
                content=message,
                topic=topic,
                priority=MessagePriority(priority) if priority in ["low", "normal", "high", "urgent"] else MessagePriority.NORMAL
            )
            
            success = asyncio.run(transport.send(msg))
            
            if success:
                console.print(f"✅ Posted to message board: {topic}", style="green")
                return "msg-id-placeholder"
            else:
                console.print("❌ Failed to post to board", style="red")
                return None

        except Exception as e:
            console.print(f"❌ Error posting to board: {e}", style="red")
            return None

    def read_board(self, topic: Optional[str] = None, limit: int = 10):
        """Read messages from shared memory board"""
        try:
            if isinstance(self.transport, RAGBoardTransport):
                transport = self.transport
            else:
                from rag_system.core.document_manager import DocumentManager
                transport = RAGBoardTransport(DocumentManager())
            
            # Use poll_messages from transport
            messages = asyncio.run(transport.poll_messages("board", topic=topic))
            
            if messages:
                console.print(f"\n📋 Message Board ({len(messages)} messages):", style="cyan")
                for i, msg in enumerate(messages[:limit], 1):
                    # Handle both dict results and AgentMessage objects
                    content = msg.content if hasattr(msg, 'content') else str(msg)
                    source = msg.from_agent if hasattr(msg, 'from_agent') else "unknown"
                    
                    panel = Panel(
                        content[:300] + ("..." if len(content) > 300 else ""),
                        title=f"[{i}] From: {source}",
                        border_style="blue"
                    )
                    console.print(panel)
                return messages
            else:
                console.print("📭 Message board is empty", style="yellow")
                return []

        except Exception as e:
            console.print(f"❌ Error reading board: {e}", style="red")
            return []


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

_messenger = None

def _get_messenger():
    """Lazy initialization of messenger"""
    global _messenger
    if not _messenger:
        _messenger = AgentMessenger()
    return _messenger

def send_to_agent(agent_id: str, message: str):
    """Send message to another agent"""
    messenger = _get_messenger()
    return messenger.send_message(agent_id, message)

def broadcast(group_id: str, message: str):
    """Broadcast to agent group"""
    messenger = _get_messenger()
    return messenger.send_to_group(group_id, message)

def post_message(message: str, topic: str = "general", from_agent: str = "claude"):
    """Post to shared message board"""
    messenger = _get_messenger()
    return messenger.post_to_board(message, topic=topic, from_agent=from_agent)

def read_messages(topic: Optional[str] = None, limit: int = 10):
    """Read from message board"""
    messenger = _get_messenger()
    return messenger.read_board(topic=topic, limit=limit)

def list_agents():
    """List all agents"""
    messenger = _get_messenger()
    return messenger.list_agents()

def list_groups():
    """List all agent groups"""
    messenger = _get_messenger()
    return messenger.list_groups()

# Aliases for easier usage
inbox = read_messages
send = send_to_agent
