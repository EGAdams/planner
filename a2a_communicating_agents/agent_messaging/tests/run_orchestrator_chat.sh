#!/bin/bash
# Launch orchestrator chat CLI using the WORKING simple async version

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
VENV_PYTHON="$REPO_ROOT/.venv/bin/python3"

cd "$REPO_ROOT/a2a_communicating_agents"

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

echo "🚀 Starting WORKING orchestrator chat..."
echo "✅ Using async WebSocket transport"
echo ""

exec "$PYTHON_BIN" simple_orchestrator_chat.py
