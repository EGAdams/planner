#!/bin/bash
# Helper to run the orchestrator routing pytest suite from the smart menu.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"

cd "$REPO_ROOT"

if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
else
    echo "python3 is required to run tests." >&2
    exit 1
fi

echo "🧪 Running orchestrator routing tests..."
"$PYTHON_BIN" -m pytest tests/unit/test_orchestrator_agent.py -q
