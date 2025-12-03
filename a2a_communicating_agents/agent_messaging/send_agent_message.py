#!/usr/bin/env python3
"""
Helper script to send messages to agents via the dashboard
Usage: python send_agent_message.py <agent_id> <message>
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from a2a_communicating_agents.agent_messaging import post_message, create_jsonrpc_request

def send_to_agent(agent_id: str, message: str):
    """Send a message to an agent"""
    
    # Determine the topic based on agent type
    # For now, we'll use 'ops' for dashboard-agent
    # You can extend this mapping as needed
    topic_mapping = {
        'dashboard-agent': 'ops',
        'orchestrator-agent': 'orchestrator'
    }
    
    topic = topic_mapping.get(agent_id, 'general')
    
    # Create a JSON-RPC request
    request = create_jsonrpc_request(
        method="agent.execute_task",
        params={
            "description": message,
            "from": "dashboard-ui"
        }
    )
    
    # Post the message
    post_message(
        message=request,
        topic=topic,
        from_agent="dashboard-ui"
    )
    
    return f"Message sent to {agent_id} on topic '{topic}'"

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python send_agent_message.py <agent_id> <message>", file=sys.stderr)
        sys.exit(1)
    
    agent_id = sys.argv[1]
    message = sys.argv[2]
    
    result = send_to_agent(agent_id, message)
    print(result)
