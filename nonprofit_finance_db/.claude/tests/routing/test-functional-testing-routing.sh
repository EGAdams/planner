#!/bin/bash
# Test suite for functional testing agent routing verification
# TDD approach - defines expected behavior before implementation

# Don't exit on error - we want to run all tests
set +e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# File paths
PROJECT_ROOT="/home/adamsl/planner/nonprofit_finance_db"
VAN_FILE="${PROJECT_ROOT}/.claude/commands/van.md"
AGENTS_FILE="${PROJECT_ROOT}/.claude-collective/agents.md"
CONFIG_FILE="${PROJECT_ROOT}/.claude/config/functional-testing-agent.conf"
LEGACY_AGENT_FILE="${PROJECT_ROOT}/.claude/agents/functional-testing-agent.md"
CODEX_AGENT_FILE="${PROJECT_ROOT}/.claude/agents/codex-functional-testing-agent.md"
SWITCHER_SCRIPT="${PROJECT_ROOT}/.claude/scripts/switch-functional-testing-agent.sh"
STATUS_SCRIPT="${PROJECT_ROOT}/.claude/scripts/show-functional-testing-status.sh"
BACKUP_DIR="${PROJECT_ROOT}/.claude/config/backups"

# Expected values
EXPECTED_ACTIVE_AGENT="codex-functional-testing-agent"
EXPECTED_BACKUP_AGENT="functional-testing-agent"

echo "========================================="
echo "Functional Testing Agent Routing Verification"
echo "========================================="
echo ""

# Helper functions
pass_test() {
    echo -e "${GREEN}✓${NC} $1"
    ((TESTS_PASSED++))
    ((TESTS_RUN++))
}

fail_test() {
    echo -e "${RED}✗${NC} $1"
    echo -e "  ${RED}Error: $2${NC}"
    ((TESTS_FAILED++))
    ((TESTS_RUN++))
}

# Test 1: Verify config file exists and is valid
test_config_file_exists() {
    if [[ -f "$CONFIG_FILE" && -r "$CONFIG_FILE" ]]; then
        pass_test "Configuration file exists and is readable"
        return 0
    else
        fail_test "Configuration file exists and is readable" "File not found or not readable"
        return 1
    fi
}

# Test 2: Verify active agent is codex-functional-testing-agent
test_config_active_agent() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        fail_test "Config specifies active agent" "Config file not found"
        return 1
    fi

    local active_agent=$(grep "ACTIVE_FUNCTIONAL_TESTING_AGENT=" "$CONFIG_FILE" | cut -d'=' -f2 | tr -d '"')

    if [[ "$active_agent" == "$EXPECTED_ACTIVE_AGENT" ]]; then
        pass_test "Config specifies active agent: $active_agent"
        return 0
    else
        fail_test "Config specifies active agent" "Expected '$EXPECTED_ACTIVE_AGENT', got '$active_agent'"
        return 1
    fi
}

# Test 3: Verify van.md has no legacy agent routing conflicts
test_van_routing_patterns() {
    if [[ ! -f "$VAN_FILE" ]]; then
        fail_test "Van.md has no routing conflicts" "Van.md not found"
        return 1
    fi

    # Check for any legacy agent references in routing contexts
    local legacy_routing=$(grep -E "browser|playwright|e2e|end-to-end" "$VAN_FILE" | grep -c "@${EXPECTED_BACKUP_AGENT}" || true)

    # Should have NO references to legacy agent in functional testing contexts
    if [[ $legacy_routing -eq 0 ]]; then
        pass_test "Van.md has no legacy agent routing conflicts"
        return 0
    else
        fail_test "Van.md has routing conflicts" "Found $legacy_routing references to legacy agent in routing"
        return 1
    fi
}

# Test 4: Verify agents.md has PRIMARY tag for Codex agent
test_agents_primary_tag() {
    if [[ ! -f "$AGENTS_FILE" ]]; then
        fail_test "Agents.md has PRIMARY tag" "Agents.md not found"
        return 1
    fi

    local has_primary=$(grep "@${EXPECTED_ACTIVE_AGENT}" "$AGENTS_FILE" | grep -c "PRIMARY" || true)

    if [[ $has_primary -gt 0 ]]; then
        pass_test "Agents.md has [PRIMARY] tag for Codex agent"
        return 0
    else
        fail_test "Agents.md has PRIMARY tag" "PRIMARY tag not found for $EXPECTED_ACTIVE_AGENT"
        return 1
    fi
}

# Test 5: Verify agents.md has LEGACY tag for Claude agent
test_agents_legacy_tag() {
    if [[ ! -f "$AGENTS_FILE" ]]; then
        fail_test "Agents.md has LEGACY tag" "Agents.md not found"
        return 1
    fi

    local has_legacy=$(grep "@${EXPECTED_BACKUP_AGENT}" "$AGENTS_FILE" | grep -c "LEGACY" || true)

    if [[ $has_legacy -gt 0 ]]; then
        pass_test "Agents.md has [LEGACY] tag for Claude agent"
        return 0
    else
        fail_test "Agents.md has LEGACY tag" "LEGACY tag not found for $EXPECTED_BACKUP_AGENT"
        return 1
    fi
}

# Test 6: Verify legacy agent has deprecation notice
test_legacy_deprecation_notice() {
    if [[ ! -f "$LEGACY_AGENT_FILE" ]]; then
        fail_test "Legacy agent has deprecation notice" "Legacy agent file not found"
        return 1
    fi

    if grep -q "DEPRECATION NOTICE" "$LEGACY_AGENT_FILE"; then
        pass_test "Legacy agent has deprecation notice"
        return 0
    else
        fail_test "Legacy agent has deprecation notice" "DEPRECATION NOTICE section not found"
        return 1
    fi
}

# Test 7: Verify switcher script exists and is executable
test_switcher_script_exists() {
    if [[ -f "$SWITCHER_SCRIPT" && -x "$SWITCHER_SCRIPT" ]]; then
        pass_test "Switcher script exists and is executable"
        return 0
    else
        fail_test "Switcher script exists and is executable" "Script not found or not executable"
        return 1
    fi
}

# Test 8: Verify status script exists and is executable
test_status_script_exists() {
    if [[ -f "$STATUS_SCRIPT" && -x "$STATUS_SCRIPT" ]]; then
        pass_test "Status script exists and is executable"
        return 0
    else
        fail_test "Status script exists and is executable" "Script not found or not executable"
        return 1
    fi
}

# Test 9: Verify backup directory exists
test_backup_directory_exists() {
    if [[ -d "$BACKUP_DIR" ]]; then
        pass_test "Backup directory exists"
        return 0
    else
        fail_test "Backup directory exists" "Directory not found at $BACKUP_DIR"
        return 1
    fi
}

# Test 10: Verify configuration consistency
test_configuration_consistency() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        fail_test "Configuration is consistent" "Config file not found"
        return 1
    fi

    source "$CONFIG_FILE"

    # Check if active agent in config matches expected
    if [[ "$ACTIVE_FUNCTIONAL_TESTING_AGENT" == "$EXPECTED_ACTIVE_AGENT" ]]; then
        pass_test "Configuration is consistent across files"
        return 0
    else
        fail_test "Configuration is consistent" "Config active agent mismatch"
        return 1
    fi
}

# Test 11: Verify Codex agent has Playwright tools preserved
test_codex_agent_playwright_tools() {
    if [[ ! -f "$CODEX_AGENT_FILE" ]]; then
        fail_test "Codex agent has Playwright tools" "Codex agent file not found"
        return 1
    fi

    # Check for key Playwright tools in frontmatter
    if grep -q "mcp__playwright__" "$CODEX_AGENT_FILE"; then
        pass_test "Codex agent preserves Playwright tool access"
        return 0
    else
        fail_test "Codex agent has Playwright tools" "Playwright tools not found in agent definition"
        return 1
    fi
}

# Test 12: Verify all routing contexts are consistent
test_all_routing_contexts_consistent() {
    if [[ ! -f "$VAN_FILE" || ! -f "$AGENTS_FILE" || ! -f "$CONFIG_FILE" ]]; then
        fail_test "All routing contexts consistent" "Required files not found"
        return 1
    fi

    # Check no mixed references to legacy agent in routing
    local mixed_refs=$(grep -E "browser.*@${EXPECTED_BACKUP_AGENT}|playwright.*@${EXPECTED_BACKUP_AGENT}|functional.*@${EXPECTED_BACKUP_AGENT}" "$VAN_FILE" | grep -v "Available" | wc -l)

    if [[ $mixed_refs -eq 0 ]]; then
        pass_test "All routing contexts use consistent agent references"
        return 0
    else
        fail_test "All routing contexts consistent" "Found $mixed_refs references to legacy agent in routing"
        return 1
    fi
}

# Run all tests
echo "Running tests..."
echo ""

test_config_file_exists
test_config_active_agent
test_van_routing_patterns
test_agents_primary_tag
test_agents_legacy_tag
test_legacy_deprecation_notice
test_switcher_script_exists
test_status_script_exists
test_backup_directory_exists
test_configuration_consistency
test_codex_agent_playwright_tools
test_all_routing_contexts_consistent

# Summary
echo ""
echo "========================================="
echo "Test Summary"
echo "========================================="
echo -e "Tests run:    $TESTS_RUN"
echo -e "${GREEN}Tests passed: $TESTS_PASSED${NC}"
if [[ $TESTS_FAILED -gt 0 ]]; then
    echo -e "${RED}Tests failed: $TESTS_FAILED${NC}"
else
    echo -e "Tests failed: $TESTS_FAILED"
fi
echo ""

if [[ $TESTS_FAILED -eq 0 ]]; then
    echo -e "${GREEN}All functional testing routing tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Please review the errors above.${NC}"
    exit 1
fi
