# Agent Priority Configuration & Switching Guide

## Overview

This system provides easy switching between testing agent implementations with full routing consistency validation.

## Current Configuration

- **Primary Agent**: `codex-test-implementation-agent` (GPT-5-Codex powered)
- **Legacy Agent**: `testing-implementation-agent` (Claude-based fallback)

## Quick Reference Commands

### Check Current Status

```bash
# Quick status check
./.claude/scripts/switch-testing-agent.sh status

# Detailed routing report
./.claude/scripts/show-routing-status.sh

# Full test validation
./.claude/tests/routing/test-agent-routing.sh
```

### Switch Agents

```bash
# Switch to Codex testing agent (recommended)
./.claude/scripts/switch-testing-agent.sh codex

# Switch to Claude testing agent (legacy fallback)
./.claude/scripts/switch-testing-agent.sh claude
```

## What Gets Updated

When you switch agents, the system automatically updates:

1. **Van.md Routing** (`.claude/commands/van.md`)
   - IMMEDIATE ROUTING table
   - COMPLEX REQUEST ANALYSIS table
   - SMART ROUTING DECISION TREE

2. **Configuration File** (`.claude/config/testing-agent.conf`)
   - Active agent setting
   - Backup agent setting
   - Switch timestamp and metadata

3. **Backup Files** (`.claude/config/backups/`)
   - Timestamped backup created before each switch
   - Allows rollback if needed

## Agent Comparison

### Codex Testing Agent [PRIMARY]

**Advantages:**
- GPT-5-Codex powered advanced code analysis
- Intelligent test generation and pattern recognition
- Superior error detection capabilities
- Enhanced test quality through Codex-powered understanding

**Use For:**
- New testing work
- Complex test scenarios
- Advanced pattern recognition needs
- Production-grade test suites

### Claude Testing Agent [LEGACY]

**Advantages:**
- Proven Claude-based test generation
- Compatible with existing workflows
- Reliable fallback option

**Use For:**
- Compatibility with existing systems
- Fallback when Codex is unavailable
- Legacy project maintenance

## Testing & Validation

### Automated Test Suite

The system includes comprehensive tests to validate routing consistency:

```bash
# Run full test suite
./.claude/tests/routing/test-agent-routing.sh
```

**Test Coverage:**
- Configuration file existence and correctness
- Van.md routing table consistency (3 locations)
- Agents.md priority tags ([PRIMARY] and [LEGACY])
- Legacy agent deprecation notice
- Switcher script functionality
- Routing pattern consistency
- No mixed agent references

**Expected Output:**
```
=========================================
Testing Agent Routing Verification
=========================================
✓ Van.md file exists and is readable
✓ Agents.md file exists and is readable
✓ Configuration file exists and is readable
✓ Config file specifies active agent: codex-test-implementation-agent
✓ Van.md IMMEDIATE ROUTING table uses codex-test-implementation-agent
✓ Van.md COMPLEX REQUEST table uses codex-test-implementation-agent
✓ Van.md DECISION TREE uses codex-test-implementation-agent
✓ Agents.md has [PRIMARY] and [LEGACY] tags
✓ Legacy agent has deprecation notice
✓ Switcher script exists and is executable
✓ Routing patterns consistent: 3 references to active agent
✓ No mixed agent references in routing tables

Tests run:    12
Tests passed: 12
Tests failed: 0

All routing tests passed!
```

### Visual Status Report

Get a detailed visual report of current configuration:

```bash
./.claude/scripts/show-routing-status.sh
```

**Example Output:**
```
╔════════════════════════════════════════════╗
║   Testing Agent Routing Status Report     ║
╔════════════════════════════════════════════╗

1. Active Agent Configuration
   ─────────────────────────────
   Active:  codex-test-implementation-agent
   Backup:  testing-implementation-agent
   Updated: 2025-11-04

2. Van.md Routing Patterns
   ─────────────────────────────
   ✓ IMMEDIATE ROUTING table: @codex-test-implementation-agent
   ✓ COMPLEX REQUEST table: @codex-test-implementation-agent
   ✓ DECISION TREE: @codex-test-implementation-agent
   ℹ  Total references: 3

3. Agent Catalog Status
   ─────────────────────────────
   ✓ codex-test-implementation-agent: [PRIMARY]
   ✓ testing-implementation-agent: [LEGACY]

4. Configuration Consistency
   ─────────────────────────────
   ✓ Config matches van.md routing
   ✓ No mixed agent references
   ✓ Sufficient routing coverage (3 ≥ 3)

5. Summary
   ─────────────────────────────
   ✓ All checks passed
   ✓ Routing configuration is consistent

╚════════════════════════════════════════════╝
```

## File Structure

```
.claude/
├── config/
│   ├── testing-agent.conf          # Active agent configuration
│   └── backups/                    # Timestamped backup files
│       ├── van_20251104_070148.md.backup
│       └── van_20251104_070159.md.backup
├── scripts/
│   ├── switch-testing-agent.sh     # Agent switching utility
│   └── show-routing-status.sh      # Visual status report
├── tests/
│   └── routing/
│       └── test-agent-routing.sh   # Automated test suite
├── commands/
│   └── van.md                      # Routing configuration (updated by switcher)
└── agents/
    ├── codex-test-implementation-agent.md
    └── testing-implementation-agent.md

.claude-collective/
└── agents.md                       # Agent catalog with priority tags
```

## Rollback & Recovery

### Manual Rollback

If you need to rollback a switch:

```bash
# Find backup files
ls -lah ./.claude/config/backups/

# Copy backup to restore
cp ./.claude/config/backups/van_TIMESTAMP.md.backup ./.claude/commands/van.md

# Update config file to match
# Edit ./.claude/config/testing-agent.conf

# Verify with test suite
./.claude/tests/routing/test-agent-routing.sh
```

### Automated Recovery

The switcher script creates backups automatically, so you can:

1. Note the timestamp before switching
2. If issues occur, locate backup: `.claude/config/backups/van_TIMESTAMP.md.backup`
3. Restore the backup file
4. Run tests to verify

## Best Practices

1. **Always run tests after switching**: Verify consistency with the test suite
2. **Check status before manual edits**: Use status script to understand current state
3. **Keep backups**: Don't delete backup files, they're small and valuable
4. **Use Codex by default**: Only switch to Claude for specific compatibility needs
5. **Validate after manual changes**: Run test suite if you manually edit van.md

## Troubleshooting

### Tests Failing After Switch

```bash
# Check current configuration
./.claude/scripts/switch-testing-agent.sh status

# View detailed status
./.claude/scripts/show-routing-status.sh

# Re-run the switch to ensure completion
./.claude/scripts/switch-testing-agent.sh codex

# Verify tests pass
./.claude/tests/routing/test-agent-routing.sh
```

### Mixed Agent References

If tests report mixed agent references:

```bash
# Check which agent is in routing
grep "@.*test.*-agent" ./.claude/commands/van.md

# Force switch to desired agent
./.claude/scripts/switch-testing-agent.sh codex

# Verify consistency
./.claude/tests/routing/test-agent-routing.sh
```

### Configuration Mismatch

If config file and routing don't match:

```bash
# Check current active agent in config
cat ./.claude/config/testing-agent.conf

# Check routing references
grep -c "@codex-test-implementation-agent" ./.claude/commands/van.md

# Run switch to synchronize
./.claude/scripts/switch-testing-agent.sh codex
```

## Implementation Details

### TDD Approach

This system was built using Test-Driven Development:

1. **RED Phase**: Created comprehensive test suite defining expected behavior
2. **GREEN Phase**: Implemented configuration, scripts, and routing updates to pass tests
3. **REFACTOR Phase**: Enhanced with visual reports, backups, and user-friendly tools

### Test-First Development

All functionality was validated through tests before implementation:
- 12 comprehensive test cases covering all aspects
- Automated validation of routing consistency
- No manual verification needed

## Future Enhancements

Potential additions:
- Support for additional testing agent variants
- Automated rollback on test failures
- Integration with CI/CD pipelines
- Agent performance metrics tracking
- A/B testing between agents

## Support & Maintenance

For issues or questions:
1. Run the test suite: `./.claude/tests/routing/test-agent-routing.sh`
2. Check status report: `./.claude/scripts/show-routing-status.sh`
3. Review backup files: `./.claude/config/backups/`
4. Consult this guide for troubleshooting steps

---

**Last Updated**: 2025-11-04
**Version**: 1.0
**Maintainer**: Feature Implementation Agent (TDD)
