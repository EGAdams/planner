#!/bin/bash
# Simple test to send a message to orchestrator

cd /home/adamsl/planner/a2a_communicating_agents/agent_messaging

# Send message via echo pipe
echo "who are you?" | timeout 20 /home/adamsl/planner/.venv/bin/python3 orchestrator_chat.py 2>&1 | head -50
