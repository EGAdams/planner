"""
Claude integration for automatic conversation logging and context enhancement
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

from .document_manager import DocumentManager
from .context_provider import ContextProvider
from ..models.document import DocumentType

class ClaudeConversationLogger:
    """Automatically log Claude conversations for memory enhancement"""
    
    def __init__(self, document_manager: Optional[DocumentManager] = None):
        """Initialize with document manager"""
        self.document_manager = document_manager or DocumentManager()
        self.conversation_buffer = []
        self.current_session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def log_user_message(self, message: str, metadata: Optional[Dict[str, Any]] = None):
        """Log a user message"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "user_message",
            "content": message,
            "metadata": metadata or {}
        }
        self.conversation_buffer.append(entry)
    
    def log_claude_response(self, response: str, context_used: Optional[str] = None, 
                          metadata: Optional[Dict[str, Any]] = None):
        """Log Claude's response"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "claude_response", 
            "content": response,
            "context_used": context_used,
            "metadata": metadata or {}
        }
        self.conversation_buffer.append(entry)
    
    def log_action_taken(self, action: str, result: str, metadata: Optional[Dict[str, Any]] = None):
        """Log an action taken by Claude"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": "action_taken",
            "action": action,
            "result": result,
            "metadata": metadata or {}
        }
        self.conversation_buffer.append(entry)
    
    def save_conversation_to_memory(self, title: Optional[str] = None, 
                                   client_name: Optional[str] = None,
                                   project_name: Optional[str] = None,
                                   tags: Optional[List[str]] = None) -> str:
        """Save the current conversation buffer to memory"""
        if not self.conversation_buffer:
            return ""
        
        # Format conversation content
        conversation_text = self._format_conversation_for_storage()
        
        # Generate title if not provided
        if not title:
            title = f"Conversation - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Extract topics and entities from conversation for better searchability
        extracted_tags = self._extract_conversation_tags()
        final_tags = list(set((tags or []) + extracted_tags))
        
        # Create document
        doc_id = self.document_manager.add_conversation_log(
            conversation_text=conversation_text,
            participant="user",
            topic=title,
            client_name=client_name,
            project_name=project_name
        )
        
        # Clear buffer after saving
        self.conversation_buffer = []
        
        return doc_id
    
    def _format_conversation_for_storage(self) -> str:
        """Format conversation buffer into readable text"""
        formatted_parts = [
            f"# Conversation Session: {self.current_session_id}",
            f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            ""
        ]
        
        for entry in self.conversation_buffer:
            timestamp = datetime.fromisoformat(entry["timestamp"]).strftime("%H:%M:%S")
            
            if entry["type"] == "user_message":
                formatted_parts.append(f"**[{timestamp}] User:**")
                formatted_parts.append(entry["content"])
                formatted_parts.append("")
                
            elif entry["type"] == "claude_response":
                formatted_parts.append(f"**[{timestamp}] Claude:**")
                formatted_parts.append(entry["content"])
                if entry.get("context_used"):
                    formatted_parts.append(f"*Context used: {entry['context_used'][:100]}...*")
                formatted_parts.append("")
                
            elif entry["type"] == "action_taken":
                formatted_parts.append(f"**[{timestamp}] Action: {entry['action']}**")
                formatted_parts.append(f"Result: {entry['result']}")
                formatted_parts.append("")
        
        return "\n".join(formatted_parts)
    
    def _extract_conversation_tags(self) -> List[str]:
        """Extract relevant tags from the conversation"""
        tags = []
        all_content = []
        
        # Combine all content
        for entry in self.conversation_buffer:
            all_content.append(entry.get("content", ""))
            if entry.get("action"):
                all_content.append(entry["action"])
        
        combined_text = " ".join(all_content).lower()
        
        # Look for common project management terms
        pm_terms = [
            "project", "client", "task", "deadline", "meeting", "requirements",
            "bug", "feature", "deploy", "test", "review", "status", "update"
        ]
        
        for term in pm_terms:
            if term in combined_text:
                tags.append(term)
        
        return tags

class ClaudeMemoryAssistant:
    """Enhanced Claude assistant with memory capabilities"""
    
    def __init__(self):
        """Initialize the memory-enhanced assistant"""
        self.document_manager = DocumentManager()
        self.context_provider = ContextProvider(self.document_manager)
        self.conversation_logger = ClaudeConversationLogger(self.document_manager)
    
    def get_enhanced_context_for_query(self, user_query: str, 
                                     client_name: Optional[str] = None,
                                     project_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get comprehensive context for a user query to enhance Claude's response
        
        Returns:
            Dictionary with context, suggestions, and metadata
        """
        # Log the user query
        self.conversation_logger.log_user_message(user_query, {
            "client_name": client_name,
            "project_name": project_name
        })
        
        # Get relevant context
        context_text = self.context_provider.get_conversation_context(
            query=user_query,
            client_name=client_name,
            project_name=project_name
        )
        
        # Get suggested next steps
        suggestions = self.context_provider.suggest_next_steps(user_query, context_text)
        
        # Get related information
        search_results = self.document_manager.search_by_context(user_query, n_results=3)
        
        return {
            "context": context_text,
            "suggestions": suggestions,
            "related_documents": [
                {
                    "title": r.metadata.get('title', 'Untitled'),
                    "type": r.metadata.get('doc_type', 'unknown'),
                    "preview": r.content[:150] + "..." if len(r.content) > 150 else r.content,
                    "relevance": f"{r.score:.2f}"
                }
                for r in search_results
            ],
            "metadata": {
                "client_name": client_name,
                "project_name": project_name,
                "query_timestamp": datetime.now().isoformat()
            }
        }
    
    def log_claude_response_with_context(self, response: str, context_used: str,
                                       actions_taken: Optional[List[Dict[str, str]]] = None):
        """Log Claude's response and any actions taken"""
        self.conversation_logger.log_claude_response(response, context_used)
        
        if actions_taken:
            for action in actions_taken:
                self.conversation_logger.log_action_taken(
                    action.get("action", "unknown"),
                    action.get("result", ""),
                    action.get("metadata", {})
                )
    
    def save_current_conversation(self, title: Optional[str] = None,
                                client_name: Optional[str] = None,
                                project_name: Optional[str] = None) -> str:
        """Save the current conversation to memory"""
        return self.conversation_logger.save_conversation_to_memory(
            title=title,
            client_name=client_name,
            project_name=project_name
        )
    
    def quick_memory_add(self, content: str, content_type: str = "note",
                        title: Optional[str] = None,
                        client_name: Optional[str] = None,
                        project_name: Optional[str] = None) -> str:
        """Quickly add something to memory"""
        if not title:
            title = f"Quick {content_type} - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        return self.document_manager.add_quick_note(
            content=content,
            title=title,
            note_type=content_type,
            client_name=client_name,
            project_name=project_name
        )
    
    def get_project_dashboard(self, project_name: str) -> Dict[str, Any]:
        """Get a comprehensive project dashboard"""
        project_summary = self.document_manager.get_project_status_summary(project_name)
        recent_docs = self.document_manager.search_by_project(project_name, n_results=5)
        
        return {
            "summary": project_summary,
            "recent_activity": [
                {
                    "title": doc.metadata.get('title', 'Untitled'),
                    "type": doc.metadata.get('doc_type', 'unknown'),
                    "created": doc.metadata.get('created_at', ''),
                    "preview": doc.content[:100] + "..." if len(doc.content) > 100 else doc.content
                }
                for doc in recent_docs
            ],
            "suggestions": self.context_provider.suggest_next_steps(f"project status {project_name}")
        }
    
    def get_client_overview(self, client_name: str) -> Dict[str, Any]:
        """Get comprehensive client overview"""
        client_context = self.context_provider.get_client_context(client_name)
        client_docs = self.document_manager.search_by_client(client_name, n_results=10)
        
        # Extract projects for this client
        projects = set()
        for doc in client_docs:
            if doc.metadata.get('project_name'):
                projects.add(doc.metadata['project_name'])
        
        return {
            "context": client_context,
            "projects": list(projects),
            "total_documents": len(client_docs),
            "recent_activity": [
                {
                    "title": doc.metadata.get('title', 'Untitled'),
                    "project": doc.metadata.get('project_name', ''),
                    "type": doc.metadata.get('doc_type', 'unknown'),
                    "preview": doc.content[:100] + "..." if len(doc.content) > 100 else doc.content
                }
                for doc in client_docs[:5]
            ]
        }