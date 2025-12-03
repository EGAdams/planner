#!/bin/bash
# Test {{TEST_NAME}}
# Description: {{TEST_DESCRIPTION}}

# Navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "🧪 Running {{TEST_NAME}} Test..."
echo "📂 Project Root: $PROJECT_ROOT"

cd "$PROJECT_ROOT"

# Run the test
if {{TEST_COMMAND}}; then
    echo "✅ {{TEST_NAME}} Test Passed"
    exit 0
else
    echo "❌ {{TEST_NAME}} Test Failed"
    exit 1
fi
