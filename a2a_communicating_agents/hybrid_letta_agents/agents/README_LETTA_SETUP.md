# Hybrid Letta Codex SDK - Setup Guide

## Problem Fixed

The original error `Error executing function run_test_suite: :` was caused by two issues:

1. **Letta server not running** - The script requires a running Letta server
2. **Missing OPENAI_API_KEY** - The Letta server needs this to validate models

## Solution Implemented

### 1. Improved Error Handling
Enhanced `run_test_suite()` in `hybrid_letta__codex_sdk.py`:
- Comprehensive try-catch blocks with detailed error messages
- Better subprocess error handling
- Timeout protection (300 seconds)
- Validates environment (sys.executable, working directory)

### 2. Letta Server Startup Script
Created `start_letta.sh` that:
- Loads environment variables from `.env` file
- Validates OPENAI_API_KEY is set
- Starts Letta server with proper configuration

## How to Use

### Prerequisites
```bash
# Install required packages
pip install letta-client
npm install -g @openai/codex

# Authenticate Codex CLI
codex login
# OR
codex auth --with-api-key

# Ensure OPENAI_API_KEY is set in your environment
export OPENAI_API_KEY="your-key-here"
# OR add it to a .env file in the project root
```

### Starting the Letta Server

**Option 1: Using the startup script (recommended)**
```bash
./start_letta.sh > /tmp/letta_server.log 2>&1 &
# Wait 10-15 seconds for server to fully start
sleep 15
```

**Option 2: Manual start**
```bash
# Ensure environment is loaded
source /path/to/.env  # if using .env file
letta server --port 8283 > /tmp/letta_server.log 2>&1 &
sleep 15
```

### Verify Server is Running
```bash
curl http://localhost:8283/
# Should return HTTP 200
```

### Run the Hybrid Letta Codex SDK
```bash
python3 hybrid_letta__codex_sdk.py
```

## Successful Workflow

When working correctly, you'll see:

1. ✅ Test Generation - Creates pytest tests from specification
2. ✅ Red Phase - Tests fail as expected (no implementation yet)
3. ✅ Code Generation - Codex generates the implementation
4. ✅ Green Phase - Tests pass with the implementation
5. ✅ TDD Validation - Validates the entire workflow

## Generated Files

- `test_add.py` - Generated test suite
- `add.py` - Generated implementation
- `tdd_contracts.jsonl` - Contract log tracking the workflow

## Troubleshooting

### Server won't start
- Check that port 8283 is not in use: `netstat -tuln | grep 8283`
- Kill existing Letta processes: `pkill -f "letta server"`
- Check logs: `tail -f /tmp/letta_server.log`

### 401 Unauthorized errors
- Verify OPENAI_API_KEY is set: `echo $OPENAI_API_KEY`
- Restart server with environment: `./start_letta.sh`

### Tool execution errors
- The improved error handling will now show detailed error messages
- Check that pytest is installed in your environment
- Verify workspace directory permissions

## Architecture

```
┌─────────────────┐
│  Orchestrator   │  (Letta Agent)
│  (GPT-4o-mini)  │
└────────┬────────┘
         │
         ├──────────┬──────────────┬────────────┬───────────────┐
         │          │              │            │               │
    ┌────▼───┐ ┌───▼────┐  ┌──────▼─────┐ ┌───▼────────┐
    │ Tester │ │ Coder  │  │ Test Runner│ │ Validator  │
    │  Tool  │ │  Tool  │  │    Tool    │ │    Tool    │
    └────────┘ └────────┘  └────────────┘ └────────────┘
         │          │              │            │
         └──────────┴──────────────┴────────────┘
                     │
              Codex CLI (GPT-5.1-Codex)
```

All tools use the same LLM via Codex CLI for consistency.
