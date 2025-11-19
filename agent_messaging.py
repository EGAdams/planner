#!/usr/bin/env python3
"""
Agent-to-Agent Messaging System

Enable AI agents to communicate with each other through:
1. Direct messages via Letta Server
2. Shared memory message boards
3. Agent groups for team collaboration

Usage:
    # Send message to another agent
    send_to_agent(agent_id, "Check out the parser fix in parsers.py:145")

    # Broadcast to all agents in a group
    broadcast_to_group(group_id, "Deployment to prod at 3pm")

    # Post to shared message board (memory-based)
    post_message("Found solution to ChromaDB $and operator issue")

    # Read messages
    read_messages(agent_id)
"""

import os
from typing import Optional, List, Dict
from datetime import datetime
from letta_client import Letta
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
import json
import uuid

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
    """Handle agent-to-agent communication"""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """Initialize Letta client for messaging"""
        if base_url is None:
            if api_key or os.getenv('LETTA_API_KEY'):
                base_url = "https://api.letta.com"
            else:
                base_url = "http://localhost:8283"

        self.base_url = base_url
        self.api_key = api_key or os.getenv('LETTA_API_KEY')

        try:
            if self.api_key:
                self.client = Letta(api_key=self.api_key)
            else:
                self.client = Letta(base_url=base_url)
            console.print(f"✅ Messenger connected to: {base_url}", style="green")
        except Exception as e:
            console.print(f"❌ Failed to connect: {e}", style="red")
            raise

    # ========================================================================
    # DIRECT AGENT MESSAGING
    # ========================================================================

    def send_message(self, agent_id: str, message: str, role: str = "user") -> Dict:
        """
        Send a direct message to another agent

        Args:
            agent_id: Target agent ID
            message: Message content
            role: Message role (user, assistant, system)

        Returns:
            Response from the agent
        """
        try:
            response = self.client.agents.messages.create(
                agent_id=agent_id,
                messages=[{
                    "role": role,
                    "content": message
                }]
            )

            console.print(f"✅ Message sent to agent {agent_id[:8]}...", style="green")
            return response

        except Exception as e:
            console.print(f"❌ Failed to send message: {e}", style="red")
            raise

    def read_messages(self, agent_id: str, limit: int = 10) -> List[Dict]:
        """
        Read messages for an agent

        Args:
            agent_id: Agent ID
            limit: Number of messages to retrieve

        Returns:
            List of messages
        """
        try:
            messages = self.client.agents.messages.list(
                agent_id=agent_id,
                limit=limit
            )

            if messages:
                console.print(f"📬 Found {len(messages)} messages", style="cyan")
                return messages
            else:
                console.print("No messages found", style="yellow")
                return []

        except Exception as e:
            console.print(f"❌ Error reading messages: {e}", style="red")
            return []

    def list_agents(self) -> List[Dict]:
        """List all available agents"""
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
        """
        Create an agent group for team collaboration

        Args:
            name: Group name
            description: Group description

        Returns:
            Group ID
        """
        try:
            group = self.client.groups.create(
                name=name,
                description=description
            )

            console.print(f"✅ Created group: {name} (ID: {group.id})", style="green")
            return group.id

        except Exception as e:
            console.print(f"❌ Error creating group: {e}", style="red")
            return None

    def send_to_group(self, group_id: str, message: str) -> Dict:
        """
        Send a message to all agents in a group

        Args:
            group_id: Target group ID
            message: Message content

        Returns:
            Response
        """
        try:
            response = self.client.groups.messages.create(
                group_id=group_id,
                messages=[{
                    "role": "user",
                    "content": message
                }]
            )

            console.print(f"✅ Broadcast to group {group_id[:8]}...", style="green")
            return response

        except Exception as e:
            console.print(f"❌ Failed to broadcast: {e}", style="red")
            raise

    def list_groups(self) -> List[Dict]:
        """List all agent groups"""
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
        Post a message to shared memory board (alternative to direct messaging)

        This uses our RAG system as a message board that all agents can read.

        Args:
            message: Message content
            topic: Topic/category
            from_agent: Sender identification
            priority: Message priority (low, normal, high, urgent)
        """
        try:
            from rag_system.core.document_manager import DocumentManager

            dm = DocumentManager()

            # Create JSON-RPC message
            task_id = str(uuid.uuid4())
            rpc_message = create_jsonrpc_request(
                method="agent.message",
                params={
                    "message": message,
                    "from_agent": from_agent,
                    "topic": topic,
                    "priority": priority,
                    "timestamp": datetime.now().isoformat()
                }
            )

            # Create message with metadata
            message_content = f"""
**From**: {from_agent}
**Topic**: {topic}
**Priority**: {priority}
**Time**: {datetime.now().isoformat()}
**Protocol**: Google A2A (JSON-RPC 2.0)

```json
{rpc_message}
```
"""

            # Store as runtime artifact
            doc_id = dm.add_runtime_artifact(
                artifact_text=message_content,
                artifact_type="agent_message",
                source=from_agent,
                project_name=topic
            )

            console.print(f"✅ Posted to message board: {topic}", style="green")
            return doc_id

        except Exception as e:
            console.print(f"❌ Error posting to board: {e}", style="red")
            return None

    def read_board(self, topic: Optional[str] = None, limit: int = 10):
        """
        Read messages from shared memory board

        Args:
            topic: Filter by topic (optional)
            limit: Number of messages to retrieve
        """
        try:
            from rag_system.core.document_manager import DocumentManager

            dm = DocumentManager()

            # Search for agent messages
            query = f"agent message {topic}" if topic else "agent message"
            results = dm.search_artifacts(
                query=query,
                artifact_type="agent_message",
                n_results=limit
            )

            if results:
                console.print(f"\n📋 Message Board ({len(results)} messages):", style="cyan")
                for i, msg in enumerate(results, 1):
                    title = msg.metadata.get('title', 'Message')
                    source = msg.metadata.get('source', 'unknown')

                    panel = Panel(
                        msg.content[:300] + ("..." if len(msg.content) > 300 else ""),
                        title=f"[{i}] From: {source}",
                        border_style="blue"
                    )
                    console.print(panel)
            else:
                console.print("📭 Message board is empty", style="yellow")

            return results

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


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI for agent messaging"""
    import argparse

    parser = argparse.ArgumentParser(description="Agent Messaging System")
    parser.add_argument('command',
                       choices=['send', 'read', 'post', 'board', 'list-agents',
                               'list-groups', 'create-group', 'broadcast'],
                       help='Command to execute')
    parser.add_argument('target', nargs='?', help='Agent ID, Group ID, or topic')
    parser.add_argument('message', nargs='?', help='Message content')
    parser.add_argument('--topic', default='general', help='Message topic')
    parser.add_argument('--from', dest='from_agent', default='human', help='Sender name')
    parser.add_argument('--api-key', help='Letta API key')
    parser.add_argument('--url', default='http://localhost:8283', help='Letta server URL')

    args = parser.parse_args()

    try:
        messenger = AgentMessenger(base_url=args.url, api_key=args.api_key)

        if args.command == 'send':
            if not args.target or not args.message:
                console.print("Usage: send <agent_id> <message>", style="red")
                return
            messenger.send_message(args.target, args.message)

        elif args.command == 'read':
            if args.target:
                messenger.read_messages(args.target)
            else:
                console.print("Usage: read <agent_id>", style="red")

        elif args.command == 'post':
            if not args.message:
                console.print("Usage: post <message> [--topic <topic>]", style="red")
                return
            messenger.post_to_board(args.message, topic=args.topic, from_agent=args.from_agent)

        elif args.command == 'board':
            messenger.read_board(topic=args.topic)

        elif args.command == 'list-agents':
            messenger.list_agents()

        elif args.command == 'list-groups':
            messenger.list_groups()

        elif args.command == 'create-group':
            if not args.target:
                console.print("Usage: create-group <group_name> <description>", style="red")
                return
            messenger.create_group(args.target, args.message or "")

        elif args.command == 'broadcast':
            if not args.target or not args.message:
                console.print("Usage: broadcast <group_id> <message>", style="red")
                return
            messenger.send_to_group(args.target, args.message)

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        console.print("\n💡 Tip: Start Letta server with: letta server", style="dim")


if __name__ == "__main__":
    main()
