#!/usr/bin/env python3
"""List all Letta agents from the local Letta server"""

import os
from letta_client import Letta

# Instantiate the Letta client with the local letta server address
letta_server_base_url = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")
print(f"Connecting to: {letta_server_base_url}")

client = Letta(base_url=letta_server_base_url)

# Call the list_agents method
try:
    response = client.agents.list(limit=50)

    # Iterate through the paginated response
    print("\nLetta Agents:")
    print("=" * 60)

    agent_count = 0
    for agent in response:
        agent_count += 1
        # AgentState object has attributes, not dict keys
        print(f"{agent_count}. Name: {agent.name}")
        print(f"   ID: {agent.id}")
        print(f"   Description: {getattr(agent, 'description', 'N/A')}")
        print("-" * 60)

    if agent_count == 0:
        print("No agents found.")
    else:
        print(f"\nTotal agents: {agent_count}")

except Exception as e:
    print(f"Error listing agents: {e}")
    import traceback
    traceback.print_exc()
