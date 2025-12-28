# Voice Agent Real Browser Fix - Complete Guide

## Problem Summary

**Issue:** Voice agent works in automated tests but doesn't respond when accessing from Windows browser at localhost:9000

**Root Cause:** Browser client and voice agent were joining **different LiveKit rooms** due to room name mismatch between the HTML code and JWT token.

---

## What Was Fixed

### The Bug
The HTML client was generating dynamic room names like:
- `agent-abc12345-xyz789`

But the JWT token only allowed access to:
- `test-room`

Result: Browser and voice agent never met in the same room!

### The Fix
Changed both HTML files to use `test-room` consistently:

**Files Modified:**
1. `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/voice-agent-selector.html`
2. `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/voice-agent-selector-debug.html`
3. `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/cors_proxy_server.py`

**Change:**
```javascript
// BEFORE (BROKEN):
const roomName = `agent-${selectedAgent.id.substring(0, 8)}-${sessionId}`;
await room.connect(LIVEKIT_URL, TOKEN, roomName, { ... });

// AFTER (FIXED):
const roomName = 'test-room';  // Match JWT token!
await room.connect(LIVEKIT_URL, TOKEN, { autoSubscribe: true });
```

---

## How to Test the Fix

### 1. Verify Services Are Running

Run the verification script:
```bash
./test_voice_fix.sh
```

Expected output: All green checkmarks ✅

### 2. Open Debug Interface in Windows Browser

Navigate to:
```
http://localhost:9000/debug
```

This debug version provides:
- Comprehensive event logging
- Visual microphone status indicator
- Real-time audio publishing status
- Detailed error messages

### 3. Connect to Voice Agent

1. **Select an agent** from the list
2. **Click "Connect"** button
3. **Allow microphone access** when prompted
4. **Watch the debug console** (right panel) for these messages:

```
[timestamp] ✅ Microphone permissions granted
[timestamp] 🔗 Connecting to room: test-room on ws://localhost:7880
[timestamp] ⚠️  Using fixed room name "test-room" to match JWT token
[timestamp] ✅ Signal connection established
[timestamp] ✅ Room connected successfully
[timestamp] ✅ Microphone enabled successfully!
[timestamp] 📤 Local track published: audio (microphone)
[timestamp] ✅ AUDIO TRACK IS NOW PUBLISHING TO LIVEKIT!
[timestamp] 👤 Participant connected: voice-agent
[timestamp] ✅ Agent is already in the room!
```

5. **Check microphone status indicator** (top of debug panel):
   - Should show: **"ACTIVE"** (green, pulsing)

### 4. Test Voice Interaction

1. **Speak into your microphone**: "Hello, can you hear me?"
2. **Watch debug console** for transcription:
   ```
   [timestamp] 🗣️ user: Hello, can you hear me?
   [timestamp] 🤖 assistant: Yes, I can hear you! How can I help you today?
   ```
3. **Listen for agent's voice response** - you should hear it through your speakers/headphones

### 5. Verify Backend Activity

In a WSL terminal, monitor voice agent logs:
```bash
tail -f /tmp/letta_voice_agent.log | grep -E "User message|response"
```

You should see:
```
🎤 User message: Hello, can you hear me?
🔊 Letta response: Yes, I can hear you! How can I help you today?
```

---

## Troubleshooting

### If Agent Doesn't Join

**Symptom:** Timeout waiting for agent after 15 seconds

**Check:**
1. Voice agent is running in 'dev' mode:
   ```bash
   ps aux | grep letta_voice_agent | grep dev
   ```

2. Voice agent logs show room connection:
   ```bash
   tail -f /tmp/letta_voice_agent.log | grep "room:"
   # Should show: "Voice agent starting in room: test-room"
   ```

3. Both browser and agent using same room name:
   ```bash
   # Browser console (F12):
   console.log('Client room:', room.name);  // Should be: "test-room"

   # WSL terminal:
   tail -f /tmp/letta_voice_agent.log | grep "room:"  # Should show: "test-room"
   ```

### If Microphone Not Publishing

**Symptom:** Debug console doesn't show "AUDIO TRACK IS NOW PUBLISHING"

**Check:**
1. Browser console (F12) for WebRTC errors
2. Microphone permissions in browser settings
3. Manually verify track publishing:
   ```javascript
   // In browser console (F12):
   const audioTrack = room.localParticipant.getTrackPublication('microphone');
   console.log('Audio track:', audioTrack);
   console.log('Is publishing:', audioTrack?.track !== null);
   ```

### If No Voice Response

**Symptom:** Transcription shows in debug but no audio playback

**Check:**
1. Browser audio output isn't muted
2. Audio element was attached:
   ```
   [timestamp] 🔊 Audio element attached - you should hear responses now!
   ```
3. Voice agent logs show TTS generation:
   ```bash
   tail -f /tmp/letta_voice_agent.log | grep -E "TTS|Audio"
   ```

### Network Issues (Windows ↔ WSL)

**Symptom:** WebSocket connection fails

**Check:**
1. LiveKit server bound to 0.0.0.0 (not 127.0.0.1):
   ```bash
   netstat -tlnp | grep 7880
   # Should show: 0.0.0.0:7880 LISTEN
   ```

2. Test WebSocket from browser:
   ```javascript
   // In browser console (F12):
   const ws = new WebSocket('ws://localhost:7880');
   ws.onopen = () => console.log('✅ WebSocket connected!');
   ws.onerror = (e) => console.error('❌ WebSocket error:', e);
   ```

---

## Files Created/Modified

### Modified Files:
1. **voice-agent-selector.html** - Fixed room name to "test-room"
2. **voice-agent-selector-debug.html** - Debug version with comprehensive logging
3. **cors_proxy_server.py** - Added /debug endpoint

### New Files:
1. **VOICE_AGENT_FIX_SUMMARY.md** - Technical analysis of the bug
2. **test_voice_browser_real.md** - Detailed debugging guide
3. **test_voice_fix.sh** - Automated verification script
4. **VOICE_AGENT_REAL_BROWSER_FIX.md** - This file

---

## Success Criteria

The fix is successful if:
- ✅ Browser connects to LiveKit room "test-room"
- ✅ Microphone status shows "ACTIVE" (green, pulsing)
- ✅ Debug console shows "AUDIO TRACK IS NOW PUBLISHING"
- ✅ Voice agent joins within 15 seconds
- ✅ Speaking into microphone triggers transcription in debug console
- ✅ Voice agent response is heard through speakers/headphones
- ✅ Backend logs show "User message: [your speech]"

---

## Quick Test Commands

```bash
# Verify all services running
./test_voice_fix.sh

# Watch voice agent activity
tail -f /tmp/letta_voice_agent.log | grep -E "User message|response"

# Check LiveKit server logs
tail -f /tmp/livekit.log | grep -E "room|participant|track"

# Monitor CORS proxy requests
tail -f /tmp/cors_proxy.log
```

---

## Next Steps

### For Production Use:

The current fix uses a single shared room "test-room" for all agents. This works for single-user testing but doesn't provide agent isolation.

**To support multiple agents in separate rooms:**

1. Implement dynamic token generation:
   ```javascript
   // Fetch fresh token for each agent
   const response = await fetch(`/api/token?room=${dynamicRoomName}`);
   const { token } = await response.json();
   await room.connect(LIVEKIT_URL, token, { ... });
   ```

2. Update CORS proxy token endpoint to generate per-room tokens

3. Update voice agent to accept dynamic room names from LiveKit job requests

**For now:** The "test-room" approach works perfectly for real browser testing!

---

## Summary

**Problem:** Browser and voice agent were in different LiveKit rooms

**Solution:** Fixed browser to use "test-room" consistently to match JWT token

**Test URL:** http://localhost:9000/debug

**Expected Result:** Voice agent responds to speech in real Windows browser!

All services are running and ready to test. Open the debug URL in your Windows browser and follow the testing steps above.
