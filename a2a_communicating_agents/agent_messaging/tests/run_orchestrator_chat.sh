#!/bin/bash
# Launch orchestrator chat CLI. Defaults to auto-starting the orchestrator agent.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
VENV_PYTHON="$REPO_ROOT/.venv/bin/python"

cd "$REPO_ROOT"

if [ -x "$VENV_PYTHON" ]; then
    PYTHON_BIN="$VENV_PYTHON"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "A Python interpreter is required to start the chat." >&2
    exit 1
fi

if [ "$#" -eq 0 ]; then
    set -- --auto-start
fi

exec "$PYTHON_BIN" a2a_communicating_agents/agent_messaging/orchestrator_chat.py "$@"
