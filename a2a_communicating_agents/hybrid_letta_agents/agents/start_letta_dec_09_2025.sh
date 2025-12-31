#!/usr/bin/env bash
set -e

cd /home/adamsl/planner

# Activate venv
source .venv/bin/activate

ENV_FILE=/home/adamsl/planner/.env
if [ -f "$ENV_FILE" ]; then
    # shellcheck disable=SC1090
    set -a
    source "$ENV_FILE"
    set +a
fi

# Sanity check – verify key is loaded
if [ -z "$OPENAI_API_KEY" ]; then
    echo "ERROR: OPENAI_API_KEY not set in environment"
    exit 1
fi
echo "OPENAI_API_KEY: loaded from environment"

# Sanity check – verify key is loaded
if [ -z "$EXA_API_KEY" ]; then
    echo "ERROR: EXA_API_KEY not set in environment"
    exit 1
fi
echo "EXA_API_KEY:    loaded from environment"

# Start the server
exec letta server
