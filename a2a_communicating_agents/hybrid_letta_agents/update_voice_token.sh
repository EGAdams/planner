#!/bin/bash
# Update the JWT token in voice-agent-selector.html with a fresh 24-hour token

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HTML_FILE="$SCRIPT_DIR/voice-agent-selector.html"
DEBUG_HTML_FILE="$SCRIPT_DIR/voice-agent-selector-debug.html"
VENV_PYTHON="/home/adamsl/planner/.venv/bin/python3"

echo "Generating fresh 24-hour JWT token..."

# Generate new token
NEW_TOKEN=$($VENV_PYTHON << 'PYTHON_EOF'
import os
import sys
from pathlib import Path
from datetime import timedelta, datetime

# Load environment
env_file = Path("/home/adamsl/ottomator-agents/livekit-agent/.env")
if env_file.exists():
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ.setdefault(key, value)

from livekit import api

api_key = os.environ.get('LIVEKIT_API_KEY')
api_secret = os.environ.get('LIVEKIT_API_SECRET')

# Create a token valid for 24 hours
token = api.AccessToken(api_key, api_secret) \
    .with_identity('user1') \
    .with_name('User') \
    .with_ttl(timedelta(hours=24)) \
    .with_grants(api.VideoGrants(
        room_join=True,
        room='test-room',
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
    ))

print(token.to_jwt())
PYTHON_EOF
)

if [ -z "$NEW_TOKEN" ]; then
    echo "ERROR: Failed to generate token"
    exit 1
fi

echo "Token generated successfully!"
echo ""

# Get current timestamp
TIMESTAMP=$(date -u '+%Y-%m-%d %H:%M:%S UTC')

update_file() {
    local target_file="$1"
    local label="$2"

    if [ ! -f "$target_file" ]; then
        echo "WARNING: $label not found at $target_file (skipping)"
        return
    fi

    cp "$target_file" "$target_file.backup"
    echo "Backed up $label to: $target_file.backup"

    sed -i.tmp "/\/\/ Token for dev mode/,/const TOKEN = '[^']*';/c\\
        // Token for dev mode (valid for 24 hours from $TIMESTAMP)\\
        // NOTE: This token will expire. Regenerate with: ./update_voice_token.sh\\
        const TOKEN = '$NEW_TOKEN';" "$target_file"
    rm -f "$target_file.tmp"

    echo "Updated token in: $target_file"
}

update_file "$HTML_FILE" "Voice Agent Selector"
update_file "$DEBUG_HTML_FILE" "Voice Agent Selector (debug)"

echo "Token valid until: $(date -u -d '+24 hours' '+%Y-%m-%d %H:%M:%S UTC')"
echo ""
echo "If CORS proxy server is running, restart it to serve the updated HTML:"
echo "  pkill -f cors_proxy_server && /home/adamsl/planner/.venv/bin/python3 $SCRIPT_DIR/cors_proxy_server.py &"
echo ""
echo "Or just refresh your browser at http://localhost:9000"
