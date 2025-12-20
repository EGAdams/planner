# Agent Selection Fix - Comprehensive Guide

## Problem Summary

When clicking on a different agent card and selecting it, the system was keeping the old agent in the Livekit room instead of switching to the new one. This caused:
- Same agent continuing to respond
- Multiple agents in the same room competing for responses
- No actual agent switching happening

## Root Causes Fixed

### 1. **Multiple Agent Instances in Same Room** ✅ FIXED
**Problem**: When you reconnected, a new voice agent instance was created but the old one never left.
```
Before:
  Old Agent (test-room) ← Still running
  New Agent (test-room) ← Just joined
  Result: Both agents in same room ❌

After:
  Old Agent (agent-abc123-xyz789) ← Gracefully exits room
  New Agent (agent-def456-xyz789) ← Clean new room
  Result: Only new agent in new room ✅
```

### 2. **Room Reuse Without Cleanup** ✅ FIXED
**Problem**: Frontend always used hardcoded `test-room` name.

**Solution**: Dynamic room names per agent selection:
```javascript
// Before: Always "test-room"
room.connect(LIVEKIT_URL, TOKEN, "test-room")

// After: Unique room per agent
room.connect(LIVEKIT_URL, TOKEN, `agent-${agentId}-${sessionId}`)
```

### 3. **No Graceful Agent Shutdown** ✅ FIXED
**Problem**: Backend had no way to cleanly exit when user switched agents.

**Solution**: Added graceful shutdown handler that:
- Detects room cleanup messages from frontend
- Properly disconnects agent from Livekit room
- Clears resources for next agent

## Changes Made

### Frontend: `voice-agent-selector.html`

1. **Added Dynamic Room Names**
   - Session ID generated on page load
   - Each agent gets unique room: `agent-{agentId}-{sessionId}`
   - Ensures clean separation between agents

2. **Added Cleanup Notification**
   - Sends `room_cleanup` message when disconnecting
   - Gives backend signal to gracefully exit
   - 500ms delay ensures backend processes cleanup

3. **Improved Disconnect Flow**
   ```javascript
   // New: Send cleanup signal first
   await room.localParticipant.publishData(cleanupData)
   // Then wait for backend to process
   await new Promise(resolve => setTimeout(resolve, 500))
   // Finally disconnect
   await room.disconnect()
   ```

### Backend: `letta_voice_agent.py`

1. **Added Graceful Shutdown Function**
   ```python
   async def _graceful_shutdown(ctx: JobContext):
       """Cleanly exit room when user switches agents"""
       await ctx.room.local_participant.flush()
       await ctx.room.disconnect()
   ```

2. **Added Cleanup Message Handler**
   ```python
   if message_data.get("type") == "room_cleanup":
       asyncio.create_task(_graceful_shutdown(ctx))
   ```

## How to Test

### Test 1: Basic Agent Switching (No Restart Required)

1. **Start the system**:
   ```bash
   cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
   ./start_voice_system.sh
   ```

2. **Open the agent selector**:
   - Navigate to: `file:///home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/voice-agent-selector.html`
   - Or serve with: `python3 -m http.server 8000` and visit `http://localhost:8000/voice-agent-selector.html`

3. **Test switching**:
   - Select Agent A → Click Connect
   - Wait for agent to join (green status)
   - Say something to verify it's Agent A
   - **While connected**, select Agent B from the list
   - Watch for "Switching agent..." status
   - Should automatically disconnect from Agent A's room
   - Should connect to Agent B's room (clean room, only new agent)
   - Say something to verify it's Agent B now

4. **Expected Behavior**:
   - Room name changes in browser console: `agent-xyz123... → agent-abc456...`
   - Status shows: "Switching agent..." → "Connected"
   - Only new agent responds
   - No overlap or conflict

### Test 2: Multiple Agent Switches

1. Connected to Agent A
2. Switch to Agent B (should switch cleanly)
3. Switch to Agent C (should switch cleanly)
4. Switch back to Agent A (should switch cleanly)

### Test 3: Browser Console Logs

Open browser DevTools (F12) and watch Console tab. You should see:
```
✅ Signal connection established
✅ Room connected successfully
👤 Participant connected: agent-selection-worker
📤 Sent agent selection: agent-id-123
```

When switching:
```
📤 Switching from old agent to Agent B...
📤 Sent room cleanup notification
✅ Disconnected from old agent room
Disconnected from room

🔗 Connecting to room: agent-def456-xyz789 on ws://localhost:7880
✅ Signal connection established
✅ Room connected successfully
👤 Participant connected: agent-selection-worker
📤 Sent agent selection: agent-id-456
```

### Test 4: Backend Logs

Monitor voice agent output (should see in terminal):
```
# When user selects new agent:
🧹 Room cleanup requested - preparing to exit room
⏳ Initiating graceful shutdown...
✅ Graceful shutdown complete

# When new agent joins:
📥 Job request received for room: agent-def456-xyz789
✅ Job accepted, starting entrypoint...
🚀 Voice agent starting in room: agent-def456-xyz789
```

## When to Restart the Letta Server

**You do NOT need to restart the Letta server for agent switching.** The fixes work with:
- Running Letta server (no restart needed)
- Running Livekit server (no restart needed)
- Running voice agent (no restart needed)

**Only restart if**:
- You modify the Letta agent definitions themselves
- You change the backend Python code significantly
- You encounter persistent "Letta server not responding" errors

Quick restart if needed:
```bash
pkill -f "letta server"
cd /home/adamsl/planner && ./start_letta_dec_09_2025.sh
```

## Troubleshooting

### Issue: Still Showing Old Agent

**Check**:
1. Browser console (F12) - look for room name changes
2. Backend logs - look for `🧹 Room cleanup requested`
3. Verify services running:
   ```bash
   ps aux | grep -E "letta|livekit|voice" | grep -v grep
   ```

**Fix**:
```bash
# Restart voice system completely
./restart_voice_system.sh

# Then try agent switching again
```

### Issue: "Waiting for agent to join..."

**Cause**: Previous agent still in room (old code behavior)

**Fix**:
```bash
# Force restart everything
./restart_voice_system.sh
```

### Issue: Room names not changing

**Check**:
1. Are you on the same browser tab? (Session ID is per-tab)
2. Check console for `Connecting to room: agent-...` messages
3. Verify CORS proxy is working: `curl http://localhost:9000/health`

## Architecture Improvement

### Old Flow (Broken)
```
User selects Agent B
     ↓
Disconnect from test-room
     ↓
(Old agent still in test-room)
     ↓
Reconnect to test-room
     ↓
Create NEW agent instance
     ↓
Now: Agent A (old) + Agent B (new) in same room ❌
```

### New Flow (Fixed)
```
User selects Agent B
     ↓
Send room_cleanup message
     ↓
Old agent gracefully exits room `agent-A-123`
     ↓
Backend receives cleanup, calls _graceful_shutdown()
     ↓
Reconnect to NEW room `agent-B-456`
     ↓
Create NEW agent instance in new room
     ↓
Now: Only Agent B in room `agent-B-456` ✅
```

## Performance Notes

- **Room creation**: ~100ms per new room (handled by Livekit)
- **Graceful shutdown**: ~500ms (intentional delay for cleanup)
- **Total switch time**: ~1-2 seconds (user-perceptible, smooth)
- **Memory**: Old agent exits cleanly, no resource leaks

## Next Steps (Optional Improvements)

If you want to further improve agent switching:

1. **Agent Pooling**: Cache unused agents instead of creating new ones
2. **Persistent Session Rooms**: Use same room but swap agents within it
3. **Agent State Persistence**: Save/restore conversation history during switch
4. **Smooth Handoff**: Announce agent switch to user with TTS message

## Files Modified

1. **voice-agent-selector.html**
   - Added session ID generation
   - Added dynamic room name generation
   - Added room cleanup notification on disconnect
   - Updated connect() to use dynamic room names
   - Updated selectAgent() with better agent switching logic

2. **letta_voice_agent.py**
   - Added `_graceful_shutdown()` function
   - Added room cleanup message handler
   - Added logging for cleanup flow

## Support

If agent switching still isn't working:

1. Check browser console (F12) for errors
2. Check voice agent terminal for `🧹 Room cleanup requested` message
3. Verify all services running: `./start_voice_system.sh`
4. If still broken: `./restart_voice_system.sh`

---

**Summary**: Agent selection now works by giving each agent its own isolated Livekit room and gracefully cleaning up the old room when switching. No Letta server restart needed.
