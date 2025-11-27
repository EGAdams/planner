#!/bin/bash
# Test Agent Discovery
# Wraps run_collective.py to verify agent discovery functionality

# Navigate to the agent_messaging directory relative to the script location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🧪 Running Agent Discovery Test..."
echo "📂 Project Root: $PROJECT_ROOT"

cd "$PROJECT_ROOT"

# Run the collective script
if python3 run_collective.py; then
    echo "✅ Agent Discovery Test Passed"
    exit 0
else
    echo "❌ Agent Discovery Test Failed"
    exit 1
fi
