# Letta Voice Agent - Root Cause Analysis Report
**Date**: December 23, 2025
**System**: Letta Voice Agent with Livekit Integration
**Issue**: Agent receives voice input but does not respond with voice output

---

## Executive Summary

The Letta Voice Agent system is experiencing **TWO critical issues** that prevent voice responses:

1. **PRIMARY ISSUE**: Letta API streaming parameter mismatch causing 422 errors
2. **SECONDARY ISSUE**: Agent session timing issue when agent selection occurs

The system successfully:
- ✅ Accepts microphone input from browser
- ✅ Transcribes speech via Deepgram STT
- ✅ Sends messages to Letta orchestrator
- ✅ Receives text responses from Letta

But FAILS to:
- ❌ Return voice responses to user
- ❌ Handle agent switching correctly when session is starting

---

## Issue #1: Letta API Streaming Parameter Mismatch

### Root Cause

**File**: `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/letta_voice_agent.py`
**Lines**: 404-409

The code attempts to enable streaming with incorrect parameters:

```python
# Line 404-409 - INCORRECT
response = await asyncio.to_thread(
    self.letta_client.agents.messages.create,
    agent_id=self.agent_id,
    messages=[{"role": "user", "content": user_message}],
    stream_tokens=True  # ❌ WRONG: requires streaming=True to be set first
)
```

### Error from Letta Server

```
HTTP/1.1 422 Unprocessable Entity
{
  "detail": "Streaming options set without streaming enabled.
             stream_tokens can only be true when streaming=true.
             Either set streaming=true or use default values for streaming options."
}
```

### Evidence from Logs

```
INFO:__mp_main__:🎤 User message: What were we working on?
INFO:__mp_main__:PRE-CALL to _get_letta_response
INFO:__mp_main__:Attempting to call Letta server with streaming...
ERROR:__mp_main__:Error in streaming response, falling back: Error code: 422 -
  {'detail': 'Streaming options set without streaming enabled...'}
```

### Consequence

1. Initial streaming call fails with 422
2. System falls back to non-streaming `_get_letta_response()`
3. Non-streaming call succeeds and returns response
4. **However**, by this time the user may have disconnected or agent session may be in wrong state

### Fix Required

**Option A**: Enable proper streaming (RECOMMENDED)
```python
# Line 404-409 - CORRECTED
response = await asyncio.to_thread(
    self.letta_client.agents.messages.create,
    agent_id=self.agent_id,
    messages=[{"role": "user", "content": user_message}],
    streaming=True,        # ✅ ADD THIS
    stream_tokens=True
)
```

**Option B**: Disable streaming altogether (SIMPLER, but slower)
```python
# Line 404-409 - SIMPLIFIED
response = await asyncio.to_thread(
    self.letta_client.agents.messages.create,
    agent_id=self.agent_id,
    messages=[{"role": "user", "content": user_message}]
    # Remove stream_tokens parameter entirely
)
```

---

## Issue #2: Agent Session Timing - "AgentSession isn't running"

### Root Cause

**File**: `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/letta_voice_agent.py`
**Lines**: 509-542 (`switch_agent` method)

When agent selection message arrives from the UI, the code tries to call `self._agent_session.say()` at line 536:

```python
# Line 534-536
switch_message = f"Switched to agent {agent_name or new_agent_id}. How can I help you?"
await self._publish_transcript("system", switch_message)
await self._agent_session.say(switch_message, allow_interruptions=True)  # ❌ FAILS
```

But the `AgentSession` is not yet running because:
1. Agent selection happens immediately when user connects
2. Session is still initializing at that moment
3. `session.start()` is called AFTER the event handlers are registered

### Evidence from Logs

```
INFO:__mp_main__:🔄 Agent selection request: Agent_66 (agent-4dfca708-49a8-4982-8e36-0f1146f9a66e)
INFO:__mp_main__:✅ Switched from agent agent-4dfca708... to agent-4dfca708... (Agent_66)
ERROR:__mp_main__:Error switching agent: AgentSession isn't running
```

### Timeline of Events

```
1. User clicks "Connect" in browser
2. Browser sends agent_selection data message
3. on_data_received() fires → switch_agent() called
4. switch_agent() tries to call session.say() ← FAILS because session not started yet
5. session.start() is called (line 857)
6. Agent is ready but user already saw error or disconnected
```

### Fix Required

**Option A**: Guard the `say()` call with session state check
```python
# Line 534-536 - CORRECTED
switch_message = f"Switched to agent {agent_name or new_agent_id}. How can I help you?"
await self._publish_transcript("system", switch_message)

# Only call say() if session is running
if hasattr(self._agent_session, 'started') and self._agent_session.started:
    await self._agent_session.say(switch_message, allow_interruptions=True)
else:
    logger.warning("Session not yet started, skipping voice announcement")
```

**Option B**: Defer agent selection until session is ready
```python
# Modify entrypoint to only process agent selection after session.start()
# Store pending agent_id and process it after session.start() completes
```

**Option C**: Make switch_message silent initially (SIMPLEST)
```python
# Line 534-536 - SIMPLIFIED
switch_message = f"Switched to agent {agent_name or new_agent_id}. How can I help you?"
await self._publish_transcript("system", switch_message)
# Remove the say() call entirely - user will see text message only
```

---

## Issue #3: Minor - Graceful Shutdown Error

### Root Cause

**File**: `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/letta_voice_agent.py`
**Line**: 739

```python
# Line 739 - INCORRECT
await ctx.room.local_participant.flush()
```

The `LocalParticipant` object doesn't have a `flush()` method.

### Evidence from Logs

```
INFO:__mp_main__:⏳ Initiating graceful shutdown...
ERROR:__mp_main__:Error during graceful shutdown: 'LocalParticipant' object has no attribute 'flush'
```

### Fix Required

```python
# Line 729-745 - CORRECTED
async def _graceful_shutdown(ctx: JobContext):
    """Gracefully shut down the voice agent when user requests cleanup."""
    try:
        logger.info("⏳ Initiating graceful shutdown...")
        # Remove invalid flush() call
        # await ctx.room.local_participant.flush()  # ❌ REMOVE THIS

        # Just disconnect directly
        await ctx.room.disconnect()
        logger.info("✅ Graceful shutdown complete")
    except Exception as e:
        logger.error(f"Error during graceful shutdown: {e}")
```

---

## Verified Working Components

Based on log analysis, the following components are functioning correctly:

1. **PostgreSQL**: Running
2. **Letta Server**: Running on port 8283, responding to requests
3. **Livekit Server**: Running on port 7880
4. **Voice Agent Process**: Running (PID 420)
5. **CORS Proxy**: Serving UI on port 9000
6. **Browser Connection**: Successfully connecting to Livekit room
7. **Microphone Input**: Audio being captured and sent
8. **Deepgram STT**: Successfully transcribing speech
   - Example: "What were we working on?" was correctly transcribed
9. **Letta Orchestrator**: Receiving messages and generating responses
   - Letta generated a detailed response about recent work
10. **Data Channel**: Messages being sent/received between browser and agent

---

## What's NOT Working

1. **TTS Voice Output**: No evidence of text being converted to speech and played
2. **Agent Switching**: Fails when session isn't ready
3. **Streaming API**: 422 error due to incorrect parameters

---

## Complete Sequence of Events (Current Behavior)

```
1. User opens http://localhost:9000
2. User selects Agent_66
3. User clicks "Connect"
4. Browser → Livekit: Join room "agent-xxxxx-sessionID"
5. Browser → Livekit: Send agent_selection data message
6. Voice Agent → Livekit: Accept job, join room
7. Voice Agent: on_data_received() fires with agent_selection
8. Voice Agent: Calls switch_agent(Agent_66)
9. ❌ ERROR: switch_agent() tries to call session.say() but session not started yet
10. Voice Agent: session.start() is called
11. Voice Agent: "✅ Voice agent ready and listening"
12. User speaks: "What were we working on?"
13. Deepgram: ✅ Transcribes successfully
14. Voice Agent: llm_node() is called with transcribed text
15. Voice Agent: ❌ Calls Letta with stream_tokens=True without streaming=True
16. Letta Server: ❌ Returns 422 Unprocessable Entity
17. Voice Agent: Falls back to non-streaming _get_letta_response()
18. Letta Server: ✅ Returns full response (435 tokens)
19. Voice Agent: "🔊 Letta response: Short summary — recent work..."
20. ❌ STOPS HERE - No TTS synthesis happens
21. User disconnects (no voice response heard)
22. Voice Agent: Attempts graceful shutdown
23. ❌ ERROR: flush() method doesn't exist
24. Voice Agent: Successfully disconnects
```

---

## Expected Sequence (After Fixes)

```
1-11. [Same as above]
12. User speaks: "What were we working on?"
13. Deepgram: ✅ Transcribes successfully
14. Voice Agent: llm_node() is called
15. Voice Agent: ✅ Calls Letta with streaming=True and stream_tokens=True
16. Letta Server: ✅ Streams response tokens
17. Voice Agent: ✅ Receives streamed response
18. Voice Agent: ✅ Calls session.say() with response text
19. OpenAI TTS: ✅ Converts text to speech
20. Livekit: ✅ Streams audio to browser
21. User: ✅ HEARS the voice response
22. [System continues to accept more input]
```

---

## Recommended Fix Priority

### Priority 1: Fix Streaming API Parameters (CRITICAL)
This is the root cause preventing responses. Apply **Option B** (disable streaming) first for immediate fix:

```python
# File: letta_voice_agent.py, lines 404-409
# Change:
response = await asyncio.to_thread(
    self.letta_client.agents.messages.create,
    agent_id=self.agent_id,
    messages=[{"role": "user", "content": user_message}]
    # Remove stream_tokens=True entirely
)
```

### Priority 2: Fix Agent Session Timing (HIGH)
Apply **Option C** (remove say() call) to prevent errors:

```python
# File: letta_voice_agent.py, line 536
# Comment out or remove:
# await self._agent_session.say(switch_message, allow_interruptions=True)
```

### Priority 3: Fix Graceful Shutdown (LOW)
Remove the invalid flush() call:

```python
# File: letta_voice_agent.py, line 739
# Remove or comment out:
# await ctx.room.local_participant.flush()
```

---

## Testing the Fixes

After applying fixes:

1. **Restart the voice agent**:
   ```bash
   cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
   ./restart_voice_system.sh
   ```

2. **Monitor logs in real-time**:
   ```bash
   tail -f /tmp/voice_agent.log | grep -E "(🎤|🔊|ERROR|streaming|say\()"
   ```

3. **Test in browser**:
   - Open http://localhost:9000
   - Select Agent_66
   - Click Connect
   - Allow microphone
   - Speak a simple question: "Hello, can you hear me?"

4. **Expected behavior**:
   - See "🎤 User message: Hello, can you hear me?"
   - See "🔊 Letta response: ..."
   - HEAR voice response in browser
   - No ERROR messages in logs

---

## Files Requiring Changes

1. **letta_voice_agent.py** (3 changes):
   - Line 404-409: Fix streaming parameters
   - Line 536: Fix or remove session.say() call
   - Line 739: Remove flush() call

Total changes: ~5 lines across 1 file

---

## Additional Observations

1. The fallback to non-streaming IS working, so the system is partially functional
2. The Letta response is being generated successfully (seen in logs)
3. The issue is NOT with API keys or authentication (those are all working)
4. The issue is NOT with Deepgram STT (transcription working perfectly)
5. The issue IS with the streaming API call and TTS pipeline execution

---

## Conclusion

The voice agent is **very close to working**. The core pipeline is functional - speech is transcribed, Letta responds with intelligent text. Only the TTS output stage needs fixing, which requires correcting the streaming API call parameters. The fixes are simple and straightforward.

**Estimated time to fix**: 5-10 minutes
**Complexity**: Low (parameter changes only)
**Risk**: Low (only affects streaming behavior, fallback already works)
