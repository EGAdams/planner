#!/usr/bin/env python3
"""Quick preview of Agent_66 cleanup"""
import os
from letta_client import Letta
from dotenv import load_dotenv

load_dotenv("/home/adamsl/planner/.env", override=True)

LETTA_BASE_URL = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")
KEEP_AGENT_ID = "agent-4dfca708-49a8-4982-8e36-0f1146f9a66e"

print("=" * 70)
print("  Agent_66 Cleanup Preview (DRY RUN)")
print("=" * 70)
print()

client = Letta(base_url=LETTA_BASE_URL)

print("📋 Fetching all agents...")
agents_list = client.agents.list()
agents = list(agents_list)

# Filter for Agent_66*
agent_66_instances = [a for a in agents if a.name.startswith("Agent_66")]

total_count = len(agent_66_instances)
keep_count = 1
delete_list = [a for a in agent_66_instances if a.id != KEEP_AGENT_ID]
delete_count = len(delete_list)

print()
print("📊 SUMMARY")
print(f"  Total Agent_66* instances: {total_count}")
print(f"  Will keep: {keep_count} agent")
print(f"  Will delete: {delete_count} agents")
print()

if delete_count == 0:
    print("✅ No duplicates found. Agent_66 is clean!")
    exit(0)

print("━" * 70)
print("AGENT TO KEEP:")
print("━" * 70)
print("✓ Name: Agent_66")
print(f"  ID: {KEEP_AGENT_ID}")
print("  Description: Remembers project status, web search, coder delegation")
print()

print("━" * 70)
print(f"AGENTS TO DELETE ({delete_count} total):")
print("━" * 70)

# Show first 20
for i, agent in enumerate(delete_list[:200], 1):
    print(f"{i}. ✗ {agent.name}")
    print(f"     ID: {agent.id}")
    if agent.description and agent.description != "None":
        print(f"     Description: {agent.description}")
    print()

if delete_count > 20:
    print(f"  ... and {delete_count - 20} more")
    print()

print("━" * 70)
print()
print("ℹ️  This is a DRY RUN - no agents were deleted.")
print()
print("To actually delete these agents, run:")
print("  ./cleanup_duplicate_agents.sh")
print()
