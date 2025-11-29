#!/usr/bin/env python3
"""
Letta Memory Bridge - Share memory blocks across agents via Letta Server

This module syncs our local RAG/ChromaDB memory with Letta's server-based memory blocks,
enabling true multi-agent shared memory.

Usage:
    # Sync local memory to Letta
    python3 letta_memory_bridge.py sync

    # Search Letta memory blocks
    python3 letta_memory_bridge.py search "query"

    # Create shared memory block
    python3 letta_memory_bridge.py create-block "block_name" "content"
"""

import os
import sys
from typing import Optional, List, Dict
from datetime import datetime
from letta_client import Letta
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

class LettaMemoryBridge:
    """Bridge between local ChromaDB and Letta server memory blocks"""

    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize Letta client

        Args:
            base_url: Letta server URL (default: http://localhost:8283 for self-hosted)
            api_key: API key for Letta Cloud (optional)
        """
        # Default to local server, fallback to cloud if API key provided
        if base_url is None:
            if api_key or os.getenv('LETTA_API_KEY'):
                base_url = "https://api.letta.com"
            else:
                base_url = "http://localhost:8283"

        self.base_url = base_url
        self.api_key = api_key or os.getenv('LETTA_API_KEY')

        # Initialize client
        try:
            if self.api_key:
                self.client = Letta(api_key=self.api_key)
            else:
                self.client = Letta(base_url=base_url)
            console.print(f"✅ Connected to Letta server: {base_url}", style="green")
        except Exception as e:
            console.print(f"❌ Failed to connect to Letta: {e}", style="red")
            raise

    def list_blocks(self) -> List[Dict]:
        """List all memory blocks on Letta server"""
        try:
            response = self.client.blocks.list()
            blocks = response.blocks if hasattr(response, 'blocks') else []
            return blocks
        except Exception as e:
            console.print(f"Error listing blocks: {e}", style="red")
            return []

    def create_block(self, label: str, value: str, template: bool = False) -> Optional[str]:
        """
        Create a new memory block on Letta server

        Args:
            label: Block label/name
            value: Block content
            template: Whether this is a template block

        Returns:
            Block ID if successful
        """
        try:
            block = self.client.blocks.create(
                label=label,
                value=value,
                template=template
            )
            console.print(f"✅ Created block: {label} (ID: {block.id})", style="green")
            return block.id
        except Exception as e:
            console.print(f"❌ Error creating block: {e}", style="red")
            return None

    def update_block(self, block_id: str, value: str) -> bool:
        """Update an existing memory block"""
        try:
            self.client.blocks.update(block_id=block_id, value=value)
            console.print(f"✅ Updated block: {block_id}", style="green")
            return True
        except Exception as e:
            console.print(f"❌ Error updating block: {e}", style="red")
            return False

    def get_block(self, block_id: str) -> Optional[Dict]:
        """Get a specific memory block"""
        try:
            block = self.client.blocks.get(block_id=block_id)
            return block
        except Exception as e:
            console.print(f"Error getting block: {e}", style="red")
            return None

    def sync_from_local_rag(self, project_name: str = "planner"):
        """
        Sync local RAG/ChromaDB memory to Letta server blocks

        This creates/updates Letta blocks with our local memory content
        """
        from rag_system.core.document_manager import DocumentManager

        console.print(f"🔄 Syncing local memory to Letta server...", style="yellow")

        dm = DocumentManager()

        # Get all runtime artifacts from local storage
        artifacts = dm.search_artifacts(query="", n_results=100)

        if not artifacts:
            console.print("No artifacts to sync", style="yellow")
            return

        # Get or create a shared memory block for this project
        block_label = f"shared_memory_{project_name}"

        # Check if block exists
        blocks = self.list_blocks()
        existing_block = next((b for b in blocks if b.label == block_label), None)

        # Compile memory content
        memory_content = f"# Shared Memory: {project_name}\n\n"
        memory_content += f"Last synced: {datetime.now().isoformat()}\n\n"

        for i, artifact in enumerate(artifacts[:50], 1):  # Limit to 50 most relevant
            title = artifact.metadata.get('title', 'Untitled')
            artifact_type = artifact.metadata.get('artifact_type', 'unknown')
            memory_content += f"## [{i}] {title} ({artifact_type})\n"
            memory_content += f"{artifact.content[:500]}\n\n"

        # Create or update block
        if existing_block:
            self.update_block(existing_block.id, memory_content)
        else:
            self.create_block(block_label, memory_content)

        console.print(f"✅ Synced {len(artifacts)} artifacts to Letta", style="green")

    def create_agent_with_shared_memory(self, agent_name: str, project_name: str = "planner"):
        """
        Create a Letta agent with access to shared memory blocks

        Args:
            agent_name: Name for the new agent
            project_name: Project to link shared memory to
        """
        try:
            # Get the shared memory block
            block_label = f"shared_memory_{project_name}"
            blocks = self.list_blocks()
            shared_block = next((b for b in blocks if b.label == block_label), None)

            if not shared_block:
                console.print(f"⚠️  No shared memory block found. Run sync first.", style="yellow")
                return None

            # Create agent with the shared block
            agent = self.client.agents.create(
                name=agent_name,
                memory_blocks=[shared_block.id],
                # Additional configuration...
            )

            console.print(f"✅ Created agent '{agent_name}' with shared memory", style="green")
            return agent.id

        except Exception as e:
            console.print(f"❌ Error creating agent: {e}", style="red")
            return None


def main():
    """CLI for Letta memory bridge"""
    import argparse

    parser = argparse.ArgumentParser(description="Letta Memory Bridge CLI")
    parser.add_argument('command', choices=['sync', 'list', 'create-block', 'search'],
                       help='Command to execute')
    parser.add_argument('query', nargs='?', help='Query or block name')
    parser.add_argument('content', nargs='?', help='Block content')
    parser.add_argument('--api-key', help='Letta API key')
    parser.add_argument('--url', default='http://localhost:8283', help='Letta server URL')
    parser.add_argument('--project', default='planner', help='Project name')

    args = parser.parse_args()

    try:
        bridge = LettaMemoryBridge(base_url=args.url, api_key=args.api_key)

        if args.command == 'sync':
            bridge.sync_from_local_rag(project_name=args.project)

        elif args.command == 'list':
            blocks = bridge.list_blocks()
            if blocks:
                table = Table(title="Letta Memory Blocks")
                table.add_column("ID", style="cyan")
                table.add_column("Label", style="green")
                table.add_column("Preview", style="white")

                for block in blocks:
                    preview = block.value[:50] + "..." if len(block.value) > 50 else block.value
                    table.add_row(block.id[:8], block.label, preview)

                console.print(table)
            else:
                console.print("No blocks found", style="yellow")

        elif args.command == 'create-block':
            if not args.query or not args.content:
                console.print("Usage: create-block <label> <content>", style="red")
                return
            bridge.create_block(args.query, args.content)

        elif args.command == 'search':
            # Search local memory and display
            from rag_system.rag_tools import recall
            results = recall(args.query or "", limit=10)
            console.print(f"Found {len(results)} results", style="cyan")

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        console.print("\n💡 Tip: Start local Letta server with: letta server", style="dim")
        console.print("   Or use Letta Cloud with --api-key=<key>", style="dim")
        sys.exit(1)


if __name__ == "__main__":
    main()
