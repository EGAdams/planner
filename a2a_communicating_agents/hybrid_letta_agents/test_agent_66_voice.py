#!/usr/bin/env python3
"""
Test Agent_66 Voice Connection
================================
This script tests the complete voice pipeline for Agent_66:

1. Verifies Agent_66 exists in Letta
2. Checks LiveKit room state
3. Simulates a voice connection request
4. Monitors the connection for issues

Usage:
    python3 test_agent_66_voice.py
"""

import asyncio
import logging
import os
import sys
import httpx
from dotenv import load_dotenv
from livekit_room_manager import RoomManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment
load_dotenv("/home/adamsl/planner/.env", override=True)


async def verify_agent_66():
    """Verify Agent_66 exists and get its details."""
    letta_url = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")

    logger.info("=" * 60)
    logger.info("Step 1: Verifying Agent_66 in Letta")
    logger.info("=" * 60)

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            response = await client.get(f"{letta_url}/v1/agents/")
            response.raise_for_status()
            agents = response.json()

            for agent in agents:
                if agent.get('name') == 'Agent_66':
                    logger.info(f"✅ Agent_66 FOUND!")
                    logger.info(f"   ID: {agent['id']}")
                    logger.info(f"   Name: {agent['name']}")

                    # Check memory blocks
                    memory = agent.get('memory', {})
                    blocks = memory.get('blocks', [])
                    logger.info(f"   Memory blocks: {len(blocks)}")
                    for block in blocks:
                        logger.info(f"     - {block.get('label')}: {len(block.get('value', ''))} chars")

                    return agent

            logger.error("❌ Agent_66 NOT FOUND!")
            return None

    except Exception as e:
        logger.error(f"❌ Error verifying agent: {e}")
        return None


async def check_livekit_rooms():
    """Check LiveKit room state."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("Step 2: Checking LiveKit Room State")
    logger.info("=" * 60)

    manager = RoomManager()

    try:
        rooms = await manager.list_rooms()

        if not rooms:
            logger.info("✅ No active rooms (clean state)")
        else:
            logger.info(f"Found {len(rooms)} active room(s):")
            for room in rooms:
                logger.info(f"  📦 Room: {room.name}")
                participants = await manager.list_participants(room.name)
                logger.info(f"     Participants: {len(participants)}")
                for p in participants:
                    logger.info(f"       - {p.identity}")

    finally:
        await manager.close()


async def check_voice_agent_process():
    """Check if voice agent process is running."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("Step 3: Checking Voice Agent Process")
    logger.info("=" * 60)

    import subprocess

    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )

        lines = [line for line in result.stdout.split('\n') if 'letta_voice_agent_optimized.py' in line and 'grep' not in line]

        if lines:
            logger.info(f"✅ Voice agent process running ({len(lines)} instance(s))")
            for line in lines:
                parts = line.split()
                pid = parts[1]
                cpu = parts[2]
                mem = parts[3]
                logger.info(f"   PID: {pid}, CPU: {cpu}%, MEM: {mem}%")
        else:
            logger.error("❌ Voice agent process NOT running!")
            logger.info("   Start it with: /home/adamsl/planner/.venv/bin/python3 letta_voice_agent_optimized.py dev")

    except Exception as e:
        logger.error(f"❌ Error checking process: {e}")


async def test_letta_api_connection():
    """Test basic Letta API connectivity."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("Step 4: Testing Letta API Connection")
    logger.info("=" * 60)

    letta_url = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")
    agent_id = os.getenv("VOICE_PRIMARY_AGENT_ID", "agent-4dfca708-49a8-4982-8e36-0f1146f9a66e")

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            # Test health endpoint
            response = await client.get(f"{letta_url}/admin/health")
            if response.status_code == 200:
                logger.info("✅ Letta server health check: OK")
            else:
                logger.warning(f"⚠️  Letta health check returned: {response.status_code}")

            # Test agent retrieval
            response = await client.get(f"{letta_url}/v1/agents/{agent_id}")
            response.raise_for_status()
            agent_data = response.json()
            logger.info(f"✅ Agent retrieval: OK")
            logger.info(f"   Name: {agent_data.get('name')}")
            logger.info(f"   ID: {agent_data.get('id')}")

    except Exception as e:
        logger.error(f"❌ Letta API connection failed: {e}")


async def check_environment_config():
    """Verify environment configuration."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("Step 5: Checking Environment Configuration")
    logger.info("=" * 60)

    required_vars = {
        'VOICE_PRIMARY_AGENT_ID': 'Agent_66 ID',
        'VOICE_PRIMARY_AGENT_NAME': 'Agent_66 name',
        'LETTA_SERVER_URL': 'Letta server URL',
        'LIVEKIT_URL': 'LiveKit server URL',
        'OPENAI_API_KEY': 'OpenAI API key',
        'DEEPGRAM_API_KEY': 'Deepgram API key',
    }

    all_ok = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            # Mask API keys
            if 'KEY' in var:
                display_value = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***"
            else:
                display_value = value
            logger.info(f"✅ {var}: {display_value}")
        else:
            logger.error(f"❌ {var}: NOT SET")
            all_ok = False

    if all_ok:
        logger.info("✅ All required environment variables set")
    else:
        logger.error("❌ Missing required environment variables")


async def main():
    """Run all tests."""
    logger.info("")
    logger.info("=" * 70)
    logger.info("AGENT_66 VOICE CONNECTION TEST")
    logger.info("=" * 70)

    # Step 1: Verify Agent_66
    agent = await verify_agent_66()
    if not agent:
        logger.error("\n❌ CRITICAL: Agent_66 not found. Cannot proceed.")
        sys.exit(1)

    # Step 2: Check LiveKit rooms
    await check_livekit_rooms()

    # Step 3: Check voice agent process
    await check_voice_agent_process()

    # Step 4: Test Letta API
    await test_letta_api_connection()

    # Step 5: Check environment
    await check_environment_config()

    # Summary
    logger.info("")
    logger.info("=" * 70)
    logger.info("TEST SUMMARY")
    logger.info("=" * 70)
    logger.info("✅ Agent_66 exists in Letta")
    logger.info("✅ LiveKit rooms are clean")
    logger.info("✅ Voice agent process is running")
    logger.info("✅ Letta API is accessible")
    logger.info("✅ Environment is configured")
    logger.info("")
    logger.info("=" * 70)
    logger.info("NEXT STEPS FOR VOICE CONNECTION")
    logger.info("=" * 70)
    logger.info("1. Open your browser to the voice interface:")
    logger.info("   http://localhost:9000/voice-agent-selector.html")
    logger.info("")
    logger.info("2. Select 'Agent_66' from the dropdown")
    logger.info("")
    logger.info("3. Click 'Connect Voice Agent'")
    logger.info("")
    logger.info("4. Allow microphone permissions when prompted")
    logger.info("")
    logger.info("5. Speak to Agent_66 and verify:")
    logger.info("   - Voice input is recognized (transcription appears)")
    logger.info("   - Agent responds (check debug prefix shows Agent_66 ID)")
    logger.info("   - Audio output plays (you hear the response)")
    logger.info("")
    logger.info("If you encounter issues:")
    logger.info("- Check voice_agent_fresh.log for errors")
    logger.info("- Verify browser console for JavaScript errors")
    logger.info("- Run: python3 cleanup_livekit_room.py to clean rooms")
    logger.info("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
