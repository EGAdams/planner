#!/usr/bin/env python3
"""
Test voice agent reliability improvements.
Validates guaranteed response delivery under failure conditions.

Tests the 12 failure modes identified by quality-agent:
1. Letta server unreachable
2. Letta timeout (>10 seconds)
3. Empty Letta response
4. Retry logic with exponential backoff
5. Circuit breaker prevents cascading failures
"""

import asyncio
import pytest
import time
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


class TestReliabilityCore:
    """Test core reliability components without full agent initialization."""

    async def test_circuit_breaker_opens_after_failures(self):
        """Test circuit breaker opens after threshold failures."""
        from letta_voice_agent_reliable import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=3, timeout_seconds=5)

        # Circuit starts closed
        assert cb.should_allow_request() is True
        assert cb.state == "closed"

        # Record 3 failures
        cb.record_failure()
        cb.record_failure()
        cb.record_failure()

        # Circuit should be open
        assert cb.state == "open"
        assert cb.should_allow_request() is False

        print("✅ Circuit breaker opens after 3 failures")

    async def test_circuit_breaker_half_open_after_timeout(self):
        """Test circuit breaker transitions to half-open after timeout."""
        from letta_voice_agent_reliable import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=2, timeout_seconds=1)

        # Open circuit
        cb.record_failure()
        cb.record_failure()
        assert cb.state == "open"

        # Wait for timeout
        await asyncio.sleep(1.1)

        # Should be half-open
        assert cb.should_allow_request() is True

        print("✅ Circuit breaker half-opens after timeout")

    async def test_circuit_breaker_closes_on_success(self):
        """Test circuit breaker closes after successful request in half-open state."""
        from letta_voice_agent_reliable import CircuitBreaker

        cb = CircuitBreaker(failure_threshold=2, timeout_seconds=1)

        # Open circuit
        cb.record_failure()
        cb.record_failure()

        # Wait for half-open
        await asyncio.sleep(1.1)
        cb.should_allow_request()  # Transition to half-open

        # Record success
        cb.record_success()

        # Should be closed
        assert cb.state == "closed"
        assert cb.failures == 0

        print("✅ Circuit breaker closes on success in half-open state")

    async def test_response_validation_rejects_empty(self):
        """Test response validation rejects empty responses."""
        from letta_voice_agent_reliable import LettaVoiceAssistant

        # Create mock context
        mock_ctx = Mock()
        mock_ctx.room = Mock()
        mock_client = Mock()

        assistant = LettaVoiceAssistant(mock_ctx, mock_client, "test-agent")

        # Test empty string
        validated = assistant._validate_response("")
        assert len(validated) > 0
        assert "didn't generate" in validated.lower()

        # Test whitespace only
        validated = assistant._validate_response("   ")
        assert len(validated) > 0
        assert "rephrase" in validated.lower()

        # Test too short
        validated = assistant._validate_response("ab")
        assert len(validated) > 0

        # Test valid response
        validated = assistant._validate_response("This is a valid response")
        assert validated == "This is a valid response"

        print("✅ Response validation rejects empty/invalid responses")

    async def test_guaranteed_fallback_always_returns(self):
        """Test guaranteed fallback NEVER returns empty."""
        from letta_voice_agent_reliable import LettaVoiceAssistant

        # Create mock context
        mock_ctx = Mock()
        mock_ctx.room = Mock()
        mock_client = Mock()

        assistant = LettaVoiceAssistant(mock_ctx, mock_client, "test-agent")

        # Test various error contexts
        contexts = [
            "timeout error",
            "circuit breaker open",
            "health check failed",
            "unknown error",
            ""
        ]

        for context in contexts:
            response = await assistant._guaranteed_fallback_response(context)
            assert response is not None
            assert len(response) > 0
            assert isinstance(response, str)
            print(f"   Fallback for '{context}': {response[:50]}...")

        print("✅ Guaranteed fallback always returns valid response")


class TestReliabilityIntegration:
    """Test full agent integration with mocked Letta client."""

    async def test_letta_server_down_returns_fallback(self):
        """Test response when Letta server is unreachable."""
        from letta_voice_agent_reliable import LettaVoiceAssistant

        # Create mock context
        mock_ctx = Mock()
        mock_ctx.room = Mock()

        # Mock Letta client that raises connection error
        mock_client = Mock()
        mock_client.agents.messages.create.side_effect = ConnectionError("Connection refused")

        assistant = LettaVoiceAssistant(mock_ctx, mock_client, "test-agent")

        # Mock health check to fail
        with patch.object(assistant, '_check_letta_health', return_value=False):
            start = time.time()
            response = await assistant._get_letta_response_with_retry("Test message")
            elapsed = time.time() - start

        # Should return fallback quickly
        assert response is not None
        assert len(response) > 0
        assert elapsed < 5.0  # Should fail fast, not wait 30 seconds
        # Accept any of the fallback messages
        assert any(keyword in response.lower() for keyword in [
            "health check", "trouble", "processing system", "connect"
        ])

        print(f"✅ Letta server down returns fallback in {elapsed:.2f}s")

    async def test_letta_timeout_returns_fallback(self):
        """Test response when Letta is slow (>10 seconds)."""
        from letta_voice_agent_reliable import LettaVoiceAssistant

        # Create mock context
        mock_ctx = Mock()
        mock_ctx.room = Mock()

        # Mock Letta client that raises TimeoutError
        mock_client = Mock()
        # Simulate timeout by having asyncio.to_thread raise TimeoutError

        assistant = LettaVoiceAssistant(mock_ctx, mock_client, "test-agent")

        # Mock health check to succeed
        # Mock asyncio.to_thread to simulate timeout
        async def mock_to_thread(*args, **kwargs):
            await asyncio.sleep(15)  # Will be interrupted by timeout
            return Mock()

        with patch.object(assistant, '_check_letta_health', return_value=True):
            with patch('asyncio.to_thread', side_effect=mock_to_thread):
                start = time.time()
                response = await assistant._get_letta_response_with_retry("Test message", max_retries=0)
                elapsed = time.time() - start

        # Should timeout at 10 seconds and return fallback
        assert response is not None
        assert len(response) > 0
        assert 9.5 < elapsed < 12.0  # 10s timeout + small overhead
        # Accept any of the fallback messages
        assert any(keyword in response.lower() for keyword in [
            "timeout", "trouble", "processing system", "longer than expected", "failed"
        ])

        print(f"✅ Letta timeout returns fallback in {elapsed:.2f}s")

    async def test_empty_letta_response_returns_fallback(self):
        """Test response when Letta returns empty message list."""
        from letta_voice_agent_reliable import LettaVoiceAssistant

        # Create mock context
        mock_ctx = Mock()
        mock_ctx.room = Mock()

        # Mock Letta client that returns empty messages
        mock_response = Mock()
        mock_response.messages = []

        mock_client = Mock()
        mock_client.agents.messages.create.return_value = mock_response

        assistant = LettaVoiceAssistant(mock_ctx, mock_client, "test-agent")

        # Mock health check to succeed
        with patch.object(assistant, '_check_letta_health', return_value=True):
            response = await assistant._get_letta_response_with_retry("Test message")

        # Should return validation fallback
        assert response is not None
        assert len(response) > 0
        assert "didn't generate" in response.lower() or "rephrase" in response.lower()

        print("✅ Empty Letta response returns validation fallback")

    async def test_retry_logic_with_backoff(self):
        """Test retry with exponential backoff."""
        from letta_voice_agent_reliable import LettaVoiceAssistant

        # Create mock context
        mock_ctx = Mock()
        mock_ctx.room = Mock()

        # Track call times
        call_times = []

        def failing_letta(*args, **kwargs):
            call_times.append(time.time())
            raise Exception("Temporary failure")

        mock_client = Mock()
        mock_client.agents.messages.create = failing_letta

        assistant = LettaVoiceAssistant(mock_ctx, mock_client, "test-agent")

        # Mock health check to succeed
        with patch.object(assistant, '_check_letta_health', return_value=True):
            start = time.time()
            response = await assistant._get_letta_response_with_retry("Test message", max_retries=2)
            elapsed = time.time() - start

        # Should have made 3 attempts (initial + 2 retries)
        assert len(call_times) == 3

        # Check exponential backoff timing
        # First retry should be ~2s after first attempt
        # Second retry should be ~4s after second attempt
        if len(call_times) >= 2:
            first_backoff = call_times[1] - call_times[0]
            assert 1.8 < first_backoff < 2.5, f"First backoff was {first_backoff}s, expected ~2s"

        if len(call_times) >= 3:
            second_backoff = call_times[2] - call_times[1]
            assert 3.8 < second_backoff < 4.5, f"Second backoff was {second_backoff}s, expected ~4s"

        # Should still return fallback response
        assert response is not None
        assert len(response) > 0

        print(f"✅ Retry logic with exponential backoff (3 attempts in {elapsed:.2f}s)")

    async def test_circuit_breaker_prevents_cascading_failures(self):
        """Test circuit breaker prevents cascading failures."""
        from letta_voice_agent_reliable import LettaVoiceAssistant

        # Create mock context
        mock_ctx = Mock()
        mock_ctx.room = Mock()

        mock_client = Mock()
        mock_client.agents.messages.create.side_effect = Exception("Service down")

        assistant = LettaVoiceAssistant(mock_ctx, mock_client, "test-agent")
        assistant.letta_circuit_breaker.failure_threshold = 3

        # Mock health check to succeed initially
        with patch.object(assistant, '_check_letta_health', return_value=True):
            # First 3 requests should fail and open circuit
            for i in range(3):
                response = await assistant._get_letta_response_with_retry(f"Message {i}", max_retries=0)
                assert response is not None

        # Circuit should be open
        assert assistant.letta_circuit_breaker.state == "open"

        # Next request should fast-fail without calling Letta
        start = time.time()
        response = await assistant._get_letta_response_with_retry("Message after circuit open", max_retries=0)
        elapsed = time.time() - start

        # Should return immediately (no health check, no Letta call)
        assert elapsed < 0.5  # Fast fail
        assert response is not None
        # Accept any of the fallback messages
        assert any(keyword in response.lower() for keyword in [
            "circuit breaker", "unavailable", "backend system", "temporarily"
        ])

        print(f"✅ Circuit breaker fast-fails after 3 failures ({elapsed:.2f}s)")


async def run_all_tests():
    """Run all reliability tests."""
    print("\n" + "="*60)
    print("RUNNING RELIABILITY TESTS")
    print("="*60 + "\n")

    core_tests = TestReliabilityCore()
    integration_tests = TestReliabilityIntegration()

    # Core component tests
    print("CORE COMPONENT TESTS:")
    print("-" * 60)
    await core_tests.test_circuit_breaker_opens_after_failures()
    await core_tests.test_circuit_breaker_half_open_after_timeout()
    await core_tests.test_circuit_breaker_closes_on_success()
    await core_tests.test_response_validation_rejects_empty()
    await core_tests.test_guaranteed_fallback_always_returns()

    print("\nINTEGRATION TESTS:")
    print("-" * 60)
    await integration_tests.test_letta_server_down_returns_fallback()
    await integration_tests.test_letta_timeout_returns_fallback()
    await integration_tests.test_empty_letta_response_returns_fallback()
    await integration_tests.test_retry_logic_with_backoff()
    await integration_tests.test_circuit_breaker_prevents_cascading_failures()

    print("\n" + "="*60)
    print("ALL RELIABILITY TESTS PASSED")
    print("="*60 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(run_all_tests())
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
