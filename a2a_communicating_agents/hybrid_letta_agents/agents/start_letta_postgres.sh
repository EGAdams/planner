#!/usr/bin/env bash
set -euo pipefail

# Start Letta against Postgres with safety checks and the Postgres SQL patch applied.
# Run from the repository root or this agents directory. Requires the .venv.

# Resolve repo root by walking up until we find .venv/bin/activate (max 4 levels).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT=""
for _ in 1 2 3 4; do
  try_root="${SCRIPT_DIR}"
  if [[ -f "${try_root}/.venv/bin/activate" ]]; then
    REPO_ROOT="${try_root}"
    break
  fi
  SCRIPT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
done

if [[ -z "${REPO_ROOT}" ]]; then
  echo "ERROR: Could not locate .venv/bin/activate by walking up from ${SCRIPT_DIR}. Set REPO_ROOT manually in this script."
  exit 1
fi

VENV_ACTIVATE="${REPO_ROOT}/.venv/bin/activate"
PATCH_TARGET="${REPO_ROOT}/.venv/lib/python3.12/site-packages/letta/orm/message.py"

if [[ ! -f "$VENV_ACTIVATE" ]]; then
  echo "ERROR: Cannot find venv at ${VENV_ACTIVATE}. Create it or adjust the path."
  exit 1
fi

source "$VENV_ACTIVATE"

# Ensure required env vars are present.
if [[ -z "${OPENAI_API_KEY:-}" ]]; then
  echo "ERROR: OPENAI_API_KEY is not set. Export it before running."
  exit 1
fi

# Default Postgres creds (created by init_letta_db.py): letta/letta@localhost:5432/letta
DEFAULT_PG_URI="postgresql+asyncpg://letta:letta@localhost:5432/letta"
PG_URI="${LETTA_PG_URI:-${LETTA_DB_URI:-${LETTA_DB_URL:-}}}"
if [[ -z "${PG_URI}" ]]; then
  echo "LETTA_PG_URI not set; defaulting to ${DEFAULT_PG_URI}"
  PG_URI="${DEFAULT_PG_URI}"
fi
# Guard against placeholder values that will crash (e.g., user:pass@host:5432/dbname).
if [[ "${PG_URI}" == *"user:pass@host:5432/dbname"* || "${PG_URI}" == *"user:pass@host"* ]]; then
  echo "Detected placeholder Postgres URI; defaulting to ${DEFAULT_PG_URI}"
  PG_URI="${DEFAULT_PG_URI}"
fi
export LETTA_PG_URI="${PG_URI}"

# Apply defensive patch so Postgres uses ON CONFLICT instead of SQLite's OR IGNORE.
if [[ ! -f "$PATCH_TARGET" ]]; then
  echo "WARNING: Patch target not found at ${PATCH_TARGET}; ensure Letta is installed in ${REPO_ROOT}/.venv."
else
  python - "$PATCH_TARGET" <<'PY'
import pathlib, sys
path = pathlib.Path(sys.argv[1])
text = path.read_text()
updated = text.replace("settings.database_engine is DatabaseChoice.POSTGRES", "settings.database_engine == DatabaseChoice.POSTGRES")
if updated != text:
    path.write_text(updated)
    print(f"Applied Postgres ON CONFLICT patch to {path}")
else:
    print("Postgres patch already applied.")
PY
fi

# Stop any existing Letta servers.
if pgrep -f "letta server" >/dev/null 2>&1; then
  echo "Stopping existing 'letta server' process..."
  pkill -f "letta server"
fi
if pgrep -f "debug_letta_server.py" >/dev/null 2>&1; then
  echo "Stopping existing 'debug_letta_server.py' process..."
  pkill -f "debug_letta_server.py"
fi

export LETTA_BASE_URL="${LETTA_BASE_URL:-http://localhost:8283}"
export LETTA_ORCHESTRATOR_MODEL="${LETTA_ORCHESTRATOR_MODEL:-openai/gpt-4o-mini}"

echo "Starting Letta on Postgres..."
echo "  LETTA_BASE_URL=${LETTA_BASE_URL}"
echo "  LETTA_ORCHESTRATOR_MODEL=${LETTA_ORCHESTRATOR_MODEL}"
echo "  DB URI: ${LETTA_PG_URI:-${LETTA_DB_URI:-${LETTA_DB_URL:-unset}}}"
echo "Press Ctrl+C to stop the server."

exec letta server --port 8283
