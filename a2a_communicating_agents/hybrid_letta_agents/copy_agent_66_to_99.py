#!/usr/bin/env python3
"""
Copy Agent_66 to create Agent_99
"""
import os
import json
import requests
from dotenv import load_dotenv

# Load environment
load_dotenv("/home/adamsl/planner/.env", override=True)

# Configuration
LETTA_BASE_URL = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")
SOURCE_AGENT_ID = "agent-4dfca708-49a8-4982-8e36-0f1146f9a66e"
NEW_AGENT_NAME = "Agent_99"

print("=" * 70)
print("COPYING Agent_66 to Agent_99")
print("=" * 70)
print()

# Step 1: Get source agent details
print(f"📥 Fetching Agent_66 details...")
response = requests.get(f"{LETTA_BASE_URL}/v1/agents/{SOURCE_AGENT_ID}")

if response.status_code != 200:
    print(f"❌ Failed to fetch agent: {response.status_code}")
    print(response.text)
    exit(1)

source_agent = response.json()
print(f"✅ Retrieved Agent_66 (ID: {SOURCE_AGENT_ID})")
print()

# Step 2: Extract configuration for new agent
print("📋 Extracting configuration...")

# Get memory blocks
memory_blocks = []
if "memory" in source_agent:
    for block_id, block_data in source_agent["memory"].items():
        if isinstance(block_data, dict) and "value" in block_data:
            memory_blocks.append({
                "label": block_data.get("label", block_id),
                "value": block_data.get("value", "")
            })

# Build new agent configuration
new_agent_config = {
    "name": NEW_AGENT_NAME,
    "description": source_agent.get("description"),
    "llm_config": source_agent.get("llm_config"),
    "embedding_config": source_agent.get("embedding_config"),
    "memory_blocks": memory_blocks if memory_blocks else None,
}

# Add optional fields if present
if "tools" in source_agent:
    new_agent_config["tools"] = source_agent["tools"]
if "system" in source_agent:
    new_agent_config["system"] = source_agent["system"]
if "tool_rules" in source_agent:
    new_agent_config["tool_rules"] = source_agent["tool_rules"]
if "tags" in source_agent:
    new_agent_config["tags"] = source_agent["tags"]

print(f"✅ Configuration extracted")
print(f"   - LLM Model: {source_agent.get('llm_config', {}).get('model', 'N/A')}")
print(f"   - Memory Blocks: {len(memory_blocks)}")
print(f"   - Tools: {len(source_agent.get('tools', []))}")
print()

# Step 3: Create new agent
print(f"🔨 Creating Agent_99...")

response = requests.post(
    f"{LETTA_BASE_URL}/v1/agents",
    headers={"Content-Type": "application/json"},
    json=new_agent_config
)

if response.status_code in [200, 201]:
    new_agent = response.json()
    new_agent_id = new_agent.get("id")

    print(f"✅ Successfully created Agent_99!")
    print()
    print(f"📊 New Agent Details:")
    print(f"   Name: {new_agent.get('name')}")
    print(f"   ID: {new_agent_id}")
    print(f"   Description: {new_agent.get('description')}")
    print()
    print(f"🎯 To use this agent in voice system:")
    print(f"   VOICE_PRIMARY_AGENT_ID={new_agent_id}")
    print(f"   VOICE_PRIMARY_AGENT_NAME={NEW_AGENT_NAME}")
    print()

else:
    print(f"❌ Failed to create agent: {response.status_code}")
    print(response.text)
    exit(1)

print("=" * 70)
print("✅ COPY COMPLETE")
print("=" * 70)
