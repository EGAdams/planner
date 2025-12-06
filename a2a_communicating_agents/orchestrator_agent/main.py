#!/usr/bin/env python3
"""
Orchestrator Agent
Routes user requests to the appropriate specialist agent using OpenAI.
"""

import sys
import os
import time
import json
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

from a2a_communicating_agents.agent_messaging import inbox, post_message, create_jsonrpc_response
from rag_system.core.document_manager import DocumentManager
from a2a_communicating_agents.orchestrator_agent.a2a_dispatcher import A2ADispatcher

AGENT_NAME = "orchestrator-agent"
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]

def log_update(message):
    print(f"[{AGENT_NAME}] {message}")

class Orchestrator:
    def __init__(self, *, llm_client=None, model_id: Optional[str] = None):
        self.known_agents = {}
        self.dispatcher = A2ADispatcher(workspace_root=WORKSPACE_ROOT)
        self.model_id = model_id or os.getenv("ORCHESTRATOR_MODEL") or os.getenv("OPENAI_MODEL") or "gpt-4o-mini"
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

    def discover_agents(self):
        """Scan workspace for agent.json files"""
        print(f"[{AGENT_NAME}] Scanning for agents...")
        registry = self.dispatcher.refresh_registry()
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
        """Use Gemini to decide which agent should handle the request"""

        if not self.client:
            return self._fallback_route(user_request)

        system_prompt = (
            "You are the Orchestrator Agent. Route the user request to the best specialist "
            "agent. Always reply with compact JSON containing keys: target_agent, reasoning, "
            "method, params."
        )
        agent_snapshot = json.dumps(self.known_agents, indent=2)
        user_prompt = (
            f"Available Agents:\n{agent_snapshot}\n\n"
            f'User Request: "{user_request}"\n\n'
            "Return JSON with target_agent (or null), reasoning, method "
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
                "reasoning": "Heuristic keyword match (no Gemini API key available).",
                "method": "agent.execute_task",
                "params": {"description": user_request},
            }
        return None


    def run(self):
        print(f"[{AGENT_NAME}] Started. Listening on topic 'orchestrator'...")
        self.discover_agents()
        
        while True:
            messages = inbox("orchestrator", limit=5, render=False)
            
            for msg in messages:
                message_id = self._extract_message_id(msg)
                if self._message_seen(message_id):
                    continue
                sender_name = (getattr(msg, "sender", "") or "").strip().lower()
                if self._is_self_reference(sender_name):
                    self._mark_message_processed(message_id)
                    continue
                try:
                    content = msg.content
                    # Unwrap markdown if present  # or find a better way to handle this
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0].strip()
                    
                    # Simple text handling for now (if not JSON-RPC)
                    # In a real system, we'd parse JSON-RPC requests to the orchestrator
                    # But here we treat the message content as the "User Request"
                    
                    user_request = content

                    # Skip if it looks like a machine response
                    if content.strip().startswith("{") and "jsonrpc" in content:
                        log_update(f"[{AGENT_NAME}] Skipping machine response: {content[:50]}...")
                        continue

                    log_update(f"[{AGENT_NAME}] Processing request: {user_request[:50]}...")
                    
                    decision = self.decide_route(user_request)
                    if not decision:
                        log_update(f"[{AGENT_NAME}] Router produced no decision; responding directly.")
                        self._respond_directly(
                            user_request=user_request,
                            reasoning="No matching agent available yet, so I'm responding directly.",
                        )
                        continue
                    raw_target = decision.get("target_agent")
                    if decision and not raw_target:
                        log_update(f"[{AGENT_NAME}] Router returned no target; responding directly.")
                        self._respond_directly(
                            user_request=user_request,
                            reasoning=decision.get("reasoning"),
                        )
                        continue

                    target_agent = self._resolve_known_agent(raw_target)
                    if decision and raw_target and not target_agent:
                        log_update(
                            f"[{AGENT_NAME}] Router suggested unknown agent '{raw_target}'; responding directly."
                        )
                        reasoning = decision.get("reasoning") or "Suggested agent is not registered."
                        self._respond_directly(
                            user_request=user_request,
                            reasoning=f"{reasoning} (Agent '{raw_target}' is not available.)",
                        )
                        continue

                    if decision and target_agent:
                        if self._is_self_reference(target_agent):
                            log_update(f"[{AGENT_NAME}] Direct chat requested; responding without delegation.")
                            self._respond_directly(
                                user_request=user_request,
                                reasoning=decision.get("reasoning"),
                            )
                            continue

                    if decision and target_agent:
                        target = target_agent
                        log_update(f"[{AGENT_NAME}] Routing to {target}")

                        params = decision.get("params", {})
                        description = params.get("description", user_request)
                        context = params.get("context", {})
                        artifacts = params.get("artifacts")

                        delegation = self.dispatcher.delegate(
                            agent_name=target,
                            description=description,
                            context=context,
                            artifacts=artifacts,
                        )
                        
                        rpc_payload = json.dumps(delegation["payload"])
                        target_topic = delegation["topic"]

                        # Send the message to the target agent
                        post_message(
                            message=rpc_payload,
                            topic=target_topic,
                            from_agent=AGENT_NAME
                        )
                        
                        # Confirm to user
                        post_message(
                            message=f"I have routed your request to **{target}**. \nReasoning: {decision['reasoning']}",
                            topic="orchestrator",
                            from_agent=AGENT_NAME
                        )
                        
                    else:
                        print(f"[{AGENT_NAME}] No suitable agent found.")
                        post_message(
                            message="I could not find a suitable agent to handle your request.",
                            topic="orchestrator",
                            from_agent=AGENT_NAME
                        )

                except Exception as e:
                    print(f"[{AGENT_NAME}] Error processing message: {e}")
                finally:
                    self._mark_message_processed(message_id)
            
            time.sleep(10)

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

    def _respond_directly(self, *, user_request: str, reasoning: Optional[str] = None) -> None:
        reply = self._generate_direct_response(user_request)
        if reasoning:
            reply = f"{reply}\n\n_{reasoning}_"
        post_message(
            message=reply,
            topic="orchestrator",
            from_agent=AGENT_NAME,
        )

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

if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.run()
