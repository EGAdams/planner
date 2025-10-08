#!/usr/bin/env python3
"""
Test Script for GPT or Other AI Agents
Copy this entire script and paste into GPT/ChatGPT/other AI
"""

import sys
sys.path.insert(0, '/home/adamsl/planner')

from rag_tools import send, inbox
from rich.console import Console

console = Console()

def main():
    console.print("\n🤖 GPT Agent Starting Test...\n", style="bold magenta")

    # Step 1: Check for messages from Claude agents
    console.print("Step 1: Checking inbox for messages from Claude", style="yellow")
    messages = inbox()

    # Step 2: Send greeting to Claude agents
    console.print("\nStep 2: Sending greeting to Claude agents", style="yellow")
    send(
        "👋 Hello Claude agents! This is GPT checking in. Cross-AI communication test!",
        topic="testing",
        from_agent="gpt-agent"
    )

    console.print("\n✅ GPT message sent!", style="green")

    # Step 3: Check for any testing messages specifically
    console.print("\nStep 3: Checking 'testing' topic messages:", style="yellow")
    inbox("testing")

    console.print("\n" + "="*60, style="dim")
    console.print("✅ GPT Agent ready!", style="bold magenta")
    console.print("\nClaude and GPT are now connected!", style="green")
    console.print("\nYou can now:", style="bold")
    console.print("  • Send messages: send('Your message', topic='testing', from_agent='gpt')")
    console.print("  • Read messages: inbox('testing')")
    console.print("  • Read all: inbox()")
    console.print("="*60 + "\n", style="dim")

if __name__ == "__main__":
    main()

# If running interactively, provide helper functions
if __name__ != "__main__":
    print("""
    GPT Agent Tools Loaded!

    Quick commands:
      send(message, topic='testing', from_agent='gpt')  # Send message
      inbox(topic='testing')                             # Read messages
      inbox()                                            # Read all messages
    """)
