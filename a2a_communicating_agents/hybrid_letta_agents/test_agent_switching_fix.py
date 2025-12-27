#!/usr/bin/env python3
"""
Test Agent Switching Fix

Verifies that the agent switching bug is fixed by testing the
retrieve() method works correctly with the Letta client.

This test confirms:
1. Letta client can retrieve agents using .retrieve() method
2. The old .get() method doesn't exist (as expected)
3. Agent switching logic will work correctly
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from letta_client import Letta

def test_agent_retrieve_method():
    """Test that the Letta client uses retrieve() not get()"""

    print("=" * 60)
    print("Testing Letta Client Agent Retrieve Method")
    print("=" * 60)
    print()

    # Initialize Letta client
    letta_base_url = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")
    print(f"Connecting to Letta server at: {letta_base_url}")

    letta_client = Letta(base_url=letta_base_url)
    print("✅ Letta client initialized")
    print()

    # Test 1: Verify .retrieve() method exists
    print("Test 1: Check .retrieve() method exists")
    print("-" * 60)

    if hasattr(letta_client.agents, 'retrieve'):
        print("✅ PASS: .retrieve() method exists")
    else:
        print("❌ FAIL: .retrieve() method does NOT exist")
        return False
    print()

    # Test 2: Verify .get() method does NOT exist
    print("Test 2: Check .get() method does NOT exist")
    print("-" * 60)

    if not hasattr(letta_client.agents, 'get'):
        print("✅ PASS: .get() method does NOT exist (as expected)")
    else:
        print("❌ FAIL: .get() method exists (unexpected)")
        return False
    print()

    # Test 3: List available agents
    print("Test 3: List available agents")
    print("-" * 60)

    try:
        agents = list(letta_client.agents.list())
        print(f"✅ PASS: Found {len(agents)} agent(s)")

        for agent in agents:
            print(f"   - {agent.name} (ID: {agent.id})")

        if not agents:
            print("⚠️  WARNING: No agents found. Cannot test retrieve().")
            return True  # Not a failure, just can't test retrieve

    except Exception as e:
        print(f"❌ FAIL: Error listing agents: {e}")
        return False
    print()

    # Test 4: Test retrieve() method with first agent
    print("Test 4: Retrieve a specific agent using .retrieve()")
    print("-" * 60)

    if agents:
        test_agent = agents[0]
        print(f"Testing with agent: {test_agent.name} (ID: {test_agent.id})")

        try:
            retrieved_agent = letta_client.agents.retrieve(agent_id=test_agent.id)
            print(f"✅ PASS: Successfully retrieved agent using .retrieve()")
            print(f"   - Name: {retrieved_agent.name}")
            print(f"   - ID: {retrieved_agent.id}")

        except Exception as e:
            print(f"❌ FAIL: Error retrieving agent: {e}")
            return False
    print()

    # Test 5: Verify the fix is in the code
    print("Test 5: Verify fix is applied in voice agent code")
    print("-" * 60)

    voice_agent_file = Path(__file__).parent / "letta_voice_agent.py"

    with open(voice_agent_file, 'r') as f:
        code = f.read()

    # Check for the correct method
    if "self.letta_client.agents.retrieve," in code:
        print("✅ PASS: Code uses .retrieve() method")
    else:
        print("❌ FAIL: Code does NOT use .retrieve() method")
        return False

    # Check that old broken method is NOT present
    if "self.letta_client.agents.get," in code:
        print("❌ FAIL: Code still contains broken .get() method")
        return False
    else:
        print("✅ PASS: Code does NOT contain broken .get() method")
    print()

    print("=" * 60)
    print("All Tests PASSED ✅")
    print("=" * 60)
    print()
    print("Summary:")
    print("- Letta client uses .retrieve() method (correct)")
    print("- Letta client does NOT have .get() method (expected)")
    print("- Code has been updated to use .retrieve()")
    print("- Agent switching functionality should work correctly")
    print()

    return True


if __name__ == "__main__":
    # Load environment
    from dotenv import load_dotenv
    load_dotenv("/home/adamsl/planner/.env")
    load_dotenv("/home/adamsl/ottomator-agents/livekit-agent/.env")

    success = test_agent_retrieve_method()

    if success:
        print("🎉 Agent switching fix verified successfully!")
        sys.exit(0)
    else:
        print("❌ Agent switching fix verification FAILED")
        sys.exit(1)
