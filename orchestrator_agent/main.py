#!/usr/bin/env python3
"""
Orchestrator Agent
Routes user requests to the appropriate specialist agent using Gemini.
"""

import sys
import os
import time
import json
import glob
from typing import Dict, List
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent_messaging import inbox, send, post_message, create_jsonrpc_request, create_jsonrpc_response
from rag_system.core.document_manager import DocumentManager

AGENT_NAME = "orchestrator-agent"
WORKSPACE_ROOT = "/home/adamsl/planner"
MODEL_ID = "gemini-2.0-flash"

class Orchestrator:
    def __init__(self):
        self.known_agents = {}
        self.client = genai.Client(api_key=os.environ.get("GOOGLE_API_KEY"))
        self.doc_manager = DocumentManager()
        
    def discover_agents(self):
        """Scan workspace for agent.json files"""
        print(f"[{AGENT_NAME}] Scanning for agents...")
        agent_files = glob.glob(os.path.join(WORKSPACE_ROOT, "**/agent.json"), recursive=True)
        
        for file_path in agent_files:
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    agent_name = data.get("name")
                    if agent_name and agent_name != AGENT_NAME:
                        self.known_agents[agent_name] = {
                            "description": data.get("description"),
                            "capabilities": data.get("capabilities", []),
                            "topics": data.get("topics", [])
                        }
            except Exception as e:
                print(f"[{AGENT_NAME}] Error reading {file_path}: {e}")
                
        print(f"[{AGENT_NAME}] Discovered {len(self.known_agents)} agents: {list(self.known_agents.keys())}")

    def decide_route(self, user_request: str) -> Dict:
        """Use Gemini to decide which agent should handle the request"""
        
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

    def run(self):
        print(f"[{AGENT_NAME}] Started. Listening on topic 'orchestrator'...")
        self.discover_agents()
        
        while True:
            # Check for new messages
            messages = inbox("orchestrator", limit=5)
            
            for msg in messages:
                try:
                    content = msg.content
                    # Unwrap markdown if present
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0].strip()
                    
                    # Simple text handling for now (if not JSON-RPC)
                    # In a real system, we'd parse JSON-RPC requests to the orchestrator
                    # But here we treat the message content as the "User Request"
                    
                    user_request = content
                    
                    # Skip if it looks like a machine response
                    if content.strip().startswith("{") and "jsonrpc" in content:
                        continue

                    print(f"[{AGENT_NAME}] Processing request: {user_request[:50]}...")
                    
                    decision = self.decide_route(user_request)
                    
                    if decision and decision.get("target_agent"):
                        target = decision["target_agent"]
                        print(f"[{AGENT_NAME}] Routing to {target}")
                        
                        # Construct JSON-RPC for the target agent
                        rpc_payload = create_jsonrpc_request(
                            method=decision.get("method", "agent.execute_task"),
                            params=decision.get("params", {})
                        )
                        
                        # Send to the target agent's topic (usually their name or a shared topic)
                        # For simplicity, we'll assume agents listen to a topic named after them OR 'ops' for ops agent
                        # Based on agent.json, dashboard-ops-agent listens to 'ops'
                        
                        target_topic = "general"
                        if "ops" in self.known_agents[target]["topics"]:
                            target_topic = "ops"
                        
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
