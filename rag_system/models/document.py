"""
Document models for the RAG system
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

class DocumentType(str, Enum):
    """Types of documents in the project management system"""
    CLIENT_PROFILE = "client_profile"
    PROJECT_DETAILS = "project_details"
    MEETING_NOTES = "meeting_notes"
    TASK_UPDATE = "task_update"
    DECISION_LOG = "decision_log"
    CODE_SNIPPET = "code_snippet"
    TEMPLATE = "template"
    CONVERSATION = "conversation"

class Document(BaseModel):
    """A document to be stored in the RAG system"""
    id: Optional[str] = None
    title: str
    content: str
    doc_type: DocumentType
    metadata: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    # Project management specific fields
    client_name: Optional[str] = None
    project_name: Optional[str] = None
    priority: Optional[str] = None  # high, medium, low
    status: Optional[str] = None    # active, completed, blocked, etc.
    
class DocumentChunk(BaseModel):
    """A chunk of a document for RAG retrieval"""
    chunk_id: str
    document_id: str
    content: str
    chunk_index: int
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
class QueryResult(BaseModel):
    """Result from a RAG query"""
    content: str
    score: float
    document_id: str
    chunk_id: str
    metadata: Dict[str, Any] = Field(default_factory=dict)