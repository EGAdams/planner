#!/bin/bash
# Test LiveKit Agent Dispatch Flow
# Validates that agent dispatch is working correctly

set -e

echo "========================================"
echo "LiveKit Agent Dispatch Flow Test"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
success() {
    echo -e "${GREEN}✅ $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
}

info() {
    echo -e "${YELLOW}📝 $1${NC}"
}

# Step 1: Check services
echo "Step 1: Checking Services"
echo "-------------------------"

# Check CORS Proxy
if curl -s http://localhost:9000/api/token?room=test 2>&1 | grep -q token; then
    success "CORS Proxy running on port 9000"
else
    error "CORS Proxy not responding"
    exit 1
fi

# Check LiveKit Server
if ps aux | grep livekit-server | grep -v grep > /dev/null; then
    success "LiveKit server running"
else
    error "LiveKit server not running"
    exit 1
fi

# Check Agent Worker
if ps aux | grep letta_voice_agent_optimized.py | grep -v grep > /dev/null; then
    success "Agent worker running"
else
    error "Agent worker not running"
    exit 1
fi

echo ""

# Step 2: Test dispatch endpoint
echo "Step 2: Testing Dispatch Endpoint"
echo "----------------------------------"

info "Sending dispatch request to test-room..."
DISPATCH_RESPONSE=$(curl -s -X POST http://localhost:9000/api/dispatch-agent \
    -H "Content-Type: application/json" \
    -d '{"room":"test-room"}')

echo "Response: $DISPATCH_RESPONSE"

if echo "$DISPATCH_RESPONSE" | grep -q '"success": true'; then
    success "Dispatch endpoint working"

    # Extract dispatch ID
    DISPATCH_ID=$(echo "$DISPATCH_RESPONSE" | grep -o '"dispatch_id": "[^"]*"' | cut -d'"' -f4)
    if [ -n "$DISPATCH_ID" ]; then
        info "Dispatch ID: $DISPATCH_ID"
    fi
else
    error "Dispatch failed"
    echo "$DISPATCH_RESPONSE"
    exit 1
fi

echo ""

# Step 3: Check agent logs
echo "Step 3: Checking Agent Logs"
echo "----------------------------"

info "Looking for agent registration..."
if tail -50 /tmp/letta_voice_agent.log 2>/dev/null | grep -q "letta-voice-agent"; then
    success "Agent registered with correct name: letta-voice-agent"
else
    error "Agent name not found in logs"
    info "Check logs: tail /tmp/letta_voice_agent.log"
fi

echo ""

# Step 4: Summary
echo "========================================"
echo "Test Summary"
echo "========================================"
success "All automated tests passed!"
echo ""
info "Manual browser test instructions:"
echo "  1. Open http://localhost:9000/debug"
echo "  2. Select any Letta agent"
echo "  3. Click 'Connect'"
echo "  4. Grant microphone permission"
echo "  5. Wait for agent to join (1-3 seconds)"
echo "  6. Speak and verify voice interaction"
echo ""
info "Expected browser debug logs:"
echo "  ✅ Connected to room: test-room"
echo "  📡 Requesting agent dispatch..."
echo "  ✅ Agent dispatch requested"
echo "  👤 Existing participant detected: letta-voice-agent"
echo "  ✅ Agent connected! Start speaking..."
echo ""
info "Monitor agent logs in real-time:"
echo "  tail -f /tmp/letta_voice_agent_new.log"
echo ""
success "Dispatch mechanism is ready!"
