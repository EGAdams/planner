#!/usr/bin/env python3
"""Test agent API and selector functionality"""

import sys
sys.path.insert(0, '/home/adamsl/planner')

from letta_client import Letta
import os
from dotenv import load_dotenv

# Load environment
load_dotenv('/home/adamsl/planner/.env')

def main():
    print("🧪 Testing Letta Agent API")
    print("=" * 50)
    print()

    # Initialize client
    print("1. Connecting to Letta server...")
    try:
        letta_client = Letta(base_url="http://localhost:8283")
        print("   ✅ Connected to http://localhost:8283")
    except Exception as e:
        print(f"   ❌ Failed to connect: {e}")
        return 1

    # List agents
    print()
    print("2. Fetching agent list...")
    try:
        agents = list(letta_client.agents.list())
        print(f"   ✅ Found {len(agents)} agents")
    except Exception as e:
        print(f"   ❌ Failed to list agents: {e}")
        return 1

    # Show sample agents
    print()
    print("3. Sample agents:")
    for i, agent in enumerate(agents[:10]):
        name = agent.name or "Unnamed"
        agent_id = agent.id
        print(f"   {i+1}. {name[:30]:30} | {agent_id}")

    if len(agents) > 10:
        print(f"   ... and {len(agents) - 10} more")

    # Check for voice_orchestrator
    print()
    print("4. Checking for voice_orchestrator...")
    orchestrator = next((a for a in agents if a.name == "voice_orchestrator"), None)
    if orchestrator:
        print(f"   ✅ Found: {orchestrator.id}")
        print(f"      Model: {orchestrator.llm_config.model if orchestrator.llm_config else 'Unknown'}")
        # Note: memory_blocks not available in list response, only in get response
    else:
        print("   ⚠️  voice_orchestrator not found")

    # Test that we can work with agents
    print()
    print("5. Testing agent access...")
    if agents:
        test_agent = agents[0]
        print(f"   ✅ Can access agent attributes: {test_agent.name}")
        print(f"      ID: {test_agent.id}")
        print(f"      Created: {test_agent.created_at}")
    else:
        print("   ❌ No agents available to test")
        return 1

    print()
    print("=" * 50)
    print("✅ All tests passed!")
    print()
    print("🎙️  Open browser to test voice interface:")
    print("   http://localhost:8888/voice-agent-selector.html")
    print()

    return 0

if __name__ == "__main__":
    sys.exit(main())
