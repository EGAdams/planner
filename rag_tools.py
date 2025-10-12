#!/usr/bin/env python3
"""
Quick RAG Memory Tools - Easy access to project memory system
Import this for instant access to memory functions in any script
"""

from typing import Optional
from datetime import datetime
from rag_system.core.document_manager import DocumentManager
from rag_system.core.context_provider import ContextProvider
from rich.console import Console

from agent_messaging_interface import AgentMessage, get_agent_messenger

console = Console()

# Global instances - initialized on first use
_doc_manager = None
_context_provider = None
_agent_messenger = None

def _get_managers():
    """Lazy initialization of managers"""
    global _doc_manager, _context_provider
    if not _doc_manager:
        _doc_manager = DocumentManager()
        _context_provider = ContextProvider(_doc_manager)
    return _doc_manager, _context_provider

# ============================================================================
# QUICK MEMORY FUNCTIONS - Use these in any script!
# ============================================================================

def remember(content: str, title: str = "Quick Note", project=None, client=None, **kwargs):
    """
    Remember something important

    Usage:
        remember("Fixed bug in parser.py line 145", "Parser bug fix")
        remember("Client wants dark mode", "Feature request", project="website")
    """
    dm, _ = _get_managers()
    # Map friendly names to actual parameter names
    if project:
        kwargs['project_name'] = project
    if client:
        kwargs['client_name'] = client
    doc_id = dm.add_quick_note(content=content, title=title, **kwargs)
    console.print(f"✅ Remembered: {title}", style="green")
    return doc_id

def recall(query: str, limit: int = 3):
    """
    Recall relevant memories

    Usage:
        results = recall("parser errors")
        results = recall("client feedback", limit=5)
    """
    dm, _ = _get_managers()
    results = dm.search_by_context(query, n_results=limit)

    if results:
        console.print(f"🧠 Found {len(results)} memories:", style="cyan")
        for i, result in enumerate(results, 1):
            title = result.metadata.get('title', 'Untitled')
            console.print(f"  [{i}] {title}")
            console.print(f"      {result.content[:100]}...", style="dim")
    else:
        console.print("No memories found", style="yellow")

    return results

def log_error(error_text: str, source: str, project=None, **kwargs):
    """
    Log an error for future reference

    Usage:
        log_error("ImportError: cached_download", "main.py:15", project="planner")
    """
    dm, _ = _get_managers()
    if project:
        kwargs['project_name'] = project
    doc_id = dm.add_runtime_artifact(
        artifact_text=error_text,
        artifact_type="error",
        source=source,
        **kwargs
    )
    console.print(f"📝 Error logged from {source}", style="red")
    return doc_id

def log_fix(description: str, workaround: str, project=None, **kwargs):
    """
    Log a fix or workaround (gotcha)

    Usage:
        log_fix("sentence-transformers v2.2.2 incompatible",
                "Upgrade to v5.1.1",
                project="planner")
    """
    dm, _ = _get_managers()
    if project:
        kwargs['project_name'] = project
    doc_id = dm.log_gotcha(
        description=description,
        workaround=workaround,
        **kwargs
    )
    console.print(f"💡 Fix logged!", style="green")
    return doc_id

def log_decision(decision: str, rationale: str, project=None, **kwargs):
    """
    Log an important decision

    Usage:
        log_decision("Use ChromaDB for vector storage",
                    "Fast, local, no external deps",
                    project="planner")
    """
    dm, _ = _get_managers()
    if project:
        kwargs['project_name'] = project
    doc_id = dm.add_runtime_artifact(
        artifact_text=f"**Decision**: {decision}\n**Rationale**: {rationale}",
        artifact_type="decision",
        source="manual_log",
        **kwargs
    )
    console.print(f"✓ Decision logged", style="blue")
    return doc_id

def get_context(query: str, client=None, project=None, **kwargs):
    """
    Get full context for a query (formatted for AI)

    Usage:
        context = get_context("What errors have we seen in the parser?")
        context = get_context("Client requirements", client="Acme Corp")
    """
    _, cp = _get_managers()
    if client:
        kwargs['client_name'] = client
    if project:
        kwargs['project_name'] = project
    context_text = cp.get_conversation_context(query=query, **kwargs)
    return context_text

def project_status(project_name: str):
    """
    Get full project overview

    Usage:
        project_status("planner")
    """
    _, cp = _get_managers()
    context = cp.get_project_context(project_name)
    console.print(context)
    return context

def client_info(client_name: str):
    """
    Get full client overview

    Usage:
        client_info("Acme Corp")
    """
    _, cp = _get_managers()
    context = cp.get_client_context(client_name)
    console.print(context)
    return context

def memory_stats():
    """Show memory system statistics"""
    dm, _ = _get_managers()
    stats = dm.get_system_stats()

    console.print("\n📊 Memory System Stats", style="bold yellow")
    console.print(f"  Total memories: {stats['total_chunks']}")
    console.print(f"  Clients: {stats['unique_clients']}")
    console.print(f"  Projects: {stats['unique_projects']}")
    console.print(f"  Storage: {stats['storage_path']}")

    if stats['document_types']:
        console.print("\n  Document types:", style="dim")
        for doc_type, count in stats['document_types'].items():
            console.print(f"    - {doc_type}: {count}", style="dim")

    return stats

# ============================================================================
# AGENT-TO-AGENT MESSAGING
# ============================================================================

def _get_agent_messenger():
    """Lazy initialization for the agent messaging backend."""
    global _agent_messenger
    if not _agent_messenger:
        dm, _ = _get_managers()
        _agent_messenger = get_agent_messenger(doc_manager=dm)
    return _agent_messenger


def send_agent_message(message: str, topic: str = "general", from_agent: str = "claude", priority: str = "normal"):
    """
    Send a message to other agents via shared message board

    Usage:
        send_agent_message("Found fix for parser bug", topic="debugging")
        send_agent_message("Deployment at 3pm", topic="ops", priority="high")
    """
    try:
        messenger = _get_agent_messenger()
        agent_message = messenger.send(
            message,
            topic=topic,
            sender=from_agent,
            priority=priority,
        )
        console.print(
            f"✅ Message sent to topic '{agent_message.topic}'", style="green"
        )
        return agent_message
    except Exception as e:
        console.print(f"❌ Error sending message: {e}", style="red")
        console.print("💡 Using memory-based fallback...", style="dim")

        # Fallback: use regular memory so the note is still saved somewhere
        topic_name = topic or "general"
        note_id = remember(
            f"[MESSAGE from {from_agent}] {message}",
            f"Agent Message: {topic_name}",
            priority=priority
        )

        return AgentMessage(
            id=note_id,
            document_id=note_id,
            content=message,
            topic=topic_name,
            sender=from_agent,
            priority=priority,
            timestamp=datetime.utcnow(),
            metadata={
                "fallback": True,
                "topic": topic_name,
                "sender": from_agent,
                "priority": priority,
                "document_id": note_id,
            },
            score=1.0,
            raw=None,
        )

def read_agent_messages(topic: Optional[str] = None, limit: int = 10, *, render: bool = True):
    """
    Read messages from other agents

    Usage:
        read_agent_messages()  # All messages
        read_agent_messages(topic="debugging")  # Specific topic
    """
    try:
        messenger = _get_agent_messenger()
        messages = messenger.receive(topic=topic, limit=limit)
        if render:
            _render_agent_messages(messages)
        return messages
    except Exception as e:
        console.print(f"❌ Error reading messages: {e}", style="red")

        # Fallback: search memory
        query = f"agent message {topic}" if topic else "agent message"
        results = recall(query, limit=limit)

        fallback_messages = []
        for result in results:
            metadata = dict(result.metadata)
            topic_name = metadata.get("topic") or metadata.get("project_name") or topic or "general"
            sender_name = metadata.get("sender") or metadata.get("source") or "unknown"
            priority_level = metadata.get("priority") or "normal"
            fallback_messages.append(
                AgentMessage(
                    id=metadata.get("document_id", result.document_id),
                    document_id=result.document_id,
                    content=result.content,
                    topic=topic_name,
                    sender=sender_name,
                    priority=priority_level,
                    timestamp=datetime.utcnow(),
                    metadata=metadata,
                    score=getattr(result, "score", 1.0),
                    raw=result,
                )
            )

        if render:
            _render_agent_messages(fallback_messages)
        return fallback_messages


def _render_agent_messages(messages: Optional[list[AgentMessage]]) -> None:
    """Pretty-print messages for interactive use."""

    if not messages:
        console.print("📭 No messages found.", style="yellow")
        return

    for msg in messages:
        timestamp = msg.timestamp.strftime('%Y-%m-%d %H:%M:%S') if msg.timestamp else '--'
        console.print(
            f"[dim]{timestamp}[/dim] [cyan]{msg.sender or 'unknown'}[/cyan] → "
            f"[bold]{msg.topic or 'general'}[/bold]: {msg.content.strip()}"
        )

# ============================================================================
# LETTA SHARED MEMORY INTEGRATION
# ============================================================================

def sync_to_letta(project_name: str = "planner", api_key: Optional[str] = None):
    """
    Sync local memory to Letta server for multi-agent sharing

    Usage:
        sync_to_letta()  # Sync to local Letta server
        sync_to_letta(api_key="xxx")  # Sync to Letta Cloud
    """
    try:
        from letta_memory_bridge import LettaMemoryBridge

        bridge = LettaMemoryBridge(api_key=api_key)
        bridge.sync_from_local_rag(project_name=project_name)
        console.print("✅ Memory synced to Letta server", style="green")

    except ImportError:
        console.print("❌ letta_memory_bridge not available", style="red")
        console.print("💡 Install with: pip install letta", style="dim")
    except Exception as e:
        console.print(f"❌ Sync failed: {e}", style="red")
        console.print("💡 Tip: Start Letta server with: letta server", style="dim")

def list_shared_blocks(api_key: Optional[str] = None):
    """
    List all shared memory blocks on Letta server

    Usage:
        list_shared_blocks()
    """
    try:
        from letta_memory_bridge import LettaMemoryBridge

        bridge = LettaMemoryBridge(api_key=api_key)
        blocks = bridge.list_blocks()

        if blocks:
            console.print(f"\n📦 Found {len(blocks)} shared memory blocks:", style="cyan")
            for block in blocks:
                console.print(f"  • {block.label}: {block.value[:80]}...", style="white")
        else:
            console.print("No shared blocks found", style="yellow")

        return blocks

    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        return []

# ============================================================================
# CONVENIENCE ALIASES
# ============================================================================

save = remember
find = recall
search = recall
status = memory_stats
sync = sync_to_letta
shared = list_shared_blocks
send = send_agent_message
inbox = read_agent_messages

# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    console.print("\n🧠 RAG Memory Tools - Quick Reference\n", style="bold cyan")

    print("Import in any script:")
    print("  from rag_tools import remember, recall, send, inbox, sync\n")

    print("Memory Functions:")
    print("  remember(content, title)         - Save a memory")
    print("  recall(query)                    - Search memories")
    print("  log_error(error, source)         - Log an error")
    print("  log_fix(description, workaround) - Log a fix/gotcha")
    print("  log_decision(decision, rationale)- Log a decision")
    print("  get_context(query)               - Get AI-ready context")
    print("  project_status(name)             - Get project overview")
    print("  client_info(name)                - Get client overview")
    print("  memory_stats()                   - Show statistics")

    print("\nAgent-to-Agent Communication:")
    print("  send_agent_message(msg, topic)   - Send message to other agents")
    print("  read_agent_messages(topic)       - Read messages from other agents")
    print("  send(msg, topic)                 - Alias for send_agent_message()")
    print("  inbox(topic)                     - Alias for read_agent_messages()")

    print("\nLetta Shared Memory:")
    print("  sync_to_letta()                  - Sync to Letta server (multi-agent sharing)")
    print("  list_shared_blocks()             - List Letta memory blocks")
    print("  sync()                           - Alias for sync_to_letta()")
    print("  shared()                         - Alias for list_shared_blocks()")

    print("\nExamples:")
    print("  remember('Fixed DB query performance', 'DB optimization')")
    print("  recall('authentication bugs')")
    print("  send('Found solution to parser bug!', topic='debugging')")
    print("  inbox('debugging')  # Read debugging messages")
    print("  sync()  # Share memories with other agents via Letta")

    print("\n✨ Memory + Messaging system ready! (Multi-agent collaboration enabled)")
