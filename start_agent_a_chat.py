#!/usr/bin/env python3
"""
Agent A Live Chat - For Claude to use in Terminal 1
"""

import sys
import time
import threading
from datetime import datetime
from rag_tools import send, inbox
from rich.console import Console

console = Console()

class AgentAChat:
    def __init__(self):
        self.agent_name = "agent-a"
        self.topic = "testing"
        self.seen_messages = set()
        self.running = True

    def check_for_new_messages(self):
        """Check for new messages and display them"""
        try:
            messages = inbox(topic=self.topic, limit=20)

            for msg in messages:
                msg_id = f"{msg.metadata.get('timestamp', '')}_{msg.metadata.get('source', '')}"

                if msg_id not in self.seen_messages:
                    self.seen_messages.add(msg_id)

                    sender = msg.metadata.get('source', 'unknown')
                    timestamp = msg.metadata.get('timestamp', '')

                    if timestamp:
                        try:
                            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                            time_str = dt.strftime('%H:%M:%S')
                        except:
                            time_str = timestamp[:8] if len(timestamp) >= 8 else timestamp
                    else:
                        time_str = datetime.now().strftime('%H:%M:%S')

                    content = msg.content
                    if '**From**:' in content:
                        lines = content.split('\n')
                        content = '\n'.join(lines[4:]) if len(lines) > 4 else content

                    # Only show new messages
                    if len(self.seen_messages) > 1:
                        if sender == self.agent_name:
                            console.print(f"[dim][{time_str}][/dim] [green]You:[/green] {content.strip()}")
                        else:
                            console.print(f"[dim][{time_str}][/dim] [cyan]{sender}:[/cyan] {content.strip()}")
                            print('\a', end='', flush=True)
        except Exception as e:
            pass

    def message_monitor(self):
        """Background thread to monitor for new messages"""
        while self.running:
            self.check_for_new_messages()
            time.sleep(2)

    def send_message(self, message):
        """Send a message"""
        send(message, topic=self.topic, from_agent=self.agent_name)
        time_str = datetime.now().strftime('%H:%M:%S')
        console.print(f"[dim][{time_str}][/dim] [green]You:[/green] {message}")

    def start_monitoring(self):
        """Start monitoring in background"""
        console.print("\n💬 Agent A Live Chat Started\n", style="bold green")
        console.print(f"✅ Monitoring topic: [yellow]{self.topic}[/yellow]")
        console.print("✅ [green]Messages from Agent B will appear automatically[/green]\n")

        # Load initial messages
        self.check_for_new_messages()

        # Start monitoring
        monitor_thread = threading.Thread(target=self.message_monitor, daemon=True)
        monitor_thread.start()

        return self

# Create global instance
_agent_a_chat = None

def start_chat():
    """Start Agent A chat session"""
    global _agent_a_chat
    if not _agent_a_chat:
        _agent_a_chat = AgentAChat()
        _agent_a_chat.start_monitoring()
    return _agent_a_chat

def send_msg(message):
    """Send a message from Agent A"""
    global _agent_a_chat
    if not _agent_a_chat:
        _agent_a_chat = start_chat()
    _agent_a_chat.send_message(message)

if __name__ == "__main__":
    chat = start_chat()
    console.print("[dim]Use send_msg('your message') to send messages[/dim]\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n\n👋 Chat stopped\n", style="yellow")
