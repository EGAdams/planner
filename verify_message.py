
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag_system.core.document_manager import DocumentManager

print("Initializing DocumentManager...")
dm = DocumentManager()
print(f"Storage Path: {dm.rag_engine.storage_path}")

print("Getting recent activities...")
results = dm.get_recent_activities(n_results=20)

found = False
for res in results:
    print(f"Found artifact: {res.metadata.get('title')} - {res.content[:50]}...")
    if "Hello orchestrator" in res.content:
        print("✅ FOUND MY MESSAGE!")
        found = True

if not found:
    print("❌ Message NOT found.")
