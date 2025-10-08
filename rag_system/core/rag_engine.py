"""
Core RAG engine using ChromaDB and sentence-transformers
"""

import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import uuid
import os
import math
from pathlib import Path
from datetime import datetime

from ..models.document import Document, DocumentChunk, QueryResult, DocumentType

class RAGEngine:
    """Main RAG engine for project management memory"""
    
    def __init__(self, storage_path: str = "./storage/chromadb", model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize the RAG engine
        
        Args:
            storage_path: Path to store ChromaDB data
            model_name: Sentence transformer model name
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.storage_path),
            settings=Settings(allow_reset=True)
        )
        
        # Initialize embedding model
        self.embedding_model = SentenceTransformer(model_name)
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="project_memory",
            metadata={"description": "Project management documents and context"}
        )
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            chunk_size: Maximum characters per chunk
            overlap: Character overlap between chunks
            
        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at word boundary
            if end < len(text):
                last_space = chunk.rfind(' ')
                if last_space > chunk_size * 0.7:  # Don't break too early
                    chunk = chunk[:last_space]
                    end = start + last_space
            
            chunks.append(chunk.strip())
            start = end - overlap
            
        return chunks
    
    def add_document(self, document: Document) -> str:
        """
        Add a document to the RAG system
        
        Args:
            document: Document to add
            
        Returns:
            Document ID
        """
        if not document.id:
            document.id = str(uuid.uuid4())
        
        # Chunk the document
        chunks = self._chunk_text(document.content)
        
        # Prepare data for ChromaDB
        chunk_ids = []
        chunk_texts = []
        chunk_metadatas = []
        
        for i, chunk_text in enumerate(chunks):
            chunk_id = f"{document.id}_chunk_{i}"
            chunk_ids.append(chunk_id)
            chunk_texts.append(chunk_text)
            
            # Combine document metadata with chunk-specific info
            chunk_metadata = {
                "document_id": document.id,
                "title": document.title,
                "doc_type": document.doc_type.value,
                "chunk_index": i,
                "created_at": document.created_at.isoformat(),
                "client_name": document.client_name or "",
                "project_name": document.project_name or "",
                "priority": document.priority or "",
                "status": document.status or "",
                "tags": ",".join(document.tags),
                "artifact_type": document.artifact_type or "",
                "source": document.source or "",
                "file_path": document.file_path or "",
                **document.metadata
            }
            chunk_metadatas.append(chunk_metadata)
        
        # Add to ChromaDB
        self.collection.add(
            ids=chunk_ids,
            documents=chunk_texts,
            metadatas=chunk_metadatas
        )
        
        return document.id
    
    def _calculate_time_decay(self, timestamp_iso: str) -> float:
        """
        Calculate time decay factor for artifact ranking
        Based on Letta's approach: ~0.1 decay per 7 days

        Args:
            timestamp_iso: ISO format timestamp string

        Returns:
            Decay factor between 0 and 1
        """
        try:
            created_at = datetime.fromisoformat(timestamp_iso)
            now = datetime.now()
            days_old = (now - created_at).total_seconds() / (60 * 60 * 24)
            # Exponential decay: 0.1 decay per 7 days
            decay = math.exp(-0.1 * (days_old / 7))
            return decay
        except (ValueError, AttributeError):
            return 0.5  # Default moderate decay if parsing fails

    def _apply_artifact_boosting(self, results: List[QueryResult]) -> List[QueryResult]:
        """
        Apply time-decay and tag-based boosting to artifact results
        Based on Letta's scoring: overlap(70%) + recency(25%) + tag_bonus(+0.10)

        Args:
            results: Initial query results

        Returns:
            Re-scored and re-sorted results
        """
        boosted_results = []

        for result in results:
            base_score = result.score
            artifact_type = result.metadata.get('artifact_type', '')
            created_at = result.metadata.get('created_at', '')

            # Apply time decay if it's a runtime artifact
            if artifact_type:
                recency_score = self._calculate_time_decay(created_at)

                # Tag boost for important artifact types
                tag_boost = 0.0
                if artifact_type in ['error', 'fix', 'decision', 'test_failure']:
                    tag_boost = 0.10

                # Blend scores: overlap(70%) + recency(25%) + tag_boost
                adjusted_score = (base_score * 0.70) + (recency_score * 0.25) + tag_boost
                result.score = min(adjusted_score, 1.0)  # Cap at 1.0

            boosted_results.append(result)

        # Re-sort by adjusted scores
        boosted_results.sort(key=lambda r: r.score, reverse=True)
        return boosted_results

    def query(self, query_text: str, n_results: int = 5,
              filter_dict: Optional[Dict[str, Any]] = None,
              apply_artifact_boosting: bool = True) -> List[QueryResult]:
        """
        Query the RAG system with optional artifact boosting

        Args:
            query_text: Query string
            n_results: Number of results to return
            filter_dict: Optional metadata filters
            apply_artifact_boosting: Apply time-decay and tag boosting for artifacts

        Returns:
            List of QueryResult objects
        """
        # Query ChromaDB - get more results for re-ranking
        fetch_count = n_results * 2 if apply_artifact_boosting else n_results

        results = self.collection.query(
            query_texts=[query_text],
            n_results=fetch_count,
            where=filter_dict
        )

        # Convert to QueryResult objects
        query_results = []
        if results['ids'] and results['ids'][0]:  # Check if we have results
            for i in range(len(results['ids'][0])):
                result = QueryResult(
                    content=results['documents'][0][i],
                    score=1.0 - results['distances'][0][i],  # Convert distance to similarity
                    document_id=results['metadatas'][0][i]['document_id'],
                    chunk_id=results['ids'][0][i],
                    metadata=results['metadatas'][0][i]
                )
                query_results.append(result)

        # Apply artifact-specific boosting if enabled
        if apply_artifact_boosting and query_results:
            query_results = self._apply_artifact_boosting(query_results)

        # Return top n_results after boosting
        return query_results[:n_results]
    
    def get_document_by_id(self, document_id: str) -> Optional[List[QueryResult]]:
        """Get all chunks for a specific document"""
        return self.query("", filter_dict={"document_id": document_id}, n_results=100)
    
    def delete_document(self, document_id: str) -> bool:
        """Delete a document and all its chunks"""
        try:
            # Get all chunk IDs for this document
            results = self.collection.get(where={"document_id": document_id})
            if results['ids']:
                self.collection.delete(ids=results['ids'])
            return True
        except Exception:
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        count = self.collection.count()
        
        # Get document types breakdown
        all_metadata = self.collection.get()['metadatas']
        doc_types = {}
        clients = set()
        projects = set()
        
        for metadata in all_metadata:
            doc_type = metadata.get('doc_type', 'unknown')
            doc_types[doc_type] = doc_types.get(doc_type, 0) + 1
            
            if metadata.get('client_name'):
                clients.add(metadata['client_name'])
            if metadata.get('project_name'):
                projects.add(metadata['project_name'])
        
        return {
            "total_chunks": count,
            "unique_clients": len(clients),
            "unique_projects": len(projects),
            "document_types": doc_types,
            "storage_path": str(self.storage_path)
        }