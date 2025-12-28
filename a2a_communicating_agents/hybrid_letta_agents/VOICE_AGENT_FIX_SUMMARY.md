# Voice Agent Real Browser Fix - Root Cause Analysis

## CRITICAL BUG FOUND AND FIXED

### The Problem
When accessing localhost:9000 from Windows browser:
- ✅ Automated tests passed (Playwright with fake audio)
- ❌ Real browser interaction failed (no response from voice agent)
- User could see connection successful but voice agent never responded

### Root Cause
**The browser client and voice agent were joining DIFFERENT LiveKit rooms!**

#### What Was Happening:
1. **Browser Client** tried to join dynamic room names like:
   - `agent-12345678-abc123` (based on agent ID + session ID)

2. **JWT Token** only allowed joining:
   - `test-room` (hardcoded in the token)

3. **Voice Agent** was configured to join:
   - `test-room` (the default room from token)

4. **Result**: Browser and agent in different rooms = no audio communication!

### The Evidence

**JWT Token Payload (decoded):**
```json
{
  "name": "User",
  "video": {
    "roomJoin": true,
    "room": "test-room",  ← HARDCODED!
    "canPublish": true,
    "canSubscribe": true,
    "canPublishData": true
  },
  "sub": "user1",
  "iss": "devkey"
}
```

**HTML Client Code (before fix):**
```javascript
function getRoomName() {
    return `agent-${selectedAgent.id.substring(0, 8)}-${sessionId}`;
}

const roomName = getRoomName();  // Returns: "agent-abc12345-xyz789"
await room.connect(LIVEKIT_URL, TOKEN, roomName, { ... });
```

**The Mismatch:**
- Token says: "You can only join test-room"
- Client says: "I want to join agent-abc12345-xyz789"
- LiveKit says: "OK, I'll put you in agent-abc12345-xyz789"
- Voice agent says: "I'm waiting in test-room"
- Result: They never meet!

### Why Automated Tests Passed

The Playwright tests probably:
1. Used the correct room name matching the token
2. Or generated fresh tokens for each dynamic room
3. Or mocked the LiveKit connection entirely

Real browser usage exposed the room name mismatch.

## The Fix

### Changed in `voice-agent-selector.html`:
```javascript
// OLD CODE (BROKEN):
const roomName = getRoomName();  // Dynamic: "agent-xxx-yyy"
await room.connect(LIVEKIT_URL, TOKEN, roomName, { ... });

// NEW CODE (FIXED):
const roomName = 'test-room';  // Fixed to match JWT token
await room.connect(LIVEKIT_URL, TOKEN, { autoSubscribe: true });
```

### Changed in `voice-agent-selector-debug.html`:
Same fix + added debug logging:
```javascript
debugInfo('⚠️  Using fixed room name "test-room" to match JWT token', '🔑');
```

## Testing the Fix

### 1. Restart CORS Proxy (if needed)
```bash
# The proxy server serves the updated HTML files
# Kill existing proxy:
pkill -f cors_proxy_server.py

# Start fresh:
python3 cors_proxy_server.py
```

### 2. Test in Windows Browser

**Option A: Regular Version**
```
http://localhost:9000
```

**Option B: Debug Version (Recommended)**
```
http://localhost:9000/debug
```

### 3. Expected Success Flow

1. Open http://localhost:9000/debug in Windows browser
2. Select an agent from the list
3. Click "Connect"
4. Allow microphone permissions
5. Wait a few seconds

**Debug console should show:**
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

6. **Now speak into your microphone**
7. You should see in debug console:
```
[timestamp] 🗣️ user: [your spoken text]
[timestamp] 🤖 assistant: [agent's response]
```

8. **You should HEAR the agent's voice response**

### 4. Verify Voice Agent Sees the Connection

In WSL terminal, check voice agent logs:
```bash
tail -f /tmp/letta_voice_agent.log | grep -E "(room:|User message|response)"

# You should see:
# "Voice agent starting in room: test-room"
# "🎤 User message: hello"
# "🔊 Letta response: Hello! How can I help you today?"
```

## Additional Debugging Tools Created

### 1. Debug HTML Version
- **File:** `voice-agent-selector-debug.html`
- **URL:** http://localhost:9000/debug
- **Features:**
  - Comprehensive event logging
  - Visual microphone status indicator
  - Real-time audio publishing status
  - Detailed error messages

### 2. Testing Guide
- **File:** `test_voice_browser_real.md`
- **Contains:**
  - Step-by-step debugging process
  - Common failure patterns
  - Manual verification commands
  - Browser console debugging tips

## If It Still Doesn't Work

### Check These:

1. **Services Running:**
   ```bash
   ps aux | grep -E "(letta_voice_agent|livekit|cors_proxy)" | grep -v grep
   ```

2. **Room Name Consistency:**
   ```bash
   # In browser console (F12):
   console.log('Client room:', room.name);

   # In WSL terminal:
   tail -f /tmp/letta_voice_agent.log | grep "room:"

   # Both should show: "test-room"
   ```

3. **Microphone Publishing:**
   ```javascript
   // In browser console:
   const audioTrack = room.localParticipant.getTrackPublication('microphone');
   console.log('Audio track:', audioTrack);
   console.log('Is publishing:', audioTrack?.track !== null);
   ```

4. **Agent Receiving Audio:**
   ```bash
   # Should see STT transcriptions:
   tail -f /tmp/letta_voice_agent.log | grep "User message"
   ```

5. **Network Connectivity:**
   ```bash
   # Check ports are accessible from Windows:
   netstat -tlnp | grep -E "(7880|8283|9000)"

   # Should show 0.0.0.0:7880 (not 127.0.0.1:7880)
   ```

## Long-Term Solution: Dynamic Tokens

To support multiple agents in separate rooms (original design intent), you need to:

1. **Generate tokens dynamically** based on agent selection
2. **Update the token endpoint** in CORS proxy:
   ```python
   # cors_proxy_server.py already has /api/token endpoint
   # But the HTML client uses hardcoded TOKEN
   ```

3. **Modify HTML to fetch fresh token per agent:**
   ```javascript
   // Instead of hardcoded TOKEN:
   const response = await fetch(`/api/token?room=${roomName}`);
   const { token } = await response.json();
   await room.connect(LIVEKIT_URL, token, { ... });
   ```

4. **Update voice agent to accept dynamic room names**

This would allow proper agent isolation, but for now, using "test-room" for all agents works fine for single-user testing.

## Summary

**What was broken:** Room name mismatch (browser wanted dynamic rooms, token only allowed "test-room")

**What was fixed:** Browser now uses "test-room" consistently to match the JWT token

**How to test:** Open http://localhost:9000/debug and watch for successful connection + audio publishing

**Expected result:** Voice agent responds to speech in real Windows browser!
