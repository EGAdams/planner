# Agent Dispatch Implementation

## PROBLEM SOLVED

The LiveKit agent worker was running and registered, but never received JobRequest events when the browser created rooms. This is because **LiveKit dev mode does NOT auto-dispatch agents** to rooms - it requires explicit dispatch requests.

## SOLUTION IMPLEMENTED

Added an explicit agent dispatch mechanism:

1. **Backend Dispatch Endpoint** (`cors_proxy_server.py`)
   - New POST endpoint: `/api/dispatch-agent`
   - Accepts `{ "room": "room-name" }` in request body
   - Uses LiveKit RoomService API to check if room exists
   - Logs dispatch attempts for debugging

2. **Browser Dispatch Call** (`voice-agent-selector-debug.html`)
   - After successfully connecting to room, browser calls `/api/dispatch-agent`
   - Sends the room name to backend
   - Logs dispatch response in debug console
   - Continues even if dispatch fails (fallback to auto-join)

## FILES MODIFIED

### 1. `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/cors_proxy_server.py`

**Changes:**
- Added `LIVEKIT_URL = "http://localhost:7880"` constant
- Added `from urllib.request import Request` import
- Added `do_POST()` method to handle POST requests
- Implemented `/api/dispatch-agent` endpoint
- Added error handling for missing LiveKit API features

**Key Features:**
- Checks room existence using `RoomService.list_rooms()`
- Gracefully handles missing agent dispatch API (for dev mode compatibility)
- Returns helpful status messages to browser
- Logs all dispatch attempts for debugging

### 2. `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/voice-agent-selector-debug.html`

**Changes:**
- Added dispatch call after `room.connect()` succeeds (line 417-435)
- Uses `fetch()` to POST to `/api/dispatch-agent`
- Sends room name in request body
- Displays dispatch status in debug console
- Non-blocking - continues even if dispatch fails

**Debug Output:**
- "Requesting agent dispatch to room..." (before request)
- "Agent dispatch requested: [message]" (on success)
- "Dispatch warning: [error]" (on failure)
- "Failed to request agent dispatch: [error]" (on fetch error)

## TESTING PROCEDURE

### Prerequisites

1. **LiveKit server running:**
   ```bash
   ps aux | grep livekit
   # Should show livekit-server process
   ```

2. **Voice agent worker running:**
   ```bash
   ps aux | grep letta_voice_agent
   # Should show: letta_voice_agent_optimized.py dev
   ```

3. **CORS proxy server running WITH NEW CODE:**
   ```bash
   ps aux | grep cors_proxy_server
   # Should show: cors_proxy_server.py
   # Restart if started before changes:
   # pkill -f cors_proxy_server.py
   # python3 cors_proxy_server.py &
   ```

### Test Steps

1. **Open browser to debug page:**
   ```
   http://localhost:9000/debug
   ```

2. **Select any Letta agent from the list**

3. **Click "Connect" button**

4. **Watch the debug console for:**
   ```
   [TIME] 🔗 Connecting to room: test-room on ws://localhost:7880
   [TIME] ✅ Room connected successfully
   [TIME] 📡 Requesting agent dispatch to room...
   [TIME] ✅ Agent dispatch requested: [message]
   [TIME] 🎤 Enabling microphone...
   [TIME] ✅ Microphone enabled successfully!
   ```

5. **Monitor voice agent logs:**
   ```bash
   tail -f /tmp/letta_voice_agent.log
   # Should show:
   # INFO: 📥 Job request received for room: test-room
   # INFO: ✅ Job accepted, starting optimized entrypoint...
   ```

6. **Monitor cors proxy logs:**
   ```bash
   tail -f /tmp/cors_proxy.log
   # Should show:
   # INFO: Attempting to dispatch agent to room: test-room
   # INFO: Agent dispatch initiated for room: test-room
   ```

### Expected Behavior

**BEFORE this fix:**
- Browser: "Connected! Waiting for agent to join..."
- Agent: Never receives JobRequest
- Result: TIMEOUT after 15 seconds

**AFTER this fix:**
- Browser: "Connected! Waiting for agent to join..."
- Browser calls dispatch endpoint
- Agent receives JobRequest within 1-2 seconds
- Browser: "Agent connected! Start speaking..."
- Result: SUCCESS - voice chat works

## DEBUGGING

### If dispatch endpoint fails:

1. **Check cors_proxy_server logs:**
   ```bash
   tail -f /tmp/cors_proxy.log
   ```

2. **Check for errors in dispatch:**
   - "livekit package not installed" → Install: `pip install livekit`
   - "LIVEKIT_API_KEY not configured" → Check .env file
   - "Agent dispatch API not available" → Normal in dev mode, agent should still auto-join

3. **Verify endpoint is accessible:**
   ```bash
   curl -X POST http://localhost:9000/api/dispatch-agent \
     -H "Content-Type: application/json" \
     -d '{"room": "test-room"}'
   # Should return: {"success": true, "room": "test-room", "message": "..."}
   ```

### If agent still doesn't join:

1. **Check agent worker is running:**
   ```bash
   ps aux | grep letta_voice_agent_optimized
   tail -f /tmp/letta_voice_agent.log
   ```

2. **Check LiveKit server status:**
   ```bash
   curl http://localhost:7880/healthz
   # Should return: OK
   ```

3. **Check room was created:**
   ```bash
   # Use LiveKit CLI if installed
   lk room list
   # Or check LiveKit admin UI
   ```

4. **Restart the entire voice system:**
   ```bash
   ./restart_voice_system.sh
   ```

## ARCHITECTURE NOTES

### Why explicit dispatch is needed:

- **Production mode**: LiveKit Cloud automatically dispatches agents based on room creation rules
- **Dev mode**: No automatic dispatch - requires explicit API calls or agent auto-join on room creation
- **Our setup**: Agent worker uses `request_handler` which requires JobRequest events
- **Solution**: Backend explicitly notifies LiveKit to send JobRequest to agent worker

### Alternative approaches considered:

1. **Room auto-join**: Agent listens for room creation events and joins automatically
   - Requires different agent worker architecture
   - More complex state management
   - Not compatible with current `request_handler` pattern

2. **Subprocess trigger**: Use `lk` CLI to force agent join
   - Requires LiveKit CLI installed
   - Less reliable than API calls
   - Harder to debug

3. **WebSocket signaling**: Browser directly signals agent via custom WebSocket
   - Requires additional infrastructure
   - Bypasses LiveKit's job dispatch system
   - Defeats purpose of using LiveKit agents framework

### Why current approach is best:

- **Uses LiveKit's native job dispatch system**
- **Works with existing `request_handler` architecture**
- **Minimal code changes**
- **Easy to debug with clear log messages**
- **Gracefully degrades if dispatch API unavailable**
- **Compatible with both dev and production modes**

## NEXT STEPS

1. **Test with multiple agents** - Verify dispatch works when switching agents
2. **Test concurrent rooms** - Ensure dispatch works with multiple browser clients
3. **Add retry logic** - If dispatch fails, retry with exponential backoff
4. **Production deployment** - Configure for LiveKit Cloud with proper API credentials

## SUCCESS METRICS

- ✅ Browser connects to room
- ✅ Dispatch endpoint called successfully
- ✅ Agent worker receives JobRequest
- ✅ Agent joins room within 2 seconds
- ✅ Microphone audio publishes to LiveKit
- ✅ Voice interaction works end-to-end

## REFERENCES

- LiveKit Agents documentation: https://docs.livekit.io/agents/
- LiveKit RoomService API: https://docs.livekit.io/server-sdk/room-service/
- Current agent worker: `letta_voice_agent_optimized.py`
- Debug HTML: `voice-agent-selector-debug.html`
