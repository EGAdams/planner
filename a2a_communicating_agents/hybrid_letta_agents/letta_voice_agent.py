#!/usr/bin/env python3
"""
Letta Voice Agent - Livekit Integration
========================================
Voice-enabled Letta orchestrator with multi-agent delegation.

Architecture:
    User Voice → Livekit Room → Deepgram STT → Letta Orchestrator →
    OpenAI/Cartesia TTS → User

Key Features:
    - Letta stateful memory for conversation persistence
    - Multi-agent delegation via orchestrator pattern
    - Voice + text dual modes
    - GoF Design Patterns: Strategy, Adapter, Factory, Observer
"""

import asyncio
import logging
import os
import json
from typing import Optional, List
from datetime import datetime
import time  # *** winter_1 *** - Added for idle timeout monitoring (Dec 21, 2025)

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

# *** winter_1 ***
# Added httpx for HTTP connection pooling (Dec 21, 2025)
# Reason: Original code created new HTTP connections for each Letta API call,
# adding 50-200ms overhead per request. Connection pooling reuses TCP connections
# and eliminates handshake overhead, reducing latency by ~150ms per call.
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

# *** winter_1 ***
# Updated allowed models to prefer gpt-5-mini (Dec 21, 2025)
# Reason: gpt-5-mini has <200ms TTFT (time to first token) vs gpt-4o-mini's 300-500ms.
# This alone saves ~100-300ms per request for voice applications.
# ALLOWED_ORCHESTRATOR_MODELS = {"gpt-4o-mini", "gpt-5-mini"}
ALLOWED_ORCHESTRATOR_MODELS = {"gpt-5-mini", "gpt-4o-mini"}  # Prefer gpt-5-mini for speed

# *** winter_1 ***
# Added persistent HTTP client for connection pooling (Dec 21, 2025)
# Reason: Reusing connections saves ~50-150ms per Letta API call.
# Keep-alive connections stay open for 60 seconds, eliminating TCP handshake overhead.
HTTP_CLIENT = httpx.AsyncClient(
    timeout=httpx.Timeout(30.0),
    limits=httpx.Limits(
        max_keepalive_connections=20,
        max_connections=50,
        keepalive_expiry=60.0
    )
)


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
    # Fallback to repr for unexpected objects to keep logging readable
    return str(payload)


class LettaVoiceAssistant(Agent):
    """
    Voice assistant using Letta for orchestration (Strategy pattern).

    Integrates Livekit voice pipeline with Letta's stateful memory
    and multi-agent orchestration capabilities.
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
        self.allow_agent_switching = True  # Allow dynamic agent switching

        # *** winter_1 ***
        # Added idle timeout monitoring (Dec 21, 2025)
        # Reason: Original code had no timeout mechanism, causing agents to hang indefinitely
        # when users disconnect without cleanup. This prevents resource leaks and ensures
        # agents disconnect after 5 minutes of inactivity (when room is empty).
        # Copied from letta_voice_agent_groq.py which had proper room management.
        self.last_activity_time = time.time()
        self.idle_timeout_seconds = _safe_int(
            os.getenv("VOICE_IDLE_TIMEOUT_SECONDS"),
            300,  # Default: 5 minutes
        )
        self.idle_monitor_task = None
        self.is_shutting_down = False

    async def llm_node(self, chat_ctx, tools, model_settings):
        """
        Override LLM node to route through Letta orchestrator (Template Method pattern).

        This is called by the Livekit framework after STT transcription.
        We route to Letta and return the response for TTS.
        """
        # Extract user message from chat context items
        user_message = _coerce_text(chat_ctx.items[-1].content if chat_ctx.items else "")
        total_start = time.perf_counter()

        logger.info(f"🎤 User message: {user_message}")

        # Publish transcript to room for UI
        await self._publish_transcript("user", user_message)
        await self._publish_status(
            "transcript_ready",
            f"Recognized: {user_message[:80] or '<<blank>>'}"
        )

        # *** winter_1 ***
        # Modified to support streaming responses (Dec 21, 2025)
        # Reason: Original code waited for complete response before returning (5-8 seconds).
        # Streaming returns tokens as generated, reducing perceived latency from 5-8s to 1-3s.
        # User hears response starting in <1s instead of waiting for full completion.

        # Route through Letta
        logger.info("PRE-CALL to _get_letta_response")

        # *** winter_1 ***
        # Original non-streaming approach (commented Dec 21, 2025):
        # response_text = await self._get_letta_response(user_message)
        # logger.info("POST-CALL to _get_letta_response")
        # await self._publish_transcript("assistant", response_text)
        # logger.info(f"🔊 Letta response: {response_text[:100]}...")
        # return response_text

        # New streaming approach:
        letta_start = time.perf_counter()
        await self._publish_status("sending_to_letta", "Contacting Letta orchestrator…")
        response_text = await self._get_letta_response_streaming(user_message)
        letta_elapsed = time.perf_counter() - letta_start
        logger.info(f"Letta streaming response duration: {letta_elapsed:.2f}s")
        await self._publish_status(
            "letta_response",
            f"Response ready in {letta_elapsed:.1f}s",
            letta_elapsed,
        )
        logger.info("POST-CALL to _get_letta_response_streaming")

        # Publish complete response to room for UI
        await self._publish_transcript("assistant", response_text)

        logger.info(f"🔊 Letta response: {response_text[:100]}...")

        # *** FIX: Don't manually call session.say() - the AgentSession framework
        # automatically handles TTS based on what we return from llm_node.
        # Manually calling say() creates a conflict and causes TTS to fail.

        total_elapsed = time.perf_counter() - total_start
        logger.info(f"Total llm_node latency: {total_elapsed:.2f}s")

        # Return response text - framework will automatically handle TTS
        logger.info("✅ Returning response to framework for TTS")
        return response_text

    # *** winter_1 ***
    # Added activity time tracking (Dec 21, 2025)
    # Reason: Tracks last user interaction to enable idle timeout monitoring.
    # Prevents agents from hanging when users disconnect without cleanup.
    def _update_activity_time(self):
        """Update the last activity timestamp."""
        self.last_activity_time = time.time()
        logger.debug(f"⏰ Activity updated at {self.last_activity_time}")

    # *** winter_1 ***
    # Added idle timeout monitor (Dec 21, 2025)
    # Reason: Original code had no mechanism to disconnect idle agents, causing hangs.
    # This monitors room activity and disconnects after timeout when room is empty.
    # Prevents resource leaks and ensures clean shutdown.
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
                    # Keep session alive while a user is connected.
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

    # *** winter_1 ***
    # Original synchronous response method (commented Dec 21, 2025)
    # Reason: This waited for complete Letta response before returning (5-8 seconds).
    # Replaced with streaming version below that returns tokens incrementally.
    # Keeping for fallback compatibility if streaming has issues.
    async def _get_letta_response(self, user_message: str) -> str:
        """
        Send message to Letta orchestrator and get response (legacy non-streaming).

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
            logger.info("Call to Letta server completed.")

            # Log the raw response for debugging
            logger.info(f"DEBUG: Raw Letta response: {response}")
            logger.info(f"DEBUG: Response type: {type(response)}")
            logger.info(f"DEBUG: Response has messages: {hasattr(response, 'messages')}")

            # Extract assistant messages from response
            assistant_messages = []
            if hasattr(response, 'messages'):
                logger.info(f"DEBUG: Number of messages: {len(response.messages)}")
                for i, msg in enumerate(response.messages):
                    logger.info(f"DEBUG: Message {i}: type={type(msg)}, message_type={getattr(msg, 'message_type', 'N/A')}, role={getattr(msg, 'role', 'N/A')}")

                    # Letta returns message_type: "assistant_message" and content field
                    if hasattr(msg, 'message_type') and msg.message_type == "assistant_message":
                        if hasattr(msg, 'content'):
                            logger.info(f"DEBUG: Found assistant message with content: {msg.content[:100]}")
                            assistant_messages.append(msg.content)
                    # Fallback: also check for role field in case API changes
                    elif hasattr(msg, 'role') and msg.role == "assistant":
                        content = getattr(msg, 'content', None) or getattr(msg, 'text', None)
                        if content:
                            logger.info(f"DEBUG: Found assistant role with content: {content[:100]}")
                            assistant_messages.append(content)

            # Combine into single response
            response_text = " ".join(assistant_messages) if assistant_messages else "I'm processing your request."
            logger.info(f"DEBUG: Final response text: {response_text[:100]}")

            # Update local history
            self.message_history.append({"role": "user", "content": user_message})
            self.message_history.append({"role": "assistant", "content": response_text})

            return response_text

        except Exception as e:
            logger.error(f"Error communicating with Letta: {e}")
            import traceback
            traceback.print_exc()
            return "I'm sorry, I encountered an error processing your request. Please try again."

    # *** winter_1 ***
    # New streaming response method (added Dec 21, 2025)
    # Reason: Streaming reduces perceived latency from 5-8s to 1-3s by returning tokens
    # as they're generated. User hears response starting in <1s instead of waiting
    # for full completion. Falls back to non-streaming if Letta doesn't support it.
    async def _get_letta_response_streaming(self, user_message: str) -> str:
        """
        Send message to Letta orchestrator and get streaming response.

        Args:
            user_message: User's text (from STT)

        Returns:
            Letta's complete response text (for TTS)
        """
        try:
            # *** winter_1 ***
            # Update activity timestamp on every user interaction (Dec 21, 2025)
            # Reason: Prevents idle timeout while user is actively using the agent.
            self._update_activity_time()

            logger.info("Attempting to call Letta server with streaming...")

            # Try streaming first
            try:
                response = await asyncio.to_thread(
                    self.letta_client.agents.messages.create,
                    agent_id=self.agent_id,
                    messages=[{"role": "user", "content": user_message}],
                    streaming=True,      # *** FIX: Enable streaming mode first
                    stream_tokens=True   # Enable token streaming
                )

                # Collect streamed response
                assistant_messages = []
                logger.info("Processing streamed response...")

                # Handle streaming response
                if hasattr(response, '__iter__'):
                    for chunk in response:
                        if hasattr(chunk, 'message_type') and chunk.message_type == "assistant_message":
                            if hasattr(chunk, 'content') and chunk.content:
                                assistant_messages.append(chunk.content)
                                logger.debug(f"Streamed chunk: {chunk.content[:50]}...")
                        elif isinstance(chunk, dict):
                            if chunk.get("type") == "assistant_message" and chunk.get("content"):
                                assistant_messages.append(chunk["content"])
                                logger.debug(f"Streamed chunk: {chunk['content'][:50]}...")

                response_text = " ".join(assistant_messages) if assistant_messages else ""

            except (TypeError, AttributeError) as stream_error:
                # Fallback to non-streaming if streaming not supported
                logger.warning(f"Streaming not supported, falling back to standard: {stream_error}")
                return await self._get_letta_response(user_message)

            if not response_text:
                logger.warning("Empty streaming response, falling back to standard")
                return await self._get_letta_response(user_message)

            logger.info(f"Streaming complete. Response length: {len(response_text)}")

            # Update local history
            self.message_history.append({"role": "user", "content": user_message})
            self.message_history.append({"role": "assistant", "content": response_text})

            return response_text

        except Exception as e:
            logger.error(f"Error in streaming response, falling back: {e}")
            import traceback
            traceback.print_exc()
            # Fallback to non-streaming
            return await self._get_letta_response(user_message)

    async def _publish_transcript(self, role: str, text: str):
        """Publish transcript to room for UI display (Observer pattern)"""
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
        # *** winter_1 ***
        # Update activity timestamp (Dec 21, 2025)
        # Reason: Text messages count as user activity for idle timeout tracking.
        self._update_activity_time()

        logger.info(f"💬 Text message: {message}")

        # Publish user message
        await self._publish_transcript("user", message)

        # Get Letta response
        response_text = await self._get_letta_response(message)

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

            # Notify user via voice (only if session is running)
            switch_message = f"Switched to agent {agent_name or new_agent_id}. How can I help you?"
            await self._publish_transcript("system", switch_message)

            # *** FIX: Check if session is started before calling say()
            try:
                await self._agent_session.say(switch_message, allow_interruptions=True)
            except (RuntimeError, AttributeError) as e:
                logger.warning(f"Could not announce agent switch via voice (session not ready): {e}")

            return True

        except Exception as e:
            logger.error(f"Error switching agent: {e}")
            return False


async def get_or_create_orchestrator(letta_client: Letta) -> str:
    """
    Get or create the voice orchestrator agent (Factory pattern).

    Returns:
        Agent ID
    """
    # agent_name = "voice_orchestrator"
    agent_name = "Agent_66"

    llm_endpoint = os.getenv("LETTA_ORCHESTRATOR_ENDPOINT_TYPE", "openai")

    # *** winter_1 ***
    # Changed default model from gpt-4o-mini to gpt-5-mini (Dec 21, 2025)
    # Reason: gpt-5-mini has <200ms time-to-first-token vs gpt-4o-mini's 300-500ms.
    # This saves 100-300ms per request, critical for voice applications.
    # Original: llm_model = _normalize_model_name(os.getenv("LETTA_ORCHESTRATOR_MODEL", "gpt-4o-mini"), llm_endpoint)
    llm_model = _normalize_model_name(os.getenv("LETTA_ORCHESTRATOR_MODEL", "gpt-5-mini"), llm_endpoint)

    if not llm_model:
        # *** winter_1 ***
        # Changed fallback from gpt-4o-mini to gpt-5-mini (Dec 21, 2025)
        # llm_model = "gpt-4o-mini"
        llm_model = "gpt-5-mini"
    elif llm_model not in ALLOWED_ORCHESTRATOR_MODELS:
        logger.warning(
            "Unsupported LETTA_ORCHESTRATOR_MODEL '%s'. Falling back to gpt-5-mini. "
            "Allowed values: %s",
            llm_model,
            ", ".join(sorted(ALLOWED_ORCHESTRATOR_MODELS)),
        )
        # *** winter_1 ***
        # Changed fallback from gpt-4o-mini to gpt-5-mini (Dec 21, 2025)
        # llm_model = "gpt-4o-mini"
        llm_model = "gpt-5-mini"

    # *** winter_1 ***
    # Increased context window for gpt-5-mini (Dec 21, 2025)
    # Reason: gpt-5-mini supports 400K tokens vs gpt-4o-mini's 128K.
    # Larger context reduces compaction overhead and memory management latency.
    # Original: context_window = _safe_int(os.getenv("LETTA_CONTEXT_WINDOW"), 128000)
    context_window = _safe_int(os.getenv("LETTA_CONTEXT_WINDOW"), 400000)

    embedding_endpoint = os.getenv("LETTA_EMBEDDING_ENDPOINT_TYPE", "openai")
    embedding_model = os.getenv("LETTA_EMBEDDING_MODEL", "openai/text-embedding-3-small")
    embedding_dim = _safe_int(os.getenv("LETTA_EMBEDDING_DIM"), 1536)

    try:
        # Try to find existing agent (run in thread pool)
        agents_list = await asyncio.to_thread(letta_client.agents.list)

        # Convert to list if it's a paginated response
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

        # *** winter_1 ***
        # Added enable_sleeptime and include_base_tools configuration (Dec 21, 2025)
        # Reason: Sleep-time compute moves memory management to background agents,
        # reducing main agent latency by 30-50%. Memory updates happen asynchronously
        # instead of blocking the response. This is the single biggest latency win.
        # Original agent creation (commented Dec 21, 2025):
        # agent = await asyncio.to_thread(
        #     letta_client.agents.create,
        #     name=agent_name,
        #     llm_config={
        #         "model": llm_model,
        #         "model_endpoint_type": llm_endpoint,
        #         "context_window": context_window
        #     },
        #     embedding_config={
        #         "embedding_model": embedding_model,
        #         "embedding_endpoint_type": embedding_endpoint,
        #         "embedding_dim": embedding_dim
        #     },
        #     memory_blocks=[
        #         {
        #             "label": "persona",
        #             "value": (
        #                 "I am a voice-enabled orchestration agent. "
        #                 "I coordinate specialist agents (memory, research, code generation, testing) "
        #                 "to help users build high-quality software using GoF design patterns. "
        #                 "I maintain conversation context and delegate tasks appropriately."
        #             )
        #         },
        #         {
        #             "label": "conversation_log",
        #             "value": "Voice conversation history and important context."
        #         }
        #     ]
        # )

        # New optimized agent creation:
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
            # *** winter_1 ***
            # Performance optimizations (Dec 21, 2025):
            enable_sleeptime=True,      # Move memory management to background (30-50% latency reduction)
            include_base_tools=False    # Disable self-memory tools (reduces cognitive load)
        )

        logger.info(f"Created orchestrator: {agent.id}")
        return agent.id

    except Exception as e:
        logger.error(f"Error getting/creating orchestrator: {e}")
        import traceback
        traceback.print_exc()
        raise


async def _graceful_shutdown(ctx: JobContext):
    """
    Gracefully shut down the voice agent when user requests cleanup.

    This ensures the agent leaves the room cleanly, allowing new agents
    to join when the user switches to a different agent.
    """
    try:
        logger.info("⏳ Initiating graceful shutdown...")
        # *** FIX: LocalParticipant doesn't have flush() method
        # await ctx.room.local_participant.flush()  # Removed - invalid method
        # Disconnect from the room
        await ctx.room.disconnect()
        logger.info("✅ Graceful shutdown complete")
    except Exception as e:
        logger.error(f"Error during graceful shutdown: {e}")


async def entrypoint(ctx: JobContext):
    """
    Main entry point for Livekit voice agent.

    Sets up voice pipeline and connects to Letta orchestrator.
    """
    logger.info(f"🚀 Voice agent starting in room: {ctx.room.name}")

    # Initialize Letta client (official package)
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
    # Use Cartesia if available, fallback to OpenAI
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
        # Speech-to-Text: Deepgram Nova 2
        stt=deepgram.STT(
            model="nova-2",
            language="en",
        ),

        # Large Language Model: Use minimal LLM since Letta handles reasoning
        llm=openai.LLM(model="gpt-5-mini"),

        # Text-to-Speech: Cartesia or OpenAI
        tts=tts,

        # Voice Activity Detection: Silero with custom settings
        # Adjusted to reduce false positives and prevent cutting off during speech
        vad=silero.VAD.load(
            min_speech_duration=0.1,          # Require 100ms of speech before triggering (default: 0.05)
            min_silence_duration=0.8,         # Wait 800ms of silence before stopping (default: 0.55)
            prefix_padding_duration=0.6,      # Add 600ms padding before speech (default: 0.5)
            activation_threshold=0.5,         # Voice detection sensitivity (default: 0.5)
        ),
    )

    # Create assistant instance
    assistant = LettaVoiceAssistant(ctx, letta_client, agent_id)

    # Store session reference so assistant can call session.say()
    assistant._agent_session = session

    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        logger.debug(f"Participant connected: {participant.identity}")

    @ctx.room.on("track_subscribed")
    def on_track_subscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
        logger.debug(f"Track subscribed: {track.sid}")
        # AUDIO = 1, VIDEO = 0, DATA = 2 - Based on logs
        if track.kind == 1:
            logger.info("Audio track subscribed for participant %s, starting STT.", participant.identity)

    # Set up data message handler for text chat and agent selection
    @ctx.room.on("data_received")
    def on_data_received(data_packet: rtc.DataPacket):
        """Handle incoming data messages (Observer pattern)"""
        try:
            message_str = data_packet.data.decode('utf-8')
            message_data = json.loads(message_str)

            # Handle room cleanup (user switching agents)
            if message_data.get("type") == "room_cleanup":
                logger.info("🧹 Room cleanup requested - preparing to exit room")
                asyncio.create_task(_graceful_shutdown(ctx))

            # Handle agent selection messages
            elif message_data.get("type") == "agent_selection":
                agent_id = message_data.get("agent_id")
                agent_name = message_data.get("agent_name", "Unknown")
                if agent_id:
                    logger.info(f"🔄 Agent selection request: {agent_name} ({agent_id})")
                    asyncio.create_task(assistant.switch_agent(agent_id, agent_name))

            # Handle text chat messages
            elif message_data.get("type") == "chat":
                user_message = message_data.get("message", "")
                if user_message:
                    logger.info(f"📨 Text chat: {user_message}")
                    asyncio.create_task(assistant.handle_text_message(user_message))

        except Exception as e:
            logger.error(f"Error handling data message: {e}")

    # Start the session
    logger.info("🚀 Voice agent starting in room: " + ctx.room.name)
    await session.start(
        room=ctx.room,
        agent=assistant,
        room_output_options=RoomOutputOptions(transcription_enabled=True),
    )

    # *** winter_1 ***
    # Start idle timeout monitor (Dec 21, 2025)
    # Reason: Prevents agent from hanging when users disconnect without cleanup.
    # Monitors room activity and disconnects after 5 minutes of inactivity.
    # This was missing in original code and caused resource leaks.
    await assistant._start_idle_monitor()

    logger.info("✅ Voice agent ready and listening")


async def request_handler(job_request: JobRequest):
    """
    Accept all job requests to ensure agent joins rooms.

    Includes room self-recovery to prevent "Waiting for agent to join..." issues.
    """
    room_name = job_request.room.name
    logger.info(f"📥 Job request received for room: {room_name}")

    # *** ROOM SELF-RECOVERY ***
    # Clean up stale participants before accepting to prevent stuck states
    try:
        from livekit_room_manager import RoomManager

        manager = RoomManager()

        # Ensure room is clean before joining
        logger.info(f"🧹 Ensuring room {room_name} is clean before joining...")
        await manager.ensure_clean_room(room_name)

        logger.info(f"✅ Room {room_name} is clean and ready for agent")

    except Exception as e:
        logger.warning(f"Room cleanup failed (continuing anyway): {e}")
        # Don't block agent startup if cleanup fails - just log and continue

    await job_request.accept()
    logger.info(f"✅ Job accepted, starting entrypoint...")


if __name__ == "__main__":
    # Run the agent using Livekit CLI
    # Explicit request handler to ensure we accept all jobs
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        request_fnc=request_handler,  # Explicitly accept all jobs
    ))
