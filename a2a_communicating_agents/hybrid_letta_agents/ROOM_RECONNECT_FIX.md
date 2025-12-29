# Room Management Reconnection Fix

## Problem Statement

Agent_66 stops responding after disconnect/reconnect cycles when using localhost:9000.

## Root Cause Analysis

### Issue 1: Agent Worker State Persistence
The LiveKit agent worker (letta_voice_agent_optimized.py) maintains state across room sessions:

```python
# In entrypoint():
assistant = LettaVoiceAssistantOptimized(ctx, letta_client, agent_id)
# This instance persists for the entire worker lifetime
# NOT recreated on reconnect
```

**Impact**:
- First connection: Agent loads memory, works correctly
- Disconnect: Agent instance remains in memory
- Reconnect: Same agent instance reused, but state may be stale

### Issue 2: Room Cleanup Not Enforced
HTML disconnect logic:
```javascript
// Sends cleanup message but doesn't wait for confirmation
await room.localParticipant.publishData(cleanupData, { reliable: true });
await new Promise(resolve => setTimeout(resolve, 500));  // Only 500ms delay
```

**Impact**:
- Room may not be fully cleaned before reconnect
- Agent worker may still be processing previous session
- Race condition between cleanup and new connection

### Issue 3: Fixed Room Name Without Session Isolation
```javascript
const roomName = 'test-room';  // Hardcoded!
```

**Impact**:
- All sessions use same room name
- No isolation between disconnect/reconnect cycles
- Previous agent worker state persists in room

### Issue 4: Agent Memory State Not Reset
```python
async def switch_agent(self, new_agent_id: str, agent_name: str = None):
    # ...
    self.message_history = []  # Clear history

    # *** CRITICAL: Reload memory for new agent
    self.memory_loaded = False
    await self._load_agent_memory()
```

The memory reload happens, but other state may persist:
- `self.letta_sync_task` - background task may still be running
- `self.idle_monitor_task` - monitoring old session
- `self.last_activity_time` - stale timestamp
- `self._agent_session` - session reference not reset

## Comprehensive Fix Strategy

### Fix 1: Add Agent Instance Reset Method

Add to `LettaVoiceAssistantOptimized` class:

```python
async def reset_for_reconnect(self):
    """
    Reset agent state for clean reconnection.

    Called when user disconnects and reconnects to ensure
    fresh state without creating new agent instance.
    """
    logger.info(f"🔄 Resetting agent state for reconnect...")

    # Cancel background tasks
    if self.letta_sync_task and not self.letta_sync_task.done():
        self.letta_sync_task.cancel()
        self.letta_sync_task = None
        logger.info("✅ Cancelled background Letta sync task")

    if self.idle_monitor_task and not self.idle_monitor_task.done():
        self.idle_monitor_task.cancel()
        self.idle_monitor_task = None
        logger.info("✅ Cancelled idle monitor task")

    # Reset state
    self.message_history = []
    self.last_activity_time = time.time()
    self.is_shutting_down = False

    # Force memory reload
    self.memory_loaded = False
    await self._load_agent_memory()

    logger.info(f"✅ Agent reset complete, ready for new session")
```

### Fix 2: Implement Reconnection Handler

Add to `entrypoint()` function:

```python
@ctx.room.on("participant_disconnected")
def on_participant_disconnected(participant: rtc.RemoteParticipant):
    """Handle user disconnect - prepare for potential reconnect"""
    logger.info(f"👋 Participant disconnected: {participant.identity}")

    # Check if this was the only human user
    remaining_humans = sum(
        1 for p in ctx.room.remote_participants.values()
        if not any(x in p.identity.lower() for x in ['agent', 'bot', 'aw_'])
    )

    if remaining_humans == 0:
        logger.info("🔄 Last human disconnected, resetting agent for reconnect...")
        asyncio.create_task(assistant.reset_for_reconnect())
```

### Fix 3: Enhanced Room Cleanup

Modify HTML disconnect logic:

```javascript
window.disconnect = async function() {
    // Clear any pending agent join timeout
    if (agentJoinTimer) {
        clearTimeout(agentJoinTimer);
        agentJoinTimer = null;
        console.log('⏰ Cleared agent join timeout');
    }

    if (room) {
        try {
            // Publish room cleanup message
            const encoder = new TextEncoder();
            const cleanupData = encoder.encode(JSON.stringify({
                type: 'room_cleanup',
                timestamp: new Date().toISOString()
            }));
            await room.localParticipant.publishData(cleanupData, { reliable: true });
            console.log('📤 Sent room cleanup notification');

            // CRITICAL FIX: Wait longer for backend to process
            await new Promise(resolve => setTimeout(resolve, 2000));  // 2 seconds

        } catch (e) {
            console.error('Error sending cleanup notification:', e);
        }

        await room.disconnect();
        room = null;
        status.textContent = 'Disconnected';
        status.className = '';
        connectBtn.disabled = selectedAgent ? false : true;
        disconnectBtn.disabled = true;
        console.log('✅ Disconnected from room and ready for reconnect');
    }
};
```

### Fix 4: Add Reconnection Detection

Modify `_graceful_shutdown()` to be a soft reset instead of full shutdown:

```python
async def _graceful_shutdown(ctx: JobContext):
    """
    Handle room cleanup request (disconnect, not full shutdown).

    This is called when user disconnects. We reset state but keep
    the agent worker running for fast reconnection.
    """
    try:
        logger.info("🔄 Room cleanup requested (preparing for potential reconnect)...")

        # Don't actually disconnect the room - let LiveKit handle that
        # Just reset our agent state
        # The room will close naturally when last participant leaves

        logger.info("✅ Agent ready for reconnection")
    except Exception as e:
        logger.error(f"Error during graceful shutdown: {e}")
```

### Fix 5: Room Health Monitor Enhancement

The `room_health_monitor.py` already handles agent dispatch, but we should ensure it doesn't interfere:

```python
# In room_health_monitor.py, modify _ensure_agent_present:
async def _ensure_agent_present(self, room_name: str, participants):
    """Dispatch the agent when humans are waiting without assistance."""
    if not participants:
        return

    human_count = 0
    agent_count = 0

    for participant in participants:
        identity = (participant.identity or "").lower()
        if self._looks_like_agent(identity):
            agent_count += 1
        else:
            human_count += 1

    # CRITICAL: Only dispatch if ZERO agents present
    # Don't interfere with existing agent workers
    if human_count > 0 and agent_count == 0:
        now = time.time()
        last_attempt = self._last_agent_dispatch.get(room_name, 0)

        if now - last_attempt < self._agent_dispatch_cooldown:
            remaining = self._agent_dispatch_cooldown - (now - last_attempt)
            logger.info(
                "Skipping dispatch for %s (cooldown %.1fs remaining)",
                room_name,
                max(0, remaining),
            )
            return

        logger.warning(
            "Room %s has %d human participant(s) but no agent. Dispatching %s...",
            room_name,
            human_count,
            self.agent_name,
        )

        # ... rest of dispatch logic
```

## Implementation Priority

### Critical (Must Have)
1. ✅ Fix 1: Add `reset_for_reconnect()` method
2. ✅ Fix 2: Add `participant_disconnected` handler
3. ✅ Fix 3: Increase disconnect cleanup delay to 2s

### Important (Should Have)
4. Fix 4: Convert `_graceful_shutdown()` to soft reset
5. Fix 5: Verify room health monitor doesn't interfere

### Optional (Nice to Have)
6. Add session ID to room names for true isolation
7. Add agent state health checks
8. Implement agent worker restart on repeated failures

## Testing Plan

### Test 1: Basic Reconnection
1. Connect to Agent_66
2. Send message, verify response
3. Disconnect
4. Wait 3 seconds
5. Reconnect
6. Send message, verify response

**Expected**: Both messages get responses from Agent_66

### Test 2: Rapid Reconnection
1. Connect
2. Disconnect immediately (before agent joins)
3. Reconnect
4. Verify agent joins and responds

**Expected**: Agent joins successfully on second attempt

### Test 3: Multiple Cycles
1. Repeat connect/disconnect 5 times
2. Send message after each reconnect

**Expected**: All messages get responses, no degradation

### Test 4: Background Task Cleanup
1. Connect
2. Send multiple messages (trigger background sync)
3. Disconnect during background sync
4. Reconnect immediately

**Expected**: No errors, clean reconnection

## Deployment Steps

### Step 1: Backup Current Version
```bash
cp letta_voice_agent_optimized.py letta_voice_agent_optimized.py.before_reconnect_fix
```

### Step 2: Apply Code Changes
- Add `reset_for_reconnect()` method to `LettaVoiceAssistantOptimized`
- Add `participant_disconnected` handler to `entrypoint()`
- Update HTML disconnect delay from 500ms to 2000ms

### Step 3: Restart Voice System
```bash
./restart_voice_system.sh
```

### Step 4: Test All Scenarios
Run through Test 1-4 above

### Step 5: Monitor Logs
```bash
tail -f voice_agent_debug.log | grep -E "Resetting agent|participant_disconnected|Room cleanup"
```

## Success Criteria

### Minimum Success
- ✅ Agent responds after first disconnect/reconnect
- ✅ No errors in logs during reconnection
- ✅ Agent state resets cleanly

### Full Success
- ✅ Agent responds correctly after 5+ reconnection cycles
- ✅ Background tasks properly cancelled
- ✅ Memory reloaded on each reconnection
- ✅ No memory leaks or stale state

## Rollback Plan

If issues occur:

```bash
# Stop voice system
pkill -f letta_voice_agent_optimized.py

# Restore backup
cp letta_voice_agent_optimized.py.before_reconnect_fix letta_voice_agent_optimized.py

# Restart
./restart_voice_system.sh
```

## Known Limitations

1. **Fixed Room Name**: Still uses `test-room` - future enhancement could use session IDs
2. **Agent Worker Reuse**: Agent worker process persists across sessions - restart required for true fresh state
3. **Memory State**: Agent memory blocks cached in memory - changes in Letta won't reflect until reload

## Future Enhancements

### Enhancement 1: Dynamic Room Names
```javascript
function getRoomName() {
    // Generate unique room per session
    return `agent-${selectedAgent.id.substring(0, 8)}-${Date.now()}`;
}
```

### Enhancement 2: Agent Worker Health Checks
```python
async def check_agent_health(self):
    """Verify agent is in good state"""
    return (
        not self.is_shutting_down and
        self.memory_loaded and
        len(self.message_history) < 1000  # Prevent unbounded growth
    )
```

### Enhancement 3: Automatic Worker Restart
```bash
# Monitor worker health and restart if needed
while true; do
    if ! pgrep -f "letta_voice_agent_optimized.py dev"; then
        echo "Worker died, restarting..."
        ./start_voice_system.sh
    fi
    sleep 30
done
```

## References

- Main agent code: `letta_voice_agent_optimized.py`
- HTML client: `voice-agent-selector.html`
- Room manager: `livekit_room_manager.py`
- Health monitor: `room_health_monitor.py`

---

**Status**: Ready for implementation
**Priority**: High (blocking user workflow)
**Estimated Effort**: 1-2 hours
**Risk Level**: Medium (requires testing)
