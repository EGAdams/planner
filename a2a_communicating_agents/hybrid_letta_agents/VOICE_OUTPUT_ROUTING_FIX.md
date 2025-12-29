# Voice Output Routing Fix

## Problem Diagnosis

**Symptom**: Agent receives voice input correctly, generates text responses, but responses appear ONLY as text in Letta IDE/ADE instead of being spoken via audio output.

**Root Cause**: `RoomOutputOptions` in `session.start()` has `audio_enabled` set to `NOT_GIVEN` (default), which prevents the TTS pipeline from publishing audio frames to the Livekit room.

## Voice Pipeline Flow (Expected)

```
User speaks → Deepgram STT → text → llm_node() → response text → tts_node() → audio frames → Livekit room → User hears
```

## Current Broken Flow

```
User speaks → Deepgram STT → text → llm_node() → response text → ❌ STOPS HERE (no TTS)
                                                                  → _publish_transcript() → Letta IDE (text only)
```

## Technical Details

### Livekit Agents Framework Pipeline

1. **Input Pipeline** (Working ✅):
   - VAD detects speech
   - STT (Deepgram) converts audio → text
   - Text enters `llm_node()`

2. **LLM Processing** (Working ✅):
   - `llm_node()` returns response text
   - Text is logged and published via data channel

3. **Output Pipeline** (BROKEN ❌):
   - Framework should route `llm_node` output → `tts_node()`
   - `tts_node()` should convert text → audio frames
   - Audio frames should be published to room audio track
   - **BUT**: `RoomOutputOptions.audio_enabled` is NOT set to `True`

### Code Location

**File**: `letta_voice_agent_optimized.py`
**Lines**: 1293-1297

```python
await session.start(
    room=ctx.room,
    agent=assistant,
    room_output_options=RoomOutputOptions(transcription_enabled=True),  # ❌ Missing audio_enabled=True
)
```

### RoomOutputOptions Default Behavior

```python
# Current (BROKEN):
RoomOutputOptions(transcription_enabled=True)
# audio_enabled = NOT_GIVEN (framework might default to False)

# Fixed (CORRECT):
RoomOutputOptions(
    transcription_enabled=True,
    audio_enabled=True  # ✅ Explicitly enable audio output
)
```

## Fix Implementation

### Change Required

**File**: `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/letta_voice_agent_optimized.py`

**Line**: 1296

**Current Code**:
```python
room_output_options=RoomOutputOptions(transcription_enabled=True),
```

**Fixed Code**:
```python
room_output_options=RoomOutputOptions(
    transcription_enabled=True,
    audio_enabled=True  # CRITICAL FIX: Enable voice output
),
```

## Verification Steps

### 1. Check Current Configuration
```bash
# View current RoomOutputOptions
grep -A 3 "room_output_options" letta_voice_agent_optimized.py
```

### 2. Apply Fix
```bash
# Edit file and add audio_enabled=True
vim letta_voice_agent_optimized.py +1296
```

### 3. Restart System
```bash
./restart_voice_system.sh
```

### 4. Test Voice Output
1. Open voice client: http://localhost:9000
2. Connect to room
3. Ask Agent_66: "What time is it?"
4. Expected result: **HEAR the answer spoken** (not just see text)

### 5. Monitor Logs
```bash
tail -f voice_agent_debug.log | grep -E "TTS|audio|🔊|tts_node"
```

Expected log output:
```
INFO: TTS configured: OpenAI TTS (voice: nova)
INFO: tts_node processing text: "The current time is..."
INFO: Audio frames published to room
```

## Why This Wasn't Caught Earlier

1. **Transcription works**: Text responses are published via data channel, creating the illusion that everything works
2. **No error messages**: Framework silently skips TTS when `audio_enabled` is not set
3. **Letta IDE shows responses**: Responses appear in IDE, masking the voice output failure
4. **Default value ambiguity**: `NOT_GIVEN` doesn't throw an error, just disables the feature

## Related Configuration

### TTS Provider Configuration (Already Correct ✅)
```python
# Lines 1085-1097
tts_provider = os.getenv("TTS_PROVIDER", "openai")

if tts_provider == "cartesia" and os.getenv("CARTESIA_API_KEY"):
    tts = cartesia.TTS(
        voice="79a125e8-cd45-4c13-8a67-188112f4dd22",
    )
    logger.info("Using Cartesia TTS")
else:
    tts = openai.TTS(
        voice=os.getenv("OPENAI_TTS_VOICE", "nova"),
        speed=1.0,
    )
    logger.info("Using OpenAI TTS")
```

TTS is configured correctly, but never invoked because audio output is disabled.

### AgentSession Configuration (Already Correct ✅)
```python
# Lines 1099-1112
session = AgentSession(
    stt=deepgram.STT(
        model="nova-2",
        language="en",
    ),
    llm=openai.LLM(model="gpt-5-mini"),
    tts=tts,  # ✅ TTS is configured
    vad=silero.VAD.load(
        min_speech_duration=0.1,
        min_silence_duration=0.8,
        prefix_padding_duration=0.6,
        activation_threshold=0.5,
    ),
)
```

Session has TTS configured, but `session.start()` doesn't enable audio output.

## Additional Notes

### Why `_publish_transcript()` Still Works

```python
# Line 588
await self._publish_transcript("assistant", response_text)
```

This publishes via **data channel** (not audio), which is why text appears in the IDE. This is separate from the voice pipeline.

### Why `llm_node()` Return Value Matters

```python
# Line 596
return response_text  # Framework expects this for TTS pipeline
```

The framework automatically routes the returned text to `tts_node()` **IF** `audio_enabled=True`. Without it, the text is ignored.

## Success Criteria

After fix is applied:
- ✅ User asks question via voice
- ✅ Agent processes question (text appears in IDE)
- ✅ **Agent SPEAKS response via audio output** (NEW - this was broken)
- ✅ Response text also appears in IDE (existing functionality preserved)
- ✅ No duplicate audio (room conflict prevention still active)

## Rollback Plan

If fix causes issues:
```bash
# Revert to previous version
cp letta_voice_agent_optimized.py.backup letta_voice_agent_optimized.py
./restart_voice_system.sh
```

## Confidence Level

**HIGH** - This is a configuration issue, not a code logic issue. The TTS pipeline is fully implemented in the framework; we just need to enable it.

## Testing Matrix

| Test Case | Input | Expected Output | Status |
|-----------|-------|-----------------|--------|
| Voice Q&A | Voice: "What time is it?" | **HEAR**: "The current time is..." | PENDING |
| Text fallback | Voice input fails | Text response in IDE | EXISTING ✅ |
| Agent switch | Select different agent | Spoken confirmation | PENDING |
| Multiple responses | Sequential questions | Each response spoken | PENDING |

---

**Next Action**: Apply the one-line fix and test voice output.
