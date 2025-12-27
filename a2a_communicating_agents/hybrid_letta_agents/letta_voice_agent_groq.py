#!/usr/bin/env python3
"""
Letta Voice Agent - OPTIMIZED with Groq Integration
====================================================
Drop-in replacement for letta_voice_agent.py with 5-10x faster LLM inference.

Key Changes:
- Groq LLM for ultra-fast inference (200-500ms vs 1500-3000ms)
- Async memory sync to Letta (non-blocking)
- Performance timing measurements
- Backwards compatible fallback to original Letta path

Usage:
    # Enable Groq mode (recommended)
    export GROQ_API_KEY=your_key_here
    export USE_GROQ_LLM=true

    # Or fall back to original Letta mode
    export USE_GROQ_LLM=false

    python letta_voice_agent_groq.py dev
"""

import asyncio
import logging
import os
import json
import time
from typing import Optional, List
from datetime import datetime

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

# Groq client (optional, for fast LLM inference)
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq not installed. Install with: pip install groq")

# Load environment variables
load_dotenv("/home/adamsl/planner/.env")
load_dotenv("/home/adamsl/ottomator-agents/livekit-agent/.env")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Letta server configuration
LETTA_BASE_URL = os.getenv("LETTA_SERVER_URL", "http://localhost:8283")
LETTA_API_KEY = os.getenv("LETTA_API_KEY")
ALLOWED_ORCHESTRATOR_MODELS = {"gpt-4o-mini", "gpt-5-mini"}

# Groq configuration
USE_GROQ = os.getenv("USE_GROQ_LLM", "false").lower() == "true"
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
# Options: llama-3.1-70b-versatile, llama-3.1-8b-instant, mixtral-8x7b-32768


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


class LettaVoiceAssistant(Agent):
    """
    Voice assistant with Groq fast inference + Letta memory (Strategy pattern).

    Supports two modes:
    1. Groq mode (USE_GROQ_LLM=true): Ultra-fast inference with async Letta sync
    2. Letta mode (USE_GROQ_LLM=false): Original Letta orchestration
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

        # Idle timeout configuration (disconnect only when room stays empty)
        self.last_activity_time = time.time()
        self.idle_timeout_seconds = _safe_int(
            os.getenv("VOICE_IDLE_TIMEOUT_SECONDS"),
            300,
        )
        self.idle_monitor_task = None
        self.is_shutting_down = False

        # Initialize Groq client if available
        self.use_groq = USE_GROQ and GROQ_AVAILABLE
        if self.use_groq:
            groq_key = os.getenv("GROQ_API_KEY")
            if groq_key:
                self.groq_client = Groq(api_key=groq_key)
                logger.info(f"⚡ Groq mode enabled (model: {GROQ_MODEL})")
            else:
                logger.warning("USE_GROQ_LLM=true but GROQ_API_KEY not set, falling back to Letta")
                self.use_groq = False
        else:
            self.groq_client = None
            logger.info("🐌 Letta mode (slower, full orchestration)")

    def _update_activity_time(self):
        """Update the last activity timestamp."""
        self.last_activity_time = time.time()
        logger.debug(f"⏰ Activity updated at {self.last_activity_time}")

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

    async def llm_node(self, chat_ctx, tools, model_settings):
        """
        Override LLM node to route through Groq (fast) or Letta (full features).
        """
        try:
            # Update activity timestamp on every user interaction
            self._update_activity_time()

            # TIMING: Start pipeline measurement
            pipeline_start = time.time()

            logger.info("✅ LLM_NODE CALLED - Processing user input")

            # Extract user message from chat context items
            user_message = _coerce_text(chat_ctx.items[-1].content if chat_ctx.items else "")

            stt_time = (time.time() - pipeline_start) * 1000
            logger.info(f"🎤 User message: '{user_message}'")
            logger.info(f"⏱️  TIMING: STT processing: {stt_time:.0f}ms")

            # Publish transcript to room for UI
            publish_start = time.time()
            await self._publish_transcript("user", user_message)
            publish_time = (time.time() - publish_start) * 1000
            logger.info(f"⏱️  TIMING: Publish transcript: {publish_time:.0f}ms")

            # Route through Groq or Letta
            llm_start = time.time()
            if self.use_groq:
                response_text = await self._get_groq_response(user_message)
            else:
                response_text = await self._get_letta_response(user_message)
            llm_time = (time.time() - llm_start) * 1000
            logger.info(f"⏱️  TIMING: LLM response: {llm_time:.0f}ms")

            # Publish response to room for UI
            publish_start2 = time.time()
            await self._publish_transcript("assistant", response_text)
            publish_time2 = (time.time() - publish_start2) * 1000
            logger.info(f"⏱️  TIMING: Publish response: {publish_time2:.0f}ms")

            logger.info(f"🔊 Response: {response_text[:100]}...")

            # TIMING: Total pipeline
            pipeline_total = (time.time() - pipeline_start) * 1000
            logger.info(f"⏱️  TIMING: TOTAL PIPELINE: {pipeline_total:.0f}ms")
            logger.info(f"⏱️  TIMING: Breakdown - STT:{stt_time:.0f}ms + LLM:{llm_time:.0f}ms + Publish:{publish_time+publish_time2:.0f}ms")

            return response_text

        except Exception as e:
            logger.error(f"❌ Error in llm_node: {e}")
            import traceback
            traceback.print_exc()
            return "I encountered an error processing your request. Please try again."

    async def _get_groq_response(self, user_message: str) -> str:
        """
        FAST PATH: Groq inference with background Letta memory sync.

        This provides 5-10x faster responses by:
        1. Using Groq's ultra-fast LLM inference
        2. Maintaining local message history
        3. Syncing to Letta asynchronously (non-blocking)
        """
        try:
            groq_start = time.time()

            # Build conversation context (last 10 messages to stay within token limits)
            context_messages = [
                {"role": "system", "content": self.instructions},
                *self.message_history[-10:],
                {"role": "user", "content": user_message}
            ]

            # Call Groq (fast!)
            response = await asyncio.to_thread(
                self.groq_client.chat.completions.create,
                model=GROQ_MODEL,
                messages=context_messages,
                temperature=0.7,
                max_tokens=200,  # Keep voice responses concise
                stream=False
            )

            response_text = response.choices[0].message.content.strip()
            groq_time = (time.time() - groq_start) * 1000
            logger.info(f"⚡ Groq inference: {groq_time:.0f}ms")

            # Update local history
            self.message_history.append({"role": "user", "content": user_message})
            self.message_history.append({"role": "assistant", "content": response_text})

            # Sync to Letta memory in background (non-blocking!)
            asyncio.create_task(self._sync_to_letta_memory(user_message, response_text))

            return response_text

        except Exception as e:
            logger.error(f"Groq error: {e}, falling back to Letta")
            # Fallback to Letta on error
            return await self._get_letta_response(user_message)

    async def _sync_to_letta_memory(self, user_msg: str, assistant_msg: str):
        """
        Background task to sync conversation to Letta for memory persistence.

        This runs asynchronously and doesn't block the voice response.
        """
        try:
            sync_start = time.time()
            await asyncio.to_thread(
                self.letta_client.agents.messages.create,
                agent_id=self.agent_id,
                messages=[
                    {"role": "user", "content": user_msg},
                    {"role": "assistant", "content": assistant_msg}
                ]
            )
            sync_time = (time.time() - sync_start) * 1000
            logger.info(f"💾 Letta memory sync: {sync_time:.0f}ms (background)")
        except Exception as e:
            logger.error(f"Letta memory sync failed: {e}")

    async def _get_letta_response(self, user_message: str) -> str:
        """
        SLOW PATH: Full Letta orchestration (original implementation).

        Use this for full Letta features (function calling, tool use, etc.)
        at the cost of slower response times.
        """
        try:
            # TIMING: Measure Letta API call
            letta_call_start = time.time()

            # Send to Letta using the official client
            logger.info("Attempting to call Letta server...")
            response = await asyncio.to_thread(
                self.letta_client.agents.messages.create,
                agent_id=self.agent_id,
                messages=[{"role": "user", "content": user_message}]
            )
            letta_call_time = (time.time() - letta_call_start) * 1000
            logger.info("Call to Letta server completed.")
            logger.info(f"⏱️  TIMING: Letta API call: {letta_call_time:.0f}ms (network + LLM)")

            # Extract assistant messages from response
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

            response_text = " ".join(assistant_messages) if assistant_messages else "I'm processing your request."

            # Update local history
            self.message_history.append({"role": "user", "content": user_message})
            self.message_history.append({"role": "assistant", "content": response_text})

            return response_text

        except Exception as e:
            logger.error(f"Error communicating with Letta: {e}")
            import traceback
            traceback.print_exc()
            return "I'm sorry, I encountered an error processing your request. Please try again."

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

    async def handle_text_message(self, message: str):
        """Handle text-only messages (no voice) from client"""
        # Update activity timestamp
        self._update_activity_time()

        logger.info(f"💬 Text message: {message}")
        await self._publish_transcript("user", message)

        # Get response (Groq or Letta)
        if self.use_groq:
            response_text = await self._get_groq_response(message)
        else:
            response_text = await self._get_letta_response(message)

        await self._publish_transcript("assistant", response_text)
        await self._agent_session.say(response_text, allow_interruptions=True)

    async def switch_agent(self, new_agent_id: str, agent_name: str = None):
        """Switch to a different Letta agent dynamically"""
        if not self.allow_agent_switching:
            logger.warning("Agent switching is disabled")
            return False

        try:
            agent = await asyncio.to_thread(
                self.letta_client.agents.retrieve,
                agent_id=new_agent_id
            )

            if not agent:
                logger.error(f"Agent {new_agent_id} not found")
                return False

            old_agent_id = self.agent_id
            self.agent_id = new_agent_id
            self.message_history = []

            logger.info(f"✅ Switched from agent {old_agent_id} to {new_agent_id} ({agent_name or 'unnamed'})")

            switch_message = f"Switched to agent {agent_name or new_agent_id}. How can I help you?"
            await self._publish_transcript("system", switch_message)
            await self._agent_session.say(switch_message, allow_interruptions=True)

            return True

        except Exception as e:
            logger.error(f"Error switching agent: {e}")
            return False


async def get_or_create_orchestrator(letta_client: Letta) -> str:
    """Get or create the voice orchestrator agent (Factory pattern)."""
    agent_name = "Agent_66"

    llm_endpoint = os.getenv("LETTA_ORCHESTRATOR_ENDPOINT_TYPE", "openai")
    llm_model = _normalize_model_name(os.getenv("LETTA_ORCHESTRATOR_MODEL", "gpt-4o-mini"), llm_endpoint)
    if not llm_model:
        llm_model = "gpt-4o-mini"
    elif llm_model not in ALLOWED_ORCHESTRATOR_MODELS:
        logger.warning(
            "Unsupported LETTA_ORCHESTRATOR_MODEL '%s'. Falling back to gpt-4o-mini.",
            llm_model,
        )
        llm_model = "gpt-4o-mini"

    context_window = _safe_int(os.getenv("LETTA_CONTEXT_WINDOW"), 128000)
    embedding_endpoint = os.getenv("LETTA_EMBEDDING_ENDPOINT_TYPE", "openai")
    embedding_model = os.getenv("LETTA_EMBEDDING_MODEL", "openai/text-embedding-3-small")
    embedding_dim = _safe_int(os.getenv("LETTA_EMBEDDING_DIM"), 1536)

    try:
        agents_list = await asyncio.to_thread(letta_client.agents.list)
        agents = list(agents_list) if agents_list else []

        for agent in agents:
            if hasattr(agent, 'name') and agent.name == agent_name:
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
                        "I coordinate specialist agents to help users build high-quality software. "
                        "I maintain conversation context and delegate tasks appropriately."
                    )
                },
                {
                    "label": "conversation_log",
                    "value": "Voice conversation history and important context."
                }
            ]
        )

        logger.info(f"Created orchestrator: {agent.id}")
        return "agent-4dfca708-49a8-4982-8e36-0f1146f9a66e" # agent.id for Agent_66

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
    """Main entry point for Livekit voice agent."""
    logger.info(f"🚀 Voice agent starting in room: {ctx.room.name}")

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
        # Speech-to-Text: Deepgram Nova 2
        stt=deepgram.STT(
            model="nova-2",
            language="en",
        ),

        # LLM: Minimal model since Groq/Letta handles reasoning
        llm=openai.LLM(model="gpt-5-mini"),

        # Text-to-Speech
        tts=tts,

        # Voice Activity Detection
        vad=silero.VAD.load(
            min_speech_duration=0.1,
            min_silence_duration=0.8,
            prefix_padding_duration=0.6,
            activation_threshold=0.5,
        ),
    )

    # Create assistant instance
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
        """Handle incoming data messages (Observer pattern)"""
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
    logger.info("🚀 Voice agent starting in room: " + ctx.room.name)
    await session.start(
        room=ctx.room,
        agent=assistant,
        room_output_options=RoomOutputOptions(transcription_enabled=True),
    )

    # Start idle timeout monitor
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
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        request_fnc=request_handler,
    ))
