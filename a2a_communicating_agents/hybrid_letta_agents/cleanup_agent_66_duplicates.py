#!/usr/bin/env python3
"""
Cleanup Agent_66 Duplicates - DELETE VERSION
Deletes all Agent_66* agents EXCEPT the correct one with project memory
"""
import os
import sys
from letta_client import Letta
from dotenv import load_dotenv
from datetime import datetime

load_dotenv("/home/adamsl/planner/.env", override=True)

# Configuration
LETTA_BASE_URL = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")
KEEP_AGENT_ID = "agent-4dfca708-49a8-4982-8e36-0f1146f9a66e"
LOG_FILE = f"/tmp/agent_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

# Colors
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

print("=" * 70)
print("  Agent_66 Cleanup Script")
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
print(f"{GREEN}✅ Found {total_count} Agent_66* instances{NC}")
print(f"{GREEN}✅ Keeping: 1 agent (ID: {KEEP_AGENT_ID}){NC}")
print(f"{RED}🗑️  Will delete: {delete_count} duplicate agents{NC}")
print()

if delete_count == 0:
    print(f"{GREEN}✅ No duplicates to delete. Agent_66 is clean!{NC}")
    sys.exit(0)

# Show first 10 agents to be deleted
print(f"{YELLOW}Preview of agents to delete (first 10):{NC}")
for i, agent in enumerate(delete_list[:100], 1):
    print(f"  {RED}✗{NC} {agent.name} ({agent.id})")

if delete_count > 10:
    print(f"  ... and {delete_count - 10} more")

print()
print(f"{YELLOW}Agent to KEEP:{NC}")
print(f"  {GREEN}✓{NC} Agent_66 ({KEEP_AGENT_ID})")
print(f"    Description: Remembers project status, web search, coder delegation")
print()

# Safety confirmation
print(f"{RED}⚠️  WARNING: This will permanently delete {delete_count} agents!{NC}")
print(f"{YELLOW}Type 'DELETE' to confirm (or anything else to cancel): {NC}", end='')
confirmation = input()

if confirmation != "DELETE":
    print(f"{BLUE}❌ Cancelled. No agents were deleted.{NC}")
    sys.exit(0)

print()
print(f"{YELLOW}🗑️  Starting deletion process...{NC}")
print(f"Log file: {LOG_FILE}")
print()

# Initialize counters
deleted = 0
failed = 0
skipped = 0

# Create log file
with open(LOG_FILE, 'w') as log:
    log.write(f"Agent Cleanup Log - {datetime.now()}\n")
    log.write("=" * 70 + "\n\n")

# Delete agents one by one
for agent in delete_list:
    # Safety check: never delete the keeper agent
    if agent.id == KEEP_AGENT_ID:
        print(f"{YELLOW}⚠️  SKIPPED (protected): {agent.id}{NC}")
        skipped += 1
        with open(LOG_FILE, 'a') as log:
            log.write(f"SKIPPED (protected): {agent.id}\n")
        continue

    # Attempt deletion
    print(f"Deleting: {agent.name} ({agent.id})... ", end='', flush=True)

    try:
        client.agents.delete(agent_id=agent.id)
        print(f"{GREEN}✓ Deleted{NC}")
        deleted += 1
        with open(LOG_FILE, 'a') as log:
            log.write(f"SUCCESS: Deleted {agent.name} ({agent.id})\n")
    except Exception as e:
        print(f"{RED}✗ Failed: {str(e)}{NC}")
        failed += 1
        with open(LOG_FILE, 'a') as log:
            log.write(f"FAILED: {agent.name} ({agent.id}) - {str(e)}\n")

print()
print("=" * 70)
print("  Cleanup Complete")
print("=" * 70)
print()
print(f"{GREEN}✅ Deleted:  {deleted} agents{NC}")
print(f"{RED}✗ Failed:   {failed} agents{NC}")
print(f"{YELLOW}⊘ Skipped:  {skipped} agents{NC}")
print()
print(f"{GREEN}✅ Kept:     1 agent ({KEEP_AGENT_ID}){NC}")
print()
print(f"Full log: {LOG_FILE}")
print()

# Verify the correct agent still exists
print(f"{YELLOW}🔍 Verifying correct agent still exists...{NC}")
try:
    verify_agent = client.agents.retrieve(agent_id=KEEP_AGENT_ID)
    print(f"{GREEN}✅ VERIFIED: Correct Agent_66 is still active!{NC}")
    print(f"   Name: {verify_agent.name}")
    print(f"   ID: {verify_agent.id}")
except Exception as e:
    print(f"{RED}⚠️  WARNING: Could not verify agent: {str(e)}{NC}")

print()
print(f"{BLUE}Run ./verify_agent_fix.py to confirm configuration.{NC}")
