#!/bin/bash
# Start all A2A agents in correct order with health checks

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🚀 Starting A2A Agent System..."
echo "================================"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Start WebSocket Server
echo -e "${YELLOW}📡 Starting WebSocket server...${NC}"
bash start_websocket_server.sh

# Wait for WebSocket server to be ready
echo -e "${YELLOW}⏳ Waiting for WebSocket server on port 3030...${NC}"
for i in {1..10}; do
    if ss -tln 2>/dev/null | grep -q ":3030 " || netstat -tln 2>/dev/null | grep -q ":3030 "; then
        echo -e "${GREEN}✅ WebSocket server is ready!${NC}"
        break
    fi
    if [ $i -eq 10 ]; then
        echo -e "${RED}❌ WebSocket server failed to start${NC}"
        exit 1
    fi
    sleep 1
done

# Step 2: Start Orchestrator
echo -e "${YELLOW}🎭 Starting Orchestrator agent...${NC}"
bash start_orchestrator.sh

# Wait a moment for orchestrator to initialize
sleep 2

# Step 3: Start Coder Agent
echo -e "${YELLOW}💻 Starting Coder agent...${NC}"
bash start_coder_agent.sh

# Wait a moment
sleep 1

# Step 4: Start Tester Agent
echo -e "${YELLOW}🧪 Starting Tester agent...${NC}"
bash start_tester_agent.sh

# Give everything a moment to stabilize
sleep 2

echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✅ All agents started successfully!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Verify status:"
echo "  - WebSocket: tail -f ../logs/websocket.log"
echo "  - Orchestrator: tail -f ../logs/orchestrator.log"
echo "  - Coder: tail -f ../logs/coder.log"
echo "  - Tester: tail -f ../logs/tester.log"
echo ""
echo "Chat with orchestrator:"
echo "  cd agent_messaging && python3 orchestrator_chat.py"
echo ""
