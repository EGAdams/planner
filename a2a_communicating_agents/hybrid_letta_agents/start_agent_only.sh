#!/bin/bash
set -e

# Load environment variables
export $(grep -v '^#' /home/adamsl/ottomator-agents/livekit-agent/.env | xargs)
export $(grep -v '^#' /home/adamsl/planner/.env | xargs)

# Change to agent directory
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents

# Start voice agent
/home/adamsl/planner/.venv/bin/python3 letta_voice_agent.py dev > /tmp/letta_voice_agent.log 2>&1 &

echo "Voice agent started. PID: $!"
echo "Check logs: tail -f /tmp/letta_voice_agent.log"
