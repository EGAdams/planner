#!/bin/bash
# Visual Routing Status Report
# Displays current testing agent configuration and routing consistency

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Paths
PROJECT_ROOT="/home/adamsl/planner/nonprofit_finance_db"
VAN_FILE="${PROJECT_ROOT}/.claude/commands/van.md"
AGENTS_FILE="${PROJECT_ROOT}/.claude-collective/agents.md"
CONFIG_FILE="${PROJECT_ROOT}/.claude/config/testing-agent.conf"

# Header
echo -e "${CYAN}╔════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║   Testing Agent Routing Status Report     ║${NC}"
echo -e "${CYAN}╔════════════════════════════════════════════╗${NC}"
echo ""

# Load configuration
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo -e "${RED}✗ Configuration file not found${NC}"
    exit 1
fi

source "$CONFIG_FILE"

# 1. Active Agent Configuration
echo -e "${BLUE}1. Active Agent Configuration${NC}"
echo "   ─────────────────────────────"
echo -e "   Active:  ${GREEN}${ACTIVE_TESTING_AGENT}${NC}"
echo -e "   Backup:  ${YELLOW}${BACKUP_TESTING_AGENT}${NC}"
echo -e "   Updated: ${LAST_SWITCHED}"
echo ""

# 2. Van.md Routing Patterns
echo -e "${BLUE}2. Van.md Routing Patterns${NC}"
echo "   ─────────────────────────────"

# Check immediate routing
if grep -A 1 '"test/validate X"' "$VAN_FILE" | tail -1 | grep -q "@${ACTIVE_TESTING_AGENT}"; then
    echo -e "   ${GREEN}✓${NC} IMMEDIATE ROUTING table: @${ACTIVE_TESTING_AGENT}"
else
    echo -e "   ${RED}✗${NC} IMMEDIATE ROUTING table: Not configured"
fi

# Check complex routing
if grep -A 1 "🧪 Testing & Quality" "$VAN_FILE" | tail -1 | grep -q "@${ACTIVE_TESTING_AGENT}"; then
    echo -e "   ${GREEN}✓${NC} COMPLEX REQUEST table: @${ACTIVE_TESTING_AGENT}"
else
    echo -e "   ${RED}✗${NC} COMPLEX REQUEST table: Not configured"
fi

# Check decision tree
if grep "Testing Focus?" "$VAN_FILE" | grep -q "@${ACTIVE_TESTING_AGENT}"; then
    echo -e "   ${GREEN}✓${NC} DECISION TREE: @${ACTIVE_TESTING_AGENT}"
else
    echo -e "   ${RED}✗${NC} DECISION TREE: Not configured"
fi

# Count total references
total_refs=$(grep -c "@${ACTIVE_TESTING_AGENT}" "$VAN_FILE" || true)
echo -e "   ${BLUE}ℹ${NC}  Total references: ${total_refs}"
echo ""

# 3. Agent Catalog Status
echo -e "${BLUE}3. Agent Catalog Status${NC}"
echo "   ─────────────────────────────"

# Check for PRIMARY tag
if grep "@${ACTIVE_TESTING_AGENT}" "$AGENTS_FILE" | grep -q "PRIMARY"; then
    echo -e "   ${GREEN}✓${NC} ${ACTIVE_TESTING_AGENT}: [PRIMARY]"
else
    echo -e "   ${YELLOW}⚠${NC} ${ACTIVE_TESTING_AGENT}: Missing [PRIMARY] tag"
fi

# Check for LEGACY tag
if grep "@${BACKUP_TESTING_AGENT}" "$AGENTS_FILE" | grep -q "LEGACY"; then
    echo -e "   ${GREEN}✓${NC} ${BACKUP_TESTING_AGENT}: [LEGACY]"
else
    echo -e "   ${YELLOW}⚠${NC} ${BACKUP_TESTING_AGENT}: Missing [LEGACY] tag"
fi
echo ""

# 4. Configuration Consistency
echo -e "${BLUE}4. Configuration Consistency${NC}"
echo "   ─────────────────────────────"

issues=0

# Check if config matches van.md
van_primary=$(grep -v "^#" "$VAN_FILE" | grep -o "@[a-z-]*test[a-z-]*-agent" | sort -u | head -1 | tr -d '@')
if [[ "$van_primary" == "$ACTIVE_TESTING_AGENT" ]]; then
    echo -e "   ${GREEN}✓${NC} Config matches van.md routing"
else
    echo -e "   ${RED}✗${NC} Config/van.md mismatch: config=${ACTIVE_TESTING_AGENT}, van=${van_primary}"
    ((issues++))
fi

# Check for mixed references
mixed_refs=$(grep -E "test.*@${BACKUP_TESTING_AGENT}|Testing.*@${BACKUP_TESTING_AGENT}" "$VAN_FILE" | grep -v "Available" | wc -l)
if [[ $mixed_refs -eq 0 ]]; then
    echo -e "   ${GREEN}✓${NC} No mixed agent references"
else
    echo -e "   ${YELLOW}⚠${NC} Found ${mixed_refs} references to backup agent in routing"
    ((issues++))
fi

# Check minimum reference count
if [[ $total_refs -ge 3 ]]; then
    echo -e "   ${GREEN}✓${NC} Sufficient routing coverage (${total_refs} ≥ 3)"
else
    echo -e "   ${RED}✗${NC} Insufficient routing coverage (${total_refs} < 3)"
    ((issues++))
fi
echo ""

# 5. Summary
echo -e "${BLUE}5. Summary${NC}"
echo "   ─────────────────────────────"
if [[ $issues -eq 0 ]]; then
    echo -e "   ${GREEN}✓ All checks passed${NC}"
    echo -e "   ${GREEN}✓ Routing configuration is consistent${NC}"
else
    echo -e "   ${YELLOW}⚠ ${issues} issue(s) detected${NC}"
    echo -e "   ${YELLOW}⚠ Consider running test suite for details${NC}"
fi
echo ""

# Footer
echo -e "${CYAN}╚════════════════════════════════════════════╝${NC}"
echo ""
echo "Run full test suite: ./.claude/tests/routing/test-agent-routing.sh"
echo "Switch agents: ./.claude/scripts/switch-testing-agent.sh {codex|claude|status}"
echo ""
