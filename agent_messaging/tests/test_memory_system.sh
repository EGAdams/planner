#!/bin/bash
# Test Memory System
# Wraps test_memory_system.py to verify unified memory functionality

# Navigate to the agent_messaging directory relative to the script location
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🧪 Running Memory System Test..."
echo "📂 Project Root: $PROJECT_ROOT"

cd "$PROJECT_ROOT"

# Run the memory system test script
if python3 test_memory_system.py; then
    echo "✅ Memory System Test Passed"
    exit 0
else
    echo "❌ Memory System Test Failed"
    exit 1
fi
