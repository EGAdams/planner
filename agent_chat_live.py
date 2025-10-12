#!/usr/bin/env python3
"""
Live Agent Chat - Real-time messaging with other agents
Messages appear as they arrive, just like a chat app
"""

import sys
import time
import threading
from datetime import datetime
from rag_tools import send, inbox
from rich.console import Console
from rich.prompt import Prompt
from rich.live import Live
from rich.panel import Panel
from rich.markdown import Markdown

console = Console()

class LiveAgentChat:
    def __init__(self, agent_name, topic):
        self.agent_name = agent_name
        self.topic = topic
        self.seen_messages = set()
        self.running = True
        self.new_messages = []

    def check_for_new_messages(self):
        """Check for new messages and display them"""
        try:
            messages = inbox(topic=self.topic, limit=20, render=False)

            for msg in messages:
                # Create unique ID from timestamp and sender
                msg_timestamp = msg.timestamp.isoformat() if msg.timestamp else ''
                msg_id = f"{msg_timestamp}_{msg.sender}"

                if msg_id not in self.seen_messages:
                    self.seen_messages.add(msg_id)

                    # Only show if it's not our own message or if it's the first run
                    sender = msg.sender or 'unknown'
                    timestamp = msg.timestamp

                    # Parse timestamp to show time only
                    if timestamp:
                        time_str = timestamp.strftime('%H:%M:%S')
                    else:
                        time_str = datetime.now().strftime('%H:%M:%S')

                    content = msg.content

                    # Only show new messages (not from initial load)
                    if len(self.seen_messages) > 1:
                        if sender == self.agent_name:
                            console.print(f"\n[dim][{time_str}][/dim] [green]You:[/green] {content.strip()}")
                        else:
                            console.print(f"\n[dim][{time_str}][/dim] [cyan]{sender}:[/cyan] {content.strip()}")
                            # Beep for new messages from others
                            print('\a', end='', flush=True)
        except Exception as e:
            pass  # Silently handle errors to avoid cluttering display

    def message_monitor(self):
        """Background thread to monitor for new messages"""
        while self.running:
            self.check_for_new_messages()
            time.sleep(2)  # Check every 2 seconds

    def start(self):
        """Start the live chat session"""
        console.print("\n💬 Live Agent Chat - Real-time Messaging\n", style="bold cyan")
        console.print(f"✅ Logged in as: [green]{self.agent_name}[/green]")
        console.print(f"📡 Monitoring topic: [yellow]{self.topic}[/yellow]")
        console.print("\n" + "="*60, style="dim")
        console.print("Commands:", style="bold")
        console.print("  • Type your message and press Enter to send")
        console.print("  • Messages from other agents appear automatically")
        console.print("  • Type 'quit' to exit")
        console.print("="*60 + "\n", style="dim")

        # Load initial messages
        console.print("📬 Loading recent messages...\n", style="yellow")
        self.check_for_new_messages()

        # Start background monitoring thread
        monitor_thread = threading.Thread(target=self.message_monitor, daemon=True)
        monitor_thread.start()

        console.print("\n✅ [green]Live monitoring active! Messages will appear as they arrive.[/green]")
        console.print("[dim]Type your message below:[/dim]\n")

        # Main input loop
        try:
            while self.running:
                user_input = input(f"\r[{self.agent_name}] ❯ ").strip()

                if user_input.lower() in ['quit', 'exit', 'q']:
                    self.running = False
                    console.print("\n👋 Logging out...", style="yellow")
                    send(
                        f"📴 {self.agent_name} has left the chat.",
                        topic=self.topic,
                        from_agent=self.agent_name
                    )
                    console.print("✅ Goodbye!\n", style="green")
                    break

                elif user_input:
                    # Send message
                    send(user_input, topic=self.topic, from_agent=self.agent_name)
                    # Show immediately in our terminal
                    time_str = datetime.now().strftime('%H:%M:%S')
                    console.print(f"[dim][{time_str}][/dim] [green]You:[/green] {user_input}")

        except KeyboardInterrupt:
            self.running = False
            console.print("\n\n👋 Interrupted. Goodbye!\n", style="yellow")

def main():
    # Get agent identity
    console.print("\n🤖 Live Agent Chat Setup\n", style="bold cyan")
    agent_name = Prompt.ask("Enter your agent name", default="agent-b")
    topic = Prompt.ask("Enter topic to monitor", default="testing")

    # Start chat
    chat = LiveAgentChat(agent_name, topic)
    chat.start()

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        console.print(f"\n❌ Error: {e}\n", style="red")
        sys.exit(1)
