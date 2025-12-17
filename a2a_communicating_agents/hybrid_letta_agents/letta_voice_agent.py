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

    async def llm_node(self, chat_ctx, tools, model_settings):
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
        logger.info("POST-CALL to _get_letta_response")

        # Publish response to room for UI
        await self._publish_transcript("assistant", response_text)

        logger.info(f"🔊 Letta response: {response_text[:100]}...")

        return response_text

    async def _get_letta_response(self, user_message: str) -> str:
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
        logger.info(f"💬 Text message: {message}")

        # Publish user message
        await self._publish_transcript("user", message)

        # Get Letta response
        response_text = await self._get_letta_response(message)

        # Publish assistant response
        await self._publish_transcript("assistant", response_text)

        # Speak the response
        await self._agent_session.say(response_text, allow_interruptions=True)


async def get_or_create_orchestrator(letta_client: Letta) -> str:
    """
    Get or create the voice orchestrator agent (Factory pattern).

    Returns:
        Agent ID
    """
    agent_name = "voice_orchestrator"

    llm_endpoint = os.getenv("LETTA_ORCHESTRATOR_ENDPOINT_TYPE", "openai")
    llm_model = _normalize_model_name(os.getenv("LETTA_ORCHESTRATOR_MODEL", "gpt-4o-mini"), llm_endpoint)
    if not llm_model:
        llm_model = "gpt-4o-mini"
    elif llm_model not in ALLOWED_ORCHESTRATOR_MODELS:
        logger.warning(
            "Unsupported LETTA_ORCHESTRATOR_MODEL '%s'. Falling back to gpt-4o-mini. "
            "Allowed values: %s",
            llm_model,
            ", ".join(sorted(ALLOWED_ORCHESTRATOR_MODELS)),
        )
        llm_model = "gpt-4o-mini"
    context_window = _safe_int(os.getenv("LETTA_CONTEXT_WINDOW"), 128000)
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
            ]
        )

        logger.info(f"Created orchestrator: {agent.id}")
        return agent.id

    except Exception as e:
        logger.error(f"Error getting/creating orchestrator: {e}")
        import traceback
        traceback.print_exc()
        raise


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

        # Voice Activity Detection: Silero
        vad=silero.VAD.load(),
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

    # Set up data message handler for text chat
    @ctx.room.on("data_received")
    def on_data_received(data_packet: rtc.DataPacket):
        """Handle incoming data messages (Observer pattern)"""
        try:
            message_str = data_packet.data.decode('utf-8')
            message_data = json.loads(message_str)

            # Handle text chat messages
            if message_data.get("type") == "chat":
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

    logger.info("✅ Voice agent ready and listening")


async def request_handler(job_request: JobRequest):
    """
    Accept all job requests to ensure agent joins rooms.
    """
    logger.info(f"📥 Job request received for room: {job_request.room.name}")
    await job_request.accept()
    logger.info(f"✅ Job accepted, starting entrypoint...")


if __name__ == "__main__":
    # Run the agent using Livekit CLI
    # Explicit request handler to ensure we accept all jobs
    cli.run_app(WorkerOptions(
        entrypoint_fnc=entrypoint,
        request_fnc=request_handler,  # Explicitly accept all jobs
    ))
