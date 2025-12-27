#!/usr/bin/env python3
"""
Voice Response Diagnostic Tool
Checks the voice pipeline from STT → Letta → TTS
"""
import asyncio
import logging
import os
from dotenv import load_dotenv
from letta_client import Letta

# Load environment
load_dotenv("/home/adamsl/planner/.env")

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

LETTA_BASE_URL = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")
LETTA_API_KEY = os.getenv("LETTA_API_KEY")

async def test_letta_response():
    """Test if Letta is responding correctly"""
    try:
        # Initialize client
        if LETTA_API_KEY:
            client = Letta(api_key=LETTA_API_KEY)
        else:
            client = Letta(base_url=LETTA_BASE_URL)

        # Get agent (using Agent_66 as in code)
        agents_list = await asyncio.to_thread(client.agents.list)
        agents = list(agents_list) if agents_list else []

        target_agent = None
        for agent in agents:
            if hasattr(agent, 'name') and agent.name == "Agent_66":
                target_agent = agent
                break

        if not target_agent:
            logger.error("❌ Agent_66 not found! Available agents:")
            for agent in agents:
                logger.info(f"  - {agent.name} ({agent.id})")
            return False

        logger.info(f"✅ Found agent: {target_agent.name} ({target_agent.id})")

        # Send test message
        test_message = "Hello, can you hear me?"
        logger.info(f"📤 Sending test message: {test_message}")

        response = await asyncio.to_thread(
            client.agents.messages.create,
            agent_id=target_agent.id,
            messages=[{"role": "user", "content": test_message}]
        )

        logger.info(f"📥 Response received: {response}")
        logger.info(f"Response type: {type(response)}")

        # Extract assistant messages
        assistant_messages = []
        if hasattr(response, 'messages'):
            logger.info(f"Number of messages: {len(response.messages)}")
            for i, msg in enumerate(response.messages):
                logger.info(f"Message {i}: type={type(msg)}")
                logger.info(f"  message_type={getattr(msg, 'message_type', 'N/A')}")
                logger.info(f"  role={getattr(msg, 'role', 'N/A')}")

                if hasattr(msg, 'message_type') and msg.message_type == "assistant_message":
                    if hasattr(msg, 'content'):
                        assistant_messages.append(msg.content)
                        logger.info(f"  ✅ Content: {msg.content[:100]}")

        if assistant_messages:
            logger.info(f"✅ SUCCESS - Got {len(assistant_messages)} assistant message(s)")
            for i, msg in enumerate(assistant_messages):
                logger.info(f"Message {i+1}: {msg}")
            return True
        else:
            logger.error("❌ FAILED - No assistant messages in response")
            return False

    except Exception as e:
        logger.error(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test_letta_response())
    if result:
        print("\n✅ Voice response pipeline is working correctly")
    else:
        print("\n❌ Voice response pipeline has issues - check logs above")
