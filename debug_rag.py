
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Importing RAGEngine...")
from rag_system.core.rag_engine import RAGEngine
print("Imported RAGEngine.")

print("Initializing RAGEngine...")
try:
    rag = RAGEngine()
    print("RAGEngine initialized successfully.")
except Exception as e:
    print(f"RAGEngine initialization failed: {e}")
