#!/usr/bin/env python3
"""
Test Letta Voice Integration
=============================
Validates that:
1. Letta server is reachable
2. Voice orchestrator agent can be created
3. Messages can be sent and responses received
4. Memory persistence works
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment
load_dotenv("/home/adamsl/planner/.env")

# Add path for imports
sys.path.insert(0, "/home/adamsl/planner")

# Import our Letta client
from a2a_communicating_agents.hybrid_letta_agents.letta_voice_agent import LettaClient


async def test_letta_connection():
    """Test 1: Basic connection to Letta server"""
    print("\n" + "="*60)
    print("TEST 1: Letta Server Connection")
    print("="*60)

    base_url = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")
    print(f"Connecting to: {base_url}")

    client = LettaClient(base_url=base_url)

    try:
        agents = await client.list_agents()
        print(f"✅ Connected! Found {len(agents)} existing agents")
        for agent in agents[:3]:  # Show first 3
            print(f"   - {agent.get('name', 'unnamed')} ({agent.get('id', 'no-id')[:8]}...)")
        return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


async def test_create_orchestrator():
    """Test 2: Create voice orchestrator agent"""
    print("\n" + "="*60)
    print("TEST 2: Create Voice Orchestrator Agent")
    print("="*60)

    base_url = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")
    client = LettaClient(base_url=base_url)

    try:
        agent = await client.create_agent(
            name="test_voice_orchestrator",
            model="openai/gpt-5-mini",
            memory_blocks=[
                {
                    "label": "persona",
                    "value": "I am a test voice orchestrator for validating integration."
                },
                {
                    "label": "test_log",
                    "value": "Test conversation log."
                }
            ]
        )

        agent_id = agent.get("id")
        print(f"✅ Orchestrator created! ID: {agent_id[:16]}...")
        return agent_id

    except Exception as e:
        print(f"❌ Creation failed: {e}")
        return None


async def test_send_message(agent_id: str):
    """Test 3: Send message and get response"""
    print("\n" + "="*60)
    print("TEST 3: Send Message and Get Response")
    print("="*60)

    base_url = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")
    client = LettaClient(base_url=base_url)

    try:
        # Send test message
        test_message = "Hello! This is a test message. Can you confirm you received it?"
        print(f"Sending: '{test_message}'")

        response = await client.send_message(
            agent_id=agent_id,
            message=test_message,
            role="user"
        )

        # Extract response
        messages = response.get("messages", [])
        assistant_messages = [
            msg.get("text", "")
            for msg in messages
            if msg.get("role") == "assistant"
        ]

        if assistant_messages:
            response_text = " ".join(assistant_messages)
            print(f"✅ Received response:")
            print(f"   '{response_text[:200]}...'")
            return True
        else:
            print("❌ No assistant response in messages")
            return False

    except Exception as e:
        print(f"❌ Message send failed: {e}")
        return False


async def test_memory_persistence(agent_id: str):
    """Test 4: Verify memory persistence across messages"""
    print("\n" + "="*60)
    print("TEST 4: Memory Persistence")
    print("="*60)

    base_url = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")
    client = LettaClient(base_url=base_url)

    try:
        # First message: Introduce name
        msg1 = "My name is Alice and I love Python programming."
        print(f"Message 1: '{msg1}'")

        response1 = await client.send_message(agent_id=agent_id, message=msg1)
        messages1 = response1.get("messages", [])
        assistant1 = [m.get("text", "") for m in messages1 if m.get("role") == "assistant"]

        if assistant1:
            print(f"Response 1: '{assistant1[0][:100]}...'")
        else:
            print("❌ No response to first message")
            return False

        # Second message: Ask to recall
        msg2 = "What is my name and what do I like?"
        print(f"\nMessage 2: '{msg2}'")

        response2 = await client.send_message(agent_id=agent_id, message=msg2)
        messages2 = response2.get("messages", [])
        assistant2 = [m.get("text", "") for m in messages2 if m.get("role") == "assistant"]

        if assistant2:
            response_text = assistant2[0]
            print(f"Response 2: '{response_text[:200]}...'")

            # Check if name and preference are recalled
            if "alice" in response_text.lower() and "python" in response_text.lower():
                print("✅ Memory persistence working! Agent remembered name and preference.")
                return True
            else:
                print("⚠️  Agent responded but didn't recall stored information")
                return False
        else:
            print("❌ No response to second message")
            return False

    except Exception as e:
        print(f"❌ Memory test failed: {e}")
        return False


async def cleanup_test_agent(agent_id: str):
    """Clean up test agent"""
    print("\n" + "="*60)
    print("CLEANUP: Removing Test Agent")
    print("="*60)

    base_url = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")

    try:
        # Use httpx directly for DELETE
        import httpx
        async with httpx.AsyncClient() as http_client:
            response = await http_client.delete(f"{base_url}/api/agents/{agent_id}")
            if response.status_code in [200, 204]:
                print(f"✅ Test agent deleted")
            else:
                print(f"⚠️  Agent deletion returned status {response.status_code}")
    except Exception as e:
        print(f"⚠️  Cleanup error (agent may still exist): {e}")


async def main():
    """Run all tests"""
    print("\n" + "🧪"*30)
    print("LETTA VOICE INTEGRATION TEST SUITE")
    print("🧪"*30)

    results = {
        "connection": False,
        "create_agent": False,
        "send_message": False,
        "memory": False
    }

    agent_id = None

    try:
        # Test 1: Connection
        results["connection"] = await test_letta_connection()
        if not results["connection"]:
            print("\n❌ CRITICAL: Cannot connect to Letta server. Aborting tests.")
            print("   Make sure Letta server is running at http://localhost:8283")
            return

        # Test 2: Create agent
        agent_id = await test_create_orchestrator()
        results["create_agent"] = agent_id is not None
        if not agent_id:
            print("\n❌ CRITICAL: Cannot create agent. Aborting remaining tests.")
            return

        # Test 3: Send message
        results["send_message"] = await test_send_message(agent_id)

        # Test 4: Memory persistence
        results["memory"] = await test_memory_persistence(agent_id)

    finally:
        # Cleanup
        if agent_id:
            await cleanup_test_agent(agent_id)

    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name}")

    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed ({int(passed/total*100)}%)")

    if all(results.values()):
        print("\n🎉 ALL TESTS PASSED! Letta voice integration is ready.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Review errors above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
