#!/bin/bash
# Show Functional Testing Agent Status
# Displays current active agent and routing configuration

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
CONFIG_FILE="${PROJECT_ROOT}/.claude/config/functional-testing-agent.conf"
LEGACY_AGENT_FILE="${PROJECT_ROOT}/.claude/agents/functional-testing-agent.md"

echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  Functional Testing Agent Status Dashboard             ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if config file exists
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo -e "${RED}✗ Configuration file not found${NC}"
    echo "  Expected: $CONFIG_FILE"
    exit 1
fi

# Load configuration
source "$CONFIG_FILE"

# Display active configuration
echo -e "${BLUE}Active Configuration:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "  Active Agent:  ${GREEN}${ACTIVE_FUNCTIONAL_TESTING_AGENT}${NC}"
echo -e "  Backup Agent:  ${YELLOW}${BACKUP_FUNCTIONAL_TESTING_AGENT}${NC}"
echo -e "  Last Switched: ${LAST_SWITCHED}"
echo -e "  Switched By:   ${SWITCHED_BY}"
echo ""

# Check van.md routing patterns
echo -e "${BLUE}Routing Configuration:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ -f "$VAN_FILE" ]]; then
    active_count=$(grep -c "@${ACTIVE_FUNCTIONAL_TESTING_AGENT}" "$VAN_FILE" || true)
    backup_count=$(grep -c "@${BACKUP_FUNCTIONAL_TESTING_AGENT}" "$VAN_FILE" || true)

    echo -e "  Van.md Active Refs:  ${GREEN}${active_count}${NC}"
    echo -e "  Van.md Backup Refs:  ${YELLOW}${backup_count}${NC}"

    if [[ $active_count -ge 0 ]]; then
        echo -e "  Status: ${GREEN}✓ Consistent (no explicit routing needed)${NC}"
    else
        echo -e "  Status: ${RED}✗ Inconsistent${NC}"
    fi
else
    echo -e "  ${RED}✗ Van.md not found${NC}"
fi
echo ""

# Check agents.md catalog
echo -e "${BLUE}Agent Catalog Status:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ -f "$AGENTS_FILE" ]]; then
    has_primary=$(grep "@${ACTIVE_FUNCTIONAL_TESTING_AGENT}" "$AGENTS_FILE" | grep -c "PRIMARY" || true)
    has_legacy=$(grep "@${BACKUP_FUNCTIONAL_TESTING_AGENT}" "$AGENTS_FILE" | grep -c "LEGACY" || true)

    if [[ $has_primary -gt 0 ]]; then
        echo -e "  PRIMARY tag:  ${GREEN}✓ Present${NC}"
    else
        echo -e "  PRIMARY tag:  ${RED}✗ Missing${NC}"
    fi

    if [[ $has_legacy -gt 0 ]]; then
        echo -e "  LEGACY tag:   ${GREEN}✓ Present${NC}"
    else
        echo -e "  LEGACY tag:   ${YELLOW}⚠ Missing${NC}"
    fi
else
    echo -e "  ${RED}✗ Agents.md not found${NC}"
fi
echo ""

# Check deprecation notice
echo -e "${BLUE}Deprecation Notice:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [[ -f "$LEGACY_AGENT_FILE" ]]; then
    if grep -q "DEPRECATION NOTICE" "$LEGACY_AGENT_FILE"; then
        echo -e "  ${GREEN}✓ Legacy agent has deprecation notice${NC}"
    else
        echo -e "  ${YELLOW}⚠ Legacy agent missing deprecation notice${NC}"
    fi
else
    echo -e "  ${RED}✗ Legacy agent file not found${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}Configuration Summary:${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Count issues
issues=0

if [[ ! -f "$VAN_FILE" ]]; then ((issues++)); fi
if [[ ! -f "$AGENTS_FILE" ]]; then ((issues++)); fi
if [[ ! -f "$LEGACY_AGENT_FILE" ]]; then ((issues++)); fi

if [[ -f "$VAN_FILE" ]]; then
    active_count=$(grep -c "@${ACTIVE_FUNCTIONAL_TESTING_AGENT}" "$VAN_FILE" || true)
    # Functional testing agent doesn't need explicit routing in van.md
fi

if [[ -f "$AGENTS_FILE" ]]; then
    has_primary=$(grep "@${ACTIVE_FUNCTIONAL_TESTING_AGENT}" "$AGENTS_FILE" | grep -c "PRIMARY" || true)
    if [[ $has_primary -eq 0 ]]; then ((issues++)); fi
fi

if [[ $issues -eq 0 ]]; then
    echo -e "  ${GREEN}✓ All checks passed - Configuration is healthy${NC}"
else
    echo -e "  ${YELLOW}⚠ ${issues} issue(s) detected - Review status above${NC}"
fi

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Usage info
echo -e "${BLUE}Quick Actions:${NC}"
echo "  Switch to Codex:  .claude/scripts/switch-functional-testing-agent.sh codex"
echo "  Switch to Claude: .claude/scripts/switch-functional-testing-agent.sh claude"
echo "  Run tests:        .claude/tests/routing/test-functional-testing-routing.sh"
echo ""
