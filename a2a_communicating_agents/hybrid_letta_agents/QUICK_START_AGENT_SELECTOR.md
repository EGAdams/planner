# Quick Start: Agent Selector

## TL;DR

```bash
# Start system
./start_voice_system.sh

# Open browser
http://localhost:8888/voice-agent-selector.html

# Select agent → Connect → Talk!
```

## What You Get

- Browse 182+ Letta agents
- Search by name or ID
- Select any agent to talk to
- Switch agents anytime
- Beautiful UI with real-time status

## URLs

| Interface | URL |
|-----------|-----|
| **Agent Selector** | http://localhost:8888/voice-agent-selector.html |
| Simple UI | http://localhost:8888/test-simple.html |
| Letta API | http://localhost:8283/v1/agents |

## Quick Test

```bash
# Test everything is working
python3 test_agent_api.py

# Should show:
# ✅ All tests passed!
```

## Popular Agents

Try these agents first:
- `voice_orchestrator` - Multi-agent coordinator
- `AliceTheBartender` - Friendly bartender character
- `BobTheMechanic` - Helpful mechanic character
- `non-profit-db-agent` - Database specialist

## How It Works

1. **Browser** fetches agent list from Letta
2. **You** select an agent
3. **Click Connect** to join voice room
4. **Browser** sends agent selection to voice worker
5. **Voice worker** switches to selected agent
6. **Start talking!**

## Troubleshooting

### Services Not Running
```bash
./start_voice_system.sh
```

### Audio Problems
```bash
./restart_voice_system.sh
```

### Check Status
```bash
# All services
ss -tlnp | grep -E ":(8283|7880|8888)"

# Voice agent
ps aux | grep "letta_voice_agent.py dev"
```

## Features

✅ Real-time agent search
✅ Agent details display
✅ Connection status
✅ Voice confirmation on switch
✅ 182+ agents available
✅ Beautiful responsive UI

## Next Steps

- Read full guide: `AGENT_SELECTOR_README.md`
- Implementation details: `IMPLEMENTATION_SUMMARY.md`
- System setup: `VOICE_SYSTEM_QUICKSTART.md`

---

**Ready in 30 seconds. Talk to any Letta agent via voice.**
