#!/usr/bin/env python3
"""
Simple Letta test - verify basic communication without complex TDD workflow.
This should respond in seconds, not minutes.
"""

import os
from letta_client import Letta

def test_simple_interaction():
    """Test a simple interaction to verify Letta is working."""
    base_url = os.environ.get("LETTA_BASE_URL", "http://localhost:8283")
    print(f"Connecting to Letta at {base_url}...")

    client = Letta(base_url=base_url)
    print("✓ Connected to Letta")

    # Create a simple agent with no tools
    print("Creating test agent...")
    agent = client.agents.create(
        model=os.environ.get("ORCH_MODEL", "openai/gpt-4o-mini"),
        embedding="openai/text-embedding-3-small",
        memory_blocks=[
            {
                "label": "role",
                "value": "You are a helpful assistant. Keep responses brief.",
                "limit": 1000,
            }
        ],
        tools=[],  # No tools for simple test
    )
    print(f"✓ Created agent: {agent.id}")

    # Send a simple message
    print("\nSending simple message...")
    print("(This should respond in ~5-10 seconds)")

    try:
        response = client.agents.messages.create(
            agent_id=agent.id,
            messages=[{"role": "user", "content": "Say hello in one sentence."}],
            timeout=30,  # Should be way faster than this
        )

        print("\n=== Response ===")
        for msg in response.messages:
            mtype = getattr(msg, "message_type", None)
            if mtype == "assistant_message":
                print(f"Assistant: {msg.content}")

        print("\n✅ Simple test PASSED - Letta is working")
        return True

    except Exception as e:
        print(f"\n❌ Simple test FAILED: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    test_simple_interaction()
