# Voice Capability Status Report

## 1. Introduction
This document provides an overview of the current status of voice integration capabilities within the project, focusing on agent interaction, and outlines known plans and relevant technical components. The goal is to consolidate information for the team and guide future development in this area.

## 2. Current Status of Voice Integration

### 2.1 LiveKit Voice Agent (LVA) Integration
A significant portion of the voice capability appears to be built around a "LiveKit Voice Agent". LiveKit is a WebRTC platform for real-time video, audio, and data.

*   **Description**: The `README.md` explicitly states: "2. **LiveKit Voice Agent** (dynamic ports) - Voice interaction agent powered by LiveKit". It also mentions a "Real-time media server for voice/video communication" (`livekit-server`).
*   **Presence in Core Files**:
    *   `backend/server.ts`: Contains configurations for `livekit-voice-agent`.
        ```typescript
        'livekit-voice-agent': {
            name: 'LiveKit Voice Agent',
        ```
    *   `events.txt`: Shows `livekit-voice-agent` as a recognized server type.
        ```
        data: [{"id":"livekit-voice-agent","name":"LiveKit Voice Agent","running":false,"orphaned":false,"color":"#c5cd3eff","type":"server"},
        ```
*   **Documentation & Testing**:
    *   `dashboard/docs/implementation/ADMIN_DASHBOARD.md`: Details "Use Case 5: Testing Voice Agent Integration", including steps to verify the full LiveKit voice stack. It mentions:
        *   "All voice-related servers must be running"
        *   "Open voice UI: http://localhost:8000/talk"
        *   "Click "Connect Voice""
    *   `dashboard/docs/guides/STARTUP.md`: Mentions `LiveKit Voice Agent` as part of the startup process.
    *   `doc/architecture/server_architecture.md`: Lists `livekit-voice-agent`.
    *   `doc/strategy/process_management_strategy.md`: Describes the `livekit-voice-agent` as a "Voice interaction service".
*   **Conclusion**: A LiveKit-based voice interaction system for agents is either implemented or in an advanced stage of development, with defined procedures for setup and testing.

### 2.2 `letta` Server Voice API
The `letta` server's OpenAPI specification indicates its role in handling voice-related API calls for agent conversations.

*   **API Endpoints**:
    *   `openapi_letta.json`: Contains references to voice-related endpoints:
        ```json
        "/v1/voice-beta/{agent_id}/chat/completions": {
            "voice"
            "summary": "Create Voice Chat Completions",
            "description": "DEPRECATED: This voice-beta endpoint has been deprecated.\n\nThe voice functionality has been integrated into the main chat completions endpoint.\nPlease use the standard /v1/agents/{agent_id}/messages endpoint instead.\n\nThis endpoint will be removed in a future version.",
            "operationId": "create_voice_chat_completions",
        ```
    *   This shows that previous voice functionality through a `/voice-beta` endpoint has been integrated into the standard `/v1/agents/{agent_id}/messages` endpoint, simplifying future interactions.
*   **Voice-Related Schemas**: The `openapi_letta.json` also defines schemas for:
    *   `voice_convo_agent`
    *   `voice_sleeptime_agent`
    *   `Audio`
    *   `ChatCompletionAudio`
    *   `InputAudio`
    *   `VoiceSleeptimeManager`
*   **Conclusion**: The `letta` server is configured to handle voice input and output within its chat completion mechanisms, allowing for programmatic voice interaction with agents.

## 3. STT/TTS Considerations
Plans and discussions exist regarding the integration of Speech-to-Text (STT) and Text-to-Speech (TTS) technologies.

*   **Future Roadmap**: `doc/planning/late_october_goals.md` mentions:
    *   "If you're using Whisper, whisper.cpp is a great project with an existing Wasm build that works in browsers and offers real-time STT using quantized models."
    *   "**ROL extra:** Incorporate the SST and TTS to one of the agents below."
*   **Current Gaps**: A `doc/planning/todolist.md` entry: `- [ ] add voice commands` suggests that while general voice interaction might be present, specific command parsing or advanced voice control is an ongoing task.
*   **Conclusion**: While voice input/output is supported, there is an explicit aim to integrate robust STT/TTS solutions like Whisper for enhanced voice command processing and more natural agent responses.

## 4. Summary and Next Steps

The project has a solid foundation for voice integration, particularly through the LiveKit Voice Agent and `letta`'s voice-enabled API. The direction for improving STT/TTS capabilities is also clear.

To further advance the voice capabilities, the immediate next steps should focus on:

1.  **Activating/Testing the LiveKit Voice Agent**: Verify the setup and functionality of the existing LiveKit Voice Agent by following the documented testing procedures (`dashboard/docs/implementation/ADMIN_DASHBOARD.md`). This will confirm the operational status of the basic voice interaction.
2.  **Exploring `letta` Voice API**: Understand how to interact with the voice capabilities of the `letta` server via the `/v1/agents/{agent_id}/messages` endpoint, leveraging the defined `Audio` schemas. This could involve crafting test API calls.
3.  **Investigating STT/TTS Integration**: Begin exploring the practical implementation of `whisper.cpp` or similar technologies for enhancing voice command recognition and generating spoken agent responses, aligning with the goals outlined in `doc/planning/late_october_goals.md`.

This report provides a clear picture of our current standing and actionable steps to move forward with voice integration.
