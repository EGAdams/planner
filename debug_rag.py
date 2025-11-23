import sys
import os
import asyncio

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from rag_system.core.document_manager import DocumentManager

async def main():
    dm = DocumentManager()
    
    print("Searching for artifacts with query 'to:board topic:planner-agent'...")
    results = dm.search_artifacts(query="to:board topic:planner-agent", n_results=20)
    
    print(f"Found {len(results)} results.")
    for res in results:
        print(f"ID: {res.document_id}")
        print(f"Content: {res.content[:100]}...")
        print(f"Metadata: {res.metadata}")
        print("-" * 20)

    print("\nSearching specifically for 'to:board'...")
    results = dm.search_artifacts(query="to:board", n_results=20)
    print(f"Found {len(results)} results.")

if __name__ == "__main__":
    asyncio.run(main())
