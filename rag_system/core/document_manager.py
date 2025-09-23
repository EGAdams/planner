"""
Document manager for handling different types of project documents
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from .rag_engine import RAGEngine
from ..models.document import Document, DocumentType, QueryResult
from ..utils.text_processing import (
    clean_text, extract_markdown_sections, extract_tags_from_text,
    detect_document_type_from_content, parse_metadata_from_text
)

class DocumentManager:
    """High-level document management interface"""
    
    def __init__(self, rag_engine: Optional[RAGEngine] = None):
        """Initialize with RAG engine"""
        self.rag_engine = rag_engine or RAGEngine()
    
    def add_document_from_file(self, file_path: str, 
                               doc_type: Optional[DocumentType] = None,
                               metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Add a document from a file
        
        Args:
            file_path: Path to the document file
            doc_type: Optional document type (will be auto-detected if not provided)
            metadata: Optional additional metadata
            
        Returns:
            Document ID
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read file content
        content = path.read_text(encoding='utf-8')
        
        # Auto-detect document type if not provided
        if not doc_type:
            detected_type = detect_document_type_from_content(content, path.name)
            doc_type = DocumentType(detected_type)
        
        # Extract metadata from content
        extracted_metadata = parse_metadata_from_text(content)
        
        # Merge metadata
        final_metadata = {
            "source_file": str(path),
            "file_extension": path.suffix,
            **extracted_metadata,
            **(metadata or {})
        }
        
        # Extract tags
        tags = extract_tags_from_text(content)
        
        # Create document
        document = Document(
            title=path.stem,
            content=clean_text(content),
            doc_type=doc_type,
            metadata=final_metadata,
            tags=tags,
            client_name=extracted_metadata.get('client'),
            project_name=extracted_metadata.get('project'),
            priority=extracted_metadata.get('priority'),
            status=extracted_metadata.get('status')
        )
        
        return self.rag_engine.add_document(document)
    
    def add_conversation_log(self, conversation_text: str, 
                           participant: str = "user",
                           topic: Optional[str] = None,
                           client_name: Optional[str] = None,
                           project_name: Optional[str] = None) -> str:
        """Add a conversation log to memory"""
        
        title = f"Conversation with {participant}"
        if topic:
            title += f" - {topic}"
        
        metadata = {
            "participant": participant,
            "topic": topic or "general",
            "conversation_type": "chat"
        }
        
        document = Document(
            title=title,
            content=clean_text(conversation_text),
            doc_type=DocumentType.CONVERSATION,
            metadata=metadata,
            client_name=client_name,
            project_name=project_name,
            tags=extract_tags_from_text(conversation_text)
        )
        
        return self.rag_engine.add_document(document)
    
    def add_quick_note(self, content: str, title: str,
                       note_type: str = "general",
                       client_name: Optional[str] = None,
                       project_name: Optional[str] = None,
                       priority: Optional[str] = None) -> str:
        """Add a quick note or update"""
        
        # Determine document type based on note_type
        doc_type_map = {
            "meeting": DocumentType.MEETING_NOTES,
            "task": DocumentType.TASK_UPDATE,
            "decision": DocumentType.DECISION_LOG,
            "code": DocumentType.CODE_SNIPPET
        }
        doc_type = doc_type_map.get(note_type, DocumentType.CONVERSATION)
        
        metadata = {
            "note_type": note_type,
            "quick_entry": True
        }
        
        document = Document(
            title=title,
            content=clean_text(content),
            doc_type=doc_type,
            metadata=metadata,
            client_name=client_name,
            project_name=project_name,
            priority=priority,
            tags=extract_tags_from_text(content)
        )
        
        return self.rag_engine.add_document(document)
    
    def search_by_context(self, query: str, n_results: int = 5) -> List[QueryResult]:
        """Search documents by semantic similarity"""
        return self.rag_engine.query(query_text=query, n_results=n_results)
    
    def search_by_client(self, client_name: str, n_results: int = 10) -> List[QueryResult]:
        """Get all documents for a specific client"""
        return self.rag_engine.query(
            query_text="",
            n_results=n_results,
            filter_dict={"client_name": client_name}
        )
    
    def search_by_project(self, project_name: str, n_results: int = 10) -> List[QueryResult]:
        """Get all documents for a specific project"""
        return self.rag_engine.query(
            query_text="",
            n_results=n_results, 
            filter_dict={"project_name": project_name}
        )
    
    def get_recent_activities(self, n_results: int = 10) -> List[QueryResult]:
        """Get recent documents/activities"""
        # For now, just get all and sort by created_at in metadata
        # ChromaDB doesn't have native date filtering yet
        results = self.rag_engine.query("", n_results=n_results * 2)
        
        # Sort by created_at if available
        def get_created_at(result):
            try:
                return datetime.fromisoformat(result.metadata.get('created_at', '1900-01-01'))
            except:
                return datetime(1900, 1, 1)
        
        sorted_results = sorted(results, key=get_created_at, reverse=True)
        return sorted_results[:n_results]
    
    def get_project_status_summary(self, project_name: str) -> Dict[str, Any]:
        """Get a comprehensive status summary for a project"""
        project_docs = self.search_by_project(project_name, n_results=50)
        
        if not project_docs:
            return {"error": f"No documents found for project: {project_name}"}
        
        # Analyze document types
        doc_types = {}
        latest_update = None
        priorities = {"high": 0, "medium": 0, "low": 0}
        statuses = {}
        
        for doc in project_docs:
            doc_type = doc.metadata.get('doc_type', 'unknown')
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            priority = doc.metadata.get('priority', '').lower()
            if priority in priorities:
                priorities[priority] += 1
                
            status = doc.metadata.get('status', 'unknown')
            statuses[status] = statuses.get(status, 0) + 1
            
            # Track latest update
            try:
                created_at = datetime.fromisoformat(doc.metadata.get('created_at', '1900-01-01'))
                if not latest_update or created_at > latest_update:
                    latest_update = created_at
            except:
                pass
        
        return {
            "project_name": project_name,
            "total_documents": len(project_docs),
            "document_types": doc_types,
            "priority_breakdown": priorities,
            "status_breakdown": statuses,
            "latest_update": latest_update.isoformat() if latest_update else None,
            "recent_documents": [
                {
                    "title": doc.metadata.get('title', 'Untitled'),
                    "type": doc.metadata.get('doc_type', 'unknown'),
                    "preview": doc.content[:100] + "..." if len(doc.content) > 100 else doc.content
                }
                for doc in project_docs[:3]
            ]
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        return self.rag_engine.get_stats()