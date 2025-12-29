#!/bin/bash
# Cleanup Duplicate Agent_66 Instances
# Deletes all Agent_66* agents EXCEPT the correct one with project memory

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
LETTA_BASE_URL="${LETTA_SERVER_URL:-http://localhost:8283}"
KEEP_AGENT_ID="agent-4dfca708-49a8-4982-8e36-0f1146f9a66e"
LOG_FILE="/tmp/agent_cleanup_$(date +%Y%m%d_%H%M%S).log"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Agent_66 Cleanup Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Create temporary file for agent list
TEMP_FILE=$(mktemp)
trap "rm -f $TEMP_FILE" EXIT

echo -e "${YELLOW}📋 Fetching all agents...${NC}"

# Get all agents and filter for Agent_66* (use venv python with timeout)
timeout 30 .venv/bin/python3 list_agents.py > "$TEMP_FILE" 2>&1

if [ $? -eq 124 ]; then
    echo -e "${YELLOW}⚠️  Timeout fetching agents. Using API directly...${NC}"
    # Fallback: use curl directly to get agents
    curl -s "http://localhost:8283/v1/agents?limit=1000" | \
        .venv/bin/python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    for agent in data:
        if agent.get('name', '').startswith('Agent_66'):
            print(f\"{agent['name']} {agent['id']}\")
except: pass
" > "$TEMP_FILE" 2>&1
fi

# Parse agent IDs from the output
AGENT_IDS=$(grep "Agent_66" "$TEMP_FILE" | awk '{print $NF}' | grep -E "^agent-" | grep -v "^$")

# Count total agents
TOTAL_COUNT=$(echo "$AGENT_IDS" | wc -l)

# Filter out the one we want to keep
TO_DELETE=$(echo "$AGENT_IDS" | grep -v "$KEEP_AGENT_ID" || true)
DELETE_COUNT=$(echo "$TO_DELETE" | grep -v "^$" | wc -l)
KEEP_COUNT=1

echo ""
echo -e "${GREEN}✅ Found ${TOTAL_COUNT} Agent_66* instances${NC}"
echo -e "${GREEN}✅ Keeping: 1 agent (ID: ${KEEP_AGENT_ID})${NC}"
echo -e "${RED}🗑️  Will delete: ${DELETE_COUNT} duplicate agents${NC}"
echo ""

if [ $DELETE_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ No duplicates to delete. Agent_66 is clean!${NC}"
    exit 0
fi

# Show first 10 agents to be deleted
echo -e "${YELLOW}Preview of agents to delete (first 10):${NC}"
echo "$TO_DELETE" | head -10 | while read -r agent_id; do
    if [ -n "$agent_id" ]; then
        # Get agent name from temp file
        AGENT_NAME=$(grep "$agent_id" "$TEMP_FILE" | head -1 | awk '{print $1}')
        if [ -z "$AGENT_NAME" ]; then
            AGENT_NAME="Agent_66"
        fi
        echo -e "  ${RED}✗${NC} $AGENT_NAME (${agent_id})"
    fi
done

if [ $DELETE_COUNT -gt 10 ]; then
    echo -e "  ... and $(($DELETE_COUNT - 10)) more"
fi

echo ""
echo -e "${YELLOW}Agent to KEEP:${NC}"
echo -e "  ${GREEN}✓${NC} Agent_66 (${KEEP_AGENT_ID})"
echo -e "    Description: Remembers project status, web search, coder delegation"
echo ""

# Safety confirmation
echo -e "${RED}⚠️  WARNING: This will permanently delete ${DELETE_COUNT} agents!${NC}"
echo -e "${YELLOW}Type 'DELETE' to confirm (or anything else to cancel):${NC} "
read -r CONFIRMATION

if [ "$CONFIRMATION" != "DELETE" ]; then
    echo -e "${BLUE}❌ Cancelled. No agents were deleted.${NC}"
    exit 0
fi

echo ""
echo -e "${YELLOW}🗑️  Starting deletion process...${NC}"
echo "Log file: $LOG_FILE"
echo ""

# Initialize counters
DELETED=0
FAILED=0
SKIPPED=0

# Delete agents one by one
echo "$TO_DELETE" | while read -r agent_id; do
    if [ -z "$agent_id" ]; then
        continue
    fi

    # Safety check: never delete the keeper agent
    if [ "$agent_id" == "$KEEP_AGENT_ID" ]; then
        echo -e "${YELLOW}⚠️  SKIPPED (protected): ${agent_id}${NC}"
        SKIPPED=$((SKIPPED + 1))
        echo "SKIPPED (protected): $agent_id" >> "$LOG_FILE"
        continue
    fi

    # Get agent name for logging
    AGENT_NAME=$(grep -B 1 "$agent_id" "$TEMP_FILE" | grep "Name:" | sed 's/.*Name: //' || echo "Unknown")

    # Attempt deletion
    echo -n "Deleting: $AGENT_NAME ($agent_id)... "

    RESPONSE=$(curl -s -w "\n%{http_code}" \
        -X DELETE \
        "${LETTA_BASE_URL}/v1/agents/${agent_id}" \
        2>&1)

    HTTP_CODE=$(echo "$RESPONSE" | tail -1)

    if [ "$HTTP_CODE" == "200" ] || [ "$HTTP_CODE" == "204" ]; then
        echo -e "${GREEN}✓ Deleted${NC}"
        DELETED=$((DELETED + 1))
        echo "SUCCESS: Deleted $AGENT_NAME ($agent_id)" >> "$LOG_FILE"
    else
        echo -e "${RED}✗ Failed (HTTP $HTTP_CODE)${NC}"
        FAILED=$((FAILED + 1))
        echo "FAILED: $AGENT_NAME ($agent_id) - HTTP $HTTP_CODE" >> "$LOG_FILE"
        echo "Response: $RESPONSE" >> "$LOG_FILE"
    fi

    # Small delay to avoid overwhelming the server
    sleep 0.1
done

# Read final counts from log file
DELETED=$(grep "^SUCCESS:" "$LOG_FILE" | wc -l)
FAILED=$(grep "^FAILED:" "$LOG_FILE" | wc -l)
SKIPPED=$(grep "^SKIPPED:" "$LOG_FILE" | wc -l)

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Cleanup Complete${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}✅ Deleted:  ${DELETED} agents${NC}"
echo -e "${RED}✗ Failed:   ${FAILED} agents${NC}"
echo -e "${YELLOW}⊘ Skipped:  ${SKIPPED} agents${NC}"
echo ""
echo -e "${GREEN}✅ Kept:     1 agent (${KEEP_AGENT_ID})${NC}"
echo ""
echo "Full log: $LOG_FILE"
echo ""

# Verify the correct agent still exists
echo -e "${YELLOW}🔍 Verifying correct agent still exists...${NC}"
VERIFY_RESPONSE=$(curl -s "${LETTA_BASE_URL}/v1/agents/${KEEP_AGENT_ID}" 2>&1)

if echo "$VERIFY_RESPONSE" | grep -q "agent-4dfca708"; then
    echo -e "${GREEN}✅ VERIFIED: Correct Agent_66 is still active!${NC}"
else
    echo -e "${RED}⚠️  WARNING: Could not verify agent. Check manually!${NC}"
fi

echo ""
echo -e "${BLUE}Run ./verify_agent_fix.py to confirm configuration.${NC}"
