#!/usr/bin/env python3
"""
Performance Test Suite for Letta Voice Agent
============================================
TDD approach to measure and validate latency optimizations.

Target: <3 seconds end-to-end response time
Current: ~16 seconds (FAILING)

Test breakdown:
1. Letta API latency (network + processing)
2. Streaming vs non-streaming comparison
3. Individual component timing (STT, LLM, TTS)
4. End-to-end pipeline latency
"""
import asyncio
import logging
import os
import time
from typing import Dict, List
from dotenv import load_dotenv
from letta_client import Letta

# Load environment
load_dotenv("/home/adamsl/planner/.env")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

LETTA_BASE_URL = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")
LETTA_API_KEY = os.getenv("LETTA_API_KEY")

# Performance thresholds (TDD targets)
TARGET_TOTAL_LATENCY = 3.0  # seconds
TARGET_LETTA_API_LATENCY = 2.0  # seconds (network + LLM)
TARGET_STREAMING_TTFT = 0.5  # seconds (time to first token)

class PerformanceMetrics:
    """Track and report performance metrics"""

    def __init__(self):
        self.metrics: Dict[str, List[float]] = {}

    def record(self, metric_name: str, value: float):
        """Record a metric value"""
        if metric_name not in self.metrics:
            self.metrics[metric_name] = []
        self.metrics[metric_name].append(value)

    def get_stats(self, metric_name: str) -> Dict[str, float]:
        """Get statistics for a metric"""
        values = self.metrics.get(metric_name, [])
        if not values:
            return {}

        return {
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'count': len(values)
        }

    def report(self):
        """Print performance report"""
        logger.info("\n" + "="*60)
        logger.info("PERFORMANCE REPORT")
        logger.info("="*60)

        for metric_name in sorted(self.metrics.keys()):
            stats = self.get_stats(metric_name)
            if stats:
                logger.info(f"\n{metric_name}:")
                logger.info(f"  Min: {stats['min']:.2f}s")
                logger.info(f"  Max: {stats['max']:.2f}s")
                logger.info(f"  Avg: {stats['avg']:.2f}s")
                logger.info(f"  Runs: {stats['count']}")


async def get_test_agent(client: Letta) -> str:
    """Get the test agent ID (Agent_66)"""
    agents_list = await asyncio.to_thread(client.agents.list)
    agents = list(agents_list) if agents_list else []

    for agent in agents:
        if hasattr(agent, 'name') and agent.name == "Agent_66":
            return agent.id

    raise RuntimeError("Agent_66 not found. Please create it first.")


async def test_non_streaming_latency(client: Letta, agent_id: str, metrics: PerformanceMetrics):
    """
    Test 1: Non-streaming latency baseline

    This measures the complete time for a non-streaming request.
    Expected: 2-5 seconds (depending on response length)
    """
    logger.info("\n" + "-"*60)
    logger.info("TEST 1: Non-streaming Latency Baseline")
    logger.info("-"*60)

    test_message = "Say hello in one sentence."

    start = time.perf_counter()

    response = await asyncio.to_thread(
        client.agents.messages.create,
        agent_id=agent_id,
        messages=[{"role": "user", "content": test_message}]
    )

    latency = time.perf_counter() - start
    metrics.record("non_streaming_total", latency)

    # Extract response
    response_text = ""
    if hasattr(response, 'messages'):
        for msg in response.messages:
            if hasattr(msg, 'message_type') and msg.message_type == "assistant_message":
                if hasattr(msg, 'content'):
                    response_text += msg.content

    logger.info(f"Request: {test_message}")
    logger.info(f"Response: {response_text[:100]}...")
    logger.info(f"Latency: {latency:.2f}s")

    if latency > TARGET_LETTA_API_LATENCY:
        logger.warning(f"⚠️  SLOW: {latency:.2f}s > target {TARGET_LETTA_API_LATENCY}s")
    else:
        logger.info(f"✅ PASS: {latency:.2f}s <= target {TARGET_LETTA_API_LATENCY}s")

    return latency


async def test_streaming_ttft(client: Letta, agent_id: str, metrics: PerformanceMetrics):
    """
    Test 2: Streaming Time-to-First-Token (TTFT)

    This measures how long it takes to receive the first token in streaming mode.
    Expected: <500ms

    CRITICAL: This test will FAIL if streaming is not truly async!
    """
    logger.info("\n" + "-"*60)
    logger.info("TEST 2: Streaming Time-to-First-Token (TTFT)")
    logger.info("-"*60)

    test_message = "Count to three slowly."

    start = time.perf_counter()
    first_token_time = None

    try:
        # Try to use streaming
        response = await asyncio.to_thread(
            client.agents.messages.create,
            agent_id=agent_id,
            messages=[{"role": "user", "content": test_message}],
            streaming=True,
            stream_tokens=True
        )

        # Measure time to first chunk
        chunk_count = 0
        if hasattr(response, '__iter__'):
            for chunk in response:
                if first_token_time is None:
                    first_token_time = time.perf_counter() - start
                    metrics.record("streaming_ttft", first_token_time)
                    logger.info(f"⏱️  First token received: {first_token_time:.3f}s")

                chunk_count += 1

        total_time = time.perf_counter() - start
        metrics.record("streaming_total", total_time)

        logger.info(f"Chunks received: {chunk_count}")
        logger.info(f"Total time: {total_time:.2f}s")

        if first_token_time is None:
            logger.error("❌ FAIL: Streaming returned no chunks!")
            return None

        if first_token_time > TARGET_STREAMING_TTFT:
            logger.warning(f"⚠️  SLOW TTFT: {first_token_time:.3f}s > target {TARGET_STREAMING_TTFT}s")
        else:
            logger.info(f"✅ PASS: {first_token_time:.3f}s <= target {TARGET_STREAMING_TTFT}s")

        # CRITICAL CHECK: If TTFT ≈ total time, streaming is NOT working!
        if first_token_time > total_time * 0.8:
            logger.error(
                f"❌ STREAMING BROKEN: TTFT ({first_token_time:.3f}s) ≈ "
                f"total time ({total_time:.2f}s)"
            )
            logger.error(
                "This indicates asyncio.to_thread() is blocking on the entire "
                "iteration before returning!"
            )

        return first_token_time

    except Exception as e:
        logger.error(f"❌ FAIL: Streaming not supported - {e}")
        import traceback
        traceback.print_exc()
        return None


async def test_component_breakdown(client: Letta, agent_id: str, metrics: PerformanceMetrics):
    """
    Test 3: Component Breakdown

    Measure individual stages:
    - Network round-trip
    - LLM processing
    - Response assembly
    """
    logger.info("\n" + "-"*60)
    logger.info("TEST 3: Component Breakdown")
    logger.info("-"*60)

    test_message = "What is 2+2?"

    # Stage 1: Measure complete request
    start = time.perf_counter()

    response = await asyncio.to_thread(
        client.agents.messages.create,
        agent_id=agent_id,
        messages=[{"role": "user", "content": test_message}]
    )

    total_latency = time.perf_counter() - start

    # Extract response
    response_text = ""
    extract_start = time.perf_counter()
    if hasattr(response, 'messages'):
        for msg in response.messages:
            if hasattr(msg, 'message_type') and msg.message_type == "assistant_message":
                if hasattr(msg, 'content'):
                    response_text += msg.content
    extract_time = time.perf_counter() - extract_start

    # Record metrics
    metrics.record("api_call_latency", total_latency)
    metrics.record("response_extraction", extract_time)

    logger.info(f"Total API latency: {total_latency:.2f}s")
    logger.info(f"Response extraction: {extract_time*1000:.0f}ms")
    logger.info(f"Response: {response_text[:100]}...")

    return total_latency


async def test_end_to_end_simulation(client: Letta, agent_id: str, metrics: PerformanceMetrics):
    """
    Test 4: End-to-End Pipeline Simulation

    Simulates the complete voice pipeline:
    1. STT (simulated - ~300ms)
    2. Letta API call
    3. TTS (simulated - ~500ms)

    Target: <3 seconds total
    """
    logger.info("\n" + "-"*60)
    logger.info("TEST 4: End-to-End Pipeline Simulation")
    logger.info("-"*60)

    test_message = "Tell me about Python in one sentence."

    # Simulate STT
    stt_latency = 0.3  # 300ms typical for Deepgram
    await asyncio.sleep(stt_latency)
    logger.info(f"STT (simulated): {stt_latency*1000:.0f}ms")

    # Letta API call
    start = time.perf_counter()
    response = await asyncio.to_thread(
        client.agents.messages.create,
        agent_id=agent_id,
        messages=[{"role": "user", "content": test_message}]
    )
    letta_latency = time.perf_counter() - start
    logger.info(f"Letta API: {letta_latency:.2f}s")

    # Extract response
    response_text = ""
    if hasattr(response, 'messages'):
        for msg in response.messages:
            if hasattr(msg, 'message_type') and msg.message_type == "assistant_message":
                if hasattr(msg, 'content'):
                    response_text += msg.content

    # Simulate TTS
    tts_latency = 0.5  # 500ms typical for OpenAI TTS
    await asyncio.sleep(tts_latency)
    logger.info(f"TTS (simulated): {tts_latency*1000:.0f}ms")

    # Calculate total
    total_latency = stt_latency + letta_latency + tts_latency
    metrics.record("end_to_end_total", total_latency)

    logger.info(f"\nTotal end-to-end: {total_latency:.2f}s")
    logger.info(f"Response: {response_text[:100]}...")

    if total_latency > TARGET_TOTAL_LATENCY:
        logger.error(f"❌ FAIL: {total_latency:.2f}s > target {TARGET_TOTAL_LATENCY}s")
    else:
        logger.info(f"✅ PASS: {total_latency:.2f}s <= target {TARGET_TOTAL_LATENCY}s")

    return total_latency


async def run_performance_tests():
    """Run all performance tests"""
    logger.info("="*60)
    logger.info("LETTA VOICE AGENT PERFORMANCE TEST SUITE")
    logger.info("="*60)

    # Initialize client
    if LETTA_API_KEY:
        client = Letta(api_key=LETTA_API_KEY)
    else:
        client = Letta(base_url=LETTA_BASE_URL)

    # Get test agent
    try:
        agent_id = await get_test_agent(client)
        logger.info(f"Using test agent: {agent_id}")
    except Exception as e:
        logger.error(f"Failed to get test agent: {e}")
        return

    # Initialize metrics
    metrics = PerformanceMetrics()

    # Run tests
    try:
        await test_non_streaming_latency(client, agent_id, metrics)
        await asyncio.sleep(1)  # Brief pause between tests

        await test_streaming_ttft(client, agent_id, metrics)
        await asyncio.sleep(1)

        await test_component_breakdown(client, agent_id, metrics)
        await asyncio.sleep(1)

        await test_end_to_end_simulation(client, agent_id, metrics)

    except Exception as e:
        logger.error(f"Test suite error: {e}")
        import traceback
        traceback.print_exc()

    # Print final report
    metrics.report()

    # Check if we met targets
    logger.info("\n" + "="*60)
    logger.info("TARGET VALIDATION")
    logger.info("="*60)

    e2e_stats = metrics.get_stats("end_to_end_total")
    if e2e_stats and e2e_stats['avg'] <= TARGET_TOTAL_LATENCY:
        logger.info(f"✅ PASS: Average e2e latency {e2e_stats['avg']:.2f}s <= {TARGET_TOTAL_LATENCY}s")
    elif e2e_stats:
        logger.error(f"❌ FAIL: Average e2e latency {e2e_stats['avg']:.2f}s > {TARGET_TOTAL_LATENCY}s")

    ttft_stats = metrics.get_stats("streaming_ttft")
    if ttft_stats and ttft_stats['avg'] <= TARGET_STREAMING_TTFT:
        logger.info(f"✅ PASS: Average TTFT {ttft_stats['avg']:.3f}s <= {TARGET_STREAMING_TTFT}s")
    elif ttft_stats:
        logger.error(f"❌ FAIL: Average TTFT {ttft_stats['avg']:.3f}s > {TARGET_STREAMING_TTFT}s")
    else:
        logger.error("❌ FAIL: Streaming not working")


if __name__ == "__main__":
    asyncio.run(run_performance_tests())
