#!/usr/bin/env python3
"""
Verify Agent_66 Memory Loading Fix

This script tests the REST API fix for loading Agent_66's memory blocks.
Run this script to confirm the fix works before starting the voice agent.

Usage:
    python3 verify_memory_fix.py
"""

import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

LETTA_BASE_URL = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")
AGENT_ID = os.getenv("VOICE_PRIMARY_AGENT_ID", "agent-4dfca708-49a8-4982-8e36-0f1146f9a66e")


async def verify_rest_api_memory():
    """Test REST API memory loading (the fix)"""
    print("\n" + "="*60)
    print("Testing REST API Memory Loading (THE FIX)")
    print("="*60)

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                f"{LETTA_BASE_URL}/v1/agents/{AGENT_ID}",
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            agent_data = response.json()

        agent_name = agent_data.get('name', 'Unknown')
        memory_data = agent_data.get('memory', {})
        memory_blocks = memory_data.get('blocks', [])

        print(f"\n✅ SUCCESS - REST API returned agent data")
        print(f"   Agent Name: {agent_name}")
        print(f"   Agent ID: {AGENT_ID}")
        print(f"   Memory Blocks Found: {len(memory_blocks)}")

        if memory_blocks:
            print("\n📋 Memory Blocks Loaded:")
            for block in memory_blocks:
                label = block.get('label', 'unknown')
                value = block.get('value', '')
                print(f"   - {label}: {len(value)} characters")

                # Show snippet of key blocks
                if label in ['persona', 'role', 'human']:
                    snippet = value[:100] + "..." if len(value) > 100 else value
                    print(f"     Preview: {snippet}")

            print("\n✅ REST API FIX WORKING - Memory blocks loaded successfully!")
            return True
        else:
            print("\n⚠️  WARNING - No memory blocks found in agent")
            print("    Agent may be newly created or have empty memory")
            return False

    except httpx.HTTPStatusError as e:
        print(f"\n❌ HTTP ERROR: {e.response.status_code}")
        print(f"   URL: {e.request.url}")
        if e.response.status_code == 404:
            print(f"   Agent ID not found: {AGENT_ID}")
            print(f"   Check VOICE_PRIMARY_AGENT_ID in .env")
        return False

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        print(f"   Letta server may not be running at {LETTA_BASE_URL}")
        return False


async def verify_asyncletta_memory():
    """Test AsyncLetta client memory loading (the bug)"""
    print("\n" + "="*60)
    print("Testing AsyncLetta Client Memory Loading (THE BUG)")
    print("="*60)

    try:
        from letta_client import AsyncLetta

        letta_client = AsyncLetta(base_url=LETTA_BASE_URL)
        agent = await letta_client.agents.retrieve(agent_id=AGENT_ID)

        agent_name = getattr(agent, 'name', 'Unknown')

        # Check memory blocks
        has_memory = hasattr(agent, 'memory') and agent.memory
        blocks = []

        if has_memory:
            # Handle both API response formats
            blocks = agent.memory.blocks if hasattr(agent.memory, 'blocks') else agent.memory

        print(f"\n⚠️  AsyncLetta client result:")
        print(f"   Agent Name: {agent_name}")
        print(f"   Has Memory Attribute: {has_memory}")
        print(f"   Memory Blocks Count: {len(blocks) if blocks else 0}")

        if blocks:
            print("\n📋 Memory Blocks from AsyncLetta:")
            for block in blocks:
                if hasattr(block, 'label') and hasattr(block, 'value'):
                    print(f"   - {block.label}: {len(block.value)} characters")
            print("\n✅ AsyncLetta client working (unexpected!)")
            return True
        else:
            print("\n❌ BUG CONFIRMED - AsyncLetta returns empty memory blocks")
            print("   This is why we need the REST API fix!")
            return False

    except Exception as e:
        print(f"\n❌ AsyncLetta test failed: {e}")
        return False


async def main():
    """Run all verification tests"""
    print("\n" + "="*60)
    print("Agent_66 Memory Loading Fix Verification")
    print("="*60)
    print(f"\nLetta Server: {LETTA_BASE_URL}")
    print(f"Agent ID: {AGENT_ID}")

    # Test health first
    print("\n" + "="*60)
    print("Testing Letta Server Health")
    print("="*60)

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{LETTA_BASE_URL}/admin/health")
            if response.status_code == 200:
                print("✅ Letta server is healthy")
            else:
                print(f"⚠️  Letta server responded with status {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot connect to Letta server: {e}")
        print("\nPlease start the Letta server before running this test:")
        print("  letta server start")
        return

    # Test REST API (the fix)
    rest_api_works = await verify_rest_api_memory()

    # Test AsyncLetta (the bug)
    asyncletta_works = await verify_asyncletta_memory()

    # Summary
    print("\n" + "="*60)
    print("VERIFICATION SUMMARY")
    print("="*60)

    if rest_api_works and not asyncletta_works:
        print("\n✅ FIX VALIDATED!")
        print("   - REST API loads memory blocks correctly")
        print("   - AsyncLetta client has the bug (empty blocks)")
        print("   - Voice agent will use REST API fix and work correctly")
    elif rest_api_works and asyncletta_works:
        print("\n✅ BOTH METHODS WORK!")
        print("   - REST API loads memory blocks")
        print("   - AsyncLetta client also working (bug may be fixed)")
        print("   - Voice agent will work with either method")
    elif not rest_api_works:
        print("\n❌ REST API FIX NOT WORKING")
        print("   - Check Letta server is running")
        print("   - Verify Agent_66 ID is correct")
        print("   - Check agent has memory blocks configured")

    print("\n" + "="*60)
    print("Next Steps:")
    print("="*60)
    if rest_api_works:
        print("1. Restart voice system: ./restart_voice_system.sh")
        print("2. Check logs for memory loading success")
        print("3. Test voice interaction with Agent_66")
    else:
        print("1. Start Letta server: letta server start")
        print("2. Verify Agent_66 exists and has memory blocks")
        print("3. Re-run this verification script")
    print()


if __name__ == "__main__":
    asyncio.run(main())
