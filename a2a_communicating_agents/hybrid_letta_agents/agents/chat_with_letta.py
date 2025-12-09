#!/usr/bin/env python3
"""
Interactive chat interface for the persistent Letta orchestrator.

Usage:
    python3 chat_with_letta.py              # Start chat session
    python3 chat_with_letta.py --reset      # Reset agent and start fresh
"""

import sys
from pathlib import Path
from datetime import datetime

# Import from our persistent module
from hybrid_letta_persistent import (
    create_letta_client,
    get_or_create_agent,
    reset_agent,
    AGENT_ID_FILE,
)


def print_banner():
    """Print welcome banner."""
    print("\n" + "="*70)
    print(" "*20 + "LETTA ORCHESTRATOR CHAT")
    print("="*70)
    print()
    print("  Type your messages to interact with the persistent agent")
    print("  Commands:")
    print("    /quit, /exit     - Exit the chat")
    print("    /reset           - Reset agent (delete memory)")
    print("    /status          - Show agent status")
    print("    /help            - Show this help")
    print()
    print("="*70 + "\n")


def print_agent_info(agent_id: str):
    """Print current agent information."""
    print(f"🤖 Agent ID: {agent_id}")
    if AGENT_ID_FILE.exists():
        print(f"💾 Memory: Persistent (saved to {AGENT_ID_FILE.name})")
    else:
        print("💾 Memory: New session")
    print()


def chat_loop():
    """Main interactive chat loop."""
    print_banner()

    # Initialize client and agent
    client = create_letta_client()
    agent_id = get_or_create_agent(client, force_new=False)

    print()
    print_agent_info(agent_id)
    print("💬 Chat session started. Type your message...\n")

    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()

            if not user_input:
                continue

            # Handle commands
            if user_input.lower() in [ "/quit", "/exit", "/q", "q", "x", "exit", "quit" ]:
                print("\n👋 Goodbye!\n")
                break

            elif user_input.lower() == "/reset":
                confirm = input("\n⚠️  Reset agent and delete all memory? (yes/no): ")
                if confirm.lower() in ["yes", "y"]:
                    reset_agent()
                    agent_id = get_or_create_agent(client, force_new=True)
                    print("\n✓ Agent reset! Starting fresh session...\n")
                    print_agent_info(agent_id)
                else:
                    print("Reset cancelled.\n")
                continue

            elif user_input.lower() == "/status":
                print()
                print_agent_info(agent_id)
                continue

            elif user_input.lower() == "/help":
                print_banner()
                continue

            # Send message to agent
            print("\n⏳ Thinking...")
            start_time = datetime.now()

            try:
                response = client.agents.messages.create(
                    agent_id=agent_id,
                    messages=[{"role": "user", "content": user_input}],
                    timeout=120,
                )

                elapsed = (datetime.now() - start_time).total_seconds()

                # Print agent response
                print(f"\n🤖 Agent ({elapsed:.1f}s):\n")

                # Show tool calls if any
                tool_calls = []
                assistant_messages = []

                for msg in response.messages:
                    mtype = getattr(msg, "message_type", None)

                    if mtype == "tool_call_message":
                        tool_name = msg.tool_call.name
                        tool_calls.append(tool_name)
                        print(f"   [Using tool: {tool_name}]")

                    elif mtype == "assistant_message":
                        assistant_messages.append(msg.content)

                if tool_calls:
                    print()

                # Print final assistant response
                for content in assistant_messages:
                    print(f"{content}\n")

            except Exception as e:
                print(f"\n❌ Error: {type(e).__name__}: {e}\n")
                print("Hint: Make sure Letta server is running at LETTA_BASE_URL\n")

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break

        except EOFError:
            print("\n\n👋 Goodbye!\n")
            break


def main():
    """Entry point."""
    # Check for reset flag
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        print("\n🔄 Resetting agent...")
        reset_agent()
        print("✓ Agent reset complete\n")
        return

    # Start chat
    chat_loop()


if __name__ == "__main__":
    main()
