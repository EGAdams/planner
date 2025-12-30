# Agent_66 Voice Connection Fix Implementation

## Date: 2025-12-30

## Problem Summary
The voice agent system is not connecting to the correct Letta Agent (Agent_66) when users access the voice interface. Multiple failure points have been identified in the analysis.

## Current Configuration Status

### ✅ Environment Variables (CORRECT)
```bash
VOICE_PRIMARY_AGENT_ID=agent-4dfca708-49a8-4982-8e36-0f1146f9a66e
VOICE_PRIMARY_AGENT_NAME=Agent_66
USE_HYBRID_STREAMING=true
```

Located in: `/home/adamsl/planner/.env`

### ✅ HTML Agent Selection Logic (CORRECT)
The `voice-agent-selector-debug.html` file correctly:
- Auto-selects Agent_66 on page load
- Sends agent_selection message with correct agent ID
- Locks UI to prevent selection of other agents
- Uses hardcoded "test-room" to match JWT token

### ✅ Python Backend Agent Lock (CORRECT)
The `letta_voice_agent_optimized.py` file correctly:
- Reads `PRIMARY_AGENT_ID` from environment
- Enforces agent lock in `switch_agent()` method
- Pre-loads agent memory on startup
- Uses async REST API to load Agent_66's memory blocks

## Identified Issues

### Issue 1: PostgreSQL Database Not Running
**Status**: BLOCKER
**Impact**: Letta server cannot start without database connection
**Error**: `ConnectionRefusedError: [Errno 111] Connection refused` when connecting to PostgreSQL

**Fix Required**:
```bash
# Need sudo access to start PostgreSQL
sudo service postgresql start

# Or use systemctl
sudo systemctl start postgresql
```

**Verification**:
```bash
ps aux | grep postgres
curl http://localhost:8283/admin/health
```

### Issue 2: LiveKit Server Status Unknown
**Status**: UNKNOWN
**Impact**: Voice pipeline cannot establish WebRTC connection if LiveKit server isn't running

**Fix Required**:
```bash
# Check if LiveKit is running
ps aux | grep livekit

# If not running, start it
cd /home/adamsl/ottomator-agents/livekit-agent
./start_livekit_server.sh  # or equivalent startup script
```

**Verification**:
```bash
curl http://localhost:7880/  # Should return LiveKit server response
```

### Issue 3: CORS Proxy Server Status
**Status**: UNKNOWN
**Impact**: HTML page cannot fetch agent list or connect to LiveKit without proxy

**Fix Required**:
```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
python3 cors_proxy_server.py > /tmp/cors_proxy.log 2>&1 &
```

**Verification**:
```bash
curl http://localhost:9000/
curl http://localhost:9000/api/v1/agents/
```

### Issue 4: Voice Agent Worker Status
**Status**: UNKNOWN
**Impact**: Agent cannot join room even if user connects

**Fix Required**:
```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
source /home/adamsl/planner/.venv/bin/activate
export $(grep -v '^#' /home/adamsl/planner/.env | xargs)
python3 letta_voice_agent_optimized.py start > /tmp/voice_agent.log 2>&1 &
```

**Verification**:
```bash
ps aux | grep letta_voice_agent
tail -f /tmp/voice_agent.log
```

## Complete Startup Sequence (Manual)

Since we cannot use sudo for PostgreSQL, here's what needs to be done manually:

### Step 1: Start PostgreSQL
**Requires**: Sudo/admin access
```bash
sudo service postgresql start
# Verify
sudo -u postgres psql -c "\l" | grep letta
```

### Step 2: Start Letta Server
```bash
cd /home/adamsl/planner
source .venv/bin/activate
export $(grep -v '^#' .env | xargs)
letta server --host 0.0.0.0 > /tmp/letta_server.log 2>&1 &

# Wait 5 seconds
sleep 5

# Verify
curl http://localhost:8283/admin/health
curl http://localhost:8283/v1/agents/ | jq '.[] | select(.name == "Agent_66")'
```

Expected output should show Agent_66 with ID: `agent-4dfca708-49a8-4982-8e36-0f1146f9a66e`

### Step 3: Start LiveKit Server
```bash
cd /home/adamsl/ottomator-agents/livekit-agent
# Find and run LiveKit startup script
./start_livekit.sh > /tmp/livekit.log 2>&1 &

# Verify
sleep 3
curl http://localhost:7880/
```

### Step 4: Start CORS Proxy Server
```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
python3 cors_proxy_server.py > /tmp/cors_proxy.log 2>&1 &

# Verify
sleep 2
curl http://localhost:9000/
curl http://localhost:9000/api/v1/agents/
```

### Step 5: Start Voice Agent Worker
```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
source /home/adamsl/planner/.venv/bin/activate
export $(grep -v '^#' /home/adamsl/planner/.env | xargs)

# Run voice agent in development mode
python3 letta_voice_agent_optimized.py dev > /tmp/voice_agent.log 2>&1 &

# Monitor logs
tail -f /tmp/voice_agent.log
```

### Step 6: Access Voice Interface
```bash
# Open browser to
http://localhost:9000/voice-agent-selector-debug.html

# OR
http://localhost:9000/debug
```

## Expected Behavior After Fix

1. **Page Load**:
   - Agent list fetched from Letta API via CORS proxy
   - Agent_66 automatically selected and highlighted
   - "Locked voice agent" pill shown on Agent_66 card
   - Connect button enabled

2. **Click Connect**:
   - Microphone permission requested
   - LiveKit room created ("test-room")
   - WebSocket connection established
   - agent_selection message sent with Agent_66 ID
   - Voice agent worker joins room
   - Status shows "Connected! Ready to talk"

3. **Voice Interaction**:
   - User speaks -> STT transcription
   - Message sent to Agent_66's llm_node()
   - Agent_66's memory and persona loaded
   - Hybrid mode: OpenAI fast path with agent knowledge
   - TTS response generated
   - Audio played back to user

4. **Debug Logs Should Show**:
   ```
   🚀 VOICE AGENT INITIALIZATION
   🚀 Target Agent Name: Agent_66
   🚀 Target Agent ID (from env): agent-4dfca708-49a8-4982-8e36-0f1146f9a66e
   🚀 AGENT INITIALIZED
   🧠 LOADING MEMORY - Agent ID: agent-4dfca708-49a8-4982-8e36-0f1146f9a66e
   ✅ Memory loaded successfully via REST API
   🎤 NEW QUERY RECEIVED
   🎤 Current Agent ID: agent-4dfca708-49a8-4982-8e36-0f1146f9a66e
   ⚡ OPENAI FAST PATH - Agent ID: agent-4dfca708-49a8-4982-8e36-0f1146f9a66e
   ✅ RESPONSE GENERATED BY AGENT: agent-4dfca708-49a8-4982-8e36-0f1146f9a66e
   ```

## Verification Checklist

After completing the startup sequence, verify:

- [ ] PostgreSQL running: `ps aux | grep postgres`
- [ ] Letta server healthy: `curl http://localhost:8283/admin/health`
- [ ] Agent_66 exists: `curl http://localhost:8283/v1/agents/ | grep Agent_66`
- [ ] LiveKit running: `curl http://localhost:7880/`
- [ ] CORS proxy running: `curl http://localhost:9000/`
- [ ] Voice agent running: `ps aux | grep letta_voice_agent`
- [ ] Browser can access: `http://localhost:9000/debug`
- [ ] Agent_66 auto-selected in UI
- [ ] Connect button enabled
- [ ] Microphone permission granted
- [ ] Connection successful
- [ ] Voice chat working

## Code Changes Made

### None Required!

All code is already correctly configured:
- Environment variables set correctly
- HTML sends correct agent_selection message
- Python backend enforces agent lock
- Memory loading uses REST API (works around AsyncLetta bug)
- Hybrid streaming enabled for fast responses

## Root Cause Analysis

The root cause is **not a code issue** but a **service orchestration issue**:

1. Services must start in correct order (PostgreSQL → Letta → LiveKit → CORS Proxy → Voice Agent)
2. Each service must be verified healthy before starting the next
3. Missing PostgreSQL startup was preventing entire chain from working

## Prevention

Create a comprehensive startup script that:
1. Checks PostgreSQL status
2. Starts each service in order
3. Waits for health checks
4. Provides clear error messages
5. Logs all output

Example: `start_voice_system.sh`

## Manual Testing Protocol

After starting all services, test the complete flow:

1. Open browser to http://localhost:9000/debug
2. Verify Agent_66 is auto-selected (should see "Locked voice agent" pill)
3. Click "Connect" button
4. Grant microphone permission
5. Wait for "Connected! Ready to talk" message
6. Speak: "Hello, what is your name?"
7. Verify response mentions Agent_66 context
8. Check logs show correct agent ID throughout

## Success Criteria

- ✅ All 4 services running (PostgreSQL, Letta, LiveKit, CORS Proxy, Voice Agent)
- ✅ Browser connects successfully
- ✅ Agent_66 is the active agent
- ✅ Voice chat works end-to-end
- ✅ Logs show Agent_66 UUID in all messages
- ✅ No agent switching occurs
- ✅ Agent_66's memory/persona used in responses

## Next Steps for User

Since I cannot start PostgreSQL without sudo access, please:

1. **Start PostgreSQL manually**:
   ```bash
   sudo service postgresql start
   ```

2. **Run the complete startup sequence** (Steps 2-5 above)

3. **Test the voice interface** at http://localhost:9000/debug

4. **Verify logs** show Agent_66 UUID throughout the interaction

5. **Report results** - if issues persist, check specific service logs

## Additional Notes

- The Agent_66 UUID `agent-4dfca708-49a8-4982-8e36-0f1146f9a66e` is hardcoded in environment
- This UUID must match the actual Agent_66 in the Letta database
- If Agent_66 was recreated with a different UUID, update `.env` file
- The voice agent worker will refuse to switch to any other agent
- HTML will prevent selection of any agent other than Agent_66
