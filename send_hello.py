import sys
import os
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent_messaging import send, post_message, create_jsonrpc_request

print("Sending 'hello' to planner-agent...")

# Create a JSON-RPC request for execute_task (which the agent handles)
# Or just a plain message if the agent handles it (my code handles JSON-RPC)
payload = create_jsonrpc_request(
    method="agent.execute_task",
    params={"description": "hello from CLI"}
)

# Send to 'planner-agent' topic on the board
post_message(message=payload, topic="planner-agent", from_agent="cli-user")

print("Message sent.")
