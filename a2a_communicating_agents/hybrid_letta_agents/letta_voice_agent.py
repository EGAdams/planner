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

    async def generate_reply(self, chat_ctx):
        """
        Override to route through Letta orchestrator (Template Method pattern).

        This is called by the Livekit framework after STT transcription.
        We route to Letta and return the response for TTS.
        """
        # Extract user message
        user_message = chat_ctx.messages[-1].content if chat_ctx.messages else ""

        logger.info(f"🎤 User message: {user_message}")

        # Publish transcript to room for UI
        await self._publish_transcript("user", user_message)

        # Route through Letta
        response_text = await self._get_letta_response(user_message)

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
            response = await asyncio.to_thread(
                self.letta_client.agents.messages.create,
                agent_id=self.agent_id,
                messages=[{"role": "user", "content": user_message}]
            )

            # Extract assistant messages from response
            assistant_messages = []
            if hasattr(response, 'messages'):
                for msg in response.messages:
                    if hasattr(msg, 'role') and msg.role == "assistant":
                        if hasattr(msg, 'text'):
                            assistant_messages.append(msg.text)

            # Combine into single response
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
        logger.info(f"💬 Text message: {message}")

        # Publish user message
        await self._publish_transcript("user", message)

        # Get Letta response
        response_text = await self._get_letta_response(message)

        # Publish assistant response
        await self._publish_transcript("assistant", response_text)

        # Speak the response
        await self.session.say(response_text, allow_interruptions=True)


async def get_or_create_orchestrator(letta_client: Letta) -> str:
    """
    Get or create the voice orchestrator agent (Factory pattern).

    Returns:
        Agent ID
    """
    agent_name = "voice_orchestrator"

    try:
        # Try to find existing agent (run in thread pool)
        agents_list = await asyncio.to_thread(letta_client.agents.list)

        # Convert to list if it's a paginated response
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
                "model": os.getenv("LETTA_ORCHESTRATOR_MODEL", "openai/gpt-4o-mini"),
                "model_endpoint_type": "openai",
                "context_window": 8000
            },
            embedding_config={
                "embedding_model": os.getenv("LETTA_EMBEDDING_MODEL", "openai/text-embedding-3-small"),
                "embedding_endpoint_type": "openai",
                "embedding_dim": 1536
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
        llm=openai.LLM(model="gpt-4o-mini"),

        # Text-to-Speech: Cartesia or OpenAI
        tts=tts,

        # Voice Activity Detection: Silero
        vad=silero.VAD.load(),
    )

    # Create assistant instance
    assistant = LettaVoiceAssistant(ctx, letta_client, agent_id)

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
    await session.start(
        room=ctx.room,
        agent=assistant,
        room_output_options=RoomOutputOptions(transcription_enabled=True),
    )

    # Generate initial greeting
    logger.info("Generating greeting...")
    greeting = await assistant._get_letta_response(
        "Greet the user warmly and introduce yourself as their voice-enabled AI orchestrator. "
        "Mention you can help with software development using design patterns."
    )
    await assistant.session.say(greeting, allow_interruptions=True)

    logger.info("✅ Voice agent ready")


if __name__ == "__main__":
    # Run the agent using Livekit CLI
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
