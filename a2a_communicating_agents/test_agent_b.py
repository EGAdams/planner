#!/usr/bin/env python3
"""
Test Script for Agent B
Run this in Terminal 2
"""

from rag_system.rag_tools import send, inbox, status
from rich.console import Console

console = Console()

def main():
    console.print("\n🤖 Agent B Starting Test...\n", style="bold green")

    # Step 1: Check inbox for Agent A's message
    console.print("Step 1: Checking inbox for messages from Agent A", style="yellow")
    messages = inbox("testing")

    if not messages:
        console.print("\n⚠️  No messages from Agent A yet.", style="yellow")
        console.print("Make sure Agent A has sent a message first!", style="yellow")
        console.print("Run: python3 test_agent_a.py\n", style="dim")
        return

    # Step 2: Send response
    console.print("\nStep 2: Sending response to Agent A", style="yellow")
    send(
        "👋 Hello Agent A! I hear you loud and clear! Agent B here.",
        topic="testing",
        from_agent="agent-b"
    )

    console.print("\n✅ Agent B response sent!", style="green")

    # Step 3: Show all messages in conversation
    console.print("\nStep 3: Showing full conversation:", style="yellow")
    inbox("testing")

    console.print("\n" + "="*60, style="dim")
    console.print("✅ Test successful!", style="bold green")
    console.print("\nAgent A and Agent B are now communicating!", style="green")
    console.print("\nNext: Go back to Agent A terminal and check inbox:", style="bold")
    console.print("  python3 -c 'from rag_tools import inbox; inbox(\"testing\")'")
    console.print("="*60 + "\n", style="dim")

if __name__ == "__main__":
    main()
