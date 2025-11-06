#!/bin/bash
# Test suite for testing agent routing verification
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
CONFIG_FILE="${PROJECT_ROOT}/.claude/config/testing-agent.conf"
LEGACY_AGENT_FILE="${PROJECT_ROOT}/.claude/agents/testing-implementation-agent.md"

# Expected values
EXPECTED_ACTIVE_AGENT="codex-test-implementation-agent"
EXPECTED_BACKUP_AGENT="testing-implementation-agent"

echo "========================================="
echo "Testing Agent Routing Verification"
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

# Test 1: Verify van.md exists and is readable
test_van_file_exists() {
    if [[ -f "$VAN_FILE" && -r "$VAN_FILE" ]]; then
        pass_test "Van.md file exists and is readable"
        return 0
    else
        fail_test "Van.md file exists and is readable" "File not found or not readable"
        return 1
    fi
}

# Test 2: Verify agents.md exists and is readable
test_agents_file_exists() {
    if [[ -f "$AGENTS_FILE" && -r "$AGENTS_FILE" ]]; then
        pass_test "Agents.md file exists and is readable"
        return 0
    else
        fail_test "Agents.md file exists and is readable" "File not found or not readable"
        return 1
    fi
}

# Test 3: Verify config file exists and is readable
test_config_file_exists() {
    if [[ -f "$CONFIG_FILE" && -r "$CONFIG_FILE" ]]; then
        pass_test "Configuration file exists and is readable"
        return 0
    else
        fail_test "Configuration file exists and is readable" "File not found or not readable"
        return 1
    fi
}

# Test 4: Verify active agent in configuration
test_config_active_agent() {
    if [[ ! -f "$CONFIG_FILE" ]]; then
        fail_test "Config file specifies active agent" "Config file not found"
        return 1
    fi

    local active_agent=$(grep "ACTIVE_TESTING_AGENT=" "$CONFIG_FILE" | cut -d'=' -f2 | tr -d '"')

    if [[ "$active_agent" == "$EXPECTED_ACTIVE_AGENT" ]]; then
        pass_test "Config file specifies active agent: $active_agent"
        return 0
    else
        fail_test "Config file specifies active agent" "Expected '$EXPECTED_ACTIVE_AGENT', got '$active_agent'"
        return 1
    fi
}

# Test 5: Verify van.md IMMEDIATE ROUTING table uses correct agent
test_van_immediate_routing() {
    if [[ ! -f "$VAN_FILE" ]]; then
        fail_test "Van.md IMMEDIATE ROUTING uses correct agent" "Van.md not found"
        return 1
    fi

    # Check the testing row in immediate routing table (agent name is on same line)
    local routing_line=$(grep '"test/validate X"' "$VAN_FILE")

    if echo "$routing_line" | grep -q "@${EXPECTED_ACTIVE_AGENT}"; then
        pass_test "Van.md IMMEDIATE ROUTING table uses $EXPECTED_ACTIVE_AGENT"
        return 0
    else
        fail_test "Van.md IMMEDIATE ROUTING table uses correct agent" "Does not reference $EXPECTED_ACTIVE_AGENT in testing row"
        return 1
    fi
}

# Test 6: Verify van.md COMPLEX REQUEST table uses correct agent
test_van_complex_routing() {
    if [[ ! -f "$VAN_FILE" ]]; then
        fail_test "Van.md COMPLEX REQUEST uses correct agent" "Van.md not found"
        return 1
    fi

    # Check the testing & quality row in complex request table (agent name is on same line)
    local routing_line=$(grep "🧪 Testing & Quality" "$VAN_FILE")

    if echo "$routing_line" | grep -q "@${EXPECTED_ACTIVE_AGENT}"; then
        pass_test "Van.md COMPLEX REQUEST table uses $EXPECTED_ACTIVE_AGENT"
        return 0
    else
        fail_test "Van.md COMPLEX REQUEST table uses correct agent" "Does not reference $EXPECTED_ACTIVE_AGENT in testing row"
        return 1
    fi
}

# Test 7: Verify van.md DECISION TREE uses correct agent
test_van_decision_tree() {
    if [[ ! -f "$VAN_FILE" ]]; then
        fail_test "Van.md DECISION TREE uses correct agent" "Van.md not found"
        return 1
    fi

    # Check the testing focus line in decision tree
    local routing_line=$(grep "Testing Focus?" "$VAN_FILE")

    if echo "$routing_line" | grep -q "@${EXPECTED_ACTIVE_AGENT}"; then
        pass_test "Van.md DECISION TREE uses $EXPECTED_ACTIVE_AGENT"
        return 0
    else
        fail_test "Van.md DECISION TREE uses correct agent" "Does not reference $EXPECTED_ACTIVE_AGENT in testing branch"
        return 1
    fi
}

# Test 8: Verify agents.md has priority tags
test_agents_priority_tags() {
    if [[ ! -f "$AGENTS_FILE" ]]; then
        fail_test "Agents.md has priority tags" "Agents.md not found"
        return 1
    fi

    local has_primary=$(grep "@${EXPECTED_ACTIVE_AGENT}" "$AGENTS_FILE" | grep -c "PRIMARY" || true)
    local has_legacy=$(grep "@${EXPECTED_BACKUP_AGENT}" "$AGENTS_FILE" | grep -c "LEGACY" || true)

    if [[ $has_primary -gt 0 && $has_legacy -gt 0 ]]; then
        pass_test "Agents.md has [PRIMARY] and [LEGACY] tags"
        return 0
    else
        fail_test "Agents.md has priority tags" "PRIMARY tag count: $has_primary, LEGACY tag count: $has_legacy (both should be > 0)"
        return 1
    fi
}

# Test 9: Verify legacy agent has deprecation notice
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

# Test 10: Verify switcher script exists and is executable
test_switcher_script_exists() {
    local switcher_script="${PROJECT_ROOT}/.claude/scripts/switch-testing-agent.sh"

    if [[ -f "$switcher_script" && -x "$switcher_script" ]]; then
        pass_test "Switcher script exists and is executable"
        return 0
    else
        fail_test "Switcher script exists and is executable" "Script not found or not executable"
        return 1
    fi
}

# Test 11: Count routing patterns consistency
test_routing_patterns_consistency() {
    if [[ ! -f "$VAN_FILE" ]]; then
        fail_test "Routing patterns are consistent" "Van.md not found"
        return 1
    fi

    # Count references to active agent in testing context (excluding examples and comments)
    local active_count=$(grep -v "^#" "$VAN_FILE" | grep -c "@${EXPECTED_ACTIVE_AGENT}" || true)

    # Should have at least 3 references (immediate, complex, decision tree)
    if [[ $active_count -ge 3 ]]; then
        pass_test "Routing patterns consistent: $active_count references to active agent"
        return 0
    else
        fail_test "Routing patterns are consistent" "Only found $active_count references, expected at least 3"
        return 1
    fi
}

# Test 12: Verify no mixed agent references in routing
test_no_mixed_routing() {
    if [[ ! -f "$VAN_FILE" ]]; then
        fail_test "No mixed agent references in routing" "Van.md not found"
        return 1
    fi

    # Check if legacy agent is still used in routing contexts (outside of catalog references)
    # Look for @testing-implementation-agent in routing tables but not in agent lists
    local mixed_refs=$(grep -E "test.*@${EXPECTED_BACKUP_AGENT}|Testing.*@${EXPECTED_BACKUP_AGENT}" "$VAN_FILE" | grep -v "Available" | wc -l)

    if [[ $mixed_refs -eq 0 ]]; then
        pass_test "No mixed agent references in routing tables"
        return 0
    else
        fail_test "No mixed agent references in routing" "Found $mixed_refs references to legacy agent in routing context"
        return 1
    fi
}

# Run all tests
echo "Running tests..."
echo ""

test_van_file_exists
test_agents_file_exists
test_config_file_exists
test_config_active_agent
test_van_immediate_routing
test_van_complex_routing
test_van_decision_tree
test_agents_priority_tags
test_legacy_deprecation_notice
test_switcher_script_exists
test_routing_patterns_consistency
test_no_mixed_routing

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
    echo -e "${GREEN}All routing tests passed!${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Please review the errors above.${NC}"
    exit 1
fi
