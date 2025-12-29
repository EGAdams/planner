# Agent_66 Room Conflict Fix - Complete Solution

## Issue Summary

**Problem**: Audio responses are being duplicated - some audio plays correctly while some gets typed back into the Letta ADE interface.

**Root Causes Identified**:
1. ✅ Only ONE voice agent process running (no process duplication)
2. ✅ No multiple agents in rooms (rooms are currently empty)
3. ❌ `VOICE_PRIMARY_AGENT_ID` environment variable NOT SET
4. ❌ Potential dual message routing (voice + direct Letta API)

## Diagnostic Results

```
Agent Process Count: 1 (HEALTHY)
Active Rooms: 0 (HEALTHY)
Agent_66 Status: EXISTS (ID: agent-4dfca708-49a8-4982-8e36-0f1146f9a66e)
Environment Config: MISSING AGENT ID
```

## The Real Problem

The issue is NOT multiple agents fighting for the same room. Instead, it's likely:

1. **Hybrid Mode Syncing**: The voice agent correctly syncs conversations to Letta memory
2. **Unexpected Direct API Calls**: Something (possibly browser extension, debugging tool, or residual connection) is ALSO sending messages directly to Letta's REST API
3. **Result**: Same conversation appears in BOTH voice output AND Letta ADE chat interface

## Fixes to Implement

### Fix 1: Set VOICE_PRIMARY_AGENT_ID Environment Variable

**Why**: This ensures the voice system uses the EXACT agent ID without searching by name, preventing any ambiguity.

**Action**:
```bash
# Add to .env file
echo "VOICE_PRIMARY_AGENT_ID=agent-4dfca708-49a8-4982-8e36-0f1146f9a66e" >> .env

# Or update .env manually:
# VOICE_PRIMARY_AGENT_ID=agent-4dfca708-49a8-4982-8e36-0f1146f9a66e
```

### Fix 2: Add Agent Instance Tracking

**Why**: Prevent multiple agent instances from being created for the same agent ID.

**Implementation**: Add singleton pattern to voice agent initialization.

**File**: `letta_voice_agent_optimized.py`

**Changes**:
```python
# Add at module level (after imports)
_ACTIVE_AGENT_INSTANCES = {}  # Track active agent instances by agent_id
_AGENT_INSTANCE_LOCK = asyncio.Lock()

# In entrypoint() function, before creating LettaVoiceAssistantOptimized:
async with _AGENT_INSTANCE_LOCK:
    if agent_id in _ACTIVE_AGENT_INSTANCES:
        logger.warning(f"⚠️  Agent {agent_id} already has active instance! Using existing instance.")
        assistant = _ACTIVE_AGENT_INSTANCES[agent_id]
        # Reset the assistant for fresh connection
        await assistant.reset_for_reconnect()
    else:
        # Create new assistant instance
        assistant = LettaVoiceAssistantOptimized(ctx, letta_client, agent_id)
        _ACTIVE_AGENT_INSTANCES[agent_id] = assistant
        logger.info(f"✅ Created new agent instance for {agent_id}")

# On disconnect, remove from tracking:
@ctx.room.on("participant_disconnected")
def on_participant_disconnected(participant: rtc.RemoteParticipant):
    # ... existing logic ...

    # When last participant disconnects, clean up instance tracking
    if remaining_humans == 0:
        async def cleanup():
            await assistant.reset_for_reconnect()
            async with _AGENT_INSTANCE_LOCK:
                if agent_id in _ACTIVE_AGENT_INSTANCES:
                    del _ACTIVE_AGENT_INSTANCES[agent_id]
                    logger.info(f"🧹 Removed agent {agent_id} from instance tracking")

        asyncio.create_task(cleanup())
```

### Fix 3: Add Room-to-Agent Mapping Validation

**Why**: Ensure only ONE agent worker is assigned per room.

**Implementation**: Track room assignments globally.

**File**: `letta_voice_agent_optimized.py`

**Changes**:
```python
# Add at module level
_ROOM_TO_AGENT = {}  # Track which agent is assigned to which room
_ROOM_ASSIGNMENT_LOCK = asyncio.Lock()

# In request_handler() function:
async def request_handler(job_request: JobRequest):
    """Accept all job requests to ensure agent joins rooms."""
    room_name = job_request.room.name
    logger.info(f"📥 Job request received for room: {room_name}")

    # Check if this room already has an agent assigned
    async with _ROOM_ASSIGNMENT_LOCK:
        if room_name in _ROOM_TO_AGENT:
            existing_agent = _ROOM_TO_AGENT[room_name]
            logger.warning(
                f"⚠️  CONFLICT DETECTED: Room {room_name} already assigned to {existing_agent}!"
            )
            logger.warning(f"   REJECTING duplicate job request to prevent agent conflict")
            await job_request.reject()
            return

        # Assign this agent to the room
        _ROOM_TO_AGENT[room_name] = agent_id  # We'll need to pass agent_id here
        logger.info(f"✅ Assigned agent {agent_id} to room {room_name}")

    # Room self-recovery
    try:
        from livekit_room_manager import RoomManager
        manager = RoomManager()
        logger.info(f"🧹 Ensuring room {room_name} is clean before joining...")
        await manager.ensure_clean_room(room_name)
        logger.info(f"✅ Room {room_name} is clean and ready for agent")
    except Exception as e:
        logger.warning(f"Room cleanup failed (continuing anyway): {e}")
    finally:
        await manager.close()

    await job_request.accept()
    logger.info(f"✅ Job accepted, starting optimized entrypoint...")

# On disconnect, remove room assignment:
@ctx.room.on("disconnected")
def on_room_disconnected(reason):
    async def cleanup_room_assignment():
        async with _ROOM_ASSIGNMENT_LOCK:
            if ctx.room.name in _ROOM_TO_AGENT:
                del _ROOM_TO_AGENT[ctx.room.name]
                logger.info(f"🧹 Cleared room assignment: {ctx.room.name}")

    asyncio.create_task(cleanup_room_assignment())
```

### Fix 4: Prevent Concurrent Agent Dispatch

**Why**: Stop the room health monitor from dispatching multiple agents to the same room.

**File**: `room_health_monitor.py`

**Current Issue**: The monitor can dispatch agents every 20 seconds if no agent is detected, potentially creating conflicts.

**Fix**: Already has cooldown logic (20s), but add room assignment check:

```python
# In _ensure_agent_present() method:
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

    # NEW CHECK: If agent exists, don't dispatch
    if agent_count > 0:
        logger.debug(f"Room {room_name} already has {agent_count} agent(s), skipping dispatch")
        return

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

        try:
            result = await dispatch_agent_async(room_name, agent_name=self.agent_name)
            if result.get("success"):
                logger.info(
                    "Dispatch result for %s: %s (dispatch_id=%s)",
                    room_name,
                    result.get("message"),
                    result.get("dispatch_id"),
                )
                # Mark this room as having been dispatched
                self._last_agent_dispatch[room_name] = now
            else:
                logger.error("Dispatch failed for %s: %s", room_name, result)
        except Exception as dispatch_err:
            logger.error("Dispatch error for %s: %s", room_name, dispatch_err)
```

### Fix 5: Validate Single Agent Per Room on Join

**Why**: Final safety check to detect and prevent conflicts at join time.

**File**: `letta_voice_agent_optimized.py`

**Add to entrypoint() after session.start():**

```python
# After session.start() in entrypoint()

# Validate only ONE agent in room
@ctx.room.on("participant_connected")
def on_validate_single_agent(participant: rtc.RemoteParticipant):
    """Validate that only one agent exists in the room."""
    if not participant.identity or 'agent' not in participant.identity.lower():
        return  # Not an agent, skip validation

    # Count agents in room
    agent_count = sum(
        1 for p in ctx.room.remote_participants.values()
        if 'agent' in (p.identity or '').lower() or
           'bot' in (p.identity or '').lower() or
           (p.identity or '').startswith('AW_')
    )

    # Include local participant if it's an agent
    if ctx.room.local_participant and ctx.room.local_participant.identity:
        if 'agent' in ctx.room.local_participant.identity.lower():
            agent_count += 1

    if agent_count > 1:
        logger.error(
            f"🚨 CONFLICT: {agent_count} agents detected in room {ctx.room.name}!"
        )
        logger.error(f"   Agents: {[p.identity for p in ctx.room.remote_participants.values()]}")
        logger.error(f"   THIS WILL CAUSE AUDIO DUPLICATION!")

        # Emergency disconnect to prevent conflict
        async def emergency_disconnect():
            await asyncio.sleep(1)  # Let other agent settle
            logger.error(f"🚨 Emergency disconnect due to agent conflict")
            await ctx.room.disconnect()

        asyncio.create_task(emergency_disconnect())
```

## Testing Protocol

### Test 1: Basic Connection
1. Restart voice system: `./restart_voice_system.sh`
2. Open browser to `http://localhost:9000`
3. Select Agent_66
4. Click Connect
5. Speak: "Hello, can you hear me?"
6. **VERIFY**: Audio plays back, no text appears in Letta ADE

### Test 2: Agent Switch
1. While connected to Agent_66, select a different agent
2. **VERIFY**: System disconnects and reconnects cleanly
3. **VERIFY**: Only ONE agent in the room at any time
4. Speak again
5. **VERIFY**: Response from NEW agent, no duplication

### Test 3: Reconnection
1. Close browser tab (disconnect)
2. Wait 5 seconds
3. Reopen and reconnect
4. **VERIFY**: Clean reconnection, no stale state
5. Speak again
6. **VERIFY**: Normal operation, no duplication

### Test 4: Concurrent Connections (Stress Test)
1. Open TWO browser tabs
2. Both select Agent_66
3. Both try to connect
4. **VERIFY**: Second connection should be rejected OR cleanly handled
5. **VERIFY**: No audio duplication in either tab

## Monitoring Commands

```bash
# Watch agent process count
watch -n 2 'ps aux | grep letta_voice_agent | grep -v grep | wc -l'

# Monitor room state
watch -n 5 '/home/adamsl/planner/.venv/bin/python3 diagnose_agent_conflict.py'

# Watch logs for conflicts
tail -f voice_agent_debug.log | grep -E "CONFLICT|duplicate|multiple|⚠️"

# Check Letta message history (should NOT increase during voice sessions)
watch -n 5 'curl -s http://localhost:8283/v1/agents/agent-4dfca708-49a8-4982-8e36-0f1146f9a66e/messages?limit=1 | python3 -m json.tool | head -20'
```

## Rollback Plan

If issues persist after fixes:

1. **Revert to backup**: `cp letta_voice_agent_optimized.py.backup letta_voice_agent_optimized.py`
2. **Disable hybrid mode**: Set `USE_HYBRID_STREAMING=false` in `.env`
3. **Stop room health monitor**: `pkill -f room_health_monitor.py`
4. **Manual dispatch only**: Rely on HTML client's `requestAgentDispatch()` only

## Success Criteria

- ✅ Only ONE agent process running per agent ID
- ✅ Only ONE agent in each room at any time
- ✅ Audio plays correctly without text duplication in Letta ADE
- ✅ Clean agent switching without conflicts
- ✅ Graceful reconnection handling
- ✅ No excessive agent initializations in logs

## Implementation Priority

1. **CRITICAL** (Do First):
   - Fix 1: Set VOICE_PRIMARY_AGENT_ID
   - Fix 5: Validate single agent per room on join

2. **HIGH** (Do Soon):
   - Fix 2: Add agent instance tracking
   - Fix 3: Add room-to-agent mapping

3. **MEDIUM** (Nice to Have):
   - Fix 4: Prevent concurrent dispatch (already has cooldown)

## Next Steps

1. Apply Fix 1 immediately (set environment variable)
2. Implement Fix 5 (validation on join)
3. Test with Test 1 protocol
4. If successful, implement remaining fixes
5. Run full test suite
6. Monitor for 24 hours to ensure stability
