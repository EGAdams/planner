#!/usr/bin/env python3
"""
Debug script to show exactly what the Letta API returns for Agent_66's memory
"""

import os
import asyncio
from letta_client import AsyncLetta

AGENT_ID = "agent-4dfca708-49a8-4982-8e36-0f1146f9a66e"
LETTA_BASE_URL = "http://localhost:8283"

async def main():
    print(f"🔍 Debugging Agent_66 Memory Structure")
    print(f"=" * 60)
    print(f"Agent ID: {AGENT_ID}")
    print(f"Letta URL: {LETTA_BASE_URL}\n")

    # Initialize client
    client = AsyncLetta(base_url=LETTA_BASE_URL)

    # Retrieve agent
    print("📡 Retrieving agent from Letta...")
    agent = await client.agents.retrieve(agent_id=AGENT_ID)
    print(f"✅ Retrieved agent: {agent.name}\n")

    # Check memory attribute
    print("🧠 Checking agent.memory attribute:")
    print(f"   - hasattr(agent, 'memory'): {hasattr(agent, 'memory')}")
    if hasattr(agent, 'memory'):
        print(f"   - type(agent.memory): {type(agent.memory)}")
        print(f"   - bool(agent.memory): {bool(agent.memory)}")
        print(f"   - agent.memory: {agent.memory}\n")

        # Check for .blocks attribute
        print("📦 Checking for .blocks attribute:")
        print(f"   - hasattr(agent.memory, 'blocks'): {hasattr(agent.memory, 'blocks')}")

        if hasattr(agent.memory, 'blocks'):
            blocks = agent.memory.blocks
            print(f"   - type(agent.memory.blocks): {type(blocks)}")
            print(f"   - len(agent.memory.blocks): {len(blocks)}")
            print()

            print("📋 Memory Blocks:")
            for i, block in enumerate(blocks):
                print(f"\n   Block {i+1}:")
                print(f"     - type: {type(block)}")
                print(f"     - hasattr 'label': {hasattr(block, 'label')}")
                print(f"     - hasattr 'value': {hasattr(block, 'value')}")
                if hasattr(block, 'label'):
                    print(f"     - label: {block.label}")
                if hasattr(block, 'value'):
                    value_preview = block.value[:100] + "..." if len(block.value) > 100 else block.value
                    print(f"     - value: {value_preview}")
        else:
            print("   ⚠️  No .blocks attribute found!")
            print(f"   - Trying to iterate directly over agent.memory...")
            try:
                count = 0
                for item in agent.memory:
                    count += 1
                    print(f"     Item {count}: {item}")
                    if count >= 3:
                        print("     (stopping at 3 items)")
                        break
            except Exception as e:
                print(f"     ❌ Cannot iterate: {e}")
    else:
        print("   ❌ No memory attribute found on agent!")

    print("\n" + "=" * 60)
    print("🏁 Debug complete")

if __name__ == "__main__":
    asyncio.run(main())
