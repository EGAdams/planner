# Claude Code Scripts

Diagnostic and utility scripts for the Claude Code collective system.

## Agent Registration Health Check

**Script**: `check-agent-registration.sh`

**Purpose**: Validates that all agent files in `.claude/agents/` are properly registered in the `.claude-collective/agents.md` registry.

### Usage

```bash
# Run from project root
./.claude/scripts/check-agent-registration.sh

# Or from anywhere
/home/adamsl/codex_test_agent/.claude/scripts/check-agent-registration.sh
```

### What It Checks

1. **Agent File Discovery**: Finds all `.md` files in `.claude/agents/`
2. **Frontmatter Validation**: Extracts and validates `name:` field
3. **Name Consistency**: Ensures filename matches frontmatter name
4. **Registration Status**: Checks if agent is listed in `agents.md`
5. **File Permissions**: Validates files are readable
6. **Registry Validation**: Verifies all registry entries have corresponding files

### Output

```
=========================================
Agent Registration Health Check
=========================================

Project Root: /home/adamsl/codex_test_agent
Agents Directory: /home/adamsl/codex_test_agent/.claude/agents
Registry File: /home/adamsl/codex_test_agent/.claude-collective/agents.md

=========================================
Agent Files Found:
=========================================

File: functional-testing-agent.md
  Name: functional-testing-agent
  Status: REGISTERED in agents.md

[... more agents ...]

=========================================
Summary:
=========================================
Total agent files: 32
Unregistered agents: 0
Registration issues: 0

=========================================
RESULT: ALL AGENTS PROPERLY REGISTERED
=========================================
```

### Exit Codes

- `0`: All agents properly registered
- `1`: Registration problems found (see output for details)

### When to Run

Run this script when:

- Adding new agent files
- Modifying agent frontmatter
- Troubleshooting "Agent type not found" errors
- Validating agent registry after changes
- Performing system health checks

### Common Issues Detected

1. **Unregistered Agent**:
   - Agent file exists but not in `agents.md`
   - Fix: Add `@agent-name` entry to `.claude-collective/agents.md`

2. **Name Mismatch**:
   - Filename doesn't match frontmatter `name:` field
   - Fix: Update frontmatter or rename file

3. **Missing Frontmatter**:
   - Agent file has no `name:` field
   - Fix: Add proper YAML frontmatter with `name:` field

4. **Registry Ghost**:
   - Entry in `agents.md` but no corresponding file
   - Fix: Remove registry entry or create missing file

### Example Fix Workflow

```bash
# 1. Run diagnostic
./.claude/scripts/check-agent-registration.sh

# 2. See issue: "codex-new-agent - NOT REGISTERED"

# 3. Edit registry
vim ./.claude-collective/agents.md

# 4. Add entry:
# - **@codex-new-agent** - Description here

# 5. Validate fix
./.claude/scripts/check-agent-registration.sh

# 6. Should show: "RESULT: ALL AGENTS PROPERLY REGISTERED"
```

---

## Future Scripts

Additional diagnostic and utility scripts will be added here as needed for collective system maintenance and validation.
