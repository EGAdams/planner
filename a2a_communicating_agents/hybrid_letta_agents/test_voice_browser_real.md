# Real Browser Voice Agent Testing Guide

This guide will help you debug why the voice agent doesn't respond in the real Windows browser even though automated tests pass.

## CRITICAL ARCHITECTURE UNDERSTANDING

The voice pipeline works like this:

1. **Browser (Windows)** - User speaks into microphone
2. **LiveKit Client (JavaScript)** - Captures audio, publishes to LiveKit
3. **LiveKit Server (WSL)** - Routes audio streams between participants
4. **Voice Agent (Python)** - Receives audio, does STT → Letta → TTS → sends audio back
5. **LiveKit Server** - Routes agent audio back to browser
6. **Browser** - Plays agent's voice response

The issue is likely in steps 1-3 (browser → LiveKit connectivity).

## STEP 1: Verify Services Are Running

```bash
# Check all services are running
ps aux | grep -E "(letta_voice_agent|livekit|cors_proxy)" | grep -v grep

# Expected output:
# - livekit-server --dev --bind 0.0.0.0
# - python letta_voice_agent_optimized.py dev
# - python cors_proxy_server.py
```

If any are missing, start them:
```bash
./start_voice_system.sh
```

## STEP 2: Access the DEBUG Version

Open in your Windows browser:
```
http://localhost:9000/debug
```

This debug version has:
- Comprehensive logging of all events
- Visual microphone status indicator
- Real-time audio publishing status
- Detailed error messages

## STEP 3: Watch for These Key Events

When you click "Connect", watch the debug console for these events IN ORDER:

### Expected Success Flow:
```
[timestamp] 📝 Checking microphone availability...
[timestamp] ✅ Found 1 microphone device(s):
[timestamp] ✅ Microphone permissions granted
[timestamp] 🔗 Creating LiveKit room...
[timestamp] ✅ Signal connection established
[timestamp] ✅ Room connected successfully
[timestamp] 🎤 Enabling microphone...
[timestamp] ✅ Microphone enabled successfully!
[timestamp] 📤 Local track published: audio (microphone)
[timestamp] ✅ AUDIO TRACK IS NOW PUBLISHING TO LIVEKIT!
[timestamp] ⏰ Waiting 15s for agent to join...
[timestamp] 👤 Participant connected: voice-agent
[timestamp] ✅ Agent is already in the room!
```

### Check the Microphone Status Indicator:
- Should show: **"ACTIVE"** (green, pulsing)
- If it shows "Not publishing" → microphone track not being published
- If it shows "Permission granted" but not "ACTIVE" → track creation failed

## STEP 4: Common Failure Patterns

### Pattern 1: Microphone Permission Denied
**Debug log shows:**
```
❌ Microphone permission denied: NotAllowedError
```

**Solution:**
- Check browser settings (chrome://settings/content/microphone)
- Make sure localhost:9000 is allowed
- Try clicking the microphone icon in address bar

### Pattern 2: Microphone Track Not Publishing
**Debug log shows:**
```
✅ Microphone enabled successfully!
```
But does NOT show:
```
📤 Local track published: audio (microphone)
```

**This is the likely issue!** The microphone is enabled but not publishing.

**Solution:** Check browser console (F12) for WebRTC errors:
```javascript
// Look for errors like:
// - getUserMedia failed
// - Track ended unexpectedly
// - RTC peer connection failed
```

### Pattern 3: Agent Doesn't Join
**Debug log shows:**
```
⏰ Waiting 15s for agent to join...
⏱️ Agent join timeout! No agent joined the room.
```

**Solution:** Check voice agent logs:
```bash
# In WSL terminal
tail -f /tmp/letta_voice_agent.log

# Look for:
# - "Job request received for room: agent-..."
# - "Job accepted, starting entrypoint..."
# - "Voice agent starting in room: ..."
```

### Pattern 4: No Audio Received From Agent
**Debug log shows:**
```
✅ Agent is already in the room!
```
But when you speak, no response comes back.

**Solution:** Check voice agent logs for STT activity:
```bash
tail -f /tmp/letta_voice_agent.log | grep "User message"

# You should see:
# "🎤 User message: [your spoken text]"
```

If you don't see this, the agent is NOT receiving your audio.

## STEP 5: Manual Audio Track Verification

Open browser console (F12) and run:
```javascript
// Check if audio track is publishing
const room = window.room; // Access the LiveKit room
const audioTrack = room.localParticipant.getTrackPublication('microphone');
console.log('Audio track:', audioTrack);
console.log('Is muted:', audioTrack?.isMuted);
console.log('Track:', audioTrack?.track);

// Check all local tracks
console.log('Local tracks:', Array.from(room.localParticipant.trackPublications.values()));
```

Expected output:
```javascript
Audio track: TrackPublication { ... }
Is muted: false
Track: LocalAudioTrack { ... }
Local tracks: [TrackPublication { source: 'microphone', kind: 'audio' }]
```

If track is null or muted, that's the issue!

## STEP 6: Force Microphone Re-activation

Try this in browser console (F12):
```javascript
// Disconnect and reconnect
await disconnect();
await new Promise(r => setTimeout(r, 2000));
await connect();
```

## STEP 7: Check LiveKit Server Logs

In WSL terminal:
```bash
# Check LiveKit server logs
journalctl -u livekit-server -f

# Or if running in terminal:
tail -f /tmp/livekit.log
```

Look for:
- Room creation: `room created name=agent-...`
- Participant joined: `participant joined`
- Track published: `track published kind=audio`

If you don't see "track published kind=audio", the browser is not sending audio to LiveKit.

## STEP 8: Network Connectivity Test

The issue might be Windows → WSL networking. Test WebSocket connectivity:

In browser console (F12):
```javascript
// Test WebSocket connection
const ws = new WebSocket('ws://localhost:7880');
ws.onopen = () => console.log('✅ WebSocket connected!');
ws.onerror = (e) => console.error('❌ WebSocket error:', e);
ws.onclose = () => console.log('WebSocket closed');
```

If WebSocket fails to connect, the issue is networking between Windows and WSL.

**Solution for WSL networking:**
```bash
# In WSL, check if ports are bound to 0.0.0.0 (not 127.0.0.1)
netstat -tlnp | grep -E "(7880|8283|9000)"

# Should show:
# 0.0.0.0:7880  (not 127.0.0.1:7880)
# 0.0.0.0:8283
# 0.0.0.0:9000
```

If bound to 127.0.0.1, restart LiveKit with:
```bash
./livekit-server --dev --bind 0.0.0.0
```

## STEP 9: Compare with Working Test

The automated tests work because they use fake audio. Let's see what's different:

**Automated test (WORKS):**
- Creates fake audio track programmatically
- No real microphone involved
- Audio is generated, not captured

**Real browser (FAILS):**
- Uses real getUserMedia() API
- Requires microphone permissions
- Audio must be captured and published

The difference is REAL microphone capture vs FAKE audio generation.

## MOST LIKELY ROOT CAUSE

Based on the symptoms (automated tests work, real browser doesn't), the issue is:

**The browser is enabling the microphone but NOT publishing the audio track to LiveKit.**

This happens when:
1. getUserMedia() succeeds
2. setMicrophoneEnabled(true) succeeds
3. But the audio track is never actually published to the room

**Fix:** Force explicit track publishing in the connection code.

## STEP 10: Try Manual Track Publishing

In browser console after connecting:
```javascript
// Get microphone stream manually
const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
const audioTrack = stream.getAudioTracks()[0];

// Create LiveKit audio track
const track = await room.localParticipant.createAudioTrack(audioTrack);

// Publish it
await room.localParticipant.publishTrack(track);

console.log('✅ Manually published audio track!');
```

If this works, the fix is to modify the connection code to explicitly publish tracks.

## DEBUGGING SUMMARY

1. Use the DEBUG version: http://localhost:9000/debug
2. Watch for "AUDIO TRACK IS NOW PUBLISHING" message
3. Check microphone status indicator (should be green "ACTIVE")
4. Open browser console (F12) and check for WebRTC errors
5. Verify audio track is published (see Step 5)
6. Check voice agent logs for STT activity
7. Test WebSocket connectivity (see Step 8)

## NEXT STEPS

After running through these steps, report back with:
1. What debug messages you see (screenshot helpful)
2. What the microphone status indicator shows
3. Any errors in browser console
4. Whether manual track publishing (Step 10) works

This will pinpoint exactly where the audio pipeline is breaking.
