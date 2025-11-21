#!/usr/bin/env python3
"""
Claude Helper - Integration script for memory-enhanced conversations
This script can be used to provide context and log conversations automatically
"""

import json
import sys
from typing import Optional, Dict, Any
from pathlib import Path

from rag_system.core.claude_integration import ClaudeMemoryAssistant

def main():
    """Main entry point for Claude helper"""
    if len(sys.argv) < 2:
        print("Usage: python claude_helper.py <command> [args...]")
        print("Commands:")
        print("  context <query> [--client=NAME] [--project=NAME]")
        print("  save-conversation <title> [--client=NAME] [--project=NAME]")  
        print("  quick-add <content> <type> <title> [--client=NAME] [--project=NAME]")
        print("  project-status <project_name>")
        print("  client-overview <client_name>")
        return
    
    command = sys.argv[1]
    assistant = ClaudeMemoryAssistant()
    
    if command == "context":
        if len(sys.argv) < 3:
            print("Error: Query required for context command")
            return
        
        query = sys.argv[2]
        client_name = extract_arg("--client")
        project_name = extract_arg("--project")
        
        context_data = assistant.get_enhanced_context_for_query(
            query, client_name, project_name
        )
        
        # Output as JSON for easy parsing
        print(json.dumps(context_data, indent=2))
    
    elif command == "save-conversation":
        if len(sys.argv) < 3:
            print("Error: Title required for save-conversation command")
            return
        
        title = sys.argv[2]
        client_name = extract_arg("--client")
        project_name = extract_arg("--project")
        
        doc_id = assistant.save_current_conversation(
            title=title,
            client_name=client_name,
            project_name=project_name
        )
        
        result = {
            "success": True,
            "document_id": doc_id,
            "message": f"Conversation saved with ID: {doc_id}"
        }
        print(json.dumps(result, indent=2))
    
    elif command == "quick-add":
        if len(sys.argv) < 5:
            print("Error: Content, type, and title required for quick-add command")
            return
        
        content = sys.argv[2]
        content_type = sys.argv[3] 
        title = sys.argv[4]
        client_name = extract_arg("--client")
        project_name = extract_arg("--project")
        
        doc_id = assistant.quick_memory_add(
            content=content,
            content_type=content_type,
            title=title,
            client_name=client_name,
            project_name=project_name
        )
        
        result = {
            "success": True,
            "document_id": doc_id,
            "message": f"Added to memory with ID: {doc_id}"
        }
        print(json.dumps(result, indent=2))
    
    elif command == "project-status":
        if len(sys.argv) < 3:
            print("Error: Project name required for project-status command")
            return
        
        project_name = sys.argv[2]
        dashboard = assistant.get_project_dashboard(project_name)
        print(json.dumps(dashboard, indent=2))
    
    elif command == "client-overview":
        if len(sys.argv) < 3:
            print("Error: Client name required for client-overview command")  
            return
        
        client_name = sys.argv[2]
        overview = assistant.get_client_overview(client_name)
        print(json.dumps(overview, indent=2))
    
    else:
        print(f"Unknown command: {command}")

def extract_arg(arg_name: str) -> Optional[str]:
    """Extract named argument from sys.argv"""
    for arg in sys.argv:
        if arg.startswith(f"{arg_name}="):
            return arg.split("=", 1)[1]
    return None

if __name__ == "__main__":
    main()