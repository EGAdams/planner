#!/usr/bin/env python3
"""
Orchestrator Agent
Routes user requests to the appropriate specialist agent using OpenAI.
"""

import sys
import os
import time
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from contextlib import suppress

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - handled gracefully at runtime
    OpenAI = None
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import shared modules
PLANNER_ROOT = Path(__file__).resolve().parents[2]
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
            if agent_name == AGENT_NAME:
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
            # Check for new messages
            messages = inbox("orchestrator", limit=5)
            
            for msg in messages:
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
                    
                    if decision and decision.get("target_agent"):
                        target = decision["target_agent"]
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
            
            time.sleep(10)

if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.run()
