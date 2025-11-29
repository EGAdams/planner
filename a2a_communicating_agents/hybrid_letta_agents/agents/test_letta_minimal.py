"""
Minimal test to debug Letta agent creation issue.
"""
import os
from dotenv import load_dotenv
load_dotenv()

from letta_client import Letta

def test_letta_connection():
    """Test basic Letta connectivity and agent creation."""
    
    print("=" * 60)
    print("LETTA SERVER CONNECTION TEST")
    print("=" * 60)
    
    # Create client
    base_url = os.getenv("LETTA_BASE_URL", "http://localhost:8283")
    print(f"\n1. Connecting to Letta server at: {base_url}")
    
    try:
        client = Letta(base_url=base_url)
        print("   ✅ Client created successfully")
    except Exception as e:
        print(f"   ❌ Failed to create client: {e}")
        return
    
    # Try to list existing agents
    print("\n2. Attempting to list existing agents...")
    try:
        agents_page = client.agents.list()
        # Handle pagination - convert to list
        agents = list(agents_page)
        print(f"   ✅ Found {len(agents)} existing agents")
        if agents:
            for agent in agents[:3]:  # Show first 3
                print(f"      - {agent.id}: {agent.name}")
    except Exception as e:
        print(f"   ❌ Failed to list agents: {e}")
        return
    
    # Try to list available models
    print("\n3. Attempting to list available models...")
    try:
        models_page = client.models.list()
        models = list(models_page)
        print(f"   ✅ Found {len(models)} available models")
        if models:
            for model in models[:5]:  # Show first 5
                print(f"      - {model}")
    except Exception as e:
        print(f"   ⚠️  Failed to list models: {e}")
    
    # Try minimal agent creation
    print("\n4. Attempting to create minimal agent...")
    try:
        agent = client.agents.create(
            name="test_minimal_agent",
        )
        print(f"   ✅ Successfully created agent: {agent.id}")
        
        # Clean up
        print("\n5. Cleaning up test agent...")
        client.agents.delete(agent_id=agent.id)
        print("   ✅ Test agent deleted")
        
    except Exception as e:
        print(f"   ❌ Failed to create agent: {e}")
        print(f"\n   Error type: {type(e).__name__}")
        print(f"   Error details: {str(e)}")
        
        # Try to get more details from the exception
        if hasattr(e, 'response'):
            print(f"\n   Response status: {e.response.status_code}")
            print(f"   Response body: {e.response.text[:500]}")
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    test_letta_connection()
