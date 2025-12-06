#!/bin/bash
# Stop all A2A agents

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🛑 Stopping all A2A agents..."

# Stop in reverse order
[ -f stop_tester_agent.sh ] && bash stop_tester_agent.sh
[ -f stop_coder_agent.sh ] && bash stop_coder_agent.sh
[ -f stop_orchestrator.sh ] && bash stop_orchestrator.sh
[ -f stop_websocket_server.sh ] && bash stop_websocket_server.sh

echo "✅ All agents stopped"
