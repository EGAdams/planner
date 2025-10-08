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
    RUNTIME_ARTIFACT = "runtime_artifact"  # For errors, logs, CI output

class ArtifactType(str, Enum):
    """Types of runtime artifacts"""
    ERROR = "error"
    RUNLOG = "runlog"
    FIX = "fix"
    DECISION = "decision"
    CI_OUTPUT = "ci_output"
    TEST_FAILURE = "test_failure"
    PR_NOTES = "pr_notes"

    # Performance & monitoring
    PERFORMANCE_LOG = "performance_log"
    SLOW_QUERY = "slow_query"
    MEMORY_SPIKE = "memory_spike"

    # Dependencies & compatibility
    DEPENDENCY_ISSUE = "dependency_issue"
    VERSION_CONFLICT = "version_conflict"
    BREAKING_CHANGE = "breaking_change"

    # Deployment & operations
    DEPLOYMENT_NOTE = "deployment_note"
    ROLLBACK = "rollback"
    CONFIG_CHANGE = "config_change"

    # Code patterns & gotchas
    GOTCHA = "gotcha"
    WORKAROUND = "workaround"
    ANTI_PATTERN = "anti_pattern"
    BEST_PRACTICE = "best_practice"

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

    # Runtime artifact specific fields
    artifact_type: Optional[str] = None  # error, runlog, fix, decision, etc.
    source: Optional[str] = None  # pytest, CI, review, etc.
    file_path: Optional[str] = None  # Associated file for artifact
    
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