# Reset Agent Handoff Workflow

Reset the agent handoff system by cleaning up state files and logs.

## What This Does

Clears all handoff-related state files so you can start a fresh agent workflow:

- Removes `.gemini/handoff/NEXT_ACTION.json` (pending delegation context)
- Clears handoff logs in `/tmp/test-driven-handoff.log` 
- Resets any stuck delegation state
- Prepares for clean workflow restart

## Usage

```bash
# Remove handoff context files
rm -f .gemini/handoff/NEXT_ACTION.json

# Clear handoff logs  
> /tmp/test-driven-handoff.log

# Optional: Clear any other temp handoff files
rm -f .gemini/handoff/*.json
```

## When to Use

- **Stuck Handoffs**: When delegation gets stuck or loops
- **Fresh Start**: Before beginning new agent workflow  
- **Testing**: Between test runs to ensure clean state
- **Debugging**: When investigating handoff issues

## Files Cleaned

- `.gemini/handoff/NEXT_ACTION.json` - Current delegation context
- `/tmp/test-driven-handoff.log` - Hook execution logs
- `.gemini/handoff/*.json` - Any other handoff state files

## Safe Operation

This only removes temporary state files, never:
- Gemini TaskMaster data (`.gemini/tasks/`)
- Agent definitions (`.gemini/agents/`)
- Hook scripts (`.gemini/hooks/`)
- Project files or code

## Verification

After reset, verify clean state:
```bash
ls .gemini/handoff/     # Should be empty or not exist
tail /tmp/test-driven-handoff.log  # Should be empty
```

Quick one-liner for complete reset:
```bash
rm -f .gemini/handoff/*.json && > /tmp/test-driven-handoff.log && echo "Handoff workflow reset complete"
```