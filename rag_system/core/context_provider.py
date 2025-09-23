"""
Context provider for memory-enhanced conversations
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from .document_manager import DocumentManager
from ..models.document import QueryResult

class ContextProvider:
    """Provides relevant context for conversations and queries"""
    
    def __init__(self, document_manager: Optional[DocumentManager] = None):
        """Initialize with document manager"""
        self.document_manager = document_manager or DocumentManager()
    
    def get_conversation_context(self, query: str, 
                               client_name: Optional[str] = None,
                               project_name: Optional[str] = None,
                               max_context_length: int = 2000) -> str:
        """
        Get relevant context for a conversation query
        
        Args:
            query: The user's query or conversation topic
            client_name: Optional client filter
            project_name: Optional project filter
            max_context_length: Maximum characters of context to return
            
        Returns:
            Formatted context string
        """
        context_parts = []
        remaining_length = max_context_length
        
        # 1. Get semantically similar content
        semantic_results = self.document_manager.search_by_context(query, n_results=5)
        
        if semantic_results:
            context_parts.append("## Relevant Information")
            for result in semantic_results[:3]:  # Limit to top 3
                if remaining_length <= 0:
                    break
                    
                snippet = self._format_result_snippet(result, max_length=300)
                if len(snippet) <= remaining_length:
                    context_parts.append(snippet)
                    remaining_length -= len(snippet)
        
        # 2. Add client-specific context if specified
        if client_name and remaining_length > 0:
            client_results = self.document_manager.search_by_client(client_name, n_results=3)
            if client_results:
                context_parts.append(f"\n## Recent {client_name} Context")
                for result in client_results[:2]:
                    if remaining_length <= 0:
                        break
                    snippet = self._format_result_snippet(result, max_length=200)
                    if len(snippet) <= remaining_length:
                        context_parts.append(snippet)
                        remaining_length -= len(snippet)
        
        # 3. Add project-specific context if specified
        if project_name and remaining_length > 0:
            project_results = self.document_manager.search_by_project(project_name, n_results=3)
            if project_results:
                context_parts.append(f"\n## {project_name} Project Status")
                for result in project_results[:2]:
                    if remaining_length <= 0:
                        break
                    snippet = self._format_result_snippet(result, max_length=200)
                    if len(snippet) <= remaining_length:
                        context_parts.append(snippet)
                        remaining_length -= len(snippet)
        
        # 4. Add recent activities if space remains
        if remaining_length > 300:
            recent_results = self.document_manager.get_recent_activities(n_results=3)
            if recent_results:
                context_parts.append("\n## Recent Activities")
                for result in recent_results:
                    if remaining_length <= 0:
                        break
                    snippet = self._format_result_snippet(result, max_length=150)
                    if len(snippet) <= remaining_length:
                        context_parts.append(snippet)
                        remaining_length -= len(snippet)
        
        return "\n".join(context_parts) if context_parts else "No relevant context found."
    
    def get_project_context(self, project_name: str) -> str:
        """Get comprehensive context for a specific project"""
        status_summary = self.document_manager.get_project_status_summary(project_name)
        
        if "error" in status_summary:
            return status_summary["error"]
        
        context_parts = [
            f"# {project_name} - Project Overview",
            "",
            f"**Total Documents**: {status_summary['total_documents']}",
            f"**Latest Update**: {status_summary['latest_update'] or 'Unknown'}",
            ""
        ]
        
        # Document types breakdown
        if status_summary['document_types']:
            context_parts.append("## Document Types")
            for doc_type, count in status_summary['document_types'].items():
                context_parts.append(f"- {doc_type.replace('_', ' ').title()}: {count}")
            context_parts.append("")
        
        # Priority breakdown
        priority_counts = status_summary['priority_breakdown']
        if any(priority_counts.values()):
            context_parts.append("## Priority Breakdown")
            for priority, count in priority_counts.items():
                if count > 0:
                    context_parts.append(f"- {priority.title()}: {count}")
            context_parts.append("")
        
        # Status breakdown  
        status_counts = status_summary['status_breakdown']
        if status_counts:
            context_parts.append("## Status Overview")
            for status, count in status_counts.items():
                if status and status != 'unknown':
                    context_parts.append(f"- {status.title()}: {count}")
            context_parts.append("")
        
        # Recent documents
        if status_summary['recent_documents']:
            context_parts.append("## Recent Documents")
            for doc in status_summary['recent_documents']:
                context_parts.append(f"**{doc['title']}** ({doc['type']})")
                context_parts.append(f"  {doc['preview']}")
                context_parts.append("")
        
        return "\n".join(context_parts)
    
    def get_client_context(self, client_name: str) -> str:
        """Get comprehensive context for a specific client"""
        client_results = self.document_manager.search_by_client(client_name, n_results=20)
        
        if not client_results:
            return f"No information found for client: {client_name}"
        
        context_parts = [
            f"# {client_name} - Client Overview",
            "",
            f"**Total Documents**: {len(client_results)}",
            ""
        ]
        
        # Analyze projects for this client
        projects = set()
        doc_types = {}
        recent_activity = None
        
        for result in client_results:
            if result.metadata.get('project_name'):
                projects.add(result.metadata['project_name'])
            
            doc_type = result.metadata.get('doc_type', 'unknown')
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            try:
                created_at = datetime.fromisoformat(result.metadata.get('created_at', '1900-01-01'))
                if not recent_activity or created_at > recent_activity:
                    recent_activity = created_at
            except:
                pass
        
        if projects:
            context_parts.append("## Associated Projects")
            for project in sorted(projects):
                context_parts.append(f"- {project}")
            context_parts.append("")
        
        if recent_activity:
            context_parts.append(f"**Last Activity**: {recent_activity.strftime('%Y-%m-%d')}")
            context_parts.append("")
        
        # Recent documents
        context_parts.append("## Recent Activity")
        for result in client_results[:5]:
            title = result.metadata.get('title', 'Untitled')
            doc_type = result.metadata.get('doc_type', 'unknown').replace('_', ' ').title()
            preview = result.content[:100] + "..." if len(result.content) > 100 else result.content
            
            context_parts.append(f"**{title}** ({doc_type})")
            context_parts.append(f"  {preview}")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def _format_result_snippet(self, result: QueryResult, max_length: int = 200) -> str:
        """Format a search result as a context snippet"""
        title = result.metadata.get('title', 'Untitled')
        doc_type = result.metadata.get('doc_type', 'unknown').replace('_', ' ').title()
        
        content = result.content
        if len(content) > max_length:
            content = content[:max_length] + "..."
        
        return f"**{title}** ({doc_type}): {content}"
    
    def suggest_next_steps(self, query: str, context: str = "") -> List[str]:
        """Suggest possible next steps based on query and context"""
        query_lower = query.lower()
        suggestions = []
        
        # Common project management next steps
        if any(word in query_lower for word in ['status', 'progress', 'update']):
            suggestions.extend([
                "Review recent project updates",
                "Check task priorities and deadlines", 
                "Update client on progress"
            ])
        
        if any(word in query_lower for word in ['client', 'meeting']):
            suggestions.extend([
                "Schedule follow-up meeting",
                "Prepare meeting agenda",
                "Document meeting outcomes"
            ])
        
        if any(word in query_lower for word in ['task', 'todo', 'work']):
            suggestions.extend([
                "Create new task entries",
                "Update task statuses",
                "Set task priorities"
            ])
        
        if any(word in query_lower for word in ['project', 'new']):
            suggestions.extend([
                "Create project documentation",
                "Set up project structure",
                "Define project milestones"
            ])
        
        # Default suggestions if no specific matches
        if not suggestions:
            suggestions = [
                "Add this conversation to memory",
                "Search for related information",
                "Update project status"
            ]
        
        return suggestions[:5]  # Limit to 5 suggestions