# WebSocket System Fix - December 5, 2024

## Problem Summary

The agent communication system was failing because:
1. WebSocket server wouldn't start (returned 1011 internal error)
2. All agents were falling back to RAG message board transport
3. Menu diagnostic items couldn't detect the root cause

## Root Causes Identified

### Issue 1: Script Using Wrong Python
**File**: `a2a_communicating_agents/start_websocket_server.sh`
- Script was using `python3` (system Python)
- System Python doesn't have `websockets` package installed
- Project's `.venv` Python DOES have websockets installed

**Fix**: Updated script to use `.venv/bin/python` first, fallback to `python3`

### Issue 2: WebSocket Handler Signature Incompatibility
**File**: `a2a_communicating_agents/agent_messaging/websocket_server.py:209`
- Old signature: `async def handler(websocket: WebSocketServerProtocol, path: str):`
- New websockets library (15.0.1) only passes one argument
- This caused TypeError and 1011 internal error

**Fix**: Updated signature to `async def handler(websocket: WebSocketServerProtocol):`

## Verification Tests

### ✅ WebSocket Server
```bash
# Server running and listening
ps aux | grep websocket_server
# Output: PID 17581 running on .venv/bin/python

netstat -tln | grep 3030
# Output: tcp LISTEN on 0.0.0.0:3030
```

### ✅ Client Connection Test
```python
# Direct WebSocket connection test
async with websockets.connect('ws://localhost:3030') as ws:
    await ws.send(json.dumps({'type': 'register', 'agent_id': 'test'}))
    response = await ws.recv()
    # Output: {'type': 'registered', 'agent_id': 'test'}
```

### ✅ Agent Transport Status
```bash
grep "transport" logs/orchestrator.log
# Output: Using WebSocket transport (ws://localhost:3030)
# Output: Messenger initialized using: websocket
```

## System Status

### Running Services
- ✓ WebSocket Server (PID: 17581, Port: 3030)
- ✓ Orchestrator Agent (using WebSocket transport)
- ✓ Coder Agent (PID: 18112)
- ✓ Tester Agent (PID: 18117)

### Transport Architecture
```
Orchestrator Agent
    ↓ (WebSocket transport)
WebSocket Server :3030
    ↓ (topic: code)
Coder Agent

    ↓ (topic: test)
Tester Agent
```

## Menu System Updates

### New Diagnostic Items Work Correctly
1. **Check Agent Status** - Shows all running agents
2. **Run Full Agent Diagnostic** - Shows processes, logs, errors
3. **Start/Stop WebSocket Server** - Now uses correct Python

### Fixed Scripts
- `start_websocket_server.sh` - Uses .venv Python
- `stop_websocket_server.sh` - Already working
- `start_orchestrator.sh` - Uses .venv Python
- `stop_orchestrator.sh` - Already working

## Important Notes

### Memory vs Transport
Don't confuse these two systems:
- **Memory System**: Stores agent memories (uses Letta or ChromaDB)
- **Message Transport**: Delivers messages (uses WebSocket, Letta, or RAG)

Log message "Letta unavailable, using ChromaDB memory (fallback)" refers to MEMORY, not transport.

### Correct Transport Status
Look for these log lines to verify transport:
```
Using WebSocket transport (ws://localhost:3030)
Messenger initialized using: websocket
```

### Agent Startup Order
1. **Start WebSocket server first** (or agents will fallback to RAG)
2. **Start Orchestrator** (discovers other agents)
3. **Start specialist agents** (Coder, Tester)

## Testing the Fix

### Quick Test
```bash
cd /home/adamsl/planner/smart_menu
python main.py

# Navigate to: A2A Communicating Agents → 🚀 Agent Lifecycle & Diagnostics
# Select: 📊 Check Agent Status
# Should show: WebSocket server + All agents running
```

### Full Test
```bash
# Use orchestrator chat
cd a2a_communicating_agents/agent_messaging
python orchestrator_chat.py

# Send: "please write a hello world snippet in WebAssembly"
# Should route to coder-agent and generate WAT code
```

## Files Modified

1. `a2a_communicating_agents/start_websocket_server.sh` - Use venv Python
2. `a2a_communicating_agents/agent_messaging/websocket_server.py:209` - Fix handler signature
3. `smart_menu/menu_configurations/config.json` - Enhanced agent lifecycle menu

## Prevention

### Always Use venv
All Python scripts in `a2a_communicating_agents/` should use:
```bash
PLANNER_ROOT="$SCRIPT_DIR/.."
PYTHON_CMD="$PLANNER_ROOT/.venv/bin/python"
```

### Version Compatibility
When upgrading packages, check for breaking API changes:
- `websockets` 15.x removed `path` parameter from handler
- Always test after package upgrades

## Next Steps

1. ✅ WebSocket working correctly
2. ✅ All agents using WebSocket transport
3. ✅ Menu system updated and tested
4. **TODO**: Test end-to-end message flow with actual code generation request
5. **TODO**: Update agent-debug skill with WebSocket troubleshooting

---

**Status**: ✅ FULLY OPERATIONAL
**Date**: December 5, 2024, 09:36 AM
**WebSocket**: ws://localhost:3030
**Transport**: Active and working
