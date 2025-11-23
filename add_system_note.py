
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag_system.core.document_manager import DocumentManager

print("Initializing DocumentManager...")
dm = DocumentManager()

note = """
**SYSTEM ALERT**: Direct Messaging (Letta) is currently OFFLINE.
**Status**: Fallback mode active.
**Instruction**: All agents must use the Message Board (RAG) for communication until further notice.
**Reason**: Letta server executable not found.
"""

print("Adding system note...")
doc_id = dm.add_runtime_artifact(
    artifact_text=note, 
    artifact_type="system_status", 
    source="admin", 
    tags=["urgent", "protocol", "system_status"]
)
print(f"✅ System note added with ID: {doc_id}")
