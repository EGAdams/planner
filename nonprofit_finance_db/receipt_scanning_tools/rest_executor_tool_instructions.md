# rest_executor Tool Instructions

This document explains how Letta agents should safely and correctly use the **`rest_executor`** tool to run commands and modify files on the code machine.

---

## What the Tool Does

`rest_executor` allows a Letta agent to:
- Execute shell commands **inside a locked workspace directory**
- Create or modify files within that workspace
- Run tests and simple scripts

The tool is backed by a secured executor server and **cannot access files outside the allowed workspace**.

---

## Workspace Scope (Hard Rule)

- **Workspace root:**
  ```
  /home/adamsl/planner/nonprofit_finance_db/receipt_scanning_tools
  ```
- All commands run relative to this directory.
- The agent **must not** attempt to reference paths outside this workspace.

---

## Allowed Commands

The executor only allows the following command binaries:

- `python`
- `python3`
- `pytest`
- `git`
- `node`
- `npm`

Any other command will be rejected.

---

## Tool Interface

### Function Name

```
rest_executor
```

### Parameters

| Name | Type | Required | Description |
|----|----|----|----|
| `command` | string | yes | The exact command to run |
| `cwd` | string | no | Working directory (use `"."`) |
| `timeout_sec` | integer | no | Timeout in seconds (default: 60) |

---

## Required Usage Rules (Agents MUST Follow)

1. **Always call the tool explicitly** when executing code or changing files
2. **Always use**:
   ```
   cwd = "."
   ```
3. Never assume files exist — verify via commands
4. Never attempt privileged or destructive operations
5. Prefer small, incremental changes

---

## Safe Command Examples

### Check repository status

```json
{
  "command": "git status",
  "cwd": "."
}
```

### Run a Python one-liner

```json
{
  "command": "python3 -c \"print('hello')\"",
  "cwd": "."
}
```

### Create or overwrite a file

```json
{
  "command": "python3 -c \"open('example.txt','w').write('ok\\n')\"",
  "cwd": "."
}
```

### Run tests

```json
{
  "command": "pytest",
  "cwd": "."
}
```

---

## Expected Output

The tool returns a JSON object:

```json
{
  "returncode": 0,
  "stdout": "...",
  "stderr": "",
  "cwd_resolved": "/home/adamsl/planner/nonprofit_finance_db/receipt_scanning_tools"
}
```

- `returncode == 0` means success
- Non‑zero return codes must be reported and analyzed

---

## Error Handling Guidance

If the tool returns an error:
- Read the `stderr` and `detail` fields carefully
- Do **not** retry blindly
- Adjust the command or explain the failure

---

## Security Model (Important)

- The executor **requires authentication** (handled automatically)
- The agent has **no network access** beyond this tool
- The agent cannot escape the workspace or run unapproved commands

---

## Agent Instruction Snippet (Recommended)

Include this in agent system prompts:

> When you need to run commands or modify files, call the `rest_executor` tool.
> Always use `cwd="."`.
> Make minimal, safe changes.
> Run tests after changes and report results.

---

## Summary

- `rest_executor` is the **only** way agents may execute code
- Workspace and command set are strictly limited
- Proper usage is required for safety and correctness

**The tool is production‑ready when used according to this document.**

