#!/usr/bin/env bash
set -euo pipefail

# Kill any running Letta server processes so we can restart cleanly.
# Matches both `letta server` and the debug helper script.
if pgrep -f "letta server" >/dev/null 2>&1; then
  echo "Stopping existing 'letta server' process..."
  pkill -f "letta server"
fi

if pgrep -f "debug_letta_server.py" >/dev/null 2>&1; then
  echo "Stopping existing 'debug_letta_server.py' process..."
  pkill -f "debug_letta_server.py"
fi

# Require an OpenAI key before starting the server.
if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "ERROR: OPENAI_API_KEY is not set. Export it, then rerun this script."
  echo "export OPENAI_API_KEY=sk-..."
  exit 1
fi

# Optional overrides; adjust as needed.
export LETTA_BASE_URL="${LETTA_BASE_URL:-http://localhost:8283}"
export LETTA_ORCHESTRATOR_MODEL="${LETTA_ORCHESTRATOR_MODEL:-openai/gpt-4o-mini}"

echo "Starting Letta server with LETTA_BASE_URL=${LETTA_BASE_URL}"
echo "Using orchestrator model: ${LETTA_ORCHESTRATOR_MODEL}"
echo "Press Ctrl+C to stop the server."

# Run in the foreground so you can see logs; remove 'exec' if you prefer background.
exec letta server
