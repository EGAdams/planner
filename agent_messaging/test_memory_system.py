#!/usr/bin/env python3
"""
Quick smoke test for unified memory system.

Tests basic functionality with ChromaDB fallback (no Letta server needed).
"""

import asyncio
from agent_messaging import remember, recall, get_recent_memories, MemoryFactory


async def test_memory_system():
    """Test basic memory operations"""
    print("🧪 Testing Unified Memory System\n")
    
    # Test 1: Create memory backend (should use ChromaDB since Letta likely not running)
    print("1️⃣  Creating memory backend...")
    try:
        backend_name, memory = await MemoryFactory.create_memory_async("test-agent")
        print(f"   ✅ Using {backend_name} backend\n")
    except Exception as e:
        print(f"   ❌ Failed to create backend: {e}\n")
        return
    
    # Test 2: Store some memories
    print("2️⃣  Storing memories...")
    try:
        id1 = await remember(
            "Dashboard server started successfully on port 3000",
            memory_type="deployment",
            source="test-agent",
            tags=["dashboard", "startup"]
        )
        print(f"   ✅ Stored memory 1: {id1[:20]}...")
        
        id2 = await remember(
            "Fixed ChromaDB rust panic by using Letta as primary backend",
            memory_type="fix",
            source="test-agent",
            tags=["chromadb", "bug-fix"]
        )
        print(f"   ✅ Stored memory 2: {id2[:20]}...\n")
        
    except Exception as e:
        print(f"   ❌ Failed to store memories: {e}\n")
        return
    
    # Test 3: Recall memories
    print("3️⃣  Recalling memories...")
    try:
        results = await recall("dashboard", limit=2)
        print(f"   ✅ Found {len(results)} memories for 'dashboard'")
        for i, mem in enumerate(results, 1):
            print(f"      [{i}] {mem.content[:60]}... (type: {mem.memory_type})")
        print()
        
    except Exception as e:
        print(f"   ❌ Failed to recall: {e}\n")
        return
    
    # Test 4: Filter by type
    print("4️⃣  Filtering by type...")
    try:
        fixes = await recall("", memory_type="fix", limit=5)
        print(f"   ✅ Found {len(fixes)} fix-type memories")
        for mem in fixes:
            print(f"      - {mem.content[:50]}...")
        print()
        
    except Exception as e:
        print(f"   ❌ Failed to filter: {e}\n")
        return
    
    # Test 5: Get recent memories
    print("5️⃣  Getting recent memories...")
    try:
        recent = await get_recent_memories(limit=3)
        print(f"   ✅ Found {len(recent)} recent memories")
        for mem in recent:
            print(f"      - [{mem.timestamp.strftime('%H:%M:%S')}] {mem.content[:40]}...")
        print()
        
    except Exception as e:
        print(f"   ❌ Failed to get recent: {e}\n")
        return
    
    # Test 6: Get stats
    print("6️⃣  Getting memory stats...")
    try:
        stats = await memory.get_stats()
        print(f"   ✅ Stats:")
        for key, value in stats.items():
            if isinstance(value, dict):
                print(f"      - {key}: {dict(list(value.items())[:3])}")
            else:
                print(f"      - {key}: {value}")
        print()
        
    except Exception as e:
        print(f"   ❌ Failed to get stats: {e}\n")
        return
    
    print("✅ All tests passed! Memory system is working correctly.\n")
    print("💡 Tips:")
    print("   - Start Letta server (letta server) to use shared memory")
    print("   - ChromaDB provides semantic search, Letta provides sharing")
    print("   - Use memory_type to categorize (error, fix, deployment, note)")


if __name__ == "__main__":
    asyncio.run(test_memory_system())
