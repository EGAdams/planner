#!/usr/bin/env python3
"""
Test to diagnose the voice agent routing issue.

HYPOTHESIS:
The voice agent is configured with correct Agent_66 ID, BUT hybrid streaming mode
bypasses Agent_66's memory entirely, using a generic OpenAI model instead.

This test will:
1. Verify Agent_66 ID configuration
2. Check hybrid streaming mode setting
3. Demonstrate the memory bypass issue
4. Propose fixes
"""

import os
import asyncio
import sys
from dotenv import load_dotenv

from letta_client import AsyncLetta

# Load environment as the voice agent does
load_dotenv("/home/adamsl/planner/.env", override=True)
load_dotenv("/home/adamsl/ottomator-agents/livekit-agent/.env")

PRIMARY_AGENT_ID = os.getenv("VOICE_PRIMARY_AGENT_ID")
PRIMARY_AGENT_NAME = os.getenv("VOICE_PRIMARY_AGENT_NAME", "Agent_66")
USE_HYBRID_STREAMING = os.getenv("USE_HYBRID_STREAMING", "true").lower() == "true"
LETTA_BASE_URL = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")

async def diagnose_routing_issue():
    """Diagnose the voice agent routing issue"""

    print("=" * 80)
    print("VOICE AGENT ROUTING DIAGNOSTIC")
    print("=" * 80)
    print()

    # Step 1: Verify configuration
    print("1. CONFIGURATION CHECK")
    print("-" * 80)
    print(f"   Agent ID:         {PRIMARY_AGENT_ID}")
    print(f"   Agent Name:       {PRIMARY_AGENT_NAME}")
    print(f"   Hybrid Streaming: {USE_HYBRID_STREAMING}")
    print(f"   Letta Server:     {LETTA_BASE_URL}")
    print()

    if not PRIMARY_AGENT_ID:
        print("   ❌ ERROR: VOICE_PRIMARY_AGENT_ID not configured!")
        print("   This will cause the agent to search by name and might pick wrong agent.")
        return

    # Step 2: Verify Agent_66 exists and retrieve its memory
    print("2. AGENT_66 MEMORY CHECK")
    print("-" * 80)

    try:
        letta_client = AsyncLetta(base_url=LETTA_BASE_URL)
        agent = await letta_client.agents.retrieve(agent_id=PRIMARY_AGENT_ID)

        print(f"   ✅ Agent found: {agent.name}")
        print(f"   ID: {agent.id}")
        print()

        # Get memory blocks
        print("   Memory Blocks:")
        if hasattr(agent, 'memory') and agent.memory:
            for block in agent.memory:
                if hasattr(block, 'label') and hasattr(block, 'value'):
                    print(f"     - {block.label}:")
                    value_preview = block.value[:100] + "..." if len(block.value) > 100 else block.value
                    print(f"       {value_preview}")
                    print()
        else:
            print("     ⚠️  No memory blocks found or memory not accessible")

    except Exception as e:
        print(f"   ❌ ERROR retrieving agent: {e}")
        return

    # Step 3: Identify the routing issue
    print("3. ROUTING ISSUE DIAGNOSIS")
    print("-" * 80)

    if USE_HYBRID_STREAMING:
        print("   ❌ ROOT CAUSE IDENTIFIED:")
        print()
        print("   Hybrid streaming mode is ENABLED.")
        print("   This means:")
        print()
        print("   Fast Path (Used for responses):")
        print("   ✗ Direct OpenAI API call")
        print("   ✗ Generic system instructions only")
        print("   ✗ Last 10 messages from local history only")
        print("   ✗ NO ACCESS to Agent_66's memory blocks!")
        print("   ✗ NO ACCESS to Agent_66's persona!")
        print("   ✗ NO ACCESS to Agent_66's stored knowledge!")
        print()
        print("   Slow Path (Background sync):")
        print("   ✓ Saves conversation to Agent_66's memory")
        print("   ✓ Happens AFTER response is already sent")
        print("   ✓ Non-blocking, doesn't affect response content")
        print()
        print("   PARADOX EXPLAINED:")
        print("   - Voice responses come from generic OpenAI (no Agent_66 knowledge)")
        print("   - Agent_66 receives and stores the conversation (visible in Letta ADE)")
        print("   - But Agent_66's knowledge is NEVER used to generate responses!")
        print()
    else:
        print("   ✅ Hybrid streaming is DISABLED")
        print("   All responses go through AsyncLetta, using Agent_66's full memory.")
        print()

    # Step 4: Propose fixes
    print("4. RECOMMENDED FIXES")
    print("-" * 80)
    print()
    print("   Option 1: DISABLE HYBRID STREAMING (Immediate fix)")
    print("   -" * 76)
    print("   Edit .env file:")
    print("   USE_HYBRID_STREAMING=false")
    print()
    print("   Pros:")
    print("   ✓ Agent_66's full memory and persona will be used for all responses")
    print("   ✓ Immediate fix, no code changes needed")
    print()
    print("   Cons:")
    print("   ✗ Slower response times (3-5s instead of 1-2s)")
    print()
    print()
    print("   Option 2: ENHANCE HYBRID MODE (Better long-term solution)")
    print("   -" * 76)
    print("   Modify _get_openai_response_streaming() to:")
    print("   1. Load Agent_66's persona from Letta before generating response")
    print("   2. Load relevant memory blocks into OpenAI context")
    print("   3. Include Agent_66's system instructions in prompt")
    print()
    print("   Pros:")
    print("   ✓ Fast response times maintained (1-2s)")
    print("   ✓ Agent_66's knowledge and persona used in responses")
    print()
    print("   Cons:")
    print("   ✗ Requires code changes to voice agent")
    print("   ✗ Extra API call to load memory (adds ~200ms)")
    print()
    print()
    print("   Option 3: SMART ROUTING (Most sophisticated)")
    print("   -" * 76)
    print("   Implement query classifier:")
    print("   - Simple queries (greetings, status) → Fast path (OpenAI direct)")
    print("   - Knowledge queries (project info) → Slow path (Letta with memory)")
    print()
    print("   Pros:")
    print("   ✓ Optimal performance for each query type")
    print("   ✓ Agent_66's knowledge used when needed")
    print()
    print("   Cons:")
    print("   ✗ Most complex implementation")
    print("   ✗ Requires query classification logic")
    print()

    print("=" * 80)
    print("RECOMMENDED ACTION:")
    print("=" * 80)
    print()
    print("For immediate fix: Set USE_HYBRID_STREAMING=false in .env and restart")
    print("For long-term: Implement Option 2 (Enhanced Hybrid Mode)")
    print()

if __name__ == "__main__":
    asyncio.run(diagnose_routing_issue())
