#!/usr/bin/env python3
"""
Test Letta Client Direct Integration
=====================================
Validates letta_client package works with Letta server.
"""

import asyncio
import os
from dotenv import load_dotenv
from letta_client import Letta

# Load environment
load_dotenv("/home/adamsl/planner/.env")

async def main():
    print("\n" + "="*60)
    print("LETTA CLIENT DIRECT TEST")
    print("="*60)

    base_url = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")
    print(f"Connecting to: {base_url}\n")

    try:
        # Initialize client
        client = Letta(base_url=base_url)
        print("✅ Letta client initialized")

        # List agents (wrapped in asyncio.to_thread for async compatibility)
        print("\nListing agents...")
        # Avoid iterator-based pagination because the local server currently 500s on
        # follow-up page requests when using the client helper's __iter__.
        agents_page = await asyncio.to_thread(client.agents.list)
        agents = list(agents_page.items)

        print(f"✅ Found {len(agents)} agents:")
        for agent in agents[:5]:  # Show first 5
            print(f"   - {agent.name} (ID: {agent.id[:16]}...)")

        # Create test agent
        print("\nCreating test agent...")
        test_agent = await asyncio.to_thread(
            client.agents.create,
            name="livekit_test_agent",
            # Use Letta's built-in free models to avoid external provider issues
            model="letta/letta-free",
            embedding="letta/letta-free",
            memory_blocks=[
                {"label": "persona", "value": "I am a test agent for Livekit integration."}
            ]
        )
        print(f"✅ Test agent created: {test_agent.id}")

        # Send test message
        print("\nSending test message...")
        response = await asyncio.to_thread(
            client.agents.messages.create,
            agent_id=test_agent.id,
            messages=[{"role": "user", "content": "Hello! Can you confirm you're working?"}]
        )

        # Extract response
        assistant_messages = [
            msg.text for msg in response.messages
            if hasattr(msg, 'role') and msg.role == "assistant" and hasattr(msg, 'text')
        ]

        if assistant_messages:
            print(f"✅ Received response:")
            print(f"   '{assistant_messages[0][:150]}...'")
        else:
            print("⚠️  No assistant response found")

        # Cleanup
        print("\nCleaning up test agent...")
        await asyncio.to_thread(client.agents.delete, agent_id=test_agent.id)
        print("✅ Test agent deleted")

        print("\n" + "="*60)
        print("🎉 ALL TESTS PASSED!")
        print("="*60)
        print("\nLetta client integration is working correctly.")
        print("The voice agent should be able to communicate with Letta.")

        return 0

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
