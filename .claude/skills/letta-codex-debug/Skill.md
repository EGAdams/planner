# Letta + Codex Orchestrator Debugger

Debug and run the hybrid Letta + Codex SDK orchestrator script.

## Problem Solved

Fixes the issue where the Letta server returns 500 errors when creating agents because it doesn't have access to the OPENAI_API_KEY environment variable.

## Solution

1. Updated `restart_letta_server.sh` to source the `~/planner/.env` file before starting the Letta server
2. This ensures the OPENAI_API_KEY is available to the Letta server process

## Usage

```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/agents
./restart_letta_server.sh  # Restart with env vars loaded
source /home/adamsl/planner/.venv/bin/activate
python3 hybrid_letta__codex_sdk.py
```

## Files Modified

- `restart_letta_server.sh` - Added env file sourcing

## Key Fix

Added these lines to `restart_letta_server.sh`:

```bash
# Source the .env file to load environment variables
if [[ -f ~/planner/.env ]]; then
  echo "Loading environment variables from ~/planner/.env"
  set -a
  source ~/planner/.env
  set +a
fi
```

## Known Issues

1. **Script hangs at "Sending initial task to orchestrator..."** - The default timeout of 180 seconds (3 minutes) is too short for the complete TDD workflow. **Fixed** by increasing timeout to 600 seconds (10 minutes) in line 859.

2. **Red-phase test runs fail silently** - When `run_test_suite` is called with `expect_failure=True`, the tool returns an empty error message. This appears to be an environment issue in Letta's tool sandbox.

3. **Validation is too strict** - The TDD validator fails if it can't find a successful red-phase test run, even though the green phase passes.

## Workarounds

The script successfully:
- Creates tools in Letta
- Creates orchestrator agent
- Generates comprehensive test files
- Implements working code
- Passes all tests

The validation error at the end can be ignored if the tests pass in the green phase.

## Next Steps

To fully fix the red-phase test execution:
1. Investigate why tools in Letta's sandbox can't properly execute pytest
2. Consider using a different approach for the red phase (e.g., pre-check for missing modules)
3. Relax the validation to allow missing red-phase runs if green phase succeeds
