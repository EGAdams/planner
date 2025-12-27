# Voice Agent No Response Issue - Root Cause Analysis

**Date**: December 21, 2025
**Issue**: No voice response after connecting to agent on localhost:9000
**Status**: ✅ ROOT CAUSE IDENTIFIED

---

## 🔍 Root Cause

**OpenAI API Authentication Failure (401 Unauthorized)**

The voice agent is failing to generate TTS (Text-to-Speech) output because the OpenAI API key is either:
1. **Invalid or expired**
2. **Lacks the necessary permissions** for TTS/audio endpoints
3. **Has exceeded quota limits**

### Evidence from Logs (`/tmp/voice_agent.log`)

```
ERROR:livekit.agents:Error in _tts_inference_task
httpx.HTTPStatusError: Client error '401 Unauthorized' for url 'https://api.openai.com/v1/audio/speech'
```

**What This Means:**
- ✅ STT (Speech-to-Text) is working - Deepgram connection is successful
- ✅ Letta orchestrator connection is working - Agent found and initialized
- ✅ Livekit WebSocket connection is working - Room joined successfully
- ❌ **TTS (Text-to-Speech) is FAILING** - OpenAI API rejecting requests

---

## 🧪 System Status Check

### Components Working ✅
1. **Letta Server**: Running on `localhost:8283` (PID 1059)
2. **Livekit Server**: Running on `localhost:7880` (PID 5327)
3. **Voice Agent Process**: Running (PID 1484)
4. **Deepgram STT**: WebSocket connection established
5. **Agent Selection**: Agent_66 found and loaded

### Component Failing ❌
**OpenAI TTS API**: Returning `401 Unauthorized`

---

## 📊 Environment Configuration

### API Key Status
```
OpenAI API Key: ✅ Present (164 characters)
Key Format: sk-proj-... (project-scoped key)
Location 1: /home/adamsl/planner/.env
Location 2: /home/adamsl/ottomator-agents/livekit-agent/.env
```

### TTS Provider Configuration
```python
# letta_voice_agent.py:718-730
tts_provider = os.getenv("TTS_PROVIDER", "openai")  # Default: "openai"

if tts_provider == "cartesia" and os.getenv("CARTESIA_API_KEY"):
    tts = cartesia.TTS(...)
else:
    tts = openai.TTS(
        voice=os.getenv("OPENAI_TTS_VOICE", "nova"),
        speed=1.0,
    )
```

**Currently Using**: OpenAI TTS (because Cartesia not configured)

---

## 🔧 Recommended Fixes (Priority Order)

### Option 1: Fix OpenAI API Key (Recommended if you want OpenAI TTS)

**Steps:**
1. **Verify API key validity**:
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

2. **Check if key has TTS permissions**:
   - Log into OpenAI dashboard
   - Verify API key has **"Audio" endpoints** enabled
   - Check quota/billing status

3. **Update the key** (if invalid):
   ```bash
   # In /home/adamsl/planner/.env and /home/adamsl/ottomator-agents/livekit-agent/.env
   OPENAI_API_KEY=sk-proj-YOUR_NEW_KEY_HERE
   ```

4. **Restart voice system**:
   ```bash
   ./restart_voice_system.sh
   ```

### Option 2: Switch to Cartesia TTS (Alternative, Fast Voice)

**Advantages**:
- Ultra-low latency (<200ms)
- High-quality voices
- More cost-effective for voice applications

**Steps:**
1. **Get Cartesia API key** from https://cartesia.ai
2. **Configure environment**:
   ```bash
   # Add to both .env files
   TTS_PROVIDER=cartesia
   CARTESIA_API_KEY=your_cartesia_key_here
   ```
3. **Restart**:
   ```bash
   ./restart_voice_system.sh
   ```

### Option 3: Use Local TTS (No API Required)

**For testing/development without API costs:**

Edit `letta_voice_agent.py:718-730` to use a local TTS:
```python
# Option: Use local Silero TTS (no API key needed)
from livekit.plugins import silero

tts = silero.TTS()  # Local TTS, no authentication required
```

**Pros**: Free, no API key required
**Cons**: Lower quality, higher latency than cloud TTS

---

## 🧪 Testing the Fix

After applying any fix, test with:

```bash
# 1. Check the logs show successful TTS initialization
tail -f /tmp/voice_agent.log | grep -E "(TTS|audio|speech)"

# 2. Connect to localhost:9000 in browser
# 3. Select Agent_66
# 4. Click Connect
# 5. Speak into microphone
# 6. Check for:
#    - "🎤 User message: ..." in logs
#    - "🔊 Letta response: ..." in logs
#    - NO "401 Unauthorized" errors
```

---

## 📝 Complete Fix Checklist

- [ ] Identify which TTS provider to use (OpenAI vs Cartesia vs Local)
- [ ] Obtain/verify API key for chosen provider
- [ ] Update both .env files:
  - `/home/adamsl/planner/.env`
  - `/home/adamsl/ottomator-agents/livekit-agent/.env`
- [ ] Restart voice system: `./restart_voice_system.sh`
- [ ] Check logs for TTS initialization: `tail -f /tmp/voice_agent.log`
- [ ] Test voice connection at http://localhost:9000
- [ ] Verify agent responds with voice

---

## 🎯 Quick Fix Command (OpenAI Key Update)

```bash
# 1. Edit the .env files
nano /home/adamsl/planner/.env
nano /home/adamsl/ottomator-agents/livekit-agent/.env

# 2. Update this line (use your valid key):
# OPENAI_API_KEY=sk-proj-YOUR_VALID_KEY_HERE

# 3. Restart
./restart_voice_system.sh

# 4. Monitor
tail -f /tmp/voice_agent.log
```

---

## 📞 What's Actually Happening

**Current Flow** (BROKEN at step 6):
1. User connects → ✅ Browser joins Livekit room
2. Microphone → ✅ Audio sent to room
3. STT → ✅ Deepgram transcribes speech to text
4. Orchestrator → ✅ Letta receives text, processes request
5. Response Generation → ✅ Letta generates text response
6. **TTS** → ❌ OpenAI TTS fails with 401 (NO AUDIO OUTPUT)
7. User hears → ❌ Nothing (because step 6 failed)

**Expected Flow** (after fix):
1. User connects → ✅ Browser joins Livekit room
2. Microphone → ✅ Audio sent to room
3. STT → ✅ Deepgram transcribes speech to text
4. Orchestrator → ✅ Letta receives text, processes request
5. Response Generation → ✅ Letta generates text response
6. **TTS** → ✅ OpenAI/Cartesia converts text to speech audio
7. User hears → ✅ Audio played through browser

---

## 🔗 Related Files

- **Main Agent**: `letta_voice_agent.py:718-730` (TTS configuration)
- **Logs**: `/tmp/voice_agent.log` (PID 1484 stdout/stderr)
- **Frontend**: `voice-agent-selector.html` (localhost:9000)
- **Environment**:
  - `/home/adamsl/planner/.env`
  - `/home/adamsl/ottomator-agents/livekit-agent/.env`

---

**Conclusion**: The issue is NOT a bug in your code - it's a simple API authentication failure. Once you update the OpenAI API key (or switch to Cartesia), voice responses will work immediately.
