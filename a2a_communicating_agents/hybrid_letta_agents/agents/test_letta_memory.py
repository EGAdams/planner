#!/usr/bin/env python3
"""
Test Letta's memory functionality by sending multiple messages to the same agent.
"""

import os
from letta_client import Letta

def test_memory():
    """Test if Letta remembers context across multiple messages."""
    base_url = os.environ.get("LETTA_BASE_URL", "http://localhost:8283")
    print(f"Connecting to Letta at {base_url}...")

    client = Letta(base_url=base_url)

    # Create agent with memory blocks
    print("\n1. Creating agent with memory blocks...")
    agent = client.agents.create(
        model=os.environ.get("ORCH_MODEL", "openai/gpt-4o-mini"),
        embedding="openai/text-embedding-3-small",
        memory_blocks=[
            {
                "label": "role",
                "value": "You are a helpful assistant with memory. You remember user preferences and previous conversations.",
                "limit": 2000,
            },
            {
                "label": "conversation_history",
                "value": "No conversations yet.",
                "limit": 3000,
            },
        ],
        tools=[],
    )
    print(f"✓ Agent created: {agent.id}")

    # Message 1: Tell agent about a preference
    print("\n2. Sending first message (establishing context)...")
    response1 = client.agents.messages.create(
        agent_id=agent.id,
        messages=[{"role": "user", "content": "My favorite color is blue and I love Python programming."}],
        timeout=30,
    )

    print("\n=== Response 1 ===")
    for msg in response1.messages:
        if getattr(msg, "message_type", None) == "assistant_message":
            print(f"Assistant: {msg.content}")

    # Message 2: Ask if it remembers
    print("\n3. Sending second message (testing memory)...")
    response2 = client.agents.messages.create(
        agent_id=agent.id,
        messages=[{"role": "user", "content": "What's my favorite color?"}],
        timeout=30,
    )

    print("\n=== Response 2 ===")
    remembered = False
    for msg in response2.messages:
        if getattr(msg, "message_type", None) == "assistant_message":
            content = msg.content
            print(f"Assistant: {content}")
            if "blue" in content.lower():
                remembered = True

    # Message 3: Ask about programming preference
    print("\n4. Sending third message (testing memory again)...")
    response3 = client.agents.messages.create(
        agent_id=agent.id,
        messages=[{"role": "user", "content": "What programming language did I say I love?"}],
        timeout=30,
    )

    print("\n=== Response 3 ===")
    remembered_python = False
    for msg in response3.messages:
        if getattr(msg, "message_type", None) == "assistant_message":
            content = msg.content
            print(f"Assistant: {content}")
            if "python" in content.lower():
                remembered_python = True

    # Check memory blocks directly
    print("\n5. Checking memory blocks directly...")
    try:
        # Get agent details to inspect memory
        agent_info = client.agents.get(agent_id=agent.id)
        print(f"\nAgent memory blocks:")
        if hasattr(agent_info, 'memory_blocks'):
            for block in agent_info.memory_blocks:
                print(f"\n  [{block.label}]:")
                print(f"  {block.value[:200]}...")  # First 200 chars
        elif hasattr(agent_info, 'memory'):
            print(f"  Memory: {agent_info.memory}")
    except Exception as e:
        print(f"  Could not retrieve memory blocks: {e}")

    # Summary
    print("\n" + "="*70)
    print("MEMORY TEST RESULTS")
    print("="*70)

    if remembered and remembered_python:
        print("✅ SUCCESS: Letta memory is WORKING!")
        print("   - Agent remembered favorite color (blue)")
        print("   - Agent remembered programming language (Python)")
        return True
    elif remembered or remembered_python:
        print("⚠️  PARTIAL: Letta memory is partially working")
        print(f"   - Remembered color: {remembered}")
        print(f"   - Remembered Python: {remembered_python}")
        return False
    else:
        print("❌ FAILED: Letta memory is NOT working")
        print("   - Agent did not remember previous context")
        return False

if __name__ == "__main__":
    test_memory()
