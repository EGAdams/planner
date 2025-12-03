#!/usr/bin/env python3
"""
Test memory system with Letta (bypassing ChromaDB).

This tests ONLY the Letta backend to avoid ChromaDB crash.
"""

import asyncio
from a2a_communicating_agents.agent_messaging import LettaMemory, LettaMemoryConfig


async def test_letta_only():
    """Test Letta backend directly"""
    print("🧪 Testing Letta Memory Backend Only\n")
    
    # Test 1: Connect to Letta
    print("1️⃣  Connecting to Letta server...")
    config = LettaMemoryConfig(base_url="http://localhost:8283")
    memory = LettaMemory(config)
    
    try:
        await memory.connect()
        print(f"   ✅ Connected to Letta server\n")
    except Exception as e:
        print(f"   ❌ Failed to connect: {e}")
        print("\n💡 Start Letta server with: letta server\n")
        return
    
    # Test 2: Store memories
    print("2️⃣  Storing memories...")
    try:
        id1 = await memory.remember(
            "Dashboard server started successfully on port 3000",
            memory_type="deployment",
            source="test-agent",
            tags=["dashboard", "startup"]
        )
        print(f"   ✅ Stored memory 1: {id1[:30]}...")
        
        id2 = await memory.remember(
            "Fixed ChromaDB rust panic by using Letta as primary backend",
            memory_type="fix",
            source="test-agent",
            tags=["chromadb", "bug-fix"],
            metadata={"severity": "high"}
        )
        print(f"   ✅ Stored memory 2: {id2[:30]}...\n")
        
    except Exception as e:
        print(f"   ❌ Failed to store: {e}\n")
        return
    
    # Test 3: Recall all memories
    print("3️⃣  Recalling all memories...")
    try:
        all_memories = await memory.recall("", limit=10)
        print(f"   ✅ Found {len(all_memories)} total memories")
        for i, mem in enumerate(all_memories[:5], 1):
            print(f"      [{i}] {mem.content[:50]}...")
        print()
        
    except Exception as e:
        print(f"   ❌ Failed to recall: {e}\n")
        return
    
    # Test 4: Search specific query
    print("4️⃣  Searching for 'dashboard'...")
    try:
        results = await memory.recall("dashboard", limit=5)
        print(f"   ✅ Found {len(results)} matches")
        for mem in results:
            print(f"      - {mem.content[:60]}...")
        print()
        
    except Exception as e:
        print(f"   ❌ Failed to search: {e}\n")
        return
    
    # Test 5: Filter by type
    print("5️⃣  Filtering by type='fix'...")
    try:
        fixes = await memory.recall("", memory_type="fix")
        print(f"   ✅ Found {len(fixes)} fix-type memories")
        for mem in fixes:
            print(f"      - {mem.content[:50]}...")
        print()
        
    except Exception as e:
        print(f"   ❌ Failed to filter: {e}\n")
        return
    
    # Test 6: Get stats
    print("6️⃣  Getting stats...")
    try:
        stats = await memory.get_stats()
        print(f"   ✅ Memory stats:")
        print(f"      - Total memories: {stats['total_memories']}")
        print(f"      - By type: {stats.get('by_type', {})}")
        print(f"      - Backend: {stats['backend']}")
        print()
        
    except Exception as e:
        print(f"   ❌ Failed to get stats: {e}\n")
        return
    
    # Test 7: Cleanup - delete test memories
    print("7️⃣  Cleaning up test memories...")
    try:
        await memory.forget(id1)
        await memory.forget(id2)
        print(f"   ✅ Deleted test memories\n")
        
    except Exception as e:
        print(f"   ⚠️  Cleanup warning: {e}\n")
    
    await memory.disconnect()
    
    print("✅ All Letta tests passed!\n")
    print("💡 Next steps:")
    print("   - Letta memory is shared across all agents")
    print("   - Start Letta server: letta server")
    print("   - Use convenience functions: remember(), recall()")


if __name__ == "__main__":
    asyncio.run(test_letta_only())
