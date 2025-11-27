#!/bin/bash
# Test Delegation
# Wraps run_collective.py to verify delegation functionality

# Navigate to the agent_messaging directory relative to the script location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🧪 Running Delegation Test..."
echo "📂 Project Root: $PROJECT_ROOT"

cd "$PROJECT_ROOT"

# Run the collective script which includes delegation simulation
if python3 run_collective.py; then
    echo "✅ Delegation Test Passed"
    exit 0
else
    echo "❌ Delegation Test Failed"
    exit 1
fi
