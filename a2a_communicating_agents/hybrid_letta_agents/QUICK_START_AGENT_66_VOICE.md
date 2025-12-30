# Quick Start: Agent_66 Voice Connection

## Connect Now (3 Steps)

1. **Open browser**:
   ```
   http://localhost:9000/voice-agent-selector.html
   ```

2. **Select Agent_66** from dropdown

3. **Click "Connect Voice Agent"** and allow microphone

## Verify It's Working

- See transcription of your speech
- Hear Agent_66 respond with voice
- Response shows: `[DEBUG: Using Agent ID ...66e | Req ...]`

## Quick Troubleshooting

### Problem: No Response

```bash
# Clean rooms
/home/adamsl/planner/.venv/bin/python3 cleanup_livekit_room.py

# Restart voice agent
pkill -9 -f "letta_voice_agent_optimized.py"
/home/adamsl/planner/.venv/bin/python3 letta_voice_agent_optimized.py dev > voice_agent_fresh.log 2>&1 &
```

### Problem: Wrong Agent Responding

Check environment:
```bash
grep VOICE_PRIMARY /home/adamsl/planner/.env
```

Should show:
```
VOICE_PRIMARY_AGENT_ID=agent-4dfca708-49a8-4982-8e36-0f1146f9a66e
VOICE_PRIMARY_AGENT_NAME=Agent_66
```

### Problem: "Waiting for agent..."

```bash
# Full reset
/home/adamsl/planner/.venv/bin/python3 cleanup_livekit_room.py --force-delete
pkill -9 -f "letta_voice_agent_optimized.py"
/home/adamsl/planner/.venv/bin/python3 letta_voice_agent_optimized.py dev > voice_agent_fresh.log 2>&1 &
```

## Test Connection

```bash
/home/adamsl/planner/.venv/bin/python3 test_agent_66_voice.py
```

## Check Logs

```bash
tail -50 voice_agent_fresh.log
```

## Created Tools

1. **cleanup_livekit_room.py** - Clean stuck rooms
2. **test_agent_66_voice.py** - Verify connection readiness
3. **AGENT_66_VOICE_CLEANUP_REPORT.md** - Full documentation

## Agent_66 Info

- **ID**: agent-4dfca708-49a8-4982-8e36-0f1146f9a66e
- **Name**: Agent_66
- **Memory**: 3 blocks (role, workspace, task_history)
- **Capabilities**: Voice orchestration, task delegation, web search, code generation

## System Status

All services running:
- Letta Server: http://localhost:8283
- LiveKit Server: ws://localhost:7880
- Voice Agent: PID 6501
- Agent_66: VERIFIED and ACCESSIBLE

## Support

For issues, check:
1. voice_agent_fresh.log
2. Browser console (F12)
3. Run test_agent_66_voice.py for diagnostics

---
Status: READY FOR VOICE CONNECTION
Last Updated: 2025-12-29 22:31
