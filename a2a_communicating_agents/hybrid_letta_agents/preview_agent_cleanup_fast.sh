#!/bin/bash
# Preview Agent_66 Cleanup (DRY RUN - FAST VERSION)
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
LETTA_BASE_URL="${LETTA_SERVER_URL:-http://localhost:8283}"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Agent_66 Cleanup Preview (FAST)${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}📋 Fetching Agent_66 instances via API...${NC}"

# Use direct API call for speed
TEMP_FILE=$(mktemp)
trap "rm -f $TEMP_FILE" EXIT

curl -s "${LETTA_BASE_URL}/v1/agents?limit=1000" | \
    .venv/bin/python3 << 'PYTHON_EOF' > "$TEMP_FILE"
import json
import sys

data = json.load(sys.stdin)
agent_66_list = []

for agent in data:
    name = agent.get('name', '')
    if name.startswith('Agent_66'):
        agent_66_list.append({
            'name': name,
            'id': agent.get('id'),
            'description': agent.get('description', 'None')
        })

# Output as simple lines
for agent in agent_66_list:
    print(f"{agent['name']} {agent['id']}")
PYTHON_EOF

# Parse results
TOTAL_COUNT=$(wc -l < "$TEMP_FILE")
KEEP_COUNT=1
DELETE_COUNT=$(grep -v "$KEEP_AGENT_ID" "$TEMP_FILE" | wc -l)

echo ""
echo -e "${BLUE}📊 SUMMARY${NC}"
echo -e "${GREEN}  Total Agent_66* instances: ${TOTAL_COUNT}${NC}"
echo -e "${GREEN}  Will keep: ${KEEP_COUNT} agent${NC}"
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

# Show first 20 agents to delete
COUNT=0
grep -v "$KEEP_AGENT_ID" "$TEMP_FILE" | head -20 | while read -r line; do
    COUNT=$((COUNT + 1))
    AGENT_NAME=$(echo "$line" | awk '{print $1}')
    AGENT_ID=$(echo "$line" | awk '{print $2}')

    echo -e "${RED}$COUNT. ✗${NC} $AGENT_NAME"
    echo -e "     ID: $AGENT_ID"
    echo ""
done

if [ $DELETE_COUNT -gt 20 ]; then
    echo -e "${YELLOW}  ... and $(($DELETE_COUNT - 20)) more${NC}"
    echo ""
fi

echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}ℹ️  This is a DRY RUN - no agents were deleted.${NC}"
echo ""
echo -e "${YELLOW}To actually delete these agents, run:${NC}"
echo -e "  ./cleanup_duplicate_agents.sh"
echo ""
