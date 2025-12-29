#!/usr/bin/env python3
"""Inspect Agent_66's full memory configuration."""
import asyncio
from letta_client import AsyncLetta

async def inspect_agent():
    client = AsyncLetta(base_url="http://localhost:8283")
    agent_id = "agent-4dfca708-49a8-4982-8e36-0f1146f9a66e"
    
    print(f"Retrieving agent: {agent_id}")
    agent = await client.agents.retrieve(agent_id=agent_id)
    
    print(f"\nAgent Name: {agent.name}")
    print(f"Agent ID: {agent.id}")
    
    print("\n=== Memory Object ===")
    print(f"Type: {type(agent.memory)}")
    print(f"Has blocks attr: {hasattr(agent.memory, 'blocks')}")
    
    if hasattr(agent.memory, 'blocks'):
        print(f"Blocks type: {type(agent.memory.blocks)}")
        print(f"Number of blocks: {len(agent.memory.blocks)}")
        
        if len(agent.memory.blocks) == 0:
            print("\n⚠️  WARNING: Agent has no memory blocks!")
            print("This agent needs memory blocks to be created.")
        else:
            print("\nMemory Blocks:")
            for i, block in enumerate(agent.memory.blocks):
                print(f"\n  Block {i+1}:")
                print(f"    Label: {block.label if hasattr(block, 'label') else 'N/A'}")
                if hasattr(block, 'value'):
                    value = str(block.value)[:200]
                    print(f"    Value: {value}...")
    
    # Check raw memory dict
    print("\n=== Raw Memory Dict ===")
    if hasattr(agent.memory, '__dict__'):
        for key, val in agent.memory.__dict__.items():
            print(f"{key}: {type(val).__name__} = {str(val)[:100]}")

if __name__ == "__main__":
    asyncio.run(inspect_agent())
