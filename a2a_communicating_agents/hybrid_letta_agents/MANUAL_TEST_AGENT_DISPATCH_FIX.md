# Manual Testing Guide - Agent Dispatch Fix

## Quick Verification (2 minutes)

### Prerequisites
1. Voice system is running: `./start_voice_system.sh`
2. Agent worker is active: `ps aux | grep letta_voice_agent`
3. LiveKit server is running: `ps aux | grep livekit-server`

### Test Steps

1. **Open Browser**
   ```
   Navigate to: http://localhost:9000/voice-agent-selector-debug.html
   ```

2. **Open Browser Console** (F12 or Right-click → Inspect → Console)

3. **Select an Agent**
   - Click on any agent in the list
   - Agent card should highlight
   - "Connect" button should enable

4. **Click Connect**

5. **Watch Debug Console** (right panel in the HTML page)

### Expected Results (AFTER FIX)

**Within 2 seconds you should see:**

```
[18:55:01] 🎤 Checking microphone availability...
[18:55:01] ✅ Found 1 microphone device(s):
[18:55:01]   1. Default Microphone (default)
[18:55:01] ✅ Microphone permissions granted
[18:55:01] 🔗 Creating LiveKit room...
[18:55:01] ✅ Signal connection established
[18:55:02] ✅ Room connected successfully
[18:55:02] ✅ Microphone enabled successfully!
[18:55:02] 👥 Existing participants in room: 1
[18:55:02] 👤 Existing participant detected: agent-AJ_NchnwDLwWVyr
[18:55:02] ✅ Agent is already in the room!
```

**Status banner should show:**
```
Agent "YourAgentName" connected! Start speaking...
```

**Microphone status indicator should show:**
```
ACTIVE (green, pulsing)
```

### What This Proves

1. ✅ Agent dispatch worked (agent joined room)
2. ✅ Browser detected existing agent (no timeout)
3. ✅ Race condition fix is working
4. ✅ Ready for voice interaction

### Expected Results (BEFORE FIX - for comparison)

If the fix wasn't applied, you would see:

```
[18:55:01] ... (same initial setup) ...
[18:55:02] ✅ Room connected successfully
[18:55:02] 👥 Existing participants in room: 1
[18:55:02] ⏰ Waiting 15s for agent to join...
[18:55:17] ⏱️ Agent join timeout! No agent joined the room.
```

Status would show:
```
Agent didn't join. Retrying (1/3) in 1s...
```

This proves the agent WAS already in the room, but the browser failed to detect it.

## Advanced Debugging

### Check Agent is Actually in Room

**Terminal 1:** Monitor agent logs
```bash
tail -f /tmp/letta_voice_agent.log | grep -E "Job request|joined room"
```

**Expected:**
```
INFO: 📥 Job request received for room: test-room
INFO: ✅ Job accepted, starting optimized entrypoint...
INFO: 🎙️ Agent joined room: test-room
```

**Terminal 2:** Check room state
```bash
/home/adamsl/planner/.venv/bin/python3 << 'PYTHON_EOF'
from livekit_room_manager import RoomManager
import asyncio

async def check():
    manager = RoomManager()
    rooms = await manager.list_rooms()
    for room in rooms:
        print(f"Room: {room.name}, Participants: {room.num_participants}")
        participants = await manager.list_participants(room.name)
        for p in participants:
            print(f"  - {p.identity}")

asyncio.run(check())
PYTHON_EOF
```

**Expected:**
```
Room: test-room, Participants: 2
  - user1
  - agent-AJ_NchnwDLwWVyr
```

### Check LiveKit Server Logs

```bash
tail -f /tmp/livekit.log | grep -E "agent-"
```

**Expected:**
```
DEBUG livekit received signal request ... participant: "agent-AJ_NchnwDLwWVyr"
DEBUG livekit handling signal request ... participant: "agent-AJ_NchnwDLwWVyr"
```

Ping requests every 5 seconds prove agent is actively connected.

## Troubleshooting

### Issue: "No microphone devices found"
**Solution:** Plug in a microphone or use a virtual audio device

### Issue: "Agent didn't join" even after fix
**Possible causes:**
1. Agent worker crashed - check: `ps aux | grep letta_voice_agent`
2. LiveKit server down - check: `ps aux | grep livekit-server`
3. Wrong room name - verify browser uses "test-room"
4. Token mismatch - regenerate token: `./update_voice_token.sh`

**Debug:**
```bash
# Restart entire system
./restart_voice_system.sh

# Check all components
ps aux | grep -E "livekit|letta_voice"

# Check logs
tail -f /tmp/letta_voice_agent.log
tail -f /tmp/livekit.log
```

### Issue: Agent joins but no audio
**Different issue** - This is about audio processing, not agent dispatch
**Check:**
1. Microphone is enabled in browser (should see "ACTIVE" indicator)
2. Audio tracks are being published (check debug console)
3. Agent is receiving audio (check agent logs for STT events)

## Success Criteria

- ✅ Browser shows "Agent connected!" within 2 seconds
- ✅ No timeout errors
- ✅ Debug console shows "Existing participant detected"
- ✅ Microphone status shows "ACTIVE"
- ✅ Can proceed to voice interaction

## Test Matrix

| Scenario | Before Fix | After Fix |
|----------|-----------|-----------|
| Agent joins before browser | ❌ Timeout | ✅ Detected |
| Agent joins after browser | ✅ Works | ✅ Works |
| Multiple reconnections | ❌ Often fails | ✅ Works |
| Fresh room creation | ✅ Works | ✅ Works |
| Existing room with agent | ❌ Timeout | ✅ Detected |

## Conclusion

The fix ensures the browser correctly detects agents regardless of join timing. This is a critical improvement for production reliability, as agent dispatch timing can vary based on system load.

**Fix Status:** ✅ Implemented in `voice-agent-selector-debug.html`
**Testing:** Automated test available in `test_agent_dispatch_fix.py`
**Documentation:** See `AGENT_DISPATCH_COMPLETE_SOLUTION.md` for full analysis
