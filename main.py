#!/usr/bin/env python3
"""
Project Management RAG System
CLI interface for memory-enhanced project management
"""

import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from typing import Optional
from pathlib import Path

from rag_system.core.document_manager import DocumentManager
from rag_system.core.context_provider import ContextProvider
from rag_system.models.document import DocumentType

app = typer.Typer(help="Project Management RAG System - Memory for your freelance business")
console = Console()

# Global instances
doc_manager = None
context_provider = None

def get_managers():
    """Initialize managers if not already done"""
    global doc_manager, context_provider
    if not doc_manager:
        doc_manager = DocumentManager()
        context_provider = ContextProvider(doc_manager)
    return doc_manager, context_provider

@app.command()
def init():
    """Initialize the RAG system"""
    console.print("🚀 Initializing RAG system...", style="bold green")
    
    # Initialize the system
    dm, cp = get_managers()
    
    # Test basic functionality
    stats = dm.get_system_stats()
    
    console.print(f"✅ RAG system initialized successfully!", style="green")
    console.print(f"📁 Storage: {stats['storage_path']}")
    console.print(f"📊 Documents: {stats['total_chunks']} chunks indexed")

@app.command()  
def ingest(file_path: str, doc_type: Optional[str] = None):
    """Ingest a document into the RAG system"""
    console.print(f"📄 Ingesting document: {file_path}", style="bold blue")
    
    dm, _ = get_managers()
    
    try:
        # Convert string doc_type to enum if provided
        document_type = None
        if doc_type:
            document_type = DocumentType(doc_type)
        
        doc_id = dm.add_document_from_file(file_path, document_type)
        console.print(f"✅ Document ingested successfully! ID: {doc_id}", style="green")
        
    except FileNotFoundError:
        console.print(f"❌ File not found: {file_path}", style="red")
    except Exception as e:
        console.print(f"❌ Error ingesting document: {str(e)}", style="red")

@app.command()
def note(
    content: str, 
    title: str,
    note_type: str = "general",
    client: Optional[str] = None,
    project: Optional[str] = None,
    priority: Optional[str] = None
):
    """Add a quick note to memory"""
    dm, _ = get_managers()
    
    try:
        doc_id = dm.add_quick_note(
            content=content,
            title=title,
            note_type=note_type,
            client_name=client,
            project_name=project,
            priority=priority
        )
        console.print(f"✅ Note added successfully! ID: {doc_id}", style="green")
    except Exception as e:
        console.print(f"❌ Error adding note: {str(e)}", style="red")

@app.command()
def search(question: str, limit: int = 5):
    """Search the knowledge base"""
    console.print(f"🔍 Searching: {question}", style="bold cyan")
    
    dm, _ = get_managers()
    
    results = dm.search_by_context(question, n_results=limit)
    
    if not results:
        console.print("No results found.", style="yellow")
        return
    
    for i, result in enumerate(results, 1):
        title = result.metadata.get('title', 'Untitled')
        doc_type = result.metadata.get('doc_type', 'unknown').replace('_', ' ').title()
        score = f"{result.score:.2f}"
        
        panel_content = f"**Type**: {doc_type} | **Relevance**: {score}\n\n{result.content[:300]}"
        if len(result.content) > 300:
            panel_content += "..."
            
        console.print(Panel(
            panel_content,
            title=f"[{i}] {title}",
            border_style="blue"
        ))

@app.command()
def context(query: str, client: Optional[str] = None, project: Optional[str] = None):
    """Get contextual information for a query"""
    console.print(f"🧠 Getting context for: {query}", style="bold magenta")
    
    _, cp = get_managers()
    
    context_text = cp.get_conversation_context(
        query=query,
        client_name=client,
        project_name=project
    )
    
    console.print(Panel(
        Markdown(context_text),
        title="📋 Relevant Context",
        border_style="magenta"
    ))
    
    # Show suggested next steps
    suggestions = cp.suggest_next_steps(query, context_text)
    if suggestions:
        console.print("\n💡 **Suggested next steps:**", style="bold")
        for suggestion in suggestions:
            console.print(f"  • {suggestion}")

@app.command()
def project(name: str):
    """Get comprehensive project overview"""
    console.print(f"📊 Project Overview: {name}", style="bold green")
    
    _, cp = get_managers()
    
    project_context = cp.get_project_context(name)
    console.print(Panel(
        Markdown(project_context),
        title=f"📋 {name}",
        border_style="green"
    ))

@app.command()
def client(name: str):
    """Get comprehensive client overview"""  
    console.print(f"👤 Client Overview: {name}", style="bold blue")
    
    _, cp = get_managers()
    
    client_context = cp.get_client_context(name)
    console.print(Panel(
        Markdown(client_context),
        title=f"👤 {name}",
        border_style="blue"
    ))

@app.command()
def recent(limit: int = 10):
    """Show recent activities"""
    console.print("⏰ Recent Activities", style="bold yellow")
    
    dm, _ = get_managers()
    
    results = dm.get_recent_activities(n_results=limit)
    
    if not results:
        console.print("No recent activities found.", style="yellow")
        return
    
    table = Table(title="Recent Activities")
    table.add_column("Title", style="cyan")
    table.add_column("Type", style="green")
    table.add_column("Client", style="blue")
    table.add_column("Project", style="magenta")
    table.add_column("Preview", style="white")
    
    for result in results:
        title = result.metadata.get('title', 'Untitled')
        doc_type = result.metadata.get('doc_type', '').replace('_', ' ').title()
        client_name = result.metadata.get('client_name', '')
        project_name = result.metadata.get('project_name', '')
        preview = result.content[:50] + "..." if len(result.content) > 50 else result.content
        
        table.add_row(title, doc_type, client_name, project_name, preview)
    
    console.print(table)

@app.command()
def status():
    """Show system status and statistics"""
    console.print("📊 RAG System Status", style="bold yellow")
    
    dm, _ = get_managers()
    stats = dm.get_system_stats()
    
    # Create main stats table
    stats_table = Table(title="System Statistics")
    stats_table.add_column("Metric", style="cyan")
    stats_table.add_column("Value", style="green")
    
    stats_table.add_row("Total Chunks", str(stats['total_chunks']))
    stats_table.add_row("Unique Clients", str(stats['unique_clients']))
    stats_table.add_row("Unique Projects", str(stats['unique_projects']))
    stats_table.add_row("Storage Path", stats['storage_path'])
    
    console.print(stats_table)
    
    # Document types breakdown
    if stats['document_types']:
        doc_table = Table(title="Document Types")
        doc_table.add_column("Type", style="magenta")
        doc_table.add_column("Count", style="yellow")
        
        for doc_type, count in stats['document_types'].items():
            doc_table.add_row(doc_type.replace('_', ' ').title(), str(count))
        
        console.print(doc_table)

@app.command()
def types():
    """Show available document types"""
    console.print("📝 Available Document Types", style="bold")
    
    types_table = Table()
    types_table.add_column("Type", style="cyan")
    types_table.add_column("Description", style="white")
    
    type_descriptions = {
        "client_profile": "Information about clients and contacts",
        "project_details": "Project specifications and requirements", 
        "meeting_notes": "Meeting summaries and action items",
        "task_update": "Task progress and status updates",
        "decision_log": "Important decisions and rationale",
        "code_snippet": "Code examples and technical notes",
        "template": "Reusable templates and boilerplates",
        "conversation": "Chat logs and general discussions"
    }
    
    for doc_type, description in type_descriptions.items():
        types_table.add_row(doc_type, description)
    
    console.print(types_table)

if __name__ == "__main__":
    app()