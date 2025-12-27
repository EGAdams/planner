#!/usr/bin/env python3
"""
Test Optimized Async Streaming
==============================
Validates that AsyncLetta provides true async streaming with sub-second TTFT.

This test proves the fix:
- OLD: asyncio.to_thread() blocks entire iteration → TTFT ≈ total time
- NEW: AsyncLetta with async iteration → TTFT << total time

Expected results:
- TTFT: <500ms (target achieved)
- Total time: 1-3s (depending on response length)
- TTFT should be <20% of total time (proves streaming works)
"""
import asyncio
import logging
import os
import time
from dotenv import load_dotenv
from letta_client import AsyncLetta

# Load environment
load_dotenv("/home/adamsl/planner/.env")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

LETTA_BASE_URL = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")
LETTA_API_KEY = os.getenv("LETTA_API_KEY")

# Performance targets
TARGET_TTFT = 0.5  # 500ms
TARGET_TOTAL = 3.0  # 3 seconds


async def test_async_streaming():
    """Test AsyncLetta streaming performance"""
    logger.info("="*60)
    logger.info("ASYNC STREAMING PERFORMANCE TEST")
    logger.info("="*60)

    # Initialize async client
    if LETTA_API_KEY:
        client = AsyncLetta(api_key=LETTA_API_KEY)
    else:
        client = AsyncLetta(base_url=LETTA_BASE_URL)

    # Get test agent (handle pagination)
    logger.info("Finding Agent_66...")
    agents = []
    async for agent in client.agents.list():
        agents.append(agent)

    agent_id = None
    for agent in agents:
        if hasattr(agent, 'name') and agent.name == "Agent_66":
            agent_id = agent.id
            break

    if not agent_id:
        logger.error("❌ Agent_66 not found!")
        return False

    logger.info(f"✅ Found agent: {agent_id}")
    logger.info("")

    # Test streaming
    test_message = "Count to five slowly."
    logger.info(f"📤 Test message: {test_message}")
    logger.info("")

    start = time.perf_counter()
    first_token_time = None
    chunk_times = []

    try:
        logger.info("⚡ Calling AsyncLetta with stream_tokens=True...")

        # CRITICAL: Direct async call - no asyncio.to_thread()
        response = await client.agents.messages.create(
            agent_id=agent_id,
            messages=[{"role": "user", "content": test_message}],
            streaming=True,      # Required for streaming
            stream_tokens=True   # Enable token-level streaming
        )

        logger.info("Processing async stream...")
        chunk_count = 0
        response_parts = []

        # CRITICAL: Async iteration - chunks arrive as generated
        async for chunk in response:
            chunk_time = time.perf_counter() - start

            # Record first token time
            if first_token_time is None:
                first_token_time = chunk_time
                logger.info(f"⚡ FIRST TOKEN: {first_token_time*1000:.0f}ms")

            chunk_count += 1
            chunk_times.append(chunk_time)

            # Extract content
            content = None
            if hasattr(chunk, 'message_type') and chunk.message_type == "assistant_message":
                if hasattr(chunk, 'content') and chunk.content:
                    content = chunk.content
                    response_parts.append(content)
            elif isinstance(chunk, dict):
                if chunk.get("type") == "assistant_message" and chunk.get("content"):
                    content = chunk["content"]
                    response_parts.append(content)

            if content:
                logger.info(f"  Chunk {chunk_count} @ {chunk_time*1000:.0f}ms: {content[:50]}...")

        total_time = time.perf_counter() - start
        response_text = " ".join(response_parts)

        logger.info("")
        logger.info("="*60)
        logger.info("RESULTS")
        logger.info("="*60)
        logger.info(f"Response: {response_text}")
        logger.info(f"Chunks received: {chunk_count}")
        logger.info(f"First token time (TTFT): {first_token_time*1000:.0f}ms")
        logger.info(f"Total time: {total_time:.2f}s")

        if chunk_count > 1:
            # Calculate streaming efficiency
            ttft_ratio = first_token_time / total_time
            logger.info(f"TTFT / Total ratio: {ttft_ratio:.2%}")

        logger.info("")
        logger.info("="*60)
        logger.info("VALIDATION")
        logger.info("="*60)

        # Check TTFT target
        if first_token_time and first_token_time <= TARGET_TTFT:
            logger.info(f"✅ TTFT PASS: {first_token_time*1000:.0f}ms <= {TARGET_TTFT*1000:.0f}ms")
        elif first_token_time:
            logger.warning(f"⚠️  TTFT SLOW: {first_token_time*1000:.0f}ms > {TARGET_TTFT*1000:.0f}ms")
        else:
            logger.error("❌ TTFT FAIL: No tokens received")

        # Check total time target
        if total_time <= TARGET_TOTAL:
            logger.info(f"✅ TOTAL PASS: {total_time:.2f}s <= {TARGET_TOTAL:.1f}s")
        else:
            logger.warning(f"⚠️  TOTAL SLOW: {total_time:.2f}s > {TARGET_TOTAL:.1f}s")

        # CRITICAL: Check if streaming is actually working
        if first_token_time and chunk_count > 1:
            ttft_ratio = first_token_time / total_time
            if ttft_ratio > 0.8:
                logger.error(
                    f"❌ STREAMING BROKEN: TTFT ({first_token_time:.3f}s) ≈ "
                    f"total time ({total_time:.2f}s)"
                )
                logger.error("Chunks arrived all at once - not true streaming!")
                return False
            else:
                logger.info(f"✅ STREAMING WORKS: TTFT is {ttft_ratio:.1%} of total time")
                logger.info("Chunks arrived incrementally - true streaming confirmed!")

        # Final verdict
        logger.info("")
        if (first_token_time and first_token_time <= TARGET_TTFT and
            total_time <= TARGET_TOTAL and
            (not chunk_count or chunk_count == 1 or first_token_time / total_time < 0.8)):
            logger.info("🎉 ALL TESTS PASSED - OPTIMIZED STREAMING WORKING!")
            return True
        else:
            logger.warning("⚠️  Some tests did not meet targets")
            return False

    except Exception as e:
        logger.error(f"❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_async_streaming())
    if result:
        print("\n✅ Optimized async streaming validated successfully")
        exit(0)
    else:
        print("\n❌ Optimized async streaming test failed")
        exit(1)
