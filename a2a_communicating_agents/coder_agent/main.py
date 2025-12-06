#!/usr/bin/env python3
"""
Coder Agent (Async Refactored with Observer Pattern)

Handles code implementation, bug fixes, refactoring, and code generation tasks.
Uses Observer Pattern for real-time WebSocket message handling.

GoF Patterns:
- Observer Pattern: Subscribes to 'code' topic, receives callbacks
- Facade Pattern: Uses AgentMessenger for simplified communication
- Singleton Pattern: Shares WebSocket transport via TransportManager
"""

import sys
import os
import time
import json
import asyncio
from pathlib import Path
from typing import Set
from collections import deque

# Add parent directory to path to import shared modules
PLANNER_ROOT = Path(__file__).resolve().parents[2]

from dotenv import load_dotenv

# Load environment variables from the workspace root
load_dotenv(dotenv_path=PLANNER_ROOT / ".env", override=True)

sys.path.insert(0, str(PLANNER_ROOT))
os.chdir(PLANNER_ROOT)

# NEW: Import async messenger
from a2a_communicating_agents.agent_messaging import AgentMessenger, AgentMessage

AGENT_NAME = "coder-agent"
AGENT_TOPIC = "code"  # Listen on the "code" topic


def log_update(message):
    print(f"[{AGENT_NAME}] {message}")


class CoderAgent:
    """
    Coder agent using Observer Pattern for real-time message handling.

    Subscribes to 'code' topic once at startup, then processes all
    messages via async callbacks.
    """

    def __init__(self):
        self._processed_message_ids: Set[str] = set()
        self._message_order: deque = deque(maxlen=200)

        # Initialize LLM client
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            self.model_id = os.getenv("CODER_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
            log_update(f"Initialized with model: {self.model_id}")
        except ImportError:
            log_update("OpenAI package not available. Code generation will be limited.")
            self.client = None
            self.model_id = None
        except Exception as e:
            log_update(f"Failed to initialize OpenAI client: {e}")
            self.client = None
            self.model_id = None

        # NEW: Create messenger instance using TransportManager singleton
        self.messenger = AgentMessenger(agent_id=AGENT_NAME)
        self._running = False

    def _extract_message_id(self, message) -> str:
        """Generate a unique ID for a message."""
        identifier = getattr(message, "document_id", None) or getattr(message, "id", None)
        if identifier:
            return str(identifier)
        timestamp = getattr(message, "timestamp", None)
        if timestamp is not None and hasattr(timestamp, "isoformat"):
            timestamp_value = timestamp.isoformat()
        else:
            timestamp_value = str(timestamp or time.time())
        content_hash = hash(getattr(message, "content", ""))
        return f"{timestamp_value}:{content_hash}"

    def _message_seen(self, message_id: str) -> bool:
        return bool(message_id and message_id in self._processed_message_ids)

    def _mark_message_processed(self, message_id: str) -> None:
        if not message_id:
            return
        if message_id in self._processed_message_ids:
            return
        if self._message_order.maxlen and len(self._message_order) >= self._message_order.maxlen:
            oldest = self._message_order.popleft()
            self._processed_message_ids.discard(oldest)
        self._message_order.append(message_id)
        self._processed_message_ids.add(message_id)

    def handle_request(self, request_data: dict) -> dict:
        """Process a coding request and return results (sync is fine)."""
        method = request_data.get("method", "")
        params = request_data.get("params", {})

        log_update(f"Handling method: {method}")
        log_update(f"Parameters: {json.dumps(params, indent=2)}")

        # Extract description from params
        description = params.get("description", "No description provided")
        context = params.get("context", {})

        # Generate code using LLM if available
        if self.client and self.model_id:
            try:
                generated_code = self._generate_code(description, context)
                response = {
                    "status": "success",
                    "message": f"Generated code for: {description}",
                    "method": method,
                    "code": generated_code,
                    "details": {
                        "description": description,
                        "context": context,
                        "agent": AGENT_NAME
                    }
                }
            except Exception as e:
                log_update(f"Error generating code: {e}")
                response = {
                    "status": "error",
                    "message": f"Failed to generate code: {str(e)}",
                    "method": method,
                    "details": {
                        "description": description,
                        "context": context,
                        "agent": AGENT_NAME
                    }
                }
        else:
            # Fallback when no LLM is available
            response = {
                "status": "acknowledged",
                "message": f"Coder agent received request but cannot generate code (no LLM configured): {description}",
                "method": method,
                "details": {
                    "description": description,
                    "context": context,
                    "agent": AGENT_NAME
                }
            }

        return response

    def _generate_code(self, description: str, context: dict) -> str:
        """Generate code based on the description using LLM (sync is fine)."""
        system_prompt = """You are an expert software developer. Generate clean, well-documented code based on the user's request.
If asked for specific languages like WebAssembly (WAT format), provide syntactically correct code with comments explaining what it does."""

        user_prompt = f"""Generate code for the following request:

{description}

Additional context: {json.dumps(context, indent=2) if context else "None"}

Provide the complete code with explanatory comments."""

        try:
            completion = self.client.chat.completions.create(
                model=self.model_id,
                temperature=0.7,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            code = completion.choices[0].message.content.strip()
            return code
        except Exception as e:
            log_update(f"LLM code generation failed: {e}")
            raise

    # ========================================================================
    # ASYNC MESSAGE HANDLER (OBSERVER PATTERN)
    # ========================================================================

    async def _handle_message(self, message: AgentMessage):
        """
        Observer callback for incoming messages (GoF Observer Pattern).

        Called automatically when messages arrive on the 'code' topic.
        """
        message_id = self._extract_message_id(message)
        if self._message_seen(message_id):
            return

        try:
            content = message.content
            sender = message.from_agent or "unknown"

            log_update(f"Received message from {sender}: {content[:100]}...")

            # Try to parse as JSON-RPC
            if content.strip().startswith("{"):
                try:
                    request_data = json.loads(content)

                    # Handle JSON-RPC request
                    if "method" in request_data:
                        # Generate response (sync call is fine)
                        response = self.handle_request(request_data)

                        # Send JSON-RPC response back
                        response_msg = json.dumps({
                            "jsonrpc": "2.0",
                            "result": response,
                            "id": request_data.get("id")
                        })

                        await self.messenger.send_to_agent(
                            agent_id="board",
                            message=response_msg,
                            topic="orchestrator"
                        )

                        # Also send human-readable message with the code
                        if response.get("status") == "success" and response.get("code"):
                            human_msg = (
                                f"✅ **Coder Agent - Code Generated**\n\n"
                                f"Task: {response['details']['description']}\n\n"
                                f"```\n{response['code']}\n```\n"
                            )
                        else:
                            human_msg = (
                                f"ℹ️ **Coder Agent Response**\n\n"
                                f"Task: {response['details']['description']}\n\n"
                                f"Status: {response.get('status', 'unknown')}\n"
                                f"Message: {response.get('message', 'No message')}"
                            )

                        await self.messenger.send_to_agent(
                            agent_id="board",
                            message=human_msg,
                            topic="orchestrator"
                        )

                except json.JSONDecodeError:
                    log_update("Failed to parse JSON content")
            else:
                # Plain text message
                log_update(f"Plain text message: {content}")

        except Exception as e:
            log_update(f"Error processing message: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self._mark_message_processed(message_id)

    # ========================================================================
    # ASYNC MAIN LOOP (OBSERVER PATTERN)
    # ========================================================================

    async def run_async(self):
        """
        Main async event loop using Observer Pattern.

        Subscribes to 'code' topic once, then handles all messages
        via the _handle_message callback.
        """
        log_update(f"Started. Listening on topic '{AGENT_TOPIC}'...")

        # Subscribe to code topic (Observer Pattern)
        await self.messenger.subscribe(AGENT_TOPIC, self._handle_message)

        log_update(f"✅ Subscribed to '{AGENT_TOPIC}' topic. Waiting for requests...")

        # Keep running
        self._running = True
        try:
            while self._running:
                await asyncio.sleep(1)  # Keep alive, messages arrive via callbacks
        except KeyboardInterrupt:
            log_update("Shutting down...")
        finally:
            self._running = False

    def stop(self):
        """Graceful shutdown."""
        self._running = False


def main():
    """Entry point with async support."""
    agent = CoderAgent()

    try:
        asyncio.run(agent.run_async())
    except KeyboardInterrupt:
        print(f"\n[{AGENT_NAME}] Shutting down gracefully...")


if __name__ == "__main__":
    main()
