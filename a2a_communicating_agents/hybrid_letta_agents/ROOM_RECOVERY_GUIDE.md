# Room Recovery System - Complete Guide

## Problem Solved

**Issue**: Voice agent system gets stuck showing "Waiting for agent to join..." indefinitely.

**Root Cause**: LiveKit rooms can get into bad states when:
- Agents crash without properly disconnecting
- Users close browsers without cleanup
- Network issues cause partial disconnections
- Previous sessions leave stale participants in rooms

**Solution**: Automatic room self-recovery system that:
1. Cleans up stale rooms on startup
2. Removes stuck participants before agent joins
3. Detects timeout and auto-retries with fresh rooms
4. Provides graceful cleanup on disconnect

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Room Recovery Flow                       │
└─────────────────────────────────────────────────────────────┘

1. STARTUP (start_voice_system.sh)
   ├─ Kill existing LiveKit server
   ├─ Clean LiveKit data directory
   ├─ Run RoomManager.cleanup_stale_rooms()
   │  ├─ Find rooms older than 5 minutes with no participants
   │  ├─ Find participants stuck in rooms > 5 minutes
   │  └─ Delete/remove stale entities
   └─ Start fresh LiveKit server

2. AGENT JOIN (request_handler in voice agent)
   ├─ Receive job request for room
   ├─ Run RoomManager.ensure_clean_room(room_name)
   │  ├─ Check if room exists
   │  ├─ If room has participants, remove them
   │  ├─ If cleanup fails, force delete room
   │  └─ Return clean state
   └─ Accept job and join room

3. CLIENT CONNECTION (voice-agent-selector.html)
   ├─ User clicks "Connect"
   ├─ Connect to room
   ├─ Start 15-second timeout timer
   ├─ On agent join: Clear timer, reset retries
   ├─ On timeout:
   │  ├─ Retry 1: Wait 1s, reconnect with new room
   │  ├─ Retry 2: Wait 2s, reconnect with new room
   │  ├─ Retry 3: Wait 3s, reconnect with new room
   │  └─ After 3 failures: Show error with troubleshooting

4. DISCONNECT (graceful shutdown)
   ├─ Client sends room_cleanup message
   ├─ Agent receives message
   ├─ Agent disconnects gracefully
   └─ Room cleanup happens automatically
```

## Components

### 1. RoomManager (`livekit_room_manager.py`)

Core room management utility with methods:

- `list_rooms()` - List all active rooms
- `get_room_info(room_name)` - Get room details
- `list_participants(room_name)` - List participants in room
- `remove_participant(room_name, identity)` - Remove specific participant
- `delete_room(room_name)` - Delete entire room
- `cleanup_stale_rooms()` - Remove stale rooms/participants
- `ensure_clean_room(room_name)` - Prepare room for agent join
- `cleanup_room(room_name, force)` - Manual cleanup

### 2. Voice Agent Integration

**File**: `letta_voice_agent.py` and `letta_voice_agent_groq.py`

**Modified**: `request_handler()` function

**What it does**:
- Before accepting a job request, runs `ensure_clean_room()`
- Removes any stuck participants from the room
- Ensures clean state before agent joins
- Logs all recovery actions

**Code**:
```python
async def request_handler(job_request: JobRequest):
    room_name = job_request.room.name

    # Clean up stale participants before joining
    try:
        from livekit_room_manager import RoomManager
        manager = RoomManager()
        await manager.ensure_clean_room(room_name)
    except Exception as e:
        logger.warning(f"Room cleanup failed: {e}")

    await job_request.accept()
```

### 3. Startup Script Integration

**File**: `start_voice_system.sh`

**Added**: Proactive room cleanup step

**What it does**:
- Runs `RoomManager.cleanup_stale_rooms()` on startup
- Removes stale rooms from previous sessions
- Prevents accumulation of stuck rooms

**Code**:
```bash
# Proactive room cleanup
python3 << 'EOF'
import asyncio
from livekit_room_manager import RoomManager

async def cleanup():
    manager = RoomManager()
    await manager.cleanup_stale_rooms()

asyncio.run(cleanup())
EOF
```

### 4. Client-Side Timeout Detection

**File**: `voice-agent-selector.html`

**Added**:
- 15-second timeout for agent join
- Automatic retry with exponential backoff (1s, 2s, 3s)
- Fresh room generation on each retry
- Error guidance after max retries

**How it works**:
```javascript
// When waiting for agent
agentJoinTimer = setTimeout(async () => {
    if (connectionRetries < MAX_RETRIES) {
        connectionRetries++;

        // Disconnect and generate new room
        await disconnect();
        sessionId = Math.random().toString(36).substring(7);

        // Retry with backoff
        setTimeout(() => connect(), 1000 * connectionRetries);
    } else {
        // Show error and troubleshooting steps
    }
}, AGENT_JOIN_TIMEOUT);
```

## Configuration

### Environment Variables

Set in `.env` file:

```bash
# LiveKit connection
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret

# Room recovery settings (optional)
ROOM_STALE_TIMEOUT=300  # Seconds before room considered stale (default: 300)
```

### Timeouts

**Stale Room Timeout**: 300 seconds (5 minutes)
- Rooms empty for > 5 minutes are deleted
- Participants in rooms > 5 minutes without activity are removed

**Agent Join Timeout**: 15 seconds
- Client waits 15 seconds for agent to join
- After timeout, retries with fresh room

**Max Retries**: 3
- Client attempts 3 reconnections with exponential backoff
- After 3 failures, shows error with troubleshooting

## Usage

### Testing the System

```bash
# Test room recovery functionality
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
python test_room_recovery.py
```

Expected output:
```
✅ RoomManager initialized
✅ Stale room cleanup complete
✅ Room 'test-recovery-room' is clean and ready
✅ Room Recovery System Test PASSED
```

### Manual Room Cleanup

```bash
# List active rooms
python -c "
import asyncio
from livekit_room_manager import RoomManager

async def main():
    manager = RoomManager()
    rooms = await manager.list_rooms()
    for room in rooms:
        print(f'{room.name}: {room.num_participants} participants')

asyncio.run(main())
"

# Clean all stale rooms
python -c "
import asyncio
from livekit_room_manager import RoomManager

async def main():
    manager = RoomManager()
    await manager.cleanup_stale_rooms()

asyncio.run(main())
"

# Force delete a specific room
python -c "
import asyncio
from livekit_room_manager import RoomManager

async def main():
    manager = RoomManager()
    await manager.delete_room('stuck-room-name')

asyncio.run(main())
"
```

### Starting the System

The recovery system is now automatic:

```bash
# Start voice system (includes room cleanup)
./start_voice_system.sh
```

This will:
1. Stop any running services
2. Clean LiveKit data directory
3. Run stale room cleanup
4. Start fresh LiveKit server
5. Start voice agent (with room recovery enabled)

### Restarting the System

```bash
# Complete clean restart (nuclear option)
./restart_voice_system.sh
```

This is the "nuclear option" that:
1. Kills all processes
2. Cleans all state
3. Runs room cleanup
4. Starts everything fresh

## Troubleshooting

### Issue: "Waiting for agent to join..." Persists

**Symptoms**:
- Client shows "Waiting for agent to join..." for > 15 seconds
- No agent appears in room
- Client automatically retries

**Diagnosis**:
```bash
# Check if voice agent is running
ps aux | grep letta_voice_agent

# Check voice agent logs
tail -f /tmp/letta_voice_agent.log

# Check LiveKit logs
tail -f /tmp/livekit.log

# List active rooms
python -c "
import asyncio
from livekit_room_manager import RoomManager
async def main():
    m = RoomManager()
    rooms = await m.list_rooms()
    print(f'{len(rooms)} active rooms')
    for r in rooms:
        participants = await m.list_participants(r.name)
        print(f'  {r.name}: {len(participants)} participants')
asyncio.run(main())
"
```

**Solutions**:

1. **Voice agent not running**:
   ```bash
   ./restart_voice_system.sh
   ```

2. **Room has stuck participants**:
   ```bash
   # Manual cleanup
   python -c "
   import asyncio
   from livekit_room_manager import RoomManager

   async def main():
       m = RoomManager()
       await m.cleanup_room('stuck-room-name', force=True)

   asyncio.run(main())
   "
   ```

3. **LiveKit server issues**:
   ```bash
   # Restart LiveKit
   pkill -9 -f livekit-server
   rm -rf /tmp/livekit
   cd /home/adamsl/ottomator-agents/livekit-agent
   nohup ./livekit-server --dev --bind 0.0.0.0 > /tmp/livekit.log 2>&1 &
   ```

### Issue: Client Retries Fail After 3 Attempts

**Symptoms**:
- Client shows "Failed to connect after 3 attempts"
- Alert shows troubleshooting steps

**This means**: Voice agent is not responding or not running

**Check**:
```bash
# Is voice agent running?
ps aux | grep letta_voice_agent | grep -v grep

# What's in the voice agent log?
tail -100 /tmp/letta_voice_agent.log

# Is LiveKit running?
ps aux | grep livekit-server | grep -v grep

# Can you connect to LiveKit?
curl -v ws://localhost:7880
```

**Fix**:
```bash
# Complete restart
./restart_voice_system.sh

# Wait for startup (check logs)
tail -f /tmp/letta_voice_agent.log

# Try connecting again
```

### Issue: Rooms Accumulating Over Time

**Symptoms**:
- Many old rooms in list
- Performance degradation

**Check**:
```bash
# Count rooms
python -c "
import asyncio
from livekit_room_manager import RoomManager

async def main():
    m = RoomManager()
    rooms = await m.list_rooms()
    print(f'{len(rooms)} rooms')

asyncio.run(main())
"
```

**Fix**:
```bash
# Run cleanup
python -c "
import asyncio
from livekit_room_manager import RoomManager

async def main():
    m = RoomManager()
    await m.cleanup_stale_rooms()

asyncio.run(main())
"

# Or restart system (includes cleanup)
./restart_voice_system.sh
```

## Logging

Room recovery actions are logged at INFO level:

```
INFO - 🧹 Ensuring room test-room is clean before joining...
INFO - Room test-room has 1 existing participant(s), cleaning them out...
INFO - Removed participant user1 from room test-room
INFO - ✅ Room test-room successfully cleaned
```

Monitor logs:
```bash
# Voice agent logs (includes room recovery)
tail -f /tmp/letta_voice_agent.log | grep -E "🧹|room|participant"

# LiveKit logs
tail -f /tmp/livekit.log

# All logs together
tail -f /tmp/letta_voice_agent.log /tmp/livekit.log
```

## Best Practices

1. **Always use start scripts**: Don't start services manually
   ```bash
   # Good
   ./start_voice_system.sh

   # Bad (skips room cleanup)
   python letta_voice_agent.py dev
   ```

2. **Restart on errors**: If things get stuck, restart everything
   ```bash
   ./restart_voice_system.sh
   ```

3. **Check logs**: Room recovery is logged, check for issues
   ```bash
   grep "🧹" /tmp/letta_voice_agent.log
   ```

4. **Periodic cleanup**: Run cleanup if system running for days
   ```bash
   # Add to cron for daily cleanup at 3am
   0 3 * * * cd /path/to/project && python -c "import asyncio; from livekit_room_manager import RoomManager; asyncio.run(RoomManager().cleanup_stale_rooms())"
   ```

5. **Monitor room count**: Alert if rooms accumulate
   ```bash
   # Check room count
   python -c "import asyncio; from livekit_room_manager import RoomManager; asyncio.run((lambda: print(f'{len(await RoomManager().list_rooms())} rooms'))())"
   ```

## Testing Checklist

Before considering the system fixed, test:

- [ ] Start fresh system: `./start_voice_system.sh`
- [ ] Run test: `python test_room_recovery.py` - should pass
- [ ] Connect from browser - agent should join within 5 seconds
- [ ] Disconnect and reconnect - should work immediately
- [ ] Close browser without disconnect - restart and reconnect should work
- [ ] Kill voice agent, try to connect - should retry and show error after 45 seconds
- [ ] Restart voice agent - should connect immediately
- [ ] Leave system idle for 10 minutes - should cleanup stale rooms
- [ ] Check logs - should see room cleanup messages

## Success Criteria

The room recovery system is working correctly when:

✅ Agent joins room within 5 seconds of client connection
✅ Client auto-retries if agent doesn't join within 15 seconds
✅ Stale rooms are cleaned up on startup
✅ Stuck participants are removed before agent joins
✅ System recovers from crashes automatically
✅ "Waiting for agent to join..." never gets stuck indefinitely

## Summary

The room recovery system provides **4 layers of protection**:

1. **Startup cleanup** - Remove stale rooms before anything runs
2. **Pre-join cleanup** - Ensure clean room before agent joins
3. **Client timeout** - Detect stuck state and retry automatically
4. **Graceful shutdown** - Clean disconnect when user leaves

This makes the system **self-healing** and prevents the "Waiting for agent to join..." issue permanently.
