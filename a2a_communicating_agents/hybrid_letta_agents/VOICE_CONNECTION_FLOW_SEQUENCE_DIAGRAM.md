# Voice Agent Connection Flow - Comprehensive Sequence Diagram

## Overview
This sequence diagram shows the complete flow when a user navigates to http://localhost:9000/voice-agent-selector-debug.html and clicks "Connect" to connect to a Letta voice agent.

## Mermaid Sequence Diagram

```mermaid
sequenceDiagram
    actor User
    participant Browser as Browser<br/>(voice-agent-selector-debug.html)
    participant CORS as CORS Proxy<br/>(cors_proxy_server.py:9000)
    participant LettaAPI as Letta API<br/>(localhost:8283)
    participant LiveKitSvr as LiveKit Server<br/>(localhost:7880)
    participant VoiceAgent as Voice Agent Process<br/>(letta_voice_agent_optimized.py)
    participant AsyncLetta as AsyncLetta Client
    participant OpenAI as OpenAI API

    %% ========================================
    %% SECTION 1: PAGE LOAD AND INITIALIZATION
    %% ========================================

    rect rgb(230, 240, 255)
        Note over User,OpenAI: SECTION 1: PAGE LOAD & AGENT SELECTION

        User->>Browser: Navigate to http://localhost:9000/voice-agent-selector-debug.html
        Browser->>CORS: GET /voice-agent-selector-debug.html
        Note over CORS: do_GET() handler<br/>Serves static HTML file
        CORS-->>Browser: 200 OK (Content-Type: text/html)

        Note over Browser: JavaScript initializes:<br/>- LiveKit client imported<br/>- Token hardcoded (24h validity)<br/>- Room name: "test-room"<br/>- Session ID generated

        Browser->>CORS: GET /api/v1/agents/
        Note over CORS: do_GET() handler<br/>Proxies to Letta API
        CORS->>LettaAPI: GET /v1/agents/
        LettaAPI-->>CORS: 200 OK [agents list]
        CORS-->>Browser: 200 OK (Content-Type: application/json)

        Note over Browser: displayAgents() called:<br/>1. Finds "Agent_66" by name<br/>2. Marks it as "primary-agent"<br/>3. Disables all other agents<br/>4. Auto-selects Agent_66

        Browser->>Browser: selectAgent(Agent_66)
        Note over Browser: Selected agent stored:<br/>selectedAgent = {<br/>  id: "agent-uuid",<br/>  name: "Agent_66"<br/>}

        Note over Browser: LED Status: Agent Selection = GREEN<br/>State Display: Agent ID & Name updated
    end

    %% ========================================
    %% SECTION 2: CONNECT BUTTON CLICK
    %% ========================================

    rect rgb(255, 240, 230)
        Note over User,OpenAI: SECTION 2: CONNECT BUTTON CLICKED

        User->>Browser: Click "Connect" button
        Browser->>Browser: window.connect() invoked

        Note over Browser: LED Status: LiveKit = YELLOW (connecting)<br/>LED Status: Audio Input = YELLOW

        Browser->>Browser: checkMicrophoneAvailability()
        Note over Browser: 1. Check navigator.mediaDevices<br/>2. Enumerate audio devices<br/>3. Request getUserMedia permissions
        Browser-->>Browser: ✅ Microphone permissions granted

        Note over Browser: LED Status: Audio Input = GREEN
    end

    %% ========================================
    %% SECTION 3: LIVEKIT ROOM CONNECTION
    %% ========================================

    rect rgb(240, 255, 240)
        Note over User,OpenAI: SECTION 3: LIVEKIT ROOM CONNECTION

        Browser->>Browser: Create LiveKit Room instance
        Note over Browser: const room = new Room({<br/>  adaptiveStream: true,<br/>  dynacast: true,<br/>  disconnectOnPageLeave: true<br/>})

        Browser->>LiveKitSvr: WebSocket connection to ws://localhost:7880
        Note over LiveKitSvr: Signal server accepts connection
        LiveKitSvr-->>Browser: WebSocket handshake complete

        Note over Browser: RoomEvent.SignalConnected fired<br/>LED Status: WebSocket = GREEN

        Browser->>LiveKitSvr: room.connect(LIVEKIT_URL, TOKEN, {...})
        Note over LiveKitSvr: Validates JWT token:<br/>- Room: "test-room" (hardcoded in token)<br/>- Identity: "user1"<br/>- Permissions: publish, subscribe, data
        LiveKitSvr-->>Browser: Connection accepted

        Note over Browser: RoomEvent.Connected fired<br/>LED Status: LiveKit = GREEN<br/>State Display: Room name = "test-room"
    end

    %% ========================================
    %% SECTION 4: AGENT SELECTION MESSAGE
    %% ========================================

    rect rgb(255, 250, 230)
        Note over User,OpenAI: SECTION 4: AGENT SELECTION MESSAGE SENT

        Note over Browser: RoomEvent.Connected handler triggered again<br/>(lines 554-571)

        Browser->>Browser: Prepare agent_selection message
        Note over Browser: const data = {<br/>  type: "agent_selection",<br/>  agent_id: selectedAgent.id,<br/>  agent_name: selectedAgent.name<br/>}

        Browser->>LiveKitSvr: publishData(agent_selection message)
        Note over Browser: LED Status: Message Send = GREEN (flashes)
        Note over LiveKitSvr: Routes data to room participants

        Note over Browser: ⚠️ CRITICAL POINT:<br/>This message tells the voice agent<br/>which Letta agent to use
    end

    %% ========================================
    %% SECTION 5: AGENT DISPATCH REQUEST
    %% ========================================

    rect rgb(240, 245, 255)
        Note over User,OpenAI: SECTION 5: AGENT DISPATCH REQUEST

        Browser->>CORS: POST /api/dispatch-agent<br/>{room: "test-room"}
        Note over CORS: do_POST() handler (line 153-196)

        CORS->>CORS: Import voice_agent_dispatcher
        Note over CORS: dispatch_agent(room_name) called

        CORS->>VoiceAgent: dispatch_agent_async("test-room")
        Note over VoiceAgent: voice_agent_dispatcher.py

        VoiceAgent->>LiveKitSvr: RoomManager.ensure_clean_room("test-room")
        Note over LiveKitSvr: 1. List participants in room<br/>2. Remove old agent participants<br/>3. Keep human users
        LiveKitSvr-->>VoiceAgent: Room cleaned

        VoiceAgent->>LiveKitSvr: AgentDispatchService.create_dispatch()
        Note over LiveKitSvr: Creates dispatch job:<br/>- Room: "test-room"<br/>- Agent name: "letta-voice-agent"
        LiveKitSvr-->>VoiceAgent: Dispatch ID returned

        VoiceAgent-->>CORS: {success: true, dispatch_id: "..."}
        CORS-->>Browser: 200 OK (dispatch response)
    end

    %% ========================================
    %% SECTION 6: VOICE AGENT STARTUP
    %% ========================================

    rect rgb(255, 245, 245)
        Note over User,OpenAI: SECTION 6: VOICE AGENT PROCESS STARTUP

        Note over LiveKitSvr: LiveKit dispatches job to agent worker

        LiveKitSvr->>VoiceAgent: JobRequest for room "test-room"
        Note over VoiceAgent: request_handler() invoked (line 1404)

        VoiceAgent->>VoiceAgent: Check _ROOM_TO_AGENT dict
        Note over VoiceAgent: ⚠️ CRITICAL CONFLICT CHECK:<br/>If room already assigned, REJECT request<br/>(Prevents multiple agents in one room)

        alt Room already has agent
            VoiceAgent->>LiveKitSvr: job_request.reject()
            Note over VoiceAgent: 🚨 DUPLICATE AGENT PREVENTED
        else Room is available
            VoiceAgent->>VoiceAgent: Assign agent to room<br/>_ROOM_TO_AGENT["test-room"] = agent_id
            VoiceAgent->>LiveKitSvr: job_request.accept()

            VoiceAgent->>VoiceAgent: entrypoint(ctx) invoked (line 1136)

            Note over VoiceAgent: Initialize AsyncLetta client:<br/>- Base URL: http://localhost:8283<br/>- API key from env

            VoiceAgent->>VoiceAgent: get_or_create_orchestrator()
            Note over VoiceAgent: Priority 1: Use PRIMARY_AGENT_ID from env<br/>Priority 2: Search for PRIMARY_AGENT_NAME="Agent_66"

            VoiceAgent->>LettaAPI: AsyncLetta.agents.list()
            LettaAPI-->>VoiceAgent: [list of agents]

            VoiceAgent->>VoiceAgent: Find agent with name="Agent_66"
            Note over VoiceAgent: ⚠️ CRITICAL AGENT SELECTION POINT:<br/>Agent ID determined HERE, not from browser!

            alt Agent_66 found
                Note over VoiceAgent: agent_id = Agent_66.id
            else Agent_66 not found
                VoiceAgent->>LettaAPI: Create new agent "Agent_66"
                LettaAPI-->>VoiceAgent: New agent ID
            end

            VoiceAgent->>VoiceAgent: Check _ACTIVE_AGENT_INSTANCES dict
            Note over VoiceAgent: ⚠️ DUPLICATE INSTANCE CHECK:<br/>Prevent multiple instances of same agent

            alt Agent instance already exists
                Note over VoiceAgent: Reuse existing instance<br/>Call reset_for_reconnect()
            else New agent instance needed
                VoiceAgent->>VoiceAgent: Create LettaVoiceAssistantOptimized instance
                Note over VoiceAgent: Store in _ACTIVE_AGENT_INSTANCES[agent_id]
            end

            VoiceAgent->>VoiceAgent: _load_agent_memory()
            Note over VoiceAgent: ⚠️ MEMORY LOADING (REST API):<br/>- GET /v1/agents/{agent_id}<br/>- Extract memory blocks (persona, etc.)<br/>- Build system instructions

            VoiceAgent->>LettaAPI: GET /v1/agents/{agent_id} (direct REST)
            Note over VoiceAgent: Bypasses AsyncLetta client bug
            LettaAPI-->>VoiceAgent: Agent data with memory blocks

            Note over VoiceAgent: Memory loaded:<br/>- agent_persona<br/>- agent_memory_blocks<br/>- agent_system_instructions

            VoiceAgent->>VoiceAgent: Configure voice pipeline:<br/>- STT: Deepgram nova-2<br/>- LLM: OpenAI gpt-5-mini<br/>- TTS: OpenAI/Cartesia<br/>- VAD: Silero

            VoiceAgent->>LiveKitSvr: Join room "test-room"
            LiveKitSvr-->>Browser: participantConnected event

            Note over Browser: Participant connected:<br/>LED Status: Agent Response = GREEN<br/>Status: "Agent connected! Start speaking..."
        end
    end

    %% ========================================
    %% SECTION 7: AGENT SELECTION MESSAGE RECEIVED
    %% ========================================

    rect rgb(250, 240, 255)
        Note over User,OpenAI: SECTION 7: AGENT PROCESSES SELECTION MESSAGE

        Note over LiveKitSvr: Previously sent agent_selection data<br/>now routed to voice agent

        LiveKitSvr->>VoiceAgent: dataReceived event
        Note over VoiceAgent: on_data_received() handler (line 1343)

        VoiceAgent->>VoiceAgent: Parse JSON message
        Note over VoiceAgent: message_type = "agent_selection"<br/>agent_id = from browser<br/>agent_name = "Agent_66"

        VoiceAgent->>VoiceAgent: assistant.switch_agent(agent_id, agent_name)

        VoiceAgent->>VoiceAgent: Check if agent_name == PRIMARY_AGENT_NAME
        Note over VoiceAgent: ⚠️ AGENT LOCK ENFORCEMENT:<br/>Only "Agent_66" allowed for voice

        alt Agent name matches PRIMARY_AGENT_NAME
            VoiceAgent->>AsyncLetta: agents.retrieve(agent_id)
            AsyncLetta->>LettaAPI: GET /v1/agents/{agent_id}
            LettaAPI-->>AsyncLetta: Agent details
            AsyncLetta-->>VoiceAgent: Agent object

            VoiceAgent->>VoiceAgent: Update self.agent_id = new_agent_id
            VoiceAgent->>VoiceAgent: Clear message_history
            VoiceAgent->>VoiceAgent: Force memory reload:<br/>memory_loaded = False<br/>_load_agent_memory()

            Note over VoiceAgent: ✅ Agent switched successfully<br/>(if agent_id different from initial)

            VoiceAgent->>Browser: publishData("Switched to agent...")
            VoiceAgent->>Browser: TTS: "Switched to agent..."
        else Agent name does NOT match
            Note over VoiceAgent: 🚫 Agent switch REJECTED<br/>Publish warning message
            VoiceAgent->>Browser: publishData("Locked to Agent_66...")
            VoiceAgent->>Browser: TTS: "Locked to Agent_66..."
        end
    end

    %% ========================================
    %% SECTION 8: MICROPHONE ENABLED
    %% ========================================

    rect rgb(245, 255, 245)
        Note over User,OpenAI: SECTION 8: MICROPHONE PUBLISHING

        Browser->>Browser: room.localParticipant.setMicrophoneEnabled(true)
        Browser->>LiveKitSvr: Publish audio track (microphone)
        LiveKitSvr-->>Browser: Track published

        Note over Browser: RoomEvent.LocalTrackPublished fired<br/>LED Status: Audio Input = GREEN<br/>State Display: Audio State = "publishing"

        Browser->>Browser: startAudioLevelMonitoring()
        Note over Browser: Poll every 500ms:<br/>Check if microphone track exists<br/>Update "ACTIVE" indicator

        LiveKitSvr->>VoiceAgent: trackSubscribed event (audio)
        Note over VoiceAgent: STT pipeline starts listening
    end

    %% ========================================
    %% SECTION 9: USER SPEAKS (VOICE QUERY)
    %% ========================================

    rect rgb(255, 255, 230)
        Note over User,OpenAI: SECTION 9: USER SPEAKS - VOICE QUERY PROCESSING

        User->>Browser: User speaks into microphone
        Browser->>LiveKitSvr: Stream audio chunks (WebRTC)
        LiveKitSvr->>VoiceAgent: Audio stream received

        VoiceAgent->>VoiceAgent: Silero VAD detects speech
        Note over VoiceAgent: Voice Activity Detection:<br/>- Min speech: 0.1s<br/>- Min silence: 0.8s<br/>- Threshold: 0.5

        VoiceAgent->>VoiceAgent: Deepgram STT processes audio
        Note over VoiceAgent: Speech-to-Text:<br/>Model: nova-2<br/>Language: en

        VoiceAgent->>VoiceAgent: Text transcription ready
        Note over VoiceAgent: user_message = "transcribed text"

        VoiceAgent->>Browser: publishData({type: "transcript", role: "user"})
        Note over Browser: LED Status: Message Receive = GREEN (flash)

        VoiceAgent->>VoiceAgent: llm_node(chat_ctx, tools, model_settings)
        Note over VoiceAgent: ⚠️ CRITICAL: LLM NODE INVOKED<br/>This is where agent selection matters!

        VoiceAgent->>VoiceAgent: Generate request hash for deduplication
        Note over VoiceAgent: Check if duplicate request:<br/>1. Already processing?<br/>2. Recently processed?

        alt Duplicate request detected
            VoiceAgent-->>VoiceAgent: Return cached response
        else New request
            VoiceAgent->>VoiceAgent: Mark request as active

            alt USE_HYBRID_STREAMING = true
                Note over VoiceAgent: HYBRID MODE (Fast Path)

                VoiceAgent->>VoiceAgent: _get_openai_response_streaming()

                VoiceAgent->>VoiceAgent: _load_agent_memory() if not loaded
                Note over VoiceAgent: ⚠️ AGENT MEMORY LOADED:<br/>- persona<br/>- memory_blocks<br/>- system_instructions

                VoiceAgent->>VoiceAgent: Build messages array
                Note over VoiceAgent: [<br/>  {role: "system", content: agent_system_instructions},<br/>  ...conversation_history[-10:],<br/>  {role: "user", content: user_message}<br/>]

                VoiceAgent->>OpenAI: POST /v1/chat/completions (streaming)
                Note over OpenAI: Model: gpt-4o-mini<br/>Stream: true<br/>Temperature: 0.7

                OpenAI-->>VoiceAgent: Stream chunks
                Note over VoiceAgent: First chunk: TTFT measured<br/>Typical: <200ms

                loop For each chunk
                    OpenAI-->>VoiceAgent: {delta: {content: "..."}}
                    VoiceAgent->>VoiceAgent: Append to response_text
                end

                OpenAI-->>VoiceAgent: [DONE]

                VoiceAgent->>VoiceAgent: Update message_history

                VoiceAgent->>VoiceAgent: Background: _sync_letta_memory_background()
                Note over VoiceAgent: Non-blocking Letta sync:<br/>Save conversation to Letta memory<br/>(runs in background task)

                VoiceAgent->>AsyncLetta: agents.messages.create()
                AsyncLetta->>LettaAPI: POST /v1/agents/{agent_id}/messages
                Note over LettaAPI: Letta processes in background<br/>(doesn't block response)

            else USE_HYBRID_STREAMING = false
                Note over VoiceAgent: LEGACY MODE (AsyncLetta)

                VoiceAgent->>VoiceAgent: _get_letta_response_async_streaming()

                VoiceAgent->>AsyncLetta: agents.messages.create(streaming=True)
                AsyncLetta->>LettaAPI: POST /v1/agents/{agent_id}/messages

                Note over LettaAPI: ⚠️ CRITICAL AGENT PROCESSING:<br/>Uses self.agent_id (set during startup/switch)

                LettaAPI-->>AsyncLetta: Stream response chunks

                loop For each chunk
                    AsyncLetta-->>VoiceAgent: {message_type: "assistant_message"}
                    VoiceAgent->>VoiceAgent: Append to response_text
                end

                AsyncLetta-->>VoiceAgent: Complete response
            end

            VoiceAgent->>VoiceAgent: Validate response (non-empty, meaningful)

            VoiceAgent->>VoiceAgent: Prepend debug info:<br/>"[DEBUG: Using Agent ID xxx | Req yyy]"

            VoiceAgent->>VoiceAgent: Cache response for deduplication
            VoiceAgent->>VoiceAgent: Remove from active_requests set
        end

        VoiceAgent->>Browser: publishData({type: "transcript", role: "assistant"})
        Note over Browser: LED Status: Message Receive = GREEN (flash)<br/>LED Status: Agent Response = GREEN

        VoiceAgent->>VoiceAgent: Return response_text to session
        Note over VoiceAgent: Session framework handles TTS pipeline

        VoiceAgent->>VoiceAgent: OpenAI/Cartesia TTS synthesis
        Note over VoiceAgent: Text-to-Speech:<br/>Voice: "nova" (OpenAI) or British narrator (Cartesia)<br/>Speed: 1.0

        VoiceAgent->>LiveKitSvr: Publish audio track (TTS response)
        LiveKitSvr->>Browser: Audio stream received

        Browser->>Browser: trackSubscribed event (audio from agent)
        Note over Browser: Attach audio element to DOM<br/>LED Status: Audio Output = GREEN

        Browser->>User: Play agent's voice response
    end

    %% ========================================
    %% SECTION 10: POTENTIAL FAILURE POINTS
    %% ========================================

    rect rgb(255, 230, 230)
        Note over User,OpenAI: SECTION 10: POTENTIAL FAILURE POINTS FOR WRONG AGENT

        Note over VoiceAgent,AsyncLetta: ⚠️ FAILURE POINT 1: Initial Agent Selection<br/>- get_or_create_orchestrator() uses PRIMARY_AGENT_NAME<br/>- If PRIMARY_AGENT_ID env var wrong → wrong agent<br/>- If PRIMARY_AGENT_NAME not found → creates new agent

        Note over Browser,VoiceAgent: ⚠️ FAILURE POINT 2: Agent Selection Message<br/>- Browser sends agent_id from UI selection<br/>- If agent doesn't match PRIMARY_AGENT_NAME → rejected<br/>- switch_agent() enforces lock to Agent_66 only

        Note over VoiceAgent,AsyncLetta: ⚠️ FAILURE POINT 3: Multiple Agent Instances<br/>- _ACTIVE_AGENT_INSTANCES prevents duplicates<br/>- If lock fails → two instances of same agent<br/>- Different instances = different self.agent_id

        Note over LiveKitSvr,VoiceAgent: ⚠️ FAILURE POINT 4: Room Assignment Conflict<br/>- _ROOM_TO_AGENT prevents multiple agents per room<br/>- If check fails → multiple agents join same room<br/>- Audio duplication and message routing conflicts

        Note over VoiceAgent,AsyncLetta: ⚠️ FAILURE POINT 5: Memory Loading<br/>- _load_agent_memory() uses self.agent_id<br/>- If agent_id wrong → loads wrong agent's memory<br/>- REST API used to bypass AsyncLetta client bug

        Note over VoiceAgent,LettaAPI: ⚠️ FAILURE POINT 6: Message Processing<br/>- llm_node() uses self.agent_id for Letta calls<br/>- If agent_id corrupted → wrong agent processes messages<br/>- Hybrid mode uses loaded memory (persona, blocks)

        Note over VoiceAgent,VoiceAgent: ⚠️ FAILURE POINT 7: Agent Switching<br/>- switch_agent() updates self.agent_id<br/>- If not properly locked → can switch to wrong agent<br/>- PRIMARY_AGENT_NAME enforcement prevents unauthorized switches
    end

    %% ========================================
    %% SECTION 11: DISCONNECT FLOW
    %% ========================================

    rect rgb(240, 240, 250)
        Note over User,OpenAI: SECTION 11: DISCONNECT FLOW

        User->>Browser: Click "Disconnect" button
        Browser->>Browser: window.disconnect() invoked

        Browser->>Browser: Prepare cleanup message
        Note over Browser: {type: "room_cleanup", timestamp: "..."}

        Browser->>LiveKitSvr: publishData(cleanup message)
        LiveKitSvr->>VoiceAgent: dataReceived event

        VoiceAgent->>VoiceAgent: on_data_received(): room_cleanup
        VoiceAgent->>VoiceAgent: _graceful_shutdown()
        VoiceAgent->>LiveKitSvr: ctx.room.disconnect()

        Browser->>LiveKitSvr: room.disconnect()
        LiveKitSvr-->>Browser: Disconnected

        LiveKitSvr->>VoiceAgent: participantDisconnected event
        VoiceAgent->>VoiceAgent: on_participant_disconnected() handler

        VoiceAgent->>VoiceAgent: Count remaining human participants

        alt Last human disconnected
            VoiceAgent->>VoiceAgent: reset_for_reconnect()
            Note over VoiceAgent: - Cancel background tasks<br/>- Clear message_history<br/>- Force memory reload<br/>- Reset activity time

            VoiceAgent->>VoiceAgent: Clear _ROOM_TO_AGENT assignment
            Note over VoiceAgent: Room now available for new connection
        else Other humans still in room
            Note over VoiceAgent: Keep agent active<br/>No cleanup needed
        end

        Note over Browser: Reset all LEDs to disconnected<br/>Clear state displays<br/>Status: "Disconnected"
    end
```

## Key Points for Debugging Wrong Agent Connection

### Critical Agent Selection Points

1. **Initial Agent Loading (Highest Priority)**
   - File: `letta_voice_agent_optimized.py`, line 1159
   - Function: `get_or_create_orchestrator()`
   - Uses `PRIMARY_AGENT_NAME` (default: "Agent_66") or `PRIMARY_AGENT_ID` from environment
   - **This determines which agent the voice system uses by default**

2. **Agent Selection Message from Browser**
   - File: `voice-agent-selector-debug.html`, lines 556-571
   - Sends `agent_id` and `agent_name` from browser selection
   - Received by voice agent in `on_data_received()` handler (line 1343)
   - **Critical**: `switch_agent()` enforces lock to PRIMARY_AGENT_NAME only

3. **Agent Instance Tracking**
   - File: `letta_voice_agent_optimized.py`, lines 96-99
   - Global dictionaries prevent duplicate agent instances:
     - `_ACTIVE_AGENT_INSTANCES[agent_id]` - One instance per agent ID
     - `_ROOM_TO_AGENT[room_name]` - One agent per room
   - **If these locks fail, multiple agents can conflict**

4. **Memory Loading**
   - File: `letta_voice_agent_optimized.py`, line 273-362
   - Function: `_load_agent_memory()`
   - Uses `self.agent_id` to fetch memory via REST API
   - **This determines whose persona/memory blocks are used**

5. **Message Processing**
   - File: `letta_voice_agent_optimized.py`, line 523-687
   - Function: `llm_node()`
   - Uses `self.agent_id` for Letta API calls (if not hybrid mode)
   - **This determines which agent processes user queries**

### Environment Variables That Control Agent Selection

```bash
VOICE_PRIMARY_AGENT_NAME=Agent_66           # Agent name to search for
VOICE_PRIMARY_AGENT_ID=<specific-uuid>      # Override with specific agent ID
USE_HYBRID_STREAMING=true                   # Enable fast OpenAI path with agent memory
```

### Diagnostic Steps

1. **Check Initial Agent Selection**
   - Look for log: `"AGENT INITIALIZED - Agent Name: ... Agent ID: ..."`
   - Verify this matches the expected Agent_66

2. **Check Agent Selection Message**
   - Look for log: `"AGENT SELECTION MESSAGE RECEIVED - Agent ID: ... Agent Name: ..."`
   - Verify browser sent correct agent_id

3. **Check Agent Lock Enforcement**
   - Look for log: `"REJECTED - Agent switch to ... enforcing Agent_66"`
   - If switching to wrong agent, this should block it

4. **Check Memory Loading**
   - Look for log: `"LOADING MEMORY - Agent ID: ... Agent Name: ..."`
   - Verify correct agent's memory is loaded

5. **Check Message Processing**
   - Look for log: `"NEW QUERY RECEIVED - Current Agent ID: ..."`
   - Look for log: `"RESPONSE GENERATED BY AGENT: ..."`
   - Verify correct agent_id in both logs

6. **Check for Duplicate Instances**
   - Look for warning: `"Agent xxx already has active instance!"`
   - Multiple instances = potential agent_id confusion

7. **Check Response Debug Prefix**
   - Every response starts with: `"[DEBUG: Using Agent ID xxx | Req yyy]"`
   - Last 8 chars of agent_id shown - verify this matches expected agent

## Room Name Handling

**CRITICAL**: The room name is hardcoded to `"test-room"` in both:
- HTML (line 576): `const roomName = 'test-room';`
- JWT token (line 14): Token allows only `"test-room"`

Dynamic room names were removed to prevent browser and agent joining different rooms.

## Files Referenced

- `voice-agent-selector-debug.html` - Browser UI and LiveKit client
- `cors_proxy_server.py` - HTTP proxy for static files and API
- `letta_voice_agent_optimized.py` - Main voice agent process
- `voice_agent_dispatcher.py` - Agent dispatch helper
- `livekit_room_manager.py` - Room cleanup and management

## Conclusion

The system has multiple safeguards to ensure the correct agent (Agent_66) is used:
1. Environment variable enforcement (PRIMARY_AGENT_NAME)
2. Agent lock in switch_agent() function
3. Duplicate instance prevention
4. Room assignment tracking

However, the **initial agent selection** in `get_or_create_orchestrator()` is the most critical point. If this selects the wrong agent, all subsequent operations will use that wrong agent until a proper agent switch is triggered and enforced.
