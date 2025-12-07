#!/bin/bash
# Start Letta server with proper environment variables

# ALWAYS load environment from /home/adamsl/planner/.env
ENV_FILE="/home/adamsl/planner/.env"

if [ -f "$ENV_FILE" ]; then
    echo "Loading environment from $ENV_FILE"
    set -a
    source "$ENV_FILE"
    set +a
else
    echo "WARNING: $ENV_FILE not found, trying relative path..."
    # Fallback to relative path
    if [ -f ../../../.env ]; then
        set -a
        source ../../../.env
        set +a
    fi
fi

# Ensure OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "ERROR: OPENAI_API_KEY is not set"
    echo "Please ensure it is defined in $ENV_FILE"
    exit 1
fi

echo "OPENAI_API_KEY is set (length: ${#OPENAI_API_KEY} chars)"

# Start Letta server
exec letta server --port 8283
