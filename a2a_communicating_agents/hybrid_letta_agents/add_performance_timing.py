#!/usr/bin/env python3
"""
Add performance timing to letta_voice_agent.py

This script adds timing measurements to identify bottlenecks without
changing functionality. Run this to instrument the code, then check logs.
"""

import sys
from pathlib import Path

LETTA_VOICE_AGENT_EXE="letta_voice_agent_groq.py"

VOICE_AGENT_PATH = Path(__file__).parent / LETTA_VOICE_AGENT_EXE

def add_timing_to_llm_node():
    """Add timing measurements to llm_node method"""

    with open(VOICE_AGENT_PATH, 'r') as f:
        content = f.read()

    # Check if already instrumented
    if "TIMING:" in content:
        print("⚠️  Timing already added to code")
        return False

    # Add import at top
    if "import time" not in content:
        content = content.replace(
            "import asyncio",
            "import asyncio\nimport time"
        )

    # Add timing to llm_node
    old_llm_node = '''    async def llm_node(self, chat_ctx, tools, model_settings):
        """
        Override LLM node to route through Letta orchestrator (Template Method pattern).

        This is called by the Livekit framework after STT transcription.
        We route to Letta and return the response for TTS.
        """
        # Extract user message from chat context items
        user_message = _coerce_text(chat_ctx.items[-1].content if chat_ctx.items else "")

        logger.info(f"🎤 User message: {user_message}")

        # Publish transcript to room for UI
        await self._publish_transcript("user", user_message)

        # Route through Letta
        logger.info("PRE-CALL to _get_letta_response")
        response_text = await self._get_letta_response(user_message)
        logger.info("POST-CALL to _get_letta_response")'''

    new_llm_node = '''    async def llm_node(self, chat_ctx, tools, model_settings):
        """
        Override LLM node to route through Letta orchestrator (Template Method pattern).

        This is called by the Livekit framework after STT transcription.
        We route to Letta and return the response for TTS.
        """
        # TIMING: Start pipeline measurement
        pipeline_start = time.time()

        # Extract user message from chat context items
        user_message = _coerce_text(chat_ctx.items[-1].content if chat_ctx.items else "")

        stt_time = (time.time() - pipeline_start) * 1000
        logger.info(f"🎤 User message: {user_message}")
        logger.info(f"⏱️  TIMING: STT processing: {stt_time:.0f}ms")

        # Publish transcript to room for UI
        publish_start = time.time()
        await self._publish_transcript("user", user_message)
        publish_time = (time.time() - publish_start) * 1000
        logger.info(f"⏱️  TIMING: Publish transcript: {publish_time:.0f}ms")

        # Route through Letta
        logger.info("PRE-CALL to _get_letta_response")
        llm_start = time.time()
        response_text = await self._get_letta_response(user_message)
        llm_time = (time.time() - llm_start) * 1000
        logger.info("POST-CALL to _get_letta_response")
        logger.info(f"⏱️  TIMING: LLM response: {llm_time:.0f}ms ⚠️ BOTTLENECK")'''

    content = content.replace(old_llm_node, new_llm_node)

    # Add timing to _get_letta_response
    old_letta_response = '''    async def _get_letta_response(self, user_message: str) -> str:
        """
        Send message to Letta orchestrator and get response.

        Args:
            user_message: User's text (from STT)

        Returns:
            Letta's response text (for TTS)
        """
        try:
            # Send to Letta using the official client
            # Run in thread pool since letta_client is synchronous
            logger.info("Attempting to call Letta server...")
            response = await asyncio.to_thread(
                self.letta_client.agents.messages.create,
                agent_id=self.agent_id,
                messages=[{"role": "user", "content": user_message}]
            )
            logger.info("Call to Letta server completed.")'''

    new_letta_response = '''    async def _get_letta_response(self, user_message: str) -> str:
        """
        Send message to Letta orchestrator and get response.

        Args:
            user_message: User's text (from STT)

        Returns:
            Letta's response text (for TTS)
        """
        try:
            # TIMING: Measure Letta API call
            letta_call_start = time.time()

            # Send to Letta using the official client
            # Run in thread pool since letta_client is synchronous
            logger.info("Attempting to call Letta server...")
            response = await asyncio.to_thread(
                self.letta_client.agents.messages.create,
                agent_id=self.agent_id,
                messages=[{"role": "user", "content": user_message}]
            )
            letta_call_time = (time.time() - letta_call_start) * 1000
            logger.info("Call to Letta server completed.")
            logger.info(f"⏱️  TIMING: Letta API call: {letta_call_time:.0f}ms (network + LLM)")'''

    content = content.replace(old_letta_response, new_letta_response)

    # Add total pipeline timing at end of llm_node
    old_return = '''        # Publish response to room for UI
        await self._publish_transcript("assistant", response_text)

        logger.info(f"🔊 Letta response: {response_text[:100]}...")

        return response_text'''

    new_return = '''        # Publish response to room for UI
        publish_start2 = time.time()
        await self._publish_transcript("assistant", response_text)
        publish_time2 = (time.time() - publish_start2) * 1000
        logger.info(f"⏱️  TIMING: Publish response: {publish_time2:.0f}ms")

        logger.info(f"🔊 Letta response: {response_text[:100]}...")

        # TIMING: Total pipeline
        pipeline_total = (time.time() - pipeline_start) * 1000
        logger.info(f"⏱️  TIMING: TOTAL PIPELINE: {pipeline_total:.0f}ms")
        logger.info(f"⏱️  TIMING: Breakdown - STT:{stt_time:.0f}ms + LLM:{llm_time:.0f}ms + Publish:{publish_time+publish_time2:.0f}ms")

        return response_text'''

    content = content.replace(old_return, new_return)

    # Write back
    with open(VOICE_AGENT_PATH, 'w') as f:
        f.write(content)

    print("✅ Added performance timing to {LETTA_VOICE_AGENT_EXE}")
    print("")
    print("Next steps:")
    print("1. Restart voice system: ./restart_voice_system.sh")
    print("2. Test voice interaction")
    print("3. Check logs: tail -f /tmp/letta_voice_agent.log | grep '⏱️'")
    print("")
    print("Look for lines like:")
    print("  ⏱️  TIMING: LLM response: 2500ms ⚠️ BOTTLENECK")
    print("  ⏱️  TIMING: TOTAL PIPELINE: 3200ms")
    return True

if __name__ == "__main__":
    if not VOICE_AGENT_PATH.exists():
        print(f"❌ Error: {VOICE_AGENT_PATH} not found")
        sys.exit(1)

    success = add_timing_to_llm_node()
    sys.exit(0 if success else 1)
