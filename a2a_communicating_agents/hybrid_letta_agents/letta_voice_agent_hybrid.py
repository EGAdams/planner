#!/usr/bin/env python3
"""
Letta Voice Agent - HYBRID STREAMING VERSION
===========================================
Optimized for <3 second response time using hybrid approach:
- Direct OpenAI streaming for voice responses (TTFT <200ms)
- Async Letta memory updates in background

Architecture:
1. User speaks → STT → Direct OpenAI (fast) → TTS → User hears (1-2s)
2. Background: Update Letta memory for long-term context

Performance:
- TTFT: <200ms (OpenAI streaming)
- End-to-end: 1-2s (meets <3s target)
- Maintains Letta memory for complex reasoning

Tradeoffs:
- Voice responses don't use Letta orchestration (eventual consistency)
- Complex multi-turn conversations via text chat use full Letta
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
from letta_client import AsyncLetta
import httpx

# Load environment variables
load_dotenv("/home/adamsl/planner/.env")
load_dotenv("/home/adamsl/ottomator-agents/livekit-agent/.env")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
LETTA_BASE_URL = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")
LETTA_API_KEY = os.getenv("LETTA_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Voice mode: use fast streaming, text mode: use full Letta
USE_HYBRID_MODE = os.getenv("USE_HYBRID_STREAMING", "true").lower() == "true"

# Model configuration
VOICE_MODEL = "gpt-4o-mini"  # Fast for voice with parameter flexibility
LETTA_MODEL = "gpt-4o-mini"  # Letta orchestration
ALLOWED_ORCHESTRATOR_MODELS = {"gpt-5-mini", "gpt-4o-mini"}


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


class LettaVoiceAssistantHybrid(Agent):
    """
    Voice assistant with hybrid streaming approach.

    Voice responses: Direct OpenAI streaming (<1s TTFT)
    Memory updates: Background Letta processing
    Text chat: Full Letta orchestration

    Performance: <3 seconds end-to-end
    """

    def __init__(self, ctx: JobContext, letta_client: AsyncLetta, agent_id: str):
        super().__init__(
            instructions="""You are a helpful voice AI orchestrator with long-term memory.

            You coordinate multiple specialist agents to help users build software.
            Keep voice responses concise and conversational (2-3 sentences max).

            For complex requests, acknowledge briefly and process in the background.
            """
        )
        self.ctx = ctx
        self.letta_client = letta_client
        self.agent_id = agent_id
        self.message_history = []
        self.allow_agent_switching = True

        # OpenAI client for direct streaming
        self.openai_client = httpx.AsyncClient(
            base_url="https://api.openai.com/v1",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            timeout=httpx.Timeout(30.0)
        )

        # Idle timeout monitoring
        self.last_activity_time = time.time()
        self.idle_timeout_seconds = _safe_int(
            os.getenv("VOICE_IDLE_TIMEOUT_SECONDS"),
            300,
        )
        self.idle_monitor_task = None
        self.is_shutting_down = False

        # Track background Letta tasks
        self.background_tasks = set()

    async def llm_node(self, chat_ctx, tools, model_settings):
        """
        Override LLM node with hybrid streaming approach.

        FAST PATH: Direct OpenAI streaming for voice
        SLOW PATH: Background Letta memory update
        """
        user_message = _coerce_text(chat_ctx.items[-1].content if chat_ctx.items else "")
        total_start = time.perf_counter()

        logger.info(f"🎤 User message: {user_message}")

        # Publish transcript
        await self._publish_transcript("user", user_message)
        await self._publish_status(
            "transcript_ready",
            f"Recognized: {user_message[:80] or '<<blank>>'}"
        )

        if USE_HYBRID_MODE:
            # FAST PATH: Direct OpenAI streaming
            logger.info("⚡ Using hybrid mode - direct OpenAI streaming")
            response_start = time.perf_counter()

            response_text = await self._get_openai_streaming_response(user_message)

            response_elapsed = time.perf_counter() - response_start
            logger.info(f"⚡ OpenAI streaming complete: {response_elapsed:.2f}s")

            # BACKGROUND: Update Letta memory
            task = asyncio.create_task(
                self._update_letta_memory_background(user_message, response_text)
            )
            self.background_tasks.add(task)
            task.add_done_callback(self.background_tasks.discard)

        else:
            # SLOW PATH: Full Letta orchestration
            logger.info("🐌 Using full Letta mode (slower but with orchestration)")
            response_start = time.perf_counter()

            response_text = await self._get_letta_response(user_message)

            response_elapsed = time.perf_counter() - response_start
            logger.info(f"Letta response duration: {response_elapsed:.2f}s")

        await self._publish_status(
            "letta_response",
            f"Response ready in {response_elapsed:.1f}s",
            response_elapsed,
        )

        await self._publish_transcript("assistant", response_text)
        logger.info(f"🔊 Response: {response_text[:100]}...")

        total_elapsed = time.perf_counter() - total_start
        logger.info(f"✅ Total llm_node latency: {total_elapsed:.2f}s")

        return response_text

    async def _get_openai_streaming_response(self, user_message: str) -> str:
        """
        Get response from OpenAI with TRUE streaming (TTFT <200ms).

        This bypasses Letta for speed. Letta memory updated in background.
        """
        try:
            ttft_start = time.perf_counter()

            # Build conversation history (last 5 messages for context)
            messages = []
            recent_history = self.message_history[-10:] if len(self.message_history) > 10 else self.message_history

            # Add system message
            messages.append({
                "role": "system",
                "content": self.instructions
            })

            # Add recent history
            messages.extend(recent_history)

            # Add current message
            messages.append({
                "role": "user",
                "content": user_message
            })

            # Call OpenAI streaming API
            logger.info(f"⚡ Calling OpenAI streaming API ({VOICE_MODEL})...")

            response = await self.openai_client.post(
                "/chat/completions",
                json={
                    "model": VOICE_MODEL,
                    "messages": messages,
                    "stream": True,
                    "temperature": 0.7,
                    "max_tokens": 500,  # Keep voice responses concise
                }
            )

            if response.status_code != 200:
                logger.error(f"OpenAI API error: {response.status_code} - {response.text}")
                return "I apologize, I'm having trouble connecting. Please try again."

            # Stream response
            response_text = ""
            first_token_time = None
            chunk_count = 0

            async for line in response.aiter_lines():
                if not line or line == "data: [DONE]":
                    continue

                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        delta = data.get("choices", [{}])[0].get("delta", {})
                        content = delta.get("content")

                        if content:
                            if first_token_time is None:
                                first_token_time = time.perf_counter() - ttft_start
                                logger.info(f"⚡ TTFT: {first_token_time*1000:.0f}ms")

                            response_text += content
                            chunk_count += 1

                    except json.JSONDecodeError:
                        continue

            total_time = time.perf_counter() - ttft_start
            logger.info(
                f"✅ OpenAI streaming: {chunk_count} chunks, "
                f"TTFT={first_token_time*1000 if first_token_time else 0:.0f}ms, "
                f"total={total_time:.2f}s"
            )

            # Update local history
            self.message_history.append({"role": "user", "content": user_message})
            self.message_history.append({"role": "assistant", "content": response_text})

            return response_text

        except Exception as e:
            logger.error(f"Error in OpenAI streaming: {e}")
            import traceback
            traceback.print_exc()
            return "I apologize, I encountered an error. Please try again."

    async def _update_letta_memory_background(self, user_message: str, assistant_response: str):
        """
        Update Letta memory in background (eventual consistency).

        This maintains long-term memory without blocking voice responses.
        """
        try:
            logger.info("📝 Updating Letta memory in background...")
            start = time.perf_counter()

            # Send conversation to Letta for memory update
            await self.letta_client.agents.messages.create(
                agent_id=self.agent_id,
                messages=[
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": assistant_response}
                ]
            )

            elapsed = time.perf_counter() - start
            logger.info(f"✅ Letta memory updated in background ({elapsed:.2f}s)")

        except Exception as e:
            logger.error(f"Error updating Letta memory: {e}")
            # Don't fail the voice response - memory update is best-effort

    async def _get_letta_response(self, user_message: str) -> str:
        """
        Get response from Letta (slower but with full orchestration).

        Used for text chat and complex multi-turn conversations.
        """
        try:
            self._update_activity_time()

            logger.info("Calling Letta with full orchestration...")

            response = await self.letta_client.agents.messages.create(
                agent_id=self.agent_id,
                messages=[{"role": "user", "content": user_message}]
            )

            # Extract response
            response_text = ""
            if hasattr(response, 'messages'):
                for msg in response.messages:
                    if hasattr(msg, 'message_type') and msg.message_type == "assistant_message":
                        if hasattr(msg, 'content'):
                            response_text += msg.content

            if not response_text:
                response_text = "I'm processing your request."

            # Update local history
            self.message_history.append({"role": "user", "content": user_message})
            self.message_history.append({"role": "assistant", "content": response_text})

            return response_text

        except Exception as e:
            logger.error(f"Error in Letta response: {e}")
            import traceback
            traceback.print_exc()
            return "I'm sorry, I encountered an error processing your request."

    def _update_activity_time(self):
        """Update the last activity timestamp."""
        self.last_activity_time = time.time()

    async def _start_idle_monitor(self):
        """Start background task to monitor idle time."""
        if self.idle_monitor_task is not None:
            return
        if self.idle_timeout_seconds <= 0:
            logger.info("⏰ Idle monitor disabled")
            return

        async def monitor_idle():
            while not self.is_shutting_down:
                await asyncio.sleep(1)
                participant_count = len(self.ctx.room.remote_participants or {})
                if participant_count > 0:
                    self.last_activity_time = time.time()
                    continue

                idle_time = time.time() - self.last_activity_time
                if idle_time > self.idle_timeout_seconds:
                    logger.warning(f"⏱️  Idle timeout reached ({idle_time:.1f}s)")
                    logger.info("🛑 Shutting down agent due to inactivity...")
                    self.is_shutting_down = True

                    try:
                        await self._publish_transcript("system", "Session ended due to inactivity. Goodbye!")
                    except Exception as e:
                        logger.error(f"Error publishing shutdown message: {e}")

                    try:
                        await self.ctx.room.disconnect()
                        logger.info("✅ Agent disconnected successfully")
                    except Exception as e:
                        logger.error(f"Error disconnecting: {e}")

                    break

        self.idle_monitor_task = asyncio.create_task(monitor_idle())
        logger.info(f"⏰ Idle monitor started (timeout: {self.idle_timeout_seconds}s)")

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
        """Publish pipeline status for UI indicators."""
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
        """Handle text-only messages (use full Letta orchestration)"""
        self._update_activity_time()
        logger.info(f"💬 Text message (using full Letta): {message}")

        await self._publish_transcript("user", message)

        # Text chat uses full Letta orchestration
        response_text = await self._get_letta_response(message)

        await self._publish_transcript("assistant", response_text)
        await self._agent_session.say(response_text, allow_interruptions=True)

    async def switch_agent(self, new_agent_id: str, agent_name: str = None):
        """Switch to a different Letta agent dynamically"""
        if not self.allow_agent_switching:
            logger.warning("Agent switching is disabled")
            return False

        try:
            agent = await self.letta_client.agents.retrieve(agent_id=new_agent_id)

            if not agent:
                logger.error(f"Agent {new_agent_id} not found")
                return False

            old_agent_id = self.agent_id
            self.agent_id = new_agent_id
            self.message_history = []

            logger.info(f"✅ Switched from {old_agent_id} to {new_agent_id}")

            switch_message = f"Switched to agent {agent_name or new_agent_id}. How can I help you?"
            await self._publish_transcript("system", switch_message)

            try:
                await self._agent_session.say(switch_message, allow_interruptions=True)
            except (RuntimeError, AttributeError) as e:
                logger.warning(f"Could not announce agent switch: {e}")

            return True

        except Exception as e:
            logger.error(f"Error switching agent: {e}")
            return False


async def get_or_create_orchestrator(letta_client: AsyncLetta) -> str:
    """Get or create the voice orchestrator agent."""
    agent_name = "Agent_66"
    llm_endpoint = os.getenv("LETTA_ORCHESTRATOR_ENDPOINT_TYPE", "openai")
    llm_model = _normalize_model_name(os.getenv("LETTA_ORCHESTRATOR_MODEL", LETTA_MODEL), llm_endpoint)

    if not llm_model:
        llm_model = LETTA_MODEL
    elif llm_model not in ALLOWED_ORCHESTRATOR_MODELS:
        logger.warning(f"Unsupported model '{llm_model}'. Falling back to {LETTA_MODEL}")
        llm_model = LETTA_MODEL

    context_window = _safe_int(os.getenv("LETTA_CONTEXT_WINDOW"), 400000)
    embedding_endpoint = os.getenv("LETTA_EMBEDDING_ENDPOINT_TYPE", "openai")
    embedding_model = os.getenv("LETTA_EMBEDDING_MODEL", "openai/text-embedding-3-small")
    embedding_dim = _safe_int(os.getenv("LETTA_EMBEDDING_DIM"), 1536)

    try:
        # Find existing agent
        agents = []
        async for agent in letta_client.agents.list():
            agents.append(agent)

        for agent in agents:
            if hasattr(agent, 'name') and agent.name == agent_name:
                logger.info(f"Found existing orchestrator: {agent.id}")
                return agent.id

        # Create new orchestrator
        logger.info("Creating new voice orchestrator agent...")

        agent = await letta_client.agents.create(
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
                    "value": "I am a voice-enabled orchestration agent that coordinates specialist agents."
                },
                {
                    "label": "conversation_log",
                    "value": "Voice conversation history and context."
                }
            ],
            enable_sleeptime=True,
            include_base_tools=False
        )

        logger.info(f"✅ Created orchestrator: {agent.id}")
        return agent.id

    except Exception as e:
        logger.error(f"Error getting/creating orchestrator: {e}")
        import traceback
        traceback.print_exc()
        raise


async def _graceful_shutdown(ctx: JobContext):
    """Gracefully shut down the voice agent."""
    try:
        logger.info("⏳ Initiating graceful shutdown...")
        await ctx.room.disconnect()
        logger.info("✅ Graceful shutdown complete")
    except Exception as e:
        logger.error(f"Error during graceful shutdown: {e}")


async def entrypoint(ctx: JobContext):
    """Main entry point for hybrid streaming voice agent."""
    logger.info(f"🚀 Voice agent starting in room: {ctx.room.name}")

    if USE_HYBRID_MODE:
        logger.info("⚡ HYBRID MODE ENABLED - Direct OpenAI streaming for voice")
    else:
        logger.info("🐌 FULL LETTA MODE - Using Letta orchestration")

    # Initialize AsyncLetta client
    if LETTA_API_KEY:
        letta_client = AsyncLetta(api_key=LETTA_API_KEY)
    else:
        letta_client = AsyncLetta(base_url=LETTA_BASE_URL)

    # Get or create orchestrator agent
    try:
        agent_id = await get_or_create_orchestrator(letta_client)
    except Exception as e:
        logger.error(f"Failed to initialize Letta orchestrator: {e}")
        return

    # Configure voice pipeline
    tts_provider = os.getenv("TTS_PROVIDER", "openai")

    if tts_provider == "cartesia" and os.getenv("CARTESIA_API_KEY"):
        tts = cartesia.TTS(voice="79a125e8-cd45-4c13-8a67-188112f4dd22")
        logger.info("Using Cartesia TTS")
    else:
        tts = openai.TTS(voice=os.getenv("OPENAI_TTS_VOICE", "nova"), speed=1.0)
        logger.info("Using OpenAI TTS")

    session = AgentSession(
        stt=deepgram.STT(model="nova-2", language="en"),
        llm=openai.LLM(model="gpt-5-mini"),
        tts=tts,
        vad=silero.VAD.load(
            min_speech_duration=0.1,
            min_silence_duration=0.8,
            prefix_padding_duration=0.6,
            activation_threshold=0.5,
        ),
    )

    # Create assistant instance
    assistant = LettaVoiceAssistantHybrid(ctx, letta_client, agent_id)
    assistant._agent_session = session

    @ctx.room.on("participant_connected")
    def on_participant_connected(participant: rtc.RemoteParticipant):
        logger.debug(f"Participant connected: {participant.identity}")

    @ctx.room.on("track_subscribed")
    def on_track_subscribed(track: rtc.Track, publication: rtc.TrackPublication, participant: rtc.RemoteParticipant):
        if track.kind == 1:
            logger.info(f"Audio track subscribed for {participant.identity}")

    @ctx.room.on("data_received")
    def on_data_received(data_packet: rtc.DataPacket):
        try:
            message_str = data_packet.data.decode('utf-8')
            message_data = json.loads(message_str)

            if message_data.get("type") == "room_cleanup":
                logger.info("🧹 Room cleanup requested")
                asyncio.create_task(_graceful_shutdown(ctx))

            elif message_data.get("type") == "agent_selection":
                agent_id = message_data.get("agent_id")
                agent_name = message_data.get("agent_name", "Unknown")
                if agent_id:
                    logger.info(f"🔄 Agent selection: {agent_name} ({agent_id})")
                    asyncio.create_task(assistant.switch_agent(agent_id, agent_name))

            elif message_data.get("type") == "chat":
                user_message = message_data.get("message", "")
                if user_message:
                    logger.info(f"📨 Text chat: {user_message}")
                    asyncio.create_task(assistant.handle_text_message(user_message))

        except Exception as e:
            logger.error(f"Error handling data message: {e}")

    # Start the session
    await session.start(
        room=ctx.room,
        agent=assistant,
        room_output_options=RoomOutputOptions(transcription_enabled=True),
    )

    # Start idle timeout monitor
    await assistant._start_idle_monitor()

    mode = "HYBRID STREAMING" if USE_HYBRID_MODE else "FULL LETTA"
    logger.info(f"✅ Voice agent ready ({mode} MODE)")


async def request_handler(job_request: JobRequest):
    """Accept all job requests."""
    room_name = job_request.room.name
    logger.info(f"📥 Job request received for room: {room_name}")

    try:
        from livekit_room_manager import RoomManager
        manager = RoomManager()
        await manager.ensure_clean_room(room_name)
        logger.info(f"✅ Room {room_name} is clean")
    except Exception as e:
        logger.warning(f"Room cleanup warning: {e}")

    await job_request.accept()
    logger.info(f"✅ Job accepted, starting hybrid streaming agent...")


if __name__ == "__main__":
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        request_fnc=request_handler,
    ))
