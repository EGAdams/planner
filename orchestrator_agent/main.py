#!/usr/bin/env python3
"""
Orchestrator Agent
Routes user requests to the appropriate specialist agent using Gemini.
"""

import sys
import os
import time
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_messaging import inbox, post_message, create_jsonrpc_response
from rag_system.core.document_manager import DocumentManager
from orchestrator_agent.a2a_dispatcher import A2ADispatcher

AGENT_NAME = "orchestrator-agent"
WORKSPACE_ROOT = Path(__file__).resolve().parents[1]
MODEL_ID = "gemini-2.0-flash"

def log_update(message):
    print(f"[{AGENT_NAME}] {message}")

class Orchestrator:
    def __init__(self):
        self.known_agents = {}
        self.dispatcher = A2ADispatcher(workspace_root=WORKSPACE_ROOT)
        api_key = os.environ.get("GOOGLE_API_KEY")
        if api_key:
            self.client: Optional[genai.Client] = genai.Client(api_key=api_key)
        else:
            self.client = None
            log_update("GOOGLE_API_KEY not set. Falling back to heuristic routing.")
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

        prompt = f"""
You are the Orchestrator Agent. Your job is to route a user request to the best available specialist agent.

Available Agents:
{json.dumps(self.known_agents, indent=2)}

User Request: "{user_request}"

Analyze the request and the available agents. Return a JSON object with:
1. "target_agent": The name of the agent to handle the request.
2. "reasoning": Why you chose this agent.
3. "method": The method to call on the agent (e.g., "agent.execute_task").
4. "params": The parameters for the method (e.g., {{ "description": "..." }}).

If no agent is suitable, set "target_agent" to null.
Return ONLY valid JSON.
"""
        try:
            response = self.client.models.generate_content(
                model=MODEL_ID,
                contents=prompt,
                config={
                    "response_mime_type": "application/json"
                }
            )
            return json.loads(response.text)
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
