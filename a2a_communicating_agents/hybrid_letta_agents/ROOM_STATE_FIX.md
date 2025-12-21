# LiveKit Room State Fix - Permanent Solution

## Problem
Voice agent would show "Waiting for agent to join..." because LiveKit's room state would get out of sync when:
- Agents restart but LiveKit keeps running
- Multiple agents register simultaneously
- Agent registration happens before LiveKit is fully ready

## Root Cause
LiveKit maintains room and participant state. When agents crash/restart while LiveKit keeps running, old room state persists and prevents new agent dispatch.

## Permanent Solution Implemented

### 1. Always Restart LiveKit Fresh
**Both `start_voice_system.sh` and `restart_voice_system.sh` now:**
- Force kill LiveKit (not just graceful stop)
- Clean up room state directory (`/tmp/livekit/`)
- Truncate old logs
- Start LiveKit completely fresh

### 2. Proper Startup Sequence with Delays
```
1. Kill all voice agents
2. Force kill and clean LiveKit
3. Start LiveKit → WAIT 3 seconds (fully ready)
4. Start voice agent → WAIT 5 seconds (agent registers)
5. Verify registration succeeded
6. Continue with CORS proxy, etc.
```

### 3. Verify Agent Registration
Scripts now check that the agent successfully registered with LiveKit before declaring "system ready":
```bash
if grep -q "registered worker" /tmp/letta_voice_agent.log; then
    echo "✓ Voice agent registered with LiveKit"
else
    echo "⚠️  Voice agent running but registration not confirmed"
fi
```

### 4. Duplicate Prevention
Emergency duplicate killer runs at the end:
- Counts running agents
- Kills duplicates automatically
- Ensures exactly ONE agent survives

## Files Modified
1. `restart_voice_system.sh` - Complete clean restart
2. `start_voice_system.sh` - Fresh start with room cleanup
3. `letta_voice_agent_groq.py` - Fixed API methods and error handling

## How To Use

### Normal Restart
```bash
./restart_voice_system.sh
```
This now guarantees:
- Clean LiveKit state
- Single voice agent
- Proper registration timing
- No room conflicts

### After Code Changes
```bash
./restart_voice_system.sh  # Always use this
```

## Prevention Checklist

✅ **LiveKit always force restarted** (not conditional)
✅ **Room state cleaned** (`/tmp/livekit/` removed)
✅ **Logs truncated** (fresh start every time)
✅ **3-second LiveKit warmup** (prevents race conditions)
✅ **5-second agent registration** (ensures LiveKit sees agent)
✅ **Registration verification** (confirms agent is ready)
✅ **Duplicate detection & cleanup** (ensures single agent)

## Why This Works

**Before:** LiveKit kept old room state → agent couldn't join existing rooms → "Waiting for agent..."

**After:** Fresh LiveKit every restart → clean room state → agent dispatches to new rooms → works instantly

## Monitoring

Watch for successful registration:
```bash
tail -f /tmp/letta_voice_agent.log | grep "registered worker"
```

Should see:
```
INFO:livekit.agents:registered worker {"workerID": "AW_xxxxx"}
```

## Troubleshooting

If still stuck on "Waiting for agent...":

1. Check agent registered:
```bash
grep "registered worker" /tmp/letta_voice_agent.log
```

2. Check only ONE agent running:
```bash
ps aux | grep "letta_voice_agent_groq.py dev" | grep -v grep | wc -l
```

3. Check LiveKit sees agent:
```bash
grep "worker registered" /tmp/livekit.log
```

4. Force clean restart:
```bash
pkill -9 -f "livekit\|letta_voice"
./restart_voice_system.sh
```

## Additional Improvements Made

### Fixed in `letta_voice_agent_groq.py`:
1. ✅ `agents.get()` API (was using wrong method)
2. ✅ Removed `flush()` call (doesn't exist in LocalParticipant)
3. ✅ Added comprehensive error handling in `llm_node`
4. ✅ Added timing measurements for debugging

### Shell Script Enhancements:
1. ✅ Room cleanup on every restart
2. ✅ Duplicate detection and automatic removal
3. ✅ Registration verification before "ready" status
4. ✅ Proper startup sequencing with delays

---

**Last Updated:** 2025-12-19
**Status:** Tested and Working
**Prevents:** Room state conflicts, duplicate agents, race conditions
