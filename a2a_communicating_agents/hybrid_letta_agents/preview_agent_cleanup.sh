#!/bin/bash
# Preview Agent_66 Cleanup (DRY RUN)
# Shows what would be deleted WITHOUT actually deleting

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
KEEP_AGENT_ID="agent-4dfca708-49a8-4982-8e36-0f1146f9a66e"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Agent_66 Cleanup Preview (DRY RUN)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Create temporary file for agent list
TEMP_FILE=$(mktemp)
trap "rm -f $TEMP_FILE" EXIT

echo -e "${YELLOW}📋 Fetching all agents...${NC}"

# Get all agents and filter for Agent_66* (use venv python with timeout)
timeout 30 .venv/bin/python3 list_agents.py > "$TEMP_FILE" 2>&1

if [ $? -eq 124 ]; then
    echo -e "${RED}⚠️  Timeout fetching agents. Using API directly...${NC}"
    # Fallback: use curl directly to get agents
    curl -s "http://localhost:8283/v1/agents?limit=1000" | \
        python3 -c "
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

echo ""
echo -e "${BLUE}📊 SUMMARY${NC}"
echo -e "${GREEN}  Total Agent_66* instances: ${TOTAL_COUNT}${NC}"
echo -e "${GREEN}  Will keep: 1 agent${NC}"
echo -e "${RED}  Will delete: ${DELETE_COUNT} agents${NC}"
echo ""

if [ $DELETE_COUNT -eq 0 ]; then
    echo -e "${GREEN}✅ No duplicates found. Agent_66 is clean!${NC}"
    exit 0
fi

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}AGENT TO KEEP:${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✓${NC} Name: Agent_66"
echo -e "  ID: ${KEEP_AGENT_ID}"
echo -e "  Description: Remembers project status, web search, coder delegation"
echo ""

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${RED}AGENTS TO DELETE (${DELETE_COUNT} total):${NC}"
echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

COUNT=0
echo "$TO_DELETE" | while read -r agent_id; do
    if [ -n "$agent_id" ]; then
        COUNT=$((COUNT + 1))
        # Get agent details from temp file or API
        AGENT_NAME=$(grep "$agent_id" "$TEMP_FILE" | head -1 | awk '{print $1}')
        if [ -z "$AGENT_NAME" ]; then
            AGENT_NAME="Agent_66"  # Default if not found
        fi

        echo -e "${RED}$COUNT. ✗${NC} $AGENT_NAME"
        echo -e "     ID: $agent_id"
        echo ""
    fi
done

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}ℹ️  This is a DRY RUN - no agents were deleted.${NC}"
echo ""
echo -e "${YELLOW}To actually delete these agents, run:${NC}"
echo -e "  ./cleanup_duplicate_agents.sh"
echo ""
