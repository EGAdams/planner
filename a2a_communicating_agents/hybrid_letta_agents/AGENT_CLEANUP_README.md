# Agent_66 Cleanup Scripts

## Overview

These scripts help clean up duplicate Agent_66 instances while safely preserving the correct one with your project memory and capabilities.

## Scripts

### 1. `preview_agent_cleanup.sh` (DRY RUN - SAFE)

**Purpose**: Preview what would be deleted WITHOUT making any changes.

**Usage**:
```bash
./preview_agent_cleanup.sh
```

**What it does**:
- Lists all Agent_66* instances
- Shows which one will be KEPT
- Shows which ones will be DELETED
- Makes NO changes to the database

**When to use**: Always run this FIRST to see what will happen.

### 2. `cleanup_duplicate_agents.sh` (DESTRUCTIVE - REQUIRES CONFIRMATION)

**Purpose**: Actually delete duplicate Agent_66 instances.

**Usage**:
```bash
./cleanup_duplicate_agents.sh
```

**What it does**:
1. Shows preview of agents to delete
2. **Asks for confirmation** (type 'DELETE' to proceed)
3. Deletes all Agent_66* agents EXCEPT the correct one
4. Logs all operations to `/tmp/agent_cleanup_*.log`
5. Verifies the correct agent still exists

**Safety Features**:
- ✅ Protected agent ID hardcoded (cannot delete by mistake)
- ✅ Requires explicit "DELETE" confirmation
- ✅ Logs every operation
- ✅ Shows progress for each deletion
- ✅ Verifies correct agent after cleanup

## The Protected Agent

**ID**: `agent-4dfca708-49a8-4982-8e36-0f1146f9a66e`

**Name**: Agent_66

**Description**: Remembers the status for all kinds of projects that we are working on. Has the ability to search the web and delegate tasks to a Coder Agent.

**This agent will NEVER be deleted** by the cleanup scripts.

## Workflow

### Step 1: Preview (Recommended)

```bash
./preview_agent_cleanup.sh
```

Review the output carefully:
- Check that the correct Agent_66 is in the "KEEP" section
- Review the list of agents to be deleted
- Confirm the count makes sense

### Step 2: Cleanup (If satisfied with preview)

```bash
./cleanup_duplicate_agents.sh
```

When prompted, type `DELETE` and press Enter to confirm.

**Any other input will cancel the operation.**

### Step 3: Verify

After cleanup, verify the configuration:

```bash
./verify_agent_fix.py
```

Expected output:
```
✅ CONFIGURATION CORRECT!
   The voice agent will use the CORRECT Agent_66
```

## Example Output

### Preview (Dry Run)

```
========================================
  Agent_66 Cleanup Preview (DRY RUN)
========================================

📋 Fetching all agents...

📊 SUMMARY
  Total Agent_66* instances: 128
  Will keep: 1 agent
  Will delete: 127 agents

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AGENT TO KEEP:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✓ Name: Agent_66
  ID: agent-4dfca708-49a8-4982-8e36-0f1146f9a66e
  Description: Remembers project status, web search, coder delegation

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
AGENTS TO DELETE (127 total):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. ✗ Agent_66-sleeptime
     ID: agent-57d00931-cd5a-4e91-afd6-c8ee5ce62503

2. ✗ Agent_66
     ID: agent-71d8962d-d31c-4d86-83f5-92791ada21bd
...
```

### Actual Cleanup

```
========================================
  Agent_66 Cleanup Script
========================================

📋 Fetching all agents...

✅ Found 128 Agent_66* instances
✅ Keeping: 1 agent (ID: agent-4dfca708-49a8-4982-8e36-0f1146f9a66e)
🗑️  Will delete: 127 duplicate agents

Preview of agents to delete (first 10):
  ✗ Agent_66-sleeptime (agent-57d00931-cd5a-4e91-afd6-c8ee5ce62503)
  ✗ Agent_66 (agent-71d8962d-d31c-4d86-83f5-92791ada21bd)
  ...

Agent to KEEP:
  ✓ Agent_66 (agent-4dfca708-49a8-4982-8e36-0f1146f9a66e)
    Description: Remembers project status, web search, coder delegation

⚠️  WARNING: This will permanently delete 127 agents!
Type 'DELETE' to confirm (or anything else to cancel): DELETE

🗑️  Starting deletion process...
Log file: /tmp/agent_cleanup_20251228_135500.log

Deleting: Agent_66-sleeptime (agent-57d00931-cd5a-4e91-afd6-c8ee5ce62503)... ✓ Deleted
Deleting: Agent_66 (agent-71d8962d-d31c-4d86-83f5-92791ada21bd)... ✓ Deleted
...

========================================
  Cleanup Complete
========================================

✅ Deleted:  127 agents
✗ Failed:   0 agents
⊘ Skipped:  0 agents

✅ Kept:     1 agent (agent-4dfca708-49a8-4982-8e36-0f1146f9a66e)

Full log: /tmp/agent_cleanup_20251228_135500.log

🔍 Verifying correct agent still exists...
✅ VERIFIED: Correct Agent_66 is still active!

Run ./verify_agent_fix.py to confirm configuration.
```

## What Gets Deleted?

The script deletes ALL agents where:
- Name starts with "Agent_66" (including Agent_66-sleeptime variants)
- ID is NOT `agent-4dfca708-49a8-4982-8e36-0f1146f9a66e`

## What NEVER Gets Deleted?

- The correct Agent_66 (agent-4dfca708-49a8-4982-8e36-0f1146f9a66e)
- Any agents with different names (e.g., "Alice", "JoslynDBAdmin", etc.)

## Logs

Cleanup logs are saved to: `/tmp/agent_cleanup_YYYYMMDD_HHMMSS.log`

Log format:
```
SUCCESS: Deleted Agent_66-sleeptime (agent-57d00931-cd5a-4e91-afd6-c8ee5ce62503)
SUCCESS: Deleted Agent_66 (agent-71d8962d-d31c-4d86-83f5-92791ada21bd)
FAILED: Agent_66 (agent-abc123) - HTTP 404
```

## Troubleshooting

### Script says "No duplicates found"

This means you only have 1 Agent_66 instance. No cleanup needed!

### Some deletions failed

Check the log file for details:
```bash
cat /tmp/agent_cleanup_*.log | grep FAILED
```

Common reasons:
- Agent already deleted in another process
- Network timeout
- Letta server not responding

### Accidentally deleted the wrong agent

If the correct agent was somehow deleted:

1. Check if there's a backup:
   ```bash
   ./list_agents.py | grep "project"
   ```

2. If found, update `.env` with the new ID:
   ```bash
   VOICE_PRIMARY_AGENT_ID=<new-agent-id>
   ```

3. Restart the voice system:
   ```bash
   ./restart_voice_system.sh
   ```

## Benefits of Cleanup

After running the cleanup:

1. **Faster agent searches** - Less database overhead
2. **Clear agent list** - Easier to manage in Letta UI
3. **No confusion** - Only one Agent_66 exists
4. **Improved performance** - Reduced Letta database size

## When to Run

- ✅ After confirming the correct agent is configured
- ✅ When you have many duplicate Agent_66 instances
- ✅ Before archiving/backing up the Letta database
- ❌ During active voice sessions (wait until idle)
- ❌ If you're unsure which agent to keep (verify first)

## Safety Checklist

Before running the cleanup script:

- [ ] Run `./verify_agent_fix.py` - confirms correct agent configured
- [ ] Run `./preview_agent_cleanup.sh` - review what will be deleted
- [ ] Verify correct agent ID: `agent-4dfca708-49a8-4982-8e36-0f1146f9a66e`
- [ ] Stop voice system (optional, but recommended): `./stop_voice_system.sh`
- [ ] Backup Letta database (optional): `pg_dump letta > letta_backup.sql`

---

**Created**: 2025-12-28
**Purpose**: Cleanup duplicate Agent_66 instances safely
**Protected Agent**: agent-4dfca708-49a8-4982-8e36-0f1146f9a66e
