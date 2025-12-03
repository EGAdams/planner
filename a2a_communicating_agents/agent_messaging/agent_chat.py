#!/usr/bin/env python3
"""
Interactive Agent Chat Session
Stay logged in and chat with other agents in real-time
"""

import sys
from typing import Optional, Sequence
from rag_system.rag_tools import send, inbox
from a2a_communicating_agents.agent_messaging.agent_messaging_interface import (
    AgentMessage,
)
from rich.console import Console
from rich.prompt import Prompt

console = Console()

def main():
    # Get agent identity
    console.print("\n🤖 Interactive Agent Chat\n", style="bold cyan")
    agent_name = Prompt.ask("Enter your agent name", default="agent-b")
    topic = Prompt.ask("Enter topic to monitor", default="testing")

    console.print(f"\n✅ Logged in as: {agent_name}", style="green")
    console.print(f"📡 Monitoring topic: {topic}", style="green")
    console.print("\n" + "="*60, style="dim")
    console.print("Commands:", style="bold")
    console.print("  • Type message to send")
    console.print("  • 'check' - Check for new messages")
    console.print("  • 'all' - Show all messages")
    console.print("  • 'quit' or 'exit' - Exit chat")
    console.print("="*60 + "\n", style="dim")

    # Show initial messages
    console.print(f"📬 Checking initial messages on '{topic}':\n", style="yellow")
    _display_messages(inbox(topic, render=False), agent_name)

    # Main loop
    while True:
        console.print()
        user_input = Prompt.ask(f"[{agent_name}]", default="check")

        if user_input.lower() in ['quit', 'exit', 'q']:
            console.print("\n👋 Logging out...", style="yellow")
            send(
                f"📴 {agent_name} logging out. Will check back later!",
                topic=topic,
                from_agent=agent_name
            )
            console.print("✅ Goodbye!\n", style="green")
            break

        elif user_input.lower() == 'check':
            console.print(f"\n📬 Checking for new messages on '{topic}':\n", style="yellow")
            _display_messages(inbox(topic, render=False), agent_name)

        elif user_input.lower() == 'all':
            console.print("\n📬 All messages:\n", style="yellow")
            _display_messages(inbox(render=False), agent_name)

        elif user_input.lower().startswith('topic:'):
            # Change topic
            new_topic = user_input.split(':', 1)[1].strip()
            topic = new_topic
            console.print(f"✅ Switched to topic: {topic}", style="green")
            _display_messages(inbox(topic, render=False), agent_name)

        elif user_input.strip():
            # Send message
            send(user_input, topic=topic, from_agent=agent_name)
            console.print(f"✅ Message sent to '{topic}'", style="green")

        else:
            # Default to checking messages
            _display_messages(inbox(topic, render=False), agent_name)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n\n👋 Interrupted. Goodbye!\n", style="yellow")
        sys.exit(0)


def _display_messages(messages: Optional[Sequence[AgentMessage]], agent_name: str) -> None:
    """Render a list of messages for the interactive chat."""

    if not messages:
        console.print("📭 No messages found.", style="yellow")
        return

    for msg in messages:
        time_str = msg.timestamp.strftime('%H:%M:%S') if msg.timestamp else '--:--:--'
        sender = msg.sender or 'unknown'
        if sender == agent_name:
            console.print(f"[dim][{time_str}][/dim] [green]You:[/green] {msg.content.strip()}")
        else:
            console.print(f"[dim][{time_str}][/dim] [cyan]{sender}:[/cyan] {msg.content.strip()}")
