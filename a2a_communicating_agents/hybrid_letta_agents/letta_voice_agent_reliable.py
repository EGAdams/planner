#!/usr/bin/env python3
"""
Letta Voice Agent - RELIABLE Edition
=====================================
Voice-enabled Letta orchestrator with GUARANTEED response delivery.

CRITICAL RELIABILITY FEATURES:
    - Circuit Breaker: Fast-fail when Letta is down (prevents 30s timeouts)
    - Health Checks: Verify Letta is up before every call
    - Timeouts: 10-second maximum per attempt
    - Retry Logic: 2 retries with exponential backoff (2s, 4s)
    - Response Validation: Ensures non-empty, meaningful responses
    - Guaranteed Fallback: ALWAYS returns a valid response (never None/empty)

This addresses all 12 failure modes identified by quality-agent:
    1. Letta server unreachable -> Health check + fast-fail
    2. Letta timeout -> 10s max timeout per attempt
    3. Empty response -> Validation catches it
    4-6. Network issues -> Retry with backoff
    7-9. API errors -> Circuit breaker prevents cascading
    10-12. Edge cases -> Guaranteed fallback response

Architecture:
    User Voice → Livekit Room → Deepgram STT → Letta Orchestrator →
    OpenAI/Cartesia TTS → User

Based on: letta_voice_agent.py with reliability enhancements
"""

import asyncio
import logging
import os
import json
from typing import Optional, List
from datetime import datetime
import time

from dotenv import load_dotenv
from livekit import rtc, agents
from livekit.agents import (
    Agent,
    AgentSession,
    JobContext,
    JobRequest,
    WorkerOptions,
    cli,
    RoomOutputOptions,
)
from livekit.plugins import openai, deepgram, silero, cartesia
from letta_client import Letta
import httpx

# Load environment variables
load_dotenv("/home/adamsl/planner/.env")
load_dotenv("/home/adamsl/ottomator-agents/livekit-agent/.env")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Letta server configuration
LETTA_BASE_URL = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")
LETTA_API_KEY = os.getenv("LETTA_API_KEY")
ALLOWED_ORCHESTRATOR_MODELS = {"gpt-5-mini", "gpt-4o-mini"}

# HTTP client for connection pooling
HTTP_CLIENT = httpx.AsyncClient(
    timeout=httpx.Timeout(30.0),
    limits=httpx.Limits(
        max_keepalive_connections=20,
        max_connections=50,
        keepalive_expiry=60.0
    )
)


# Utility functions (from original)
def _normalize_model_name(model_name: Optional[str], endpoint: str) -> Optional[str]:
    """Strip provider prefixes (e.g., openai/gpt-4o-mini) from model names."""
    if not model_name:
        return model_name
    normalized = model_name.strip()
    lowered = normalized.lower()
    endpoint_lower = endpoint.lower()
    for prefix in (f"{endpoint_lower}/", f"{endpoint_lower}:"):
        if lowered.startswith(prefix):
            return normalized[len(prefix) :]
    return normalized


def _safe_int(value: Optional[str], default: int) -> int:
    """Convert env strings to ints without raising on bad input."""
    try:
        return int(value) if value is not None else default
    except (TypeError, ValueError):
        return default


def _coerce_text(payload) -> str:
    """Best-effort conversion of STT payloads into a plain string."""
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload
    if isinstance(payload, (list, tuple)):
        parts: List[str] = []
        for item in payload:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                text_val = item.get("text") or item.get("content")
                if isinstance(text_val, str):
                    parts.append(text_val)
            else:
                text_attr = getattr(item, "text", None)
                if isinstance(text_attr, str):
                    parts.append(text_attr)
        return " ".join(part for part in parts if part)
    return str(payload)


# RELIABILITY COMPONENT: Circuit Breaker
class CircuitBreaker:
    """
    Prevents cascading failures by fast-failing when service is down.

    States:
        - CLOSED: Normal operation, requests allowed
        - OPEN: Service is down, fast-fail all requests
        - HALF_OPEN: Testing if service recovered

    When threshold failures occur, circuit opens and fast-fails requests
    for timeout_seconds. After timeout, circuit goes half-open to test
    if service recovered.
    """
    def __init__(self, failure_threshold=3, timeout_seconds=30):
        self.failures = 0
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.last_failure_time = None
        self.state = "closed"  # closed, open, half-open

    def should_allow_request(self) -> bool:
        """Check if request should be allowed through circuit."""
        if self.state == "closed":
            return True
        elif self.state == "open":
            # Check if timeout has passed
            if self.last_failure_time and time.time() - self.last_failure_time > self.timeout_seconds:
                self.state = "half-open"
                logger.info("🔄 Circuit breaker half-open, trying request")
                return True
            logger.warning(f"⚡ Circuit breaker OPEN, fast-failing")
            return False
        else:  # half-open
            return True

    def record_success(self):
        """Record successful request."""
        if self.state == "half-open":
            logger.info("✅ Circuit breaker closed, service recovered")
        self.failures = 0
        self.state = "closed"

    def record_failure(self):
        """Record failed request."""
        self.failures += 1
        self.last_failure_time = time.time()
        if self.failures >= self.failure_threshold:
            if self.state != "open":
                logger.error(f"⚡ Circuit breaker OPEN after {self.failures} failures")
            self.state = "open"


class LettaVoiceAssistant(Agent):
    """
    Voice assistant using Letta for orchestration with guaranteed reliability.

    GUARANTEED: This agent ALWAYS returns a valid response, even if:
        - Letta server is down
        - Network is slow/timing out
        - Letta returns empty response
        - Any other error condition

    Reliability is achieved through:
        1. Circuit breaker (fast-fail when Letta is down)
        2. Health checks (verify Letta before calling)
        3. Timeouts (10s max per attempt)
        4. Retry logic (2 retries with exponential backoff)
        5. Response validation (ensure non-empty responses)
        6. Guaranteed fallback (always returns valid message)
    """

    def __init__(self, ctx: JobContext, letta_client: Letta, agent_id: str):
        super().__init__(
            instructions="""You are a helpful voice AI orchestrator with long-term memory.

            You coordinate multiple specialist agents to help users build software.
            You have access to:
            - Memory management agents
            - Research agents
            - Code generation agents
            - Testing agents

            When a user asks for help:
            1. Understand their request
            2. Decide if you can handle it directly or need to delegate
            3. If delegating, explain what you're doing
            4. Provide clear, concise voice responses

            Keep responses conversational and brief for voice output.
            Save important information to your memory blocks for future reference.
            """
        )
        self.ctx = ctx
        self.letta_client = letta_client
        self.agent_id = agent_id
        self.message_history = []
        self.allow_agent_switching = True

        # Idle timeout monitoring
        self.last_activity_time = time.time()
        self.idle_timeout_seconds = _safe_int(
            os.getenv("VOICE_IDLE_TIMEOUT_SECONDS"),
            300,  # Default: 5 minutes
        )
        self.idle_monitor_task = None
        self.is_shutting_down = False

        # RELIABILITY: Circuit breaker for Letta server
        self.letta_circuit_breaker = CircuitBreaker(
            failure_threshold=3,
            timeout_seconds=30
        )

    def _update_activity_time(self):
        """Update the last activity timestamp."""
        self.last_activity_time = time.time()
        logger.debug(f"⏰ Activity updated at {self.last_activity_time}")

    async def _check_letta_health(self) -> bool:
        """
        Quick health check before calling Letta.

        Fast-fail if Letta is down to prevent 30-second timeouts.
        Uses 2-second timeout to fail quickly.

        Returns:
            True if Letta is healthy, False otherwise
        """
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{LETTA_BASE_URL}/admin/health", timeout=2.0)
                return response.status_code == 200
        except Exception as e:
            logger.warning(f"⚠️  Letta health check failed: {e}")
            return False

    async def _guaranteed_fallback_response(self, error_context: str) -> str:
        """
        ALWAYS returns a valid response, even if everything fails.

        This is the last line of defense to ensure the agent NEVER
        returns None or empty string.

        Args:
            error_context: Description of what went wrong

        Returns:
            A valid, user-friendly error message (never empty/None)
        """
        # Select message based on error context
        if "timeout" in error_context.lower():
            message = "I'm taking longer than expected. Let me try a simpler approach."
        elif "circuit" in error_context.lower():
            message = "My backend system is temporarily unavailable. Please try again in a moment."
        elif "health" in error_context.lower():
            message = "I can't connect to my processing system. Please check if the Letta server is running."
        else:
            message = "I'm having trouble connecting to my processing system right now."

        logger.error(f"🚨 FALLBACK RESPONSE: {error_context} -> {message}")

        # Update activity time even on errors
        self._update_activity_time()

        return message

    def _validate_response(self, response_text: str) -> str:
        """
        Ensure response is non-empty and meaningful.

        Args:
            response_text: The response to validate

        Returns:
            Validated response (or fallback if invalid)
        """
        if not response_text:
            return "I didn't generate a response. Could you rephrase that?"

        cleaned = response_text.strip()

        if len(cleaned) < 3:
            return "I need a moment to process that. Could you rephrase?"

        # Check if response is just punctuation or whitespace
        if not any(c.isalnum() for c in cleaned):
            return "I'm having trouble formulating a response. Please try again."

        return response_text

    async def _get_letta_response_with_retry(self, user_message: str, max_retries=2) -> str:
        """
        Send message to Letta with retry logic and circuit breaker protection.

        GUARANTEED to return a valid response string (never None or empty).

        Reliability features:
            1. Circuit breaker check (fast-fail if Letta is down)
            2. Health check before calling
            3. 10-second timeout per attempt
            4. Exponential backoff (2s, 4s)
            5. Response validation
            6. Guaranteed fallback response

        Args:
            user_message: User's text (from STT)
            max_retries: Maximum number of retries (default 2)

        Returns:
            Letta's response text or fallback message (never None/empty)
        """
        # Update activity timestamp
        self._update_activity_time()

        # RELIABILITY CHECK 1: Circuit breaker
        if not self.letta_circuit_breaker.should_allow_request():
            return await self._guaranteed_fallback_response("Circuit breaker open - service unavailable")

        # RELIABILITY CHECK 2: Health check (fast-fail if Letta is down)
        if not await self._check_letta_health():
            self.letta_circuit_breaker.record_failure()
            return await self._guaranteed_fallback_response("Letta server health check failed")

        # Retry loop with exponential backoff
        last_error = None
        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    backoff_seconds = 2 ** attempt  # Exponential backoff: 2s, 4s
                    logger.info(f"⏳ Retry {attempt}/{max_retries} after {backoff_seconds}s backoff")
                    await asyncio.sleep(backoff_seconds)

                # Log attempt
                logger.info(f"📞 Calling Letta (attempt {attempt + 1}/{max_retries + 1})...")

                # RELIABILITY CHECK 3: Call Letta with timeout
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.letta_client.agents.messages.create,
                        agent_id=self.agent_id,
                        messages=[{"role": "user", "content": user_message}]
                    ),
                    timeout=10.0  # 10-second maximum per attempt
                )

                # Extract assistant messages
                assistant_messages = []
                if hasattr(response, 'messages'):
                    for msg in response.messages:
                        if hasattr(msg, 'message_type') and msg.message_type == "assistant_message":
                            if hasattr(msg, 'content'):
                                assistant_messages.append(msg.content)
                        elif hasattr(msg, 'role') and msg.role == "assistant":
                            content = getattr(msg, 'content', None) or getattr(msg, 'text', None)
                            if content:
                                assistant_messages.append(content)

                # RELIABILITY CHECK 4: Validate response
                response_text = " ".join(assistant_messages) if assistant_messages else ""
                validated_response = self._validate_response(response_text)

                # If validation changed the response, it means original was invalid
                if validated_response != response_text and response_text:
                    logger.warning(f"⚠️  Response validation changed output: '{response_text[:50]}' -> '{validated_response[:50]}'")

                # Update history
                self.message_history.append({"role": "user", "content": user_message})
                self.message_history.append({"role": "assistant", "content": validated_response})

                # Record success in circuit breaker
                self.letta_circuit_breaker.record_success()

                logger.info(f"✅ Letta response received ({len(validated_response)} chars)")
                return validated_response

            except asyncio.TimeoutError:
                last_error = f"Timeout after 10 seconds (attempt {attempt + 1})"
                logger.error(f"⏱️  {last_error}")
                self.letta_circuit_breaker.record_failure()

            except Exception as e:
                last_error = f"{type(e).__name__}: {str(e)}"
                logger.error(f"❌ Letta call failed (attempt {attempt + 1}): {last_error}")
                self.letta_circuit_breaker.record_failure()

                if attempt == max_retries:
                    # Last attempt failed - return guaranteed fallback
                    break

        # RELIABILITY CHECK 5: All retries failed - return guaranteed fallback
        return await self._guaranteed_fallback_response(f"Failed after {max_retries + 1} attempts: {last_error}")

    async def llm_node(self, chat_ctx, tools, model_settings):
        """
        Override LLM node to route through Letta orchestrator.
        GUARANTEED to return a valid response (never None or empty).
        """
        # Extract user message
        user_message = _coerce_text(chat_ctx.items[-1].content if chat_ctx.items else "")
        total_start = time.perf_counter()

        logger.info(f"🎤 User message: {user_message}")

        # Publish transcript
        await self._publish_transcript("user", user_message)
        await self._publish_status("transcript_ready", f"Recognized: {user_message[:80] or '<<blank>>'}")

        # Route through Letta with retry and circuit breaker protection
        logger.info("PRE-CALL to _get_letta_response_with_retry")
        letta_start = time.perf_counter()
        await self._publish_status("sending_to_letta", "Contacting Letta orchestrator…")

        response_text = await self._get_letta_response_with_retry(user_message)

        letta_elapsed = time.perf_counter() - letta_start
        logger.info(f"Letta response duration: {letta_elapsed:.2f}s")
        await self._publish_status("letta_response", f"Response ready in {letta_elapsed:.1f}s", letta_elapsed)

        # Final validation (paranoid check - method should guarantee valid response)
        if not response_text or len(response_text.strip()) < 3:
            logger.error(f"🚨 CRITICAL: Invalid response after all safeguards: '{response_text}'")
            response_text = "I apologize, something went wrong with my response generation."

        # Publish complete response
        await self._publish_transcript("assistant", response_text)
        logger.info(f"🔊 Letta response: {response_text[:100]}...")

        total_elapsed = time.perf_counter() - total_start
        logger.info(f"Total llm_node latency: {total_elapsed:.2f}s")

        return response_text

    async def _publish_transcript(self, role: str, text: str):
        """Publish transcript to room for UI display"""
        try:
            data = json.dumps({
                "type": "transcript",
                "role": role,
                "text": text,
                "timestamp": datetime.now().isoformat()
            })
            await self.ctx.room.local_participant.publish_data(
                payload=data.encode(),
                reliable=True,
            )
        except Exception as e:
            logger.error(f"Error publishing transcript: {e}")

    async def _publish_status(self, stage: str, detail: str = "", duration: float | None = None):
        """Publish fine-grained pipeline status for the UI indicators."""
        try:
            payload = {
                "type": "status_update",
                "stage": stage,
                "detail": detail,
                "timestamp": datetime.now().isoformat()
            }
            if duration is not None:
                payload["duration"] = duration

            await self.ctx.room.local_participant.publish_data(
                payload=json.dumps(payload).encode(),
                reliable=True,
            )
        except Exception as e:
            logger.error(f"Error publishing status update '{stage}': {e}")

    async def handle_text_message(self, message: str):
        """Handle text-only messages (no voice) from client"""
        self._update_activity_time()
        logger.info(f"💬 Text message: {message}")

        # Publish user message
        await self._publish_transcript("user", message)

        # Get Letta response with reliability guarantees
        response_text = await self._get_letta_response_with_retry(message)

        # Publish assistant response
        await self._publish_transcript("assistant", response_text)

        # Speak the response
        await self._agent_session.say(response_text, allow_interruptions=True)

    async def switch_agent(self, new_agent_id: str, agent_name: str = None):
        """Switch to a different Letta agent dynamically"""
        if not self.allow_agent_switching:
            logger.warning("Agent switching is disabled")
            return False

        try:
            # Verify the new agent exists
            agent = await asyncio.to_thread(
                self.letta_client.agents.retrieve,
                agent_id=new_agent_id
            )

            if not agent:
                logger.error(f"Agent {new_agent_id} not found")
                return False

            # Switch to new agent
            old_agent_id = self.agent_id
            self.agent_id = new_agent_id
            self.message_history = []  # Clear history for new agent

            logger.info(f"✅ Switched from agent {old_agent_id} to {new_agent_id} ({agent_name or 'unnamed'})")

            # Notify user via voice
            switch_message = f"Switched to agent {agent_name or new_agent_id}. How can I help you?"
            await self._publish_transcript("system", switch_message)

            try:
                await self._agent_session.say(switch_message, allow_interruptions=True)
            except (RuntimeError, AttributeError) as e:
                logger.warning(f"Could not announce agent switch via voice (session not ready): {e}")

            return True

        except Exception as e:
            logger.error(f"Error switching agent: {e}")
            return False

    async def _start_idle_monitor(self):
        """Start background task to monitor idle time and disconnect after timeout."""
        if self.idle_monitor_task is not None:
            return  # Already running
        if self.idle_timeout_seconds <= 0:
            logger.info("⏰ Idle monitor disabled (VOICE_IDLE_TIMEOUT_SECONDS <= 0)")
            return

        async def monitor_idle():
            while not self.is_shutting_down:
                await asyncio.sleep(1)  # Check every second
                participant_count = len(self.ctx.room.remote_participants or {})
                if participant_count > 0:
                    # Keep session alive while a user is connected
                    self.last_activity_time = time.time()
                    continue

                idle_time = time.time() - self.last_activity_time
                if idle_time > self.idle_timeout_seconds:
                    logger.warning(
                        "⏱️  Idle timeout reached with no remote participants "
                        f"({idle_time:.1f}s > {self.idle_timeout_seconds}s)"
                    )
                    logger.info("🛑 Shutting down agent due to inactivity...")

                    # Set shutdown flag
                    self.is_shutting_down = True

                    # Notify user
                    try:
                        await self._publish_transcript(
                            "system",
                            "Session ended due to inactivity. Goodbye!"
                        )
                    except Exception as e:
                        logger.error(f"Error publishing shutdown message: {e}")

                    # Disconnect from room
                    try:
                        await self.ctx.room.disconnect()
                        logger.info("✅ Agent disconnected successfully")
                    except Exception as e:
                        logger.error(f"Error disconnecting: {e}")

                    break

        self.idle_monitor_task = asyncio.create_task(monitor_idle())
        logger.info(f"⏰ Idle monitor started (timeout: {self.idle_timeout_seconds}s)")


# Agent creation and setup (from original)
async def get_or_create_orchestrator(letta_client: Letta) -> str:
    """Get or create the voice orchestrator agent (Factory pattern)."""
    agent_name = "Agent_66"
    llm_endpoint = os.getenv("LETTA_ORCHESTRATOR_ENDPOINT_TYPE", "openai")
    llm_model = _normalize_model_name(os.getenv("LETTA_ORCHESTRATOR_MODEL", "gpt-5-mini"), llm_endpoint)

    if not llm_model:
        llm_model = "gpt-5-mini"
    elif llm_model not in ALLOWED_ORCHESTRATOR_MODELS:
        logger.warning(
            "Unsupported LETTA_ORCHESTRATOR_MODEL '%s'. Falling back to gpt-5-mini. "
            "Allowed values: %s",
            llm_model,
            ", ".join(sorted(ALLOWED_ORCHESTRATOR_MODELS)),
        )
        llm_model = "gpt-5-mini"

    context_window = _safe_int(os.getenv("LETTA_CONTEXT_WINDOW"), 400000)
    embedding_endpoint = os.getenv("LETTA_EMBEDDING_ENDPOINT_TYPE", "openai")
    embedding_model = os.getenv("LETTA_EMBEDDING_MODEL", "openai/text-embedding-3-small")
    embedding_dim = _safe_int(os.getenv("LETTA_EMBEDDING_DIM"), 1536)

    try:
        # Try to find existing agent
        agents_list = await asyncio.to_thread(letta_client.agents.list)
        agents = list(agents_list) if agents_list else []

        for agent in agents:
            if hasattr(agent, 'name') and agent.name == agent_name:
                updates = {}
                current_llm = getattr(agent, "llm_config", None)
                current_embedding = getattr(agent, "embedding_config", None)

                llm_needs_update = not current_llm or any([
                    getattr(current_llm, "model", None) != llm_model,
                    getattr(current_llm, "model_endpoint_type", None) != llm_endpoint,
                    getattr(current_llm, "context_window", None) != context_window,
                ])
                if llm_needs_update:
                    updates["llm_config"] = {
                        "model": llm_model,
                        "model_endpoint_type": llm_endpoint,
                        "context_window": context_window,
                    }

                embedding_needs_update = not current_embedding or any([
                    getattr(current_embedding, "embedding_model", None) != embedding_model,
                    getattr(current_embedding, "embedding_endpoint_type", None) != embedding_endpoint,
                    getattr(current_embedding, "embedding_dim", None) != embedding_dim,
                ])
                if embedding_needs_update:
                    updates["embedding_config"] = {
                        "embedding_model": embedding_model,
                        "embedding_endpoint_type": embedding_endpoint,
                        "embedding_dim": embedding_dim,
                    }

                if updates:
                    logger.info(
                        "Updating voice orchestrator %s config (llm_model=%s, embedding_model=%s)",
                        agent.id,
                        llm_model,
                        embedding_model,
                    )
                    await asyncio.to_thread(
                        letta_client.agents.update,
                        agent_id=agent.id,
                        **updates,
                    )

                logger.info(f"Found existing orchestrator: {agent.id}")
                return agent.id

        # Create new orchestrator
        logger.info("Creating new voice orchestrator agent...")
        agent = await asyncio.to_thread(
            letta_client.agents.create,
            name=agent_name,
            llm_config={
                "model": llm_model,
                "model_endpoint_type": llm_endpoint,
                "context_window": context_window
            },
            embedding_config={
                "embedding_model": embedding_model,
                "embedding_endpoint_type": embedding_endpoint,
                "embedding_dim": embedding_dim
            },
            memory_blocks=[
                {
                    "label": "persona",
                    "value": (
                        "I am a voice-enabled orchestration agent. "
                        "I coordinate specialist agents (memory, research, code generation, testing) "
                        "to help users build high-quality software using GoF design patterns. "
                        "I maintain conversation context and delegate tasks appropriately."
                    )
                },
                {
                    "label": "conversation_log",
                    "value": "Voice conversation history and important context."
                }
            ],
            enable_sleeptime=True,      # Move memory management to background
            include_base_tools=False    # Disable self-memory tools
        )

        logger.info(f"Created orchestrator: {agent.id}")
        return agent.id

    except Exception as e:
        logger.error(f"Error getting/creating orchestrator: {e}")
        import traceback
        traceback.print_exc()
        raise


async def _graceful_shutdown(ctx: JobContext):
    """Gracefully shut down the voice agent when user requests cleanup."""
    try:
        logger.info("⏳ Initiating graceful shutdown...")
        await ctx.room.disconnect()
        logger.info("✅ Graceful shutdown complete")
    except Exception as e:
        logger.error(f"Error during graceful shutdown: {e}")


async def entrypoint(ctx: JobContext):
    """
    Main entry point for Livekit voice agent.
    Sets up voice pipeline and connects to Letta orchestrator.
    """
    logger.info(f"🚀 RELIABLE Voice agent starting in room: {ctx.room.name}")

    # Initialize Letta client
    if LETTA_API_KEY:
        letta_client = Letta(api_key=LETTA_API_KEY)
    else:
        letta_client = Letta(base_url=LETTA_BASE_URL)

    # Get or create orchestrator agent
    try:
        agent_id = await get_or_create_orchestrator(letta_client)
    except Exception as e:
        logger.error(f"Failed to initialize Letta orchestrator: {e}")
        return

    # Configure voice pipeline
    tts_provider = os.getenv("TTS_PROVIDER", "openai")

    if tts_provider == "cartesia" and os.getenv("CARTESIA_API_KEY"):
        tts = cartesia.TTS(
            voice="79a125e8-cd45-4c13-8a67-188112f4dd22",  # British narrator
        )
        logger.info("Using Cartesia TTS")
    else:
        tts = openai.TTS(
            voice=os.getenv("OPENAI_TTS_VOICE", "nova"),
            speed=1.0,
        )
        logger.info("Using OpenAI TTS")

    session = AgentSession(
        stt=deepgram.STT(
            model="nova-2",
            language="en",
        ),
        llm=openai.LLM(model="gpt-5-mini"),
        tts=tts,
        vad=silero.VAD.load(
            min_speech_duration=0.1,
            min_silence_duration=0.8,
            prefix_padding_duration=0.6,
            activation_threshold=0.5,
        ),
    )

    # Create RELIABLE assistant instance
    assistant = LettaVoiceAssistant(ctx, letta_client, agent_id)
    assistant._agent_session = session

    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        logger.debug(f"Participant connected: {participant.identity}")

    @ctx.room.on("track_subscribed")
    def on_track_subscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
        logger.debug(f"Track subscribed: {track.sid}")
        if track.kind == 1:
            logger.info("Audio track subscribed for participant %s, starting STT.", participant.identity)

    @ctx.room.on("data_received")
    def on_data_received(data_packet: rtc.DataPacket):
        """Handle incoming data messages"""
        try:
            message_str = data_packet.data.decode('utf-8')
            message_data = json.loads(message_str)

            if message_data.get("type") == "room_cleanup":
                logger.info("🧹 Room cleanup requested - preparing to exit room")
                asyncio.create_task(_graceful_shutdown(ctx))

            elif message_data.get("type") == "agent_selection":
                agent_id = message_data.get("agent_id")
                agent_name = message_data.get("agent_name", "Unknown")
                if agent_id:
                    logger.info(f"🔄 Agent selection request: {agent_name} ({agent_id})")
                    asyncio.create_task(assistant.switch_agent(agent_id, agent_name))

            elif message_data.get("type") == "chat":
                user_message = message_data.get("message", "")
                if user_message:
                    logger.info(f"📨 Text chat: {user_message}")
                    asyncio.create_task(assistant.handle_text_message(user_message))

        except Exception as e:
            logger.error(f"Error handling data message: {e}")

    # Start the session
    logger.info("🚀 RELIABLE voice agent starting in room: " + ctx.room.name)
    await session.start(
        room=ctx.room,
        agent=assistant,
        room_output_options=RoomOutputOptions(transcription_enabled=True),
    )

    # Start idle timeout monitor
    await assistant._start_idle_monitor()

    logger.info("✅ RELIABLE voice agent ready and listening")
    logger.info("🛡️  Reliability features active:")
    logger.info("   • Circuit breaker (fast-fail when Letta is down)")
    logger.info("   • Health checks (verify Letta before calls)")
    logger.info("   • 10-second timeout per attempt")
    logger.info("   • 2 retries with exponential backoff")
    logger.info("   • Response validation (ensures non-empty)")
    logger.info("   • Guaranteed fallback (ALWAYS returns valid response)")


async def request_handler(job_request: JobRequest):
    """Accept all job requests with enhanced room validation and retry logic."""
    room_name = job_request.room.name
    logger.info(f"📥 Job request received for room: {room_name}")

    # Enhanced room self-recovery with retry
    max_cleanup_retries = 3
    for attempt in range(max_cleanup_retries):
        try:
            from livekit_room_manager import RoomManager
            manager = RoomManager()

            logger.info(f"🧹 Ensuring room {room_name} is clean (attempt {attempt + 1}/{max_cleanup_retries})...")
            await manager.ensure_clean_room(room_name)

            # Verify room is actually clean
            rooms = await manager.list_rooms()
            room_participants = []
            for room in rooms:
                if room.name == room_name:
                    participants = await manager.list_participants(room_name)
                    room_participants = participants
                    if len(participants) > 0:
                        # Check if they're agents or stale
                        stale_found = False
                        for p in participants:
                            is_agent = (
                                'agent' in p.identity.lower() or
                                'bot' in p.identity.lower() or
                                p.identity.startswith('AW_')
                            )
                            if is_agent:
                                stale_found = True
                                break

                        if stale_found:
                            logger.warning(f"Room still has stale/agent participants after cleanup, retrying...")
                            await asyncio.sleep(1)
                            continue
                        else:
                            logger.info(f"Room has {len(participants)} active human users - proceeding")
                            break

            logger.info(f"✅ Room {room_name} is clean and ready for agent")
            break

        except Exception as e:
            if attempt == max_cleanup_retries - 1:
                logger.error(f"Room cleanup failed after {max_cleanup_retries} attempts: {e}")
                # Continue anyway - agent will try to join
            else:
                logger.warning(f"Room cleanup attempt {attempt + 1} failed: {e}, retrying...")
                await asyncio.sleep(2)

    await job_request.accept()
    logger.info(f"✅ Job accepted, starting RELIABLE entrypoint...")


if __name__ == "__main__":
    # Run the RELIABLE agent using Livekit CLI
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        request_fnc=request_handler,
    ))
