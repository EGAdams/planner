#!/usr/bin/env python3
"""
Verify that the voice agent is configured to use the correct Agent_66
"""
import os
from dotenv import load_dotenv

# Load environment as the agent does
load_dotenv("/home/adamsl/planner/.env", override=True)
load_dotenv("/home/adamsl/ottomator-agents/livekit-agent/.env")

# Check configuration
PRIMARY_AGENT_ID = os.getenv("VOICE_PRIMARY_AGENT_ID")
PRIMARY_AGENT_NAME = os.getenv("VOICE_PRIMARY_AGENT_NAME", "Agent_66")

print("=" * 70)
print("VOICE AGENT CONFIGURATION VERIFICATION")
print("=" * 70)

if PRIMARY_AGENT_ID:
    print(f"✅ VOICE_PRIMARY_AGENT_ID is configured")
    print(f"   Agent ID: {PRIMARY_AGENT_ID}")
    print(f"   Agent Name: {PRIMARY_AGENT_NAME}")
    print()
    print("🎯 Expected Agent:")
    print("   Name: Agent_66")
    print("   Description: Remembers the status for all kinds of projects...")
    print("   ID: agent-4dfca708-49a8-4982-8e36-0f1146f9a66e")
    print()

    if PRIMARY_AGENT_ID == "agent-4dfca708-49a8-4982-8e36-0f1146f9a66e":
        print("✅ CONFIGURATION CORRECT!")
        print("   The voice agent will use the CORRECT Agent_66")
    else:
        print("⚠️  WARNING: Agent ID doesn't match expected")
        print(f"   Expected: agent-4dfca708-49a8-4982-8e36-0f1146f9a66e")
        print(f"   Got:      {PRIMARY_AGENT_ID}")
else:
    print("❌ VOICE_PRIMARY_AGENT_ID is NOT configured")
    print("   The agent will search by name and might pick a random Agent_66")
    print()
    print("🔧 Fix: Add to /home/adamsl/planner/.env:")
    print("   VOICE_PRIMARY_AGENT_ID=agent-4dfca708-49a8-4982-8e36-0f1146f9a66e")
    print("   VOICE_PRIMARY_AGENT_NAME=Agent_66")

print("=" * 70)
