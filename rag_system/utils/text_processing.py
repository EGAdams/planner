"""
Text processing utilities for the RAG system
"""

import re
from typing import List, Dict, Any
from pathlib import Path

def clean_text(text: str) -> str:
    """Clean and normalize text for processing"""
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    # Remove leading/trailing whitespace
    text = text.strip()
    return text

def extract_markdown_sections(text: str) -> Dict[str, str]:
    """Extract sections from markdown text based on headers"""
    sections = {}
    current_section = "content"
    current_text = []
    
    lines = text.split('\n')
    for line in lines:
        # Check for markdown headers
        header_match = re.match(r'^(#{1,6})\s+(.*)', line)
        if header_match:
            # Save previous section
            if current_text:
                sections[current_section] = clean_text('\n'.join(current_text))
            
            # Start new section
            current_section = header_match.group(2).lower().replace(' ', '_')
            current_text = []
        else:
            current_text.append(line)
    
    # Save final section
    if current_text:
        sections[current_section] = clean_text('\n'.join(current_text))
    
    return sections

def extract_tags_from_text(text: str) -> List[str]:
    """Extract hashtag-style tags from text"""
    # Find hashtags
    hashtags = re.findall(r'#(\w+)', text)
    
    # Find @ mentions (could be client/project names)
    mentions = re.findall(r'@(\w+)', text)
    
    # Combine and clean
    tags = list(set(hashtags + mentions))
    return [tag.lower() for tag in tags]

def detect_document_type_from_content(text: str, filename: str = "") -> str:
    """Heuristically detect document type from content and filename"""
    text_lower = text.lower()
    filename_lower = filename.lower()
    
    # Check filename patterns first
    if any(word in filename_lower for word in ['client', 'profile']):
        return "client_profile"
    elif any(word in filename_lower for word in ['meeting', 'notes']):
        return "meeting_notes"
    elif any(word in filename_lower for word in ['task', 'todo', 'update']):
        return "task_update"
    elif any(word in filename_lower for word in ['project', 'spec', 'requirements']):
        return "project_details"
    
    # Check content patterns
    if any(phrase in text_lower for phrase in ['client:', 'contact:', 'company:']):
        return "client_profile"
    elif any(phrase in text_lower for phrase in ['meeting with', 'discussed', 'action items']):
        return "meeting_notes"
    elif any(phrase in text_lower for phrase in ['task:', 'todo:', 'completed:', 'status:']):
        return "task_update"
    elif any(phrase in text_lower for phrase in ['project:', 'requirements:', 'scope:']):
        return "project_details"
    elif any(phrase in text_lower for phrase in ['decided', 'decision:', 'agreed']):
        return "decision_log"
    elif any(phrase in text_lower for phrase in ['def ', 'function', 'class ', '```']):
        return "code_snippet"
    
    return "conversation"  # Default fallback

def parse_metadata_from_text(text: str) -> Dict[str, Any]:
    """Extract metadata from text using common patterns"""
    metadata = {}
    
    # Look for key-value patterns
    patterns = {
        'client': r'client[:\s]+([^\n]+)',
        'project': r'project[:\s]+([^\n]+)', 
        'priority': r'priority[:\s]+([^\n]+)',
        'status': r'status[:\s]+([^\n]+)',
        'date': r'date[:\s]+([^\n]+)',
        'deadline': r'deadline[:\s]+([^\n]+)'
    }
    
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            metadata[key] = match.group(1).strip()
    
    return metadata