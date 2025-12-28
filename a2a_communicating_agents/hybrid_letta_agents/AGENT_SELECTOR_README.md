# Letta Voice Agent Selector

## Overview

The Letta Voice Agent Selector provides a browser-based interface to select and communicate with any Letta agent via voice. You can switch between agents dynamically during a voice session.

> **Important (Dec 27, 2025):** The production/debug selectors are now **locked to `Agent_66`** to prevent the UI from drifting to LiveKit-only agents. Other cards remain visible for reference, but they are disabled and the backend rejects non-`Agent_66` switches to guarantee the Letta orchestrator stays in control.

## Features

- Browse all available Letta agents (182+ agents)
- Search agents by name or ID
- View agent details (memory blocks, model config, creation date)
- Connect to the locked `Agent_66` voice orchestrator (other agents are view-only)
- Real-time status updates with enforced Agent_66 lock pill on the UI

## Quick Start

### 1. Start the Voice System

```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
./start_voice_system.sh
```

This starts:
- PostgreSQL (if needed)
- Letta Server (port 8283)
- Livekit Server (port 7880)
- Voice Agent Worker (in DEV mode)
- Demo Web Server (port 8888)

### 2. Open the Agent Selector

Open your browser to:

```
http://localhost:8888/voice-agent-selector.html
```

### 3. Select an Agent

1. Browse the list of available agents
2. Use the search box to filter by name or ID
3. Click on an agent card to select it
4. Review the agent details in the right panel

### 4. Connect and Talk

1. Click the **Connect** button
2. Allow microphone access when prompted
3. Wait for "Agent connected! Start speaking..."
4. Start talking to your agent!

## Agent Lock Enforcement (Dec 27, 2025)

**Symptom:** Browser sessions at `localhost:9000/debug` occasionally latched onto the generic LiveKit worker instead of the Letta orchestrator, producing bland responses and bypassing `Agent_66`.

**Detection:** LiveKit logs lacked `🔄 Agent selection request: Agent_66` entries while the UI still showed a successful connection. Manual debugging confirmed the selector let users pick non-Letta agents, which the backend dutifully switched to.

**Automated Fix:** Both selector pages now auto-select and highlight `Agent_66`, disable every other card, and resend the primary agent ID after each reconnect. The backend (`letta_voice_agent_optimized.py`) cross-checks every `agent_selection` payload and refuses to switch if the target’s name is not `Agent_66`, voicing a lock warning instead. Together these changes guarantee every room stays on the intended Letta agent without manual babysitting.

## How It Works

### Architecture

```
Browser                 Livekit Room              Voice Agent Worker         Letta Server
  |                           |                           |                         |
  |-- Select Agent ---------> |                           |                         |
  |                           |                           |                         |
  |-- Connect --------------> |                           |                         |
  |                           |                           |                         |
  |                           |-- Join Room ------------> |                         |
  |                           |                           |                         |
  |-- Agent Selection Data -> |-- Forward Selection ----> |                         |
  |                           |                           |                         |
  |                           |                           |-- Switch Agent -------> |
  |                           |                           |                         |
  |-- Voice Input ----------> |-- STT -----------------> |-- Send to Letta ------> |
  |                           |                           |                         |
  |<- Voice Output ---------- |<- TTS ------------------- |<- Response ------------ |
```

### Agent Selection Flow

1. **Browser loads agents**: Fetches list from Letta API at `http://localhost:8283/v1/agents`
2. **User selects agent**: Stores agent ID and name locally
3. **User connects**: Establishes Livekit WebRTC connection
4. **Agent selection sent**: Browser sends JSON message via data channel:
   ```json
   {
     "type": "agent_selection",
     "agent_id": "agent-e8f31f19-9eed-4a57-9042-afa52f85d71a",
     "agent_name": "voice_orchestrator"
   }
   ```
5. **Voice agent switches**: Backend calls `assistant.switch_agent()` to change active agent
6. **Confirmation**: Agent speaks "Switched to agent [name]. How can I help you?"

### Dynamic Agent Switching

> ⚠️ Production/debug builds now block manual switching and always revert to `Agent_66`. The steps below describe the legacy free-for-all selector and remain here for historical context.

You can switch agents during an active voice session:

1. Select a different agent from the list
2. Click **Connect** again (disconnects and reconnects)
3. The voice agent will switch to the new agent
4. Previous conversation history is cleared (each agent has independent memory)

## File Locations

### Frontend
- **Agent Selector UI**: `/home/adamsl/ottomator-agents/livekit-agent/voice-agent-selector.html`
- **Original Simple UI**: `/home/adamsl/ottomator-agents/livekit-agent/test-simple.html`

### Backend
- **Voice Agent**: `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/letta_voice_agent.py`
- **Startup Script**: `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/start_voice_system.sh`

## Agent Types

The system has 182+ agents including:

- **voice_orchestrator**: Default multi-agent coordinator
- **livekit_test_agent**: Testing agent
- **AliceTheBartender**: Character-based agent
- **BobTheMechanic**: Character-based agent
- **non-profit-db-agent**: Database specialist
- **bank_specialist**: Banking domain expert
- Many auto-generated agents with creative names

## API Reference

### Browser to Voice Agent Messages

#### Agent Selection
```json
{
  "type": "agent_selection",
  "agent_id": "agent-xxxxx",
  "agent_name": "AgentName"
}
```

#### Text Chat (existing)
```json
{
  "type": "chat",
  "message": "Hello, agent!"
}
```

### Voice Agent to Browser Messages

#### Transcript Updates
```json
{
  "type": "transcript",
  "role": "user|assistant|system",
  "text": "Message content",
  "timestamp": "2025-12-17T12:00:00Z"
}
```

## Troubleshooting

### Agent List Not Loading

**Symptom**: "Failed to load agents" error

**Solution**:
```bash
# Check Letta server is running
curl http://localhost:8283/v1/agents

# If not running, start it
./start_voice_system.sh
```

### Cannot Connect to Agent

**Symptom**: "Connection timeout" or "Waiting for agent to join..." never resolves

**Solution**:
```bash
# Check voice agent is running in DEV mode
ps aux | grep "letta_voice_agent.py dev"

# Check for duplicates (causes audio cutting)
ps aux | grep "letta_voice_agent" | grep -v grep

# Restart voice system
./restart_voice_system.sh
```

### Agent Doesn't Respond

**Symptom**: Agent connects but doesn't speak back

**Solutions**:

1. **Check agent exists**:
   ```bash
   curl http://localhost:8283/v1/agents/[agent-id]
   ```

2. **Check voice agent logs**:
   ```bash
   tail -f /tmp/voice_agent.log
   ```

3. **Check for errors in browser console** (F12)

### Audio Cuts Off

**Symptom**: Agent starts speaking but cuts off after 1-2 seconds

**Root Cause**: Multiple voice agents running (duplicate processes)

**Solution**:
```bash
# Restart script auto-detects and kills duplicates
./restart_voice_system.sh
```

### Different Agent Selection Not Working

**Symptom**: Selecting different agents doesn't change behavior

**Verification**:
- Check browser console for "Sent agent selection: [agent-id]"
- Check voice agent logs for "Agent selection request: [name]"
- Look for "Switched from agent X to Y" in logs

## Advanced Usage

### Testing Agent Switching

1. Connect to `voice_orchestrator` agent
2. Say "Hello, who are you?"
3. Disconnect
4. Select `AliceTheBartender` agent
5. Connect
6. Say "Hello, who are you?"
7. You should hear different personality/responses

### Creating Custom Agents

You can create new agents via Letta API or UI, then they'll automatically appear in the selector:

```bash
# Using Letta CLI
letta agents create --name "MyCustomAgent"

# Refresh the agent list in browser
# Click "Refresh Agents" button
```

### Filtering Large Agent Lists

With 182+ agents, use the search feature:
- Search by name: "alice", "bob", "orchestrator"
- Search by ID prefix: "agent-e8f", "agent-123"
- Search is case-insensitive and matches partial strings

## Technical Details

### Voice Pipeline Components

1. **Speech-to-Text**: Deepgram Nova 2
2. **LLM**: Letta agents (configured per agent)
3. **Text-to-Speech**: OpenAI TTS (nova voice) or Cartesia
4. **Voice Activity Detection**: Silero VAD with optimized settings
5. **WebRTC**: Livekit for real-time audio streaming

### Agent Memory

Each Letta agent maintains:
- **Persona block**: Agent's role and capabilities
- **Conversation log**: History of interactions
- **Custom blocks**: Agent-specific memory structures

When you switch agents, the conversation history resets but each agent retains its own persistent memory.

### Performance

- Agent list loads in <1 second for 182 agents
- Voice latency: ~500ms (STT + Letta + TTS)
- Agent switching: ~1-2 seconds
- Connection timeout: 15 seconds

## Security Notes

⚠️ **Development Mode**: The current setup uses:
- Hardcoded dev token with 1-year expiration
- No authentication on Letta API
- Localhost-only access

For production use:
- Generate short-lived tokens per session
- Add authentication to Letta API
- Use HTTPS/WSS for external access
- Implement proper CORS policies

## Future Enhancements

Potential improvements:
- [ ] Save favorite agents
- [ ] Agent categorization/tags
- [ ] Multi-agent conversation (group chat)
- [ ] Voice cloning per agent
- [ ] Conversation history export
- [ ] Real-time transcript display in UI
- [ ] Agent performance metrics
- [ ] Custom agent creation from UI

## Support

For issues or questions:
1. Check logs: `/tmp/voice_agent.log`, `/tmp/livekit.log`
2. Review browser console (F12)
3. Run diagnostic: `./test_voice_system.sh`
4. Restart system: `./restart_voice_system.sh`

## Related Documentation

- `VOICE_SYSTEM_QUICKSTART.md`: Quick start guide
- `DUPLICATE_PREVENTION.md`: Handling duplicate agent processes
- `SYSTEMD_SETUP.md`: Production deployment with systemd
- `.claude/skills/voice-agent-expert/README.md`: Voice agent expert skill guide
