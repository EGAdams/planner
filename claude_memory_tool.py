#!/usr/bin/env python3
"""
Claude Memory Tool - Simple interface for Claude to access RAG memory
"""

import sys
import json
from pathlib import Path

# Add the project root to the Python path
sys.path.append(str(Path(__file__).parent))

from rag_system.core.document_manager import DocumentManager
from rag_system.core.context_provider import ContextProvider

def get_conversation_context(query, client=None, project=None, limit=5):
    """Get conversation context for a query"""
    try:
        doc_manager = DocumentManager()
        context_provider = ContextProvider(doc_manager)
        
        # Get contextual information
        context_text = context_provider.get_conversation_context(
            query=query,
            client_name=client,
            project_name=project
        )
        
        # Get search results
        results = doc_manager.search_by_context(query, n_results=limit)
        
        return {
            "success": True,
            "context": context_text,
            "results": [
                {
                    "title": r.metadata.get('title', 'Untitled'),
                    "type": r.metadata.get('doc_type', 'unknown'),
                    "client": r.metadata.get('client_name', ''),
                    "project": r.metadata.get('project_name', ''),
                    "content": r.content,
                    "score": f"{r.score:.3f}"
                }
                for r in results
            ]
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "context": "",
            "results": []
        }

def save_conversation_note(content, title, note_type="conversation", client=None, project=None):
    """Save a conversation note to memory"""
    try:
        doc_manager = DocumentManager()
        doc_id = doc_manager.add_quick_note(
            content=content,
            title=title,
            note_type=note_type,
            client_name=client,
            project_name=project
        )
        return {
            "success": True,
            "document_id": doc_id,
            "message": f"Note saved with ID: {doc_id}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "document_id": None
        }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python claude_memory_tool.py search <query> [--client=NAME] [--project=NAME] [--limit=N]")
        print("  python claude_memory_tool.py save <content> <title> [--type=TYPE] [--client=NAME] [--project=NAME]")
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Parse arguments
    def get_arg(prefix):
        for arg in sys.argv:
            if arg.startswith(f"{prefix}="):
                return arg.split("=", 1)[1]
        return None
    
    if command == "search":
        if len(sys.argv) < 3:
            print("Error: Query required")
            sys.exit(1)
        
        query = sys.argv[2]
        client = get_arg("--client")
        project = get_arg("--project")
        limit = int(get_arg("--limit") or "5")
        
        result = get_conversation_context(query, client, project, limit)
        print(json.dumps(result, indent=2))
    
    elif command == "save":
        if len(sys.argv) < 4:
            print("Error: Content and title required")
            sys.exit(1)
        
        content = sys.argv[2]
        title = sys.argv[3]
        note_type = get_arg("--type") or "conversation"
        client = get_arg("--client")
        project = get_arg("--project")
        
        result = save_conversation_note(content, title, note_type, client, project)
        print(json.dumps(result, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)