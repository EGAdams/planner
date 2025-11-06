#!/bin/bash
# Functional Testing Agent Switcher Script
# Switches between codex and claude functional testing agents in routing configuration

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Paths
PROJECT_ROOT="/home/adamsl/planner/nonprofit_finance_db"
VAN_FILE="${PROJECT_ROOT}/.claude/commands/van.md"
CONFIG_FILE="${PROJECT_ROOT}/.claude/config/functional-testing-agent.conf"
BACKUP_DIR="${PROJECT_ROOT}/.claude/config/backups"

# Agent names
CODEX_AGENT="codex-functional-testing-agent"
CLAUDE_AGENT="functional-testing-agent"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Function to show current status
show_status() {
    echo -e "${BLUE}Current Functional Testing Agent Configuration${NC}"
    echo "======================================"

    if [[ ! -f "$CONFIG_FILE" ]]; then
        echo -e "${RED}Error: Configuration file not found${NC}"
        exit 1
    fi

    source "$CONFIG_FILE"

    echo -e "Active Agent: ${GREEN}${ACTIVE_FUNCTIONAL_TESTING_AGENT}${NC}"
    echo -e "Backup Agent: ${YELLOW}${BACKUP_FUNCTIONAL_TESTING_AGENT}${NC}"
    echo "Last Switched: ${LAST_SWITCHED}"
    echo "Switched By: ${SWITCHED_BY}"
    echo ""

    # Check van.md consistency
    local functional_refs=$(grep -c "@${ACTIVE_FUNCTIONAL_TESTING_AGENT}" "$VAN_FILE" || true)
    echo "Van.md References: ${functional_refs}"

    if [[ $functional_refs -ge 1 ]]; then
        echo -e "${GREEN}✓${NC} Routing configuration is consistent"
    else
        echo -e "${YELLOW}⚠${NC} Warning: Expected at least 1 reference, found ${functional_refs}"
    fi
}

# Function to create backup
create_backup() {
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    local backup_file="${BACKUP_DIR}/van_functional_${timestamp}.md.backup"

    echo -e "${BLUE}Creating backup...${NC}"
    cp "$VAN_FILE" "$backup_file"
    echo -e "${GREEN}✓${NC} Backup created: ${backup_file}"
}

# Function to switch to codex agent
switch_to_codex() {
    echo -e "${BLUE}Switching to Codex Functional Testing Agent...${NC}"

    # Create backup first
    create_backup

    # Update van.md - replace claude agent with codex agent in routing contexts
    sed -i "s/@${CLAUDE_AGENT}/@${CODEX_AGENT}/g" "$VAN_FILE"

    # Update config file
    cat > "$CONFIG_FILE" << EOF
# Functional Testing Agent Configuration
# This file tracks which functional testing agent is actively used in the collective routing

ACTIVE_FUNCTIONAL_TESTING_AGENT="${CODEX_AGENT}"
BACKUP_FUNCTIONAL_TESTING_AGENT="${CLAUDE_AGENT}"
LAST_SWITCHED="$(date +"%Y-%m-%d")"
SWITCHED_BY="switch-functional-testing-agent.sh"

# Agent Descriptions
# Active: GPT-5-Codex powered real browser testing with Playwright validation and intelligent test execution
# Backup: Claude-based real browser testing with Playwright (legacy fallback option)
EOF

    echo -e "${GREEN}✓${NC} Successfully switched to ${CODEX_AGENT}"
    echo ""
    validate_switch
}

# Function to switch to claude agent
switch_to_claude() {
    echo -e "${BLUE}Switching to Claude Functional Testing Agent...${NC}"

    # Create backup first
    create_backup

    # Update van.md - replace codex agent with claude agent in routing contexts
    sed -i "s/@${CODEX_AGENT}/@${CLAUDE_AGENT}/g" "$VAN_FILE"

    # Update config file
    cat > "$CONFIG_FILE" << EOF
# Functional Testing Agent Configuration
# This file tracks which functional testing agent is actively used in the collective routing

ACTIVE_FUNCTIONAL_TESTING_AGENT="${CLAUDE_AGENT}"
BACKUP_FUNCTIONAL_TESTING_AGENT="${CODEX_AGENT}"
LAST_SWITCHED="$(date +"%Y-%m-%d")"
SWITCHED_BY="switch-functional-testing-agent.sh"

# Agent Descriptions
# Active: Claude-based real browser testing with Playwright (fallback mode)
# Backup: GPT-5-Codex powered real browser testing with Playwright validation
EOF

    echo -e "${GREEN}✓${NC} Successfully switched to ${CLAUDE_AGENT}"
    echo ""
    validate_switch
}

# Function to validate the switch
validate_switch() {
    echo -e "${BLUE}Validating configuration...${NC}"

    source "$CONFIG_FILE"

    # Check if van.md has the correct references
    local active_refs=$(grep -c "@${ACTIVE_FUNCTIONAL_TESTING_AGENT}" "$VAN_FILE" || true)

    if [[ $active_refs -ge 1 ]]; then
        echo -e "${GREEN}✓${NC} Van.md updated correctly (${active_refs} references)"
    else
        echo -e "${RED}✗${NC} Warning: Only ${active_refs} references found, expected at least 1"
    fi

    echo -e "${GREEN}✓${NC} Configuration file updated"
    echo ""
    show_status
}

# Main command handler
case "${1:-}" in
    codex)
        switch_to_codex
        ;;
    claude)
        switch_to_claude
        ;;
    status)
        show_status
        ;;
    *)
        echo "Usage: $0 {codex|claude|status}"
        echo ""
        echo "Commands:"
        echo "  codex   - Switch to Codex functional testing agent (GPT-5-Codex)"
        echo "  claude  - Switch to Claude functional testing agent (legacy)"
        echo "  status  - Show current active agent configuration"
        echo ""
        echo "Examples:"
        echo "  $0 codex    # Switch to Codex agent"
        echo "  $0 claude   # Switch to Claude agent"
        echo "  $0 status   # Check current configuration"
        exit 1
        ;;
esac
