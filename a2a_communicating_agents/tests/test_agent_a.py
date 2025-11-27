#!/usr/bin/env python3
"""
Test Script for Agent A
Run this in Terminal 1
"""

from rag_system.rag_tools import send, inbox, status
from rich.console import Console

console = Console()

def main():
    console.print("\n🤖 Agent A Starting Test...\n", style="bold cyan")

    # Step 1: Check current status
    console.print("Step 1: Checking system status", style="yellow")
    status()

    # Step 2: Check inbox (see if Agent B has sent anything)
    console.print("\nStep 2: Checking inbox for messages from other agents", style="yellow")
    messages = inbox()

    # Step 3: Send initial message
    console.print("\nStep 3: Sending test message to Agent B", style="yellow")
    send(
        "👋 Hello Agent B! This is Agent A. Can you hear me?",
        topic="testing",
        from_agent="agent-a"
    )

    console.print("\n✅ Agent A test message sent!", style="green")
    console.print("\n" + "="*60, style="dim")
    console.print("Next steps:", style="bold")
    console.print("1. Start Agent B in another terminal: python3 test_agent_b.py")
    console.print("2. Wait for Agent B's response")
    console.print("3. Check inbox with: python3 -c 'from rag_tools import inbox; inbox(\"testing\")'")
    console.print("="*60 + "\n", style="dim")

if __name__ == "__main__":
    main()
