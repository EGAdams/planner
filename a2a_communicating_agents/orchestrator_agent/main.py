#!/usr/bin/env python3
"""
Orchestrator Agent (Async Refactored with Observer Pattern)

Routes user requests to the appropriate specialist agent using OpenAI.
Uses Observer Pattern for real-time WebSocket message handling.

GoF Patterns:
- Observer Pattern: Subscribes to 'orchestrator' topic, receives callbacks
- Facade Pattern: Uses AgentMessenger for simplified communication
- Singleton Pattern: Shares WebSocket transport via TransportManager
"""

import sys
import os
import time
import json
import asyncio
from collections import deque
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional, Set
from contextlib import suppress

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - handled gracefully at runtime
    OpenAI = None

# Add parent directory to path to import shared modules
PLANNER_ROOT = Path(__file__).resolve().parents[2]

from dotenv import load_dotenv

# Load environment variables from the workspace root so we use the shared .env,
# overriding any previously exported conflicting keys.
load_dotenv(dotenv_path=PLANNER_ROOT / ".env", override=True)

sys.path.insert(0, str(PLANNER_ROOT))
os.chdir(PLANNER_ROOT)

# NEW: Import async messenger and AgentMessage
from a2a_communicating_agents.agent_messaging import (
    AgentMessenger,  # Uses TransportManager singleton
    create_jsonrpc_response,
    AgentMessage,  # For type hints
)
from rag_system.core.document_manager import DocumentManager
from a2a_communicating_agents.orchestrator_agent.a2a_dispatcher import A2ADispatcher

AGENT_NAME = "orchestrator-agent"
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]


def log_update(message):
    print(f"[{AGENT_NAME}] {message}")


class Orchestrator:
    """
    Orchestrator using Observer Pattern for real-time message handling.

    Subscribes to 'orchestrator' topic once at startup, then processes all
    messages via async callbacks. No polling loop needed.
    """

    def __init__(self, *, llm_client=None, model_id: Optional[str] = None):
        self.known_agents = {}
        self.dispatcher = A2ADispatcher(workspace_root=WORKSPACE_ROOT)
        self.model_id = model_id or os.getenv("ORCHESTRATOR_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-5-mini"
        if llm_client is not None:
            self.client = llm_client
        elif OpenAI is None:
            self.client = None
            log_update("openai package not available. Falling back to heuristic routing.")
        elif os.environ.get("OPENAI_API_KEY"):
            self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        else:
            self.client = None
            log_update("OPENAI_API_KEY not set. Falling back to heuristic routing.")
        self.doc_manager = DocumentManager()
        self._processed_message_ids: Set[str] = set()
        self._message_order: Deque[str] = deque(maxlen=200)
        self._self_aliases = self._build_self_aliases()
        self._ignored_senders = {AGENT_NAME.lower(), "orchestrator"}
        self._self_profile = self._load_self_profile()
        self._self_context = self._build_self_context()

        # NEW: Create messenger instance using TransportManager singleton
        self.messenger = AgentMessenger(agent_id=AGENT_NAME)
        self._running = False

    def _build_self_aliases(self) -> Set[str]:
        aliases = {
            AGENT_NAME,
            AGENT_NAME.replace("-", " "),
            AGENT_NAME.replace("_", " "),
            AGENT_NAME.replace("-", ""),
            AGENT_NAME.replace("_", ""),
            "orchestrator",
            "the orchestrator",
            "orchestrator agent",
            "orchestrator-agent",
        }
        normalized = {self._normalize_identifier(alias) for alias in aliases if alias}
        return {alias for alias in normalized if alias}

    @staticmethod
    def _normalize_identifier(value: str) -> str:
        return "".join(ch for ch in value.lower() if ch.isalnum())

    def _is_self_reference(self, value: Optional[str]) -> bool:
        if not value:
            return False
        normalized = self._normalize_identifier(value)
        if normalized in self._self_aliases:
            return True
        return "orchestrator" in value.lower()

    def _resolve_known_agent(self, value: Optional[str]) -> Optional[str]:
        """Return the canonical agent name if it's registered in known_agents."""
        if not value:
            return None
        normalized = self._normalize_identifier(str(value))
        for agent_name in self.known_agents.keys():
            if self._normalize_identifier(agent_name) == normalized:
                return agent_name
        return None

    def _load_self_profile(self) -> Dict[str, Any]:
        agent_card = WORKSPACE_ROOT / "agent.json"
        if not agent_card.exists():
            return {}
        try:
            with agent_card.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:  # pragma: no cover - defensive logging
            log_update(f"Failed to read agent card: {exc}")
            return {}

    def _build_self_context(self) -> str:
        description = self._self_profile.get("description") or (
            "You coordinate a spoke-and-hub collective of agents. "
            "Keep conversations grounded in routing best practices."
        )
        capability_lines = []
        for cap in self._self_profile.get("capabilities", []):
            if isinstance(cap, dict):
                name = cap.get("name")
                cap_desc = cap.get("description")
                if name or cap_desc:
                    capability_lines.append(f"- {name or 'capability'}: {cap_desc or ''}".strip())
        topics = ", ".join(self._self_profile.get("topics", []))
        context_segments = [
            "You are the Orchestrator Agent responsible for routing work across the collective.",
            f"Profile: {description}",
        ]
        if capability_lines:
            context_segments.append("Capabilities:\n" + "\n".join(capability_lines))
        if topics:
            context_segments.append(f"Topics: {topics}")
        context_segments.append(
            "Answer as a helpful coordinator. Give short, actionable replies and "
            "invite the user to describe tasks that you can route."
        )
        return "\n\n".join(context_segments)

    def _format_memory_status(self, memory_info: Dict[str, Any]) -> str:
        backend = memory_info.get("backend") or "unknown"
        namespace = memory_info.get("namespace")
        connected = memory_info.get("connected")
        status = "connected" if connected else ("disconnected" if connected is False else "unknown")
        namespace_segment = f" ({namespace})" if namespace else ""
        return f"{backend}{namespace_segment} -> {status}"

    async def discover_agents(self):
        """Scan workspace for agent.json files (async)"""
        print(f"[{AGENT_NAME}] Scanning for agents...")
        registry = await self.dispatcher.refresh_registry()
        snapshot = self.dispatcher.routing_snapshot()

        for agent_name, info in snapshot.items():
            if not agent_name:
                continue
            if self._is_self_reference(agent_name):
                continue
            memory_info = info.get("memory") or {}
            self.known_agents[agent_name] = {
                "description": info.get("description"),
                "capabilities": info.get("capabilities", []),
                "topics": info.get("topics", []),
                "memory": memory_info,
            }
            log_update(
                f"{agent_name} memory backend: {self._format_memory_status(memory_info)}"
            )
        print(f"[{AGENT_NAME}] Discovered {len(self.known_agents)} agents: {list(self.known_agents.keys())}")

    def decide_route(self, user_request: str) -> Dict:
        """Use LLM to decide which agent should handle the request"""

        if not self.client:
            return self._fallback_route(user_request)

        system_prompt = (
            "You are the Orchestrator Agent. Route the user request to the best specialist "
            "agent based on their capabilities and topics. \n\n"
            "IMPORTANT ROUTING RULES:\n"
            "- For code writing, implementation, snippets, or programming tasks -> use 'coder-agent'\n"
            "- For testing, QA, or validation tasks -> use 'tester-agent'\n"
            "- For dashboard or UI state management -> use 'dashboard-agent'\n\n"
            "Always reply with compact JSON containing keys: target_agent, reasoning, method, params."
        )
        agent_snapshot = json.dumps(self.known_agents, indent=2)
        user_prompt = (
            f"Available Agents:\n{agent_snapshot}\n\n"
            f'User Request: "{user_request}"\n\n'
            "Analyze the request and select the most appropriate agent based on:\n"
            "1. Keywords in the request (code, write, implement, test, dashboard)\n"
            "2. Agent capabilities and topics\n"
            "3. The ROUTING RULES defined above\n\n"
            "Return JSON with target_agent (must match exactly), reasoning, method "
            '(default "agent.execute_task"), and params (context, description, artifacts).'
        )

        try:
            completion = self.client.chat.completions.create(
                model=self.model_id,
                temperature=0,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = (completion.choices[0].message.content or "").strip()
            if content.startswith("```"):
                fence = "```json" if content.startswith("```json") else "```"
                with suppress(IndexError):
                    content = content.split(fence, 1)[1].split("```", 1)[0].strip()
            return json.loads(content)
        except Exception as e:
            print(f"[{AGENT_NAME}] Error in decision making: {e}")
            return None

    def _fallback_route(self, user_request: str) -> Optional[Dict]:
        """Simple keyword-based router when no API client is available."""
        normalized = user_request.lower()

        # Priority keywords for specific agents
        priority_mappings = {
            "coder-agent": ["code", "write", "implement", "program", "function", "snippet", "webassembly", "wasm", "python", "javascript", "java"],
            "tester-agent": ["test", "validate", "check", "verify", "qa", "quality"],
            "dashboard-agent": ["dashboard", "ui", "interface", "display", "status"],
        }

        # Check priority keywords first
        for agent_name, keywords in priority_mappings.items():
            if agent_name in self.known_agents:
                for keyword in keywords:
                    if keyword in normalized:
                        return {
                            "target_agent": agent_name,
                            "reasoning": f"Matched priority keyword '{keyword}' for {agent_name}.",
                            "method": "agent.execute_task",
                            "params": {"description": user_request},
                        }

        # Fallback to general scoring
        best_agent = None
        best_score = 0

        for agent_name, metadata in self.known_agents.items():
            score = 0
            if agent_name.lower() in normalized:
                score += 5

            descriptions: List[str] = []
            if isinstance(metadata.get("description"), str):
                descriptions.append(metadata["description"])
            if isinstance(metadata.get("capabilities"), list):
                descriptions.extend(metadata["capabilities"])
            if isinstance(metadata.get("topics"), list):
                descriptions.extend(metadata["topics"])

            combined = " ".join(descriptions).lower()
            for token in normalized.split():
                if token and token in combined:
                    score += 1

            if score > best_score:
                best_score = score
                best_agent = agent_name

        if best_agent and best_score:
            return {
                "target_agent": best_agent,
                "reasoning": "Heuristic keyword match (no LLM API key available).",
                "method": "agent.execute_task",
                "params": {"description": user_request},
            }
        return None

    def _get_topic_for_agent(self, agent_name: str) -> str:
        """Map agent name to its topic."""
        topic_map = {
            "coder-agent": "code",
            "tester-agent": "test",
            "dashboard-agent": "ops",
        }
        return topic_map.get(agent_name, agent_name)

    # ========================================================================
    # ASYNC MESSAGE HANDLER (OBSERVER PATTERN)
    # ========================================================================

    async def _handle_message(self, message: AgentMessage):
        """
        Observer callback for incoming messages (GoF Observer Pattern).

        Called automatically when messages arrive on the 'orchestrator' topic.
        This replaces the old polling loop with real-time event-driven handling.
        """
        # Check if already processed
        message_id = self._extract_message_id(message)
        if self._message_seen(message_id):
            return

        # Check if from self
        sender_name = (message.from_agent or "").strip().lower()
        if self._is_self_reference(sender_name):
            self._mark_message_processed(message_id)
            return

        try:
            content = message.content

            # Unwrap markdown if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()

            # Skip JSON-RPC responses
            if content.strip().startswith("{") and "jsonrpc" in content:
                log_update(f"Skipping machine response: {content[:50]}...")
                self._mark_message_processed(message_id)
                return

            log_update(f"Processing request: {content[:50]}...")

            # Route the message
            decision = self.decide_route(content)

            if not decision:
                log_update("Router produced no decision; responding directly.")
                await self._respond_directly_async(
                    user_request=content,
                    reasoning="No matching agent available yet, so I'm responding directly.",
                )
                self._mark_message_processed(message_id)
                return

            raw_target = decision.get("target_agent")
            if not raw_target:
                log_update("Router returned no target; responding directly.")
                await self._respond_directly_async(
                    user_request=content,
                    reasoning=decision.get("reasoning"),
                )
                self._mark_message_processed(message_id)
                return

            target_agent = self._resolve_known_agent(raw_target)
            if raw_target and not target_agent:
                log_update(f"Router suggested unknown agent '{raw_target}'; responding directly.")
                reasoning = decision.get("reasoning") or "Suggested agent is not registered."
                await self._respond_directly_async(
                    user_request=content,
                    reasoning=f"{reasoning} (Agent '{raw_target}' is not available.)",
                )
                self._mark_message_processed(message_id)
                return

            if self._is_self_reference(target_agent):
                log_update("Direct chat requested; responding without delegation.")
                await self._respond_directly_async(
                    user_request=content,
                    reasoning=decision.get("reasoning"),
                )
                self._mark_message_processed(message_id)
                return

            # Route to target agent
            log_update(f"Routing to {target_agent}")

            params = decision.get("params", {})
            description = params.get("description", content)
            context = params.get("context", {})
            artifacts = params.get("artifacts")

            delegation = await self.dispatcher.delegate(
                agent_name=target_agent,
                description=description,
                context=context,
                artifacts=artifacts,
            )

            rpc_payload = json.dumps(delegation["payload"])
            target_topic = delegation["topic"]

            # Send to target agent via shared transport
            await self.messenger.send_to_agent(
                agent_id="board",
                message=rpc_payload,
                topic=target_topic
            )

            # Confirm to user on orchestrator topic
            await self.messenger.send_to_agent(
                agent_id="board",
                message=f"I have routed your request to **{target_agent}**. \nReasoning: {decision['reasoning']}",
                topic="orchestrator"
            )

            self._mark_message_processed(message_id)

        except Exception as e:
            log_update(f"Error processing message: {e}")
            import traceback
            traceback.print_exc()
            self._mark_message_processed(message_id)

    async def _respond_directly_async(
        self,
        user_request: str,
        reasoning: Optional[str] = None
    ):
        """Send response back to orchestrator topic (async)."""
        reply = self._generate_direct_response(user_request)
        if reasoning:
            reply = f"{reply}\n\n_{reasoning}_"

        await self.messenger.send_to_agent(
            agent_id="board",
            message=reply,
            topic="orchestrator"
        )

    # ========================================================================
    # ASYNC MAIN LOOP (OBSERVER PATTERN)
    # ========================================================================

    async def run_async(self):
        """
        Main async event loop using Observer Pattern.

        Subscribes to 'orchestrator' topic once, then handles all messages
        via the _handle_message callback. No polling needed!
        """
        log_update("Started. Listening on topic 'orchestrator'...")

        # Discover agents (async)
        await self.discover_agents()

        # Subscribe to orchestrator topic (Observer Pattern)
        # Messages will be delivered to _handle_message callback automatically
        await self.messenger.subscribe("orchestrator", self._handle_message)

        log_update("✅ Subscribed to 'orchestrator' topic. Waiting for messages...")

        # Keep running (just maintain event loop)
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

    # ========================================================================
    # HELPER METHODS (UNCHANGED - sync is fine)
    # ========================================================================

    def _extract_message_id(self, message) -> str:
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

    def _generate_direct_response(self, user_request: str) -> str:
        """Craft a conversational response when the user is chatting with the orchestrator."""
        if self.client:
            try:
                completion = self.client.chat.completions.create(
                    model=self.model_id,
                    temperature=0.4,
                    messages=[
                        {
                            "role": "system",
                            "content": self._self_context,
                        },
                        {
                            "role": "user",
                            "content": user_request,
                        },
                    ],
                )
                content = (completion.choices[0].message.content or "").strip()
                if content:
                    return content
            except Exception as exc:  # pragma: no cover - transport errors handled at runtime
                log_update(f"LLM response failed, falling back to default reply: {exc}")

        description = self._self_profile.get("description") or "I coordinate tasks across the collective."
        helpful_hint = (
            "Share the problem you would like me to route, and I'll pick the best specialist to help."
        )
        return (
            f"I am the Orchestrator Agent. {description} "
            f"I cannot escalate this request automatically, but I can help plan next steps. "
            f"Your message was: \"{user_request.strip()}\". {helpful_hint}"
        )


def main():
    """Entry point with async support."""
    orchestrator = Orchestrator()

    try:
        asyncio.run(orchestrator.run_async())
    except KeyboardInterrupt:
        print(f"\n[{AGENT_NAME}] Shutting down gracefully...")


if __name__ == "__main__":
    main()
