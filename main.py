#!/usr/bin/env python3
"""
Planner Agent Server
The primary orchestration and planning agent for the workspace.
"""

import sys
import os
import time
import json
from typing import Dict, Any, Optional

# Add parent directory to path to import shared modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from a2a_communicating_agents.agent_messaging import inbox, send, post_message, create_jsonrpc_response
from rag_system.core.document_manager import DocumentManager

AGENT_NAME = "planner-agent"
# Listen to specific topic and general
TOPICS = ["planner-agent", "general"]

def log_update(message):
    print(f"[{AGENT_NAME}] {message}")
    # Also log to file for debugging since stdout might be captured elsewhere
    with open("/tmp/planner-agent.log", "a") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")

def handle_plan_task(params: Dict[str, Any]) -> Dict[str, Any]:
    objective = params.get("objective")
    log_update(f"Planning task: {objective}")
    
    # Mock planning logic
    return {
        "plan": [
            f"Analyze requirements for '{objective}'",
            "Research existing solutions",
            "Draft implementation plan",
            "Execute plan",
            "Verify results"
        ]
    }

def handle_research_topic(params: Dict[str, Any]) -> Dict[str, Any]:
    topic = params.get("topic")
    log_update(f"Researching topic: {topic}")
    
    # Mock research logic
    return {
        "summary": f"Research results for '{topic}'",
        "findings": [
            f"Finding 1 about {topic}",
            f"Finding 2 about {topic}"
        ]
    }

def process_message(msg):
    try:
        content = msg.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()

        # Skip if not JSON
        if not content.strip().startswith("{"):
            return

        data = json.loads(content)

        if data.get("jsonrpc") != "2.0":
            return

        method = data.get("method")
        params = data.get("params", {})
        req_id = data.get("id")

        result = None
        error = None

        log_update(f"Received method: {method}")

        if method == "agent.execute_task":
            description = params.get("description")
            log_update(f"Executing task: {description}")
            result = {"status": "completed", "output": f"Executed: {description}"}

        elif method == "plan_task":
            result = handle_plan_task(params)

        elif method == "research_topic":
            result = handle_research_topic(params)
            
        else:
            # Unknown method
            return

        if (result or error) and req_id:
            response = create_jsonrpc_response(result, req_id)
            if error:
                response["error"] = error
                if "result" in response:
                    del response["result"]

            # Send back to orchestrator or general if sender unknown
            # Ideally we reply to the sender, but the message object might not have it clearly 
            # if it's not in the metadata. 
            # We'll post to 'orchestrator' as a safe default for now.
            target_topic = "orchestrator"
            if msg.sender and msg.sender != "unknown":
                target_topic = msg.sender
                
            post_message(
                message=response,
                topic=target_topic,
                from_agent=AGENT_NAME
            )
            log_update(f"Sent response to {target_topic}")

    except Exception as e:
        log_update(f"Error processing message: {e}")

def run_agent_loop():
    log_update(f"Agent started. Listening on topics: {TOPICS}")

    while True:
        for topic in TOPICS:
            # Check inbox
            log_update(f"Checking inbox for topic: {topic}")
            messages = inbox(topic, limit=5)
            log_update(f"Inbox returned {len(messages)} messages")
            
            if messages:
                log_update(f"Polled {len(messages)} messages for topic {topic}")
            
            for msg in messages:
                process_message(msg)

        time.sleep(2) # Poll every 2 seconds

if __name__ == "__main__":
    run_agent_loop()
