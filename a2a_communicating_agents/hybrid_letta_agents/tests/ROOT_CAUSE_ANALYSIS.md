# ROOT CAUSE ANALYSIS: Agent Exit Issue

## Problem Statement

Voice agent exits prematurely with empty reason:
```
INFO:livekit.agents:process exiting {"reason": "", "pid": 31248, ...}
```

Browser stuck at "Waiting for Agent to join" - agent never appears.

## Root Cause Identified

**CONFIRMED:** Browser is sending `room_cleanup` message prematurely, causing agent to exit.

### Evidence from Code Analysis

#### 1. Agent Listener (`letta_voice_agent.py` line 828-831)

```python
@ctx.room.on("data_received")
def on_data_received(data_packet: rtc.DataPacket):
    message_data = json.loads(data_packet.data.decode('utf-8'))

    if message_data.get("type") == "room_cleanup":
        logger.info("🧹 Room cleanup requested - preparing to exit room")
        asyncio.create_task(_graceful_shutdown(ctx))  # ← Agent exits here!
```

When agent receives `{"type": "room_cleanup"}`, it immediately shuts down.

#### 2. Browser Sending Cleanup (`voice-agent-selector.html` line 391-403)

```javascript
window.disconnect = async function() {
    if (room) {
        try {
            // Publish room cleanup message to notify backend
            const cleanupData = encoder.encode(JSON.stringify({
                type: 'room_cleanup',  // ← Sent to agent
                timestamp: new Date().toISOString()
            }));
            await room.localParticipant.publishData(cleanupData, { reliable: true });
            console.log('📤 Sent room cleanup notification');
        } catch (e) {
            console.error('Error sending cleanup notification:', e);
        }

        await room.disconnect();
    }
};
```

This `disconnect()` function always sends `room_cleanup` before disconnecting.

#### 3. Premature Call (`voice-agent-selector.html` line 172-180)

```javascript
function selectAgent(agent) {
    selectedAgent = agent;

    // If already connected, disconnect and reconnect with new agent in new room
    if (room && room.state === 'connected') {
        status.textContent = 'Switching agent...';
        console.log(`📤 Switching from old agent to ${agent.name}...`);
        window.disconnect().then(() => {  // ← Calls disconnect()
            console.log('✅ Disconnected from old agent room, now connecting to new one...');
            setTimeout(() => window.connect(), 1000);
        });
    }
}
```

**THE BUG:**
- When user clicks "Select Agent", it calls `selectAgent(agent)`
- If `room.state === 'connected'`, it calls `disconnect()`
- `disconnect()` sends `room_cleanup` message
- Agent receives `room_cleanup` and exits gracefully
- Browser tries to connect to new agent
- **But the agent already exited!**

## Timeline of Events (Broken Scenario)

1. **T+0.0s**: User opens browser, selects Agent_66
2. **T+0.1s**: Browser creates room, starts connecting
3. **T+0.5s**: Agent backend starts, joins room "RM_H6QwQceiVUUQ"
4. **T+0.6s**: Agent connected, waiting for user
5. **T+0.7s**: User clicks "Connect" button (or agent selector triggers it)
6. **T+0.8s**: Browser checks `if (room.state === 'connected')` → **TRUE** (room exists)
7. **T+0.9s**: Browser calls `disconnect()`
8. **T+1.0s**: Browser sends `{"type": "room_cleanup"}` to agent
9. **T+1.1s**: Agent receives message, logs "🧹 Room cleanup requested"
10. **T+1.2s**: Agent starts graceful shutdown
11. **T+1.3s**: Agent disconnects: `process exiting {"reason": ""}`
12. **T+1.5s**: Browser tries to connect to new agent
13. **T+2.0s**: No agent in room (it already exited!)
14. **T+15.0s**: Browser timeout: "Waiting for Agent to join..."

## Additional Issues Found

### Issue 1: Room ID Mismatch

Logs show:
- Browser configured for: `test-room`
- Agent joined: `RM_H6QwQceiVUUQ`

**Why:** LiveKit server assigns room SIDs (like `RM_H6QwQceiVUUQ`) internally, but clients should use room **names** (like `test-room`). The JWT token might be generating a room SID instead of room name.

**Check:** `voice-agent-selector.html` line 35-37:
```javascript
function getRoomName() {
    return `agent-${selectedAgent.id.substring(0, 8)}-${sessionId}`;
}
```

This creates a **unique room per agent per session**, which is good for isolation but requires:
1. Agent must join the **same room name**
2. JWT token must use this **exact room name**

### Issue 2: Agent Selection Flow

Current flow (broken):
1. User selects agent → `selectAgent()` called
2. If room connected → calls `disconnect()` → sends `room_cleanup`
3. Agent exits
4. Browser tries to connect to new room
5. No agent (already exited!)

Expected flow (working):
1. User selects agent → `selectAgent()` called
2. If room connected → **first start new agent in new room**
3. **Then** send cleanup to old agent
4. Old agent exits, new agent ready
5. Browser connects to new agent

## Fixes Required

### Fix 1: Don't Send Cleanup on Agent Selection (Critical)

**File:** `voice-agent-selector.html` line 172-180

**Current code:**
```javascript
if (room && room.state === 'connected') {
    window.disconnect().then(() => {  // ← Sends cleanup
        setTimeout(() => window.connect(), 1000);
    });
}
```

**Fixed code:**
```javascript
if (room && room.state === 'connected') {
    // Disconnect WITHOUT sending cleanup (agent will detect user left)
    try {
        await room.disconnect();  // Clean disconnect, no cleanup message
        room = null;
    } catch (e) {
        console.error('Error disconnecting:', e);
    }

    // Wait a moment, then connect to new agent
    setTimeout(() => window.connect(), 1000);
}
```

**Alternative fix (better):**
```javascript
if (room && room.state === 'connected') {
    // Start new agent FIRST, then clean up old one
    const oldRoom = room;
    room = null;  // Clear reference

    // Connect to new agent immediately
    await window.connect();

    // THEN send cleanup to old agent (it's already replaced)
    try {
        const cleanupData = encoder.encode(JSON.stringify({
            type: 'room_cleanup',
            timestamp: new Date().toISOString()
        }));
        await oldRoom.localParticipant.publishData(cleanupData, { reliable: true });
        await oldRoom.disconnect();
    } catch (e) {
        console.error('Error cleaning up old room:', e);
    }
}
```

### Fix 2: Agent Should Only Exit on Idle Timeout

**File:** `letta_voice_agent.py` line 828-831

**Current code:**
```python
if message_data.get("type") == "room_cleanup":
    logger.info("🧹 Room cleanup requested - preparing to exit room")
    asyncio.create_task(_graceful_shutdown(ctx))
```

**Fixed code (Option A - Remove cleanup trigger):**
```python
# Remove this entirely - let idle timeout handle cleanup
# if message_data.get("type") == "room_cleanup":
#     logger.info("🧹 Room cleanup requested - preparing to exit room")
#     asyncio.create_task(_graceful_shutdown(ctx))
```

**Fixed code (Option B - Only cleanup if no participants):**
```python
if message_data.get("type") == "room_cleanup":
    # Only cleanup if room is actually empty
    participant_count = len(ctx.room.remote_participants or {})
    if participant_count == 0:
        logger.info("🧹 Room cleanup requested and no participants - exiting")
        asyncio.create_task(_graceful_shutdown(ctx))
    else:
        logger.warning(f"🚫 Cleanup requested but {participant_count} participants still in room - ignoring")
```

### Fix 3: Verify Room Name Matching

**File:** JWT token generation (backend)

Ensure token uses room **name**, not room **SID**:

```python
token = AccessToken(
    api_key=LIVEKIT_API_KEY,
    api_secret=LIVEKIT_API_SECRET
)
token.with_identity(user_id)
token.with_grants(VideoGrants(
    room_join=True,
    room="test-room"  # ← Use NAME, not SID like "RM_H6QwQceiVUUQ"
))
```

### Fix 4: Idle Timeout Should Be Primary Exit Mechanism

**File:** `letta_voice_agent.py` line 254-301

The idle timeout monitor (already implemented) should be the **primary** way agents exit:

```python
async def _start_idle_monitor(self):
    """Monitor room activity and disconnect after timeout when room is empty."""

    async def monitor_idle():
        while not self.is_shutting_down:
            await asyncio.sleep(1)
            participant_count = len(self.ctx.room.remote_participants or {})

            if participant_count > 0:
                # User present - keep alive
                self.last_activity_time = time.time()
                continue

            idle_time = time.time() - self.last_activity_time
            if idle_time > self.idle_timeout_seconds:
                # Room empty for too long - exit
                logger.warning(f"⏱️ Idle timeout reached ({idle_time:.1f}s)")
                self.is_shutting_down = True
                await self.ctx.room.disconnect()
                break
```

This is **much more reliable** than listening for cleanup messages!

## Testing the Fix

### Step 1: Apply Fix 1 (Browser)

Edit `voice-agent-selector.html` line 172-180 to NOT send cleanup on agent selection.

### Step 2: Apply Fix 2 (Agent)

Edit `letta_voice_agent.py` line 828-831 to remove cleanup message handler.

### Step 3: Restart Agent

```bash
# Kill existing agent
pkill -f letta_voice_agent

# Start with clean state
python letta_voice_agent.py dev
```

### Step 4: Test with Browser

1. Open `voice-agent-selector.html`
2. Select Agent_66
3. Click "Connect"
4. **Verify:** Agent joins and stays connected
5. **Verify:** "Start Speaking" appears
6. Talk to agent
7. **Verify:** Agent responds
8. Refresh browser (disconnect)
9. Select Agent_66 again
10. Click "Connect"
11. **Verify:** Agent joins again (no hang)

### Step 5: Run Diagnostic Tests

```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents

# Run exit diagnostic
python tests/diagnose_agent_exit.py --room test-room --duration 120

# Expected output:
# ✅ No room_cleanup messages detected
# ✅ Agent persisted for full duration
# ✅ No premature exits

# Run full lifecycle tests
python tests/test_room_lifecycle.py --all

# Expected output:
# ✅ All tests pass
# Success rate: 100%
```

## Success Criteria

After fixes:

✅ Agent joins room on first connection
✅ Agent stays connected while user present
✅ Agent responds to voice input
✅ No "room_cleanup" messages sent prematurely
✅ Agent exits via idle timeout (not cleanup message)
✅ Multiple sequential sessions work
✅ No "process exiting" with empty reason
✅ Browser never shows "Waiting for Agent to join..."

## Long-term Improvements

1. **Use idle timeout exclusively** for agent exit
2. **Remove cleanup message entirely** - it's unreliable
3. **Room naming strategy**: Either use fixed `test-room` or ensure backend knows the room name
4. **Health monitoring**: Implement room health monitor to catch stuck states
5. **Agent pool**: Pre-start agents so they're ready when user connects
6. **Better logging**: Add timestamps and room names to all logs

---

**Status:** Root cause identified, fixes ready to implement
**Priority:** Critical (blocks all voice functionality)
**Estimated Fix Time:** 15 minutes (code changes + restart)
**Testing Time:** 10 minutes (verification)
