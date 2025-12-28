# Voice Agent Exit Diagnostic Guide

## Problem Summary

Based on user logs, the voice agent is exiting prematurely with empty reason:

```
INFO:livekit.agents:process exiting
21:51:14.696 INFO   livekit.agents   process exiting {"reason": "", "pid": 31248, ...}
```

**Symptoms:**
1. Agent process exits immediately after starting
2. Browser shows "Waiting for Agent to join" but agent never joins
3. Previously worked briefly (showed "Start Speaking") but now fails earlier
4. Room ID mismatch: Agent joined "RM_H6QwQceiVUUQ" but we configured "test-room"

## Root Cause Analysis

Based on code review and logs, the likely causes are:

### 1. Room Cleanup Message Triggered Prematurely

The agent has a data message handler that listens for `{"type": "room_cleanup"}`:

```python
@ctx.room.on("data_received")
def on_data_received(data_packet: rtc.DataPacket):
    message_data = json.loads(data_packet.data.decode('utf-8'))

    if message_data.get("type") == "room_cleanup":
        logger.info("🧹 Room cleanup requested - preparing to exit room")
        asyncio.create_task(_graceful_shutdown(ctx))
```

**If the browser sends this message prematurely (on load, on agent switch, etc.), the agent will exit!**

### 2. Room ID Mismatch

Logs show:
- Browser configured to join: `test-room`
- Agent joined: `RM_H6QwQceiVUUQ` (different room!)

This could be:
- JWT token generating wrong room name
- Agent triggered with wrong room parameter
- LiveKit server creating different room than requested

### 3. Agent Job Lifecycle

The agent uses `request_handler` to accept jobs. If the job completes immediately or has wrong configuration, agent exits with empty reason.

## Diagnostic Tools

### Tool 1: Agent Exit Diagnostic

**Purpose:** Monitor agent in real-time and capture:
- Room ID mismatches
- Premature `room_cleanup` messages
- Data messages sent to agent
- Exit timing and reasons

**Usage:**
```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
python tests/diagnose_agent_exit.py --room test-room --duration 120
```

**What it checks:**
1. Room name vs Room SID matching
2. Monitors for `room_cleanup` messages
3. Monitors for `agent_selection` messages
4. Detects premature agent exits
5. Generates diagnostic report: `diagnostic_report.json`

**Expected output if working correctly:**
```
✓ User connected to room
✓ Room name and SID are different (normal)
✓ Agent should join room NAME: 'test-room'
✓ Agent still connected
✓ No room_cleanup messages detected
✓ Agent persisted for full duration
```

**Expected output if broken:**
```
❌ ROOM_CLEANUP MESSAGE DETECTED at 2.3s!
❌ AGENT EXITED PREMATURELY at 3.1s!
❌ ROOT CAUSE: Browser is sending room_cleanup message!
```

### Tool 2: Room Lifecycle Tests

**Purpose:** Comprehensive test suite for room management robustness.

**Usage:**
```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents

# Run all tests
python tests/test_room_lifecycle.py --all

# Run specific tests
python tests/test_room_lifecycle.py --test room_state
python tests/test_room_lifecycle.py --test join_leave_cycle
python tests/test_room_lifecycle.py --test sequential_sessions
python tests/test_room_lifecycle.py --test agent_persistence
python tests/test_room_lifecycle.py --test error_recovery
```

**Tests included:**

1. **Room State Check**
   - Verifies room exists/doesn't exist correctly
   - Participant count accuracy
   - Room metadata accessible

2. **Join/Leave Cycle** (10 iterations)
   - Agent can join room multiple times
   - Agent cleanup is successful
   - No state corruption after repeated cycles
   - No memory leaks

3. **Sequential Sessions** (5 sessions)
   - User connects → Agent joins → User disconnects → Agent exits
   - Repeat multiple times
   - Verify each cycle is clean

4. **Agent Persistence** (60 seconds)
   - Agent joins room successfully
   - Agent stays connected for specified duration
   - Agent doesn't exit prematurely

5. **Error Recovery**
   - Invalid room names
   - Duplicate participants
   - Force disconnects
   - Room deletion while connected

## Fixing the Issue

### Fix 1: Check Browser JavaScript

The browser is likely sending `room_cleanup` too early. Check for:

```javascript
// BAD: Sending cleanup on page load or agent switch
window.addEventListener('load', () => {
  room.localParticipant.publishData({
    type: 'room_cleanup'  // ❌ This will kill the agent!
  });
});

// GOOD: Only send cleanup when explicitly switching agents
function switchAgent(newAgentId) {
  // First send cleanup
  room.localParticipant.publishData({
    type: 'room_cleanup'
  });

  // Wait for cleanup, then connect to new room
  setTimeout(() => {
    connectToNewAgent(newAgentId);
  }, 1000);
}
```

**Look for:**
- `sendDataMessage({type: 'room_cleanup'})`
- When is this being called?
- Is it being called on page load?
- Is it being called before agent joins?

### Fix 2: Verify Room Name Configuration

Check JWT token generation:

```python
# In your backend token generation code
token = AccessToken(
    api_key=LIVEKIT_API_KEY,
    api_secret=LIVEKIT_API_SECRET
)
token.with_identity(user_id)
token.with_grants(VideoGrants(
    room_join=True,
    room="test-room"  # ✓ Make sure this is "test-room", not a room SID
))
```

### Fix 3: Agent Request Handler

The agent's `request_handler` should log the room name it's joining:

```python
async def request_handler(job_request: JobRequest):
    room_name = job_request.room.name
    logger.info(f"📥 Job request received for room: {room_name}")

    # ✓ Verify this logs "test-room", not "RM_H6QwQceiVUUQ"

    await job_request.accept()
```

### Fix 4: Remove Premature Cleanup Triggers

In the browser code, ensure cleanup is ONLY triggered when:
- User explicitly switches to a different agent
- User explicitly closes the session

**NOT when:**
- Page loads
- Agent first joins
- User refreshes browser
- Agent connects

## Testing the Fix

After applying fixes:

1. **Run diagnostic first:**
   ```bash
   python tests/diagnose_agent_exit.py --room test-room --duration 120
   ```

2. **Check diagnostic report:**
   ```bash
   cat diagnostic_report.json | jq '.summary'
   ```

3. **Run full lifecycle tests:**
   ```bash
   python tests/test_room_lifecycle.py --all
   ```

4. **Manual browser test:**
   - Open browser to voice interface
   - Check browser console for data messages
   - Verify agent joins and stays connected
   - Talk to agent
   - Verify agent responds
   - Disconnect and reconnect
   - Verify multiple sessions work

## Expected Log Sequence (Working Correctly)

### Browser connects:
```
[Browser] Connecting to room: test-room
[Browser] Connected successfully
[Browser] Waiting for agent...
```

### Agent starts:
```
INFO: 📥 Job request received for room: test-room
INFO: ✅ Job accepted, starting entrypoint...
INFO: 🚀 Voice agent starting in room: test-room
INFO: ✅ Voice agent ready and listening
```

### User speaks:
```
INFO: 🎤 User message: Hello
INFO: 🔊 Letta response: Hi! How can I help you?
```

### User disconnects:
```
INFO: ⏱️  Idle timeout reached (no participants)
INFO: 🛑 Shutting down agent due to inactivity...
INFO: ✅ Agent disconnected successfully
```

## Expected Log Sequence (Broken - Premature Exit)

### Browser connects:
```
[Browser] Connecting to room: test-room
[Browser] Sending agent_selection message  # ❌ Too early!
```

### Agent starts and immediately gets cleanup:
```
INFO: 📥 Job request received for room: RM_H6QwQceiVUUQ  # ❌ Wrong room!
INFO: ✅ Job accepted, starting entrypoint...
INFO: 🚀 Voice agent starting in room: RM_H6QwQceiVUUQ
INFO: 🧹 Room cleanup requested - preparing to exit room  # ❌ Premature!
INFO: ⏳ Initiating graceful shutdown...
INFO: ✅ Graceful shutdown complete
INFO: process exiting {"reason": ""}  # ❌ Empty reason!
```

## Key Files to Check

1. **Browser JavaScript** (agent selection/switching):
   - Look for `publishData` or `sendDataMessage` calls
   - Check when `room_cleanup` is sent
   - Check when `agent_selection` is sent

2. **Backend JWT Token Generation**:
   - Verify room name is `"test-room"`
   - Not room SID like `"RM_H6QwQceiVUUQ"`

3. **Agent Configuration**:
   - `letta_voice_agent.py` line 869-897 (request_handler)
   - Check room cleanup logic line 828-831

4. **Frontend Room Connection**:
   - How is room name passed to LiveKit?
   - Is it hardcoded as `"test-room"`?
   - Or is it using a room SID?

## Contact Points for Debugging

1. **Check what room browser is connecting to:**
   ```javascript
   console.log("Connecting to room:", roomName);
   ```

2. **Check what room agent receives:**
   ```python
   logger.info(f"Job request room: {job_request.room.name}")
   ```

3. **Check data messages being sent:**
   ```javascript
   room.localParticipant.on('dataMessageReceived', (msg) => {
     console.log("Data message sent:", msg);
   });
   ```

4. **Monitor agent data messages:**
   Already logged in `on_data_received` handler

## Success Criteria

After fixes are applied, you should see:

✅ Agent joins room "test-room" (matches browser)
✅ Agent stays connected while user is present
✅ Agent responds to voice input
✅ No premature "room_cleanup" messages
✅ Agent only exits when user disconnects or times out
✅ Multiple sequential sessions work (connect, talk, disconnect, connect again)
✅ No "process exiting" with empty reason

## Next Steps

1. Run diagnostics to identify exact failure point
2. Fix the identified issue (likely browser sending cleanup too early)
3. Re-run diagnostics to verify fix
4. Run full lifecycle test suite
5. Manual browser testing with multiple sessions

---

**Generated by Feature Implementation Agent - TDD Business Logic**
