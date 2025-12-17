---
name: Voice Agent Expert
description: Expert guidance for the Letta Voice Agent system with Livekit integration. Use when setting up voice chat, connecting to agents via voice, troubleshooting voice pipelines, or when users want to talk (speak/hear) to their Letta agent rather than text chat.
allowed-tools: Bash, Read, Grep, Glob, Write
---

# Voice Agent Expert

Expert guidance for the Letta Voice Agent system - enabling voice conversations with Letta agents via Livekit WebRTC infrastructure.

## Architecture Overview

```
User Voice → Livekit Room → Deepgram STT → Letta Orchestrator → OpenAI/Cartesia TTS → User Hears Response
```

### Components Required

| Component | Port | Purpose |
|-----------|------|---------|
| **Letta Server** | 8283 | Stateful agent memory & orchestration |
| **Livekit Server** | 7880 | WebRTC rooms for audio streaming |
| **Voice Agent Worker** | - | Bridges Livekit ↔ Letta |
| **Browser/Playground** | - | Frontend with microphone access |

### Key Files

- **Voice Agent**: `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/letta_voice_agent.py`
- **Text Chat**: `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/agents/chat_with_letta.py`
- **Livekit Env**: `/home/adamsl/ottomator-agents/livekit-agent/.env`
- **Letta Start Script**: `/home/adamsl/planner/start_letta_dec_09_2025.sh`

## Prerequisites

### Required API Keys (in `/home/adamsl/ottomator-agents/livekit-agent/.env`)

```bash
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
DEEPGRAM_API_KEY=your_key      # Speech-to-Text
OPENAI_API_KEY=your_key        # TTS and LLM fallback
CARTESIA_API_KEY=your_key      # Optional: Better TTS
```

### Check API Keys Status

```bash
grep -E "LIVEKIT|DEEPGRAM|CARTESIA|OPENAI" /home/adamsl/ottomator-agents/livekit-agent/.env | sed 's/=.*/=***/'
```

## ⚠️ CRITICAL: Common Issues Learned

### Issue #1: START vs DEV Mode (MOST COMMON)

**CRITICAL**: The voice agent has two modes:

| Mode | Behavior | Result |
|------|----------|--------|
| `letta_voice_agent.py start` | ❌ Waits for external dispatch | **TIMES OUT** - won't join rooms |
| `letta_voice_agent.py dev` | ✅ Auto-joins rooms | **WORKS** - connects immediately |

**Always use `dev` mode for local testing!**

### Issue #2: Duplicate Processes (VERY COMMON)

Multiple voice agents running simultaneously causes:
- ❌ WebSocket timeout errors
- ❌ "room connection has timed out (signal)" errors
- ❌ Agent joins but doesn't respond

**Check for duplicates:**
```bash
ps aux | grep "letta_voice_agent" | grep -v grep
```

**If you see more than ONE process, kill all and restart:**
```bash
pkill -f "letta_voice_agent.py"
/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/start_voice_system.sh
```

### Issue #3: Token Expiration

Tokens expire after ~6 hours. If you see connection errors:
```bash
# Generate fresh token
/home/adamsl/planner/.venv/bin/python3 /home/adamsl/planner/.claude/skills/voice-agent-expert/scripts/generate_token.py
```

## Instructions

### 1. Check System Status

First, verify all required services are running:

```bash
# Check Letta server (port 8283)
ss -tlnp 2>/dev/null | grep 8283 && echo "Letta: RUNNING" || echo "Letta: NOT RUNNING"

# Check Livekit server (port 7880)
ss -tlnp 2>/dev/null | grep 7880 && echo "Livekit: RUNNING" || echo "Livekit: NOT RUNNING"

# Check voice agent worker
ps aux | grep letta_voice | grep -v grep && echo "Voice Agent: RUNNING" || echo "Voice Agent: NOT RUNNING"
```

### 2. Start Letta Server (if not running)

```bash
cd /home/adamsl/planner
./start_letta_dec_09_2025.sh
```

Or manually:
```bash
cd /home/adamsl/planner
source .venv/bin/activate
export $(grep -v '^#' .env | xargs)
letta server
```

### 3. Start Livekit Server (if not running)

```bash
# If you have livekit-server installed locally
livekit-server --dev

# Or check if it's already running
ps aux | grep livekit-server | grep -v grep
```

### 4. Start Voice Agent Worker

```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
export $(grep -v '^#' /home/adamsl/ottomator-agents/livekit-agent/.env | xargs)
/home/adamsl/planner/.venv/bin/python3 letta_voice_agent.py start
```

### 5. Generate Connection Token

Run this to generate a token for the browser:

```bash
export $(grep -v '^#' /home/adamsl/ottomator-agents/livekit-agent/.env | xargs)
/home/adamsl/planner/.venv/bin/python3 << 'EOF'
from livekit import api
import os

token = api.AccessToken(os.environ['LIVEKIT_API_KEY'], os.environ['LIVEKIT_API_SECRET']) \
    .with_identity('user1') \
    .with_name('User') \
    .with_grants(api.VideoGrants(
        room_join=True,
        room='test-room',
    ))

print('='*60)
print('CONNECTION INFO FOR PLAYGROUND')
print('='*60)
print(f'URL: ws://localhost:7880')
print()
print(f'Token:')
print(token.to_jwt())
print('='*60)
EOF
```

### 6. Connect via Browser

1. Go to: **https://agents-playground.livekit.io/**
2. Click **"Connect"** or the gear/settings icon
3. Enter:
   - **URL**: `ws://localhost:7880`
   - **Token**: (paste the token from step 5)
4. Click **Connect**
5. **Allow microphone access** when prompted
6. Start talking!

## Alternative: Text Chat (No Voice Setup Required)

If you just want to chat with your Letta agent without voice:

```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/agents
/home/adamsl/planner/.venv/bin/python3 chat_with_letta.py
```

Or send a single message:
```bash
/home/adamsl/planner/.venv/bin/python3 hybrid_letta_persistent.py "Your message here"
```

## Quick Start Scripts

### Smart Startup (Idempotent - Safe to Run Anytime)

Use this after a reboot or when you're not sure what's running:

```bash
/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/start_voice_system.sh
```

This script:
- ✓ Checks each service and only starts what's NOT running
- ✓ Safe to run multiple times (idempotent)
- ✓ Perfect for after reboot or fresh start
- ✓ Detects and fixes voice agents running in wrong mode

### Clean Restart (When Things Are Broken)

Use this when you have connection issues or duplicate processes:

```bash
/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/restart_voice_system.sh
```

This script:
- Kills ALL existing voice agents and Livekit instances
- Starts everything fresh from scratch
- Use when you have timeout errors or conflicts

### Quick Aliases

Add to your `~/.bashrc`:
```bash
alias start-voice='/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/start_voice_system.sh'
alias restart-voice='/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/restart_voice_system.sh'
```

## Quick Diagnostic Checklist

Run through this when things aren't working:

```bash
# 1. Check for duplicate voice agents (MOST COMMON ISSUE)
ps aux | grep "letta_voice_agent" | grep -v grep
# Should see ONLY ONE process with "dev" in command

# 2. Check if voice agent is in DEV mode
ps aux | grep "letta_voice_agent.py dev" | grep -v grep
# Should see one result. If empty, you're in START mode (wrong!)

# 3. Verify all services running
ss -tlnp 2>/dev/null | grep -E "8283|7880"
# Should see both ports

# 4. Test Livekit responding
curl http://localhost:7880/
# Should return "OK"

# 5. Generate fresh token if needed
/home/adamsl/planner/.venv/bin/python3 /home/adamsl/planner/.claude/skills/voice-agent-expert/scripts/generate_token.py
```

**If ANY check fails, run:**
```bash
/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/start_voice_system.sh
```

## Troubleshooting

### Problem: "room connection has timed out (signal)"

**This is almost always one of two issues:**

1. **Voice agent in START mode instead of DEV mode**
   ```bash
   # Check mode
   ps aux | grep "letta_voice_agent" | grep -v grep

   # If you see "start" instead of "dev", fix it:
   pkill -f "letta_voice_agent.py"
   cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
   export $(grep -v '^#' /home/adamsl/ottomator-agents/livekit-agent/.env | xargs)
   /home/adamsl/planner/.venv/bin/python3 letta_voice_agent.py dev
   ```

2. **Multiple voice agents running (duplicate processes)**
   ```bash
   # Check for duplicates
   ps aux | grep "letta_voice_agent" | grep -v grep

   # Should see ONLY ONE. If more, kill all and restart:
   pkill -f "letta_voice_agent.py"
   /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/start_voice_system.sh
   ```

### Problem: "Letta server not responding"

```bash
# Check if running
curl -s http://localhost:8283/ | head -5

# Check process
ps aux | grep "letta server" | grep -v grep

# Restart
pkill -f "letta server"
cd /home/adamsl/planner && ./start_letta_dec_09_2025.sh
```

### Problem: "Voice agent won't start"

```bash
# Check for missing dependencies
/home/adamsl/planner/.venv/bin/python3 -c "from livekit import rtc, agents; print('OK')"

# Check for missing env vars
export $(grep -v '^#' /home/adamsl/ottomator-agents/livekit-agent/.env | xargs)
echo "LIVEKIT_URL: $LIVEKIT_URL"
echo "DEEPGRAM_API_KEY set: $([ -n \"$DEEPGRAM_API_KEY\" ] && echo 'yes' || echo 'NO')"
```

### Problem: "Can't connect from browser"

1. Make sure you're using `ws://` not `wss://` for localhost
2. Token may have expired (they last ~6 hours) - generate a new one
3. Check browser console for WebRTC errors
4. Ensure microphone permissions are granted

### Problem: "Agent joins but doesn't respond"

```bash
# Check Letta agent exists
curl -s http://localhost:8283/v1/agents | python3 -m json.tool | head -20

# Check voice agent logs (run in foreground to see output)
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
export $(grep -v '^#' /home/adamsl/ottomator-agents/livekit-agent/.env | xargs)
/home/adamsl/planner/.venv/bin/python3 letta_voice_agent.py start
# Watch for errors in terminal
```

### Problem: "localhost:7880 just shows OK"

That's the Livekit server health check - it's working correctly. The Livekit server doesn't have a built-in UI. You must use:
- **https://agents-playground.livekit.io/** (recommended)
- Or build a custom frontend

## Complete System Diagnostic

Run the diagnostic script:

```bash
python3 /home/adamsl/planner/.claude/skills/voice-agent-expert/scripts/diagnose_voice_system.py
```

## Architecture Deep Dive

### Voice Pipeline Flow

1. **User speaks** → Browser captures audio via WebRTC
2. **Livekit Room** → Routes audio to connected agents
3. **Voice Agent Worker** → Receives audio stream
4. **Deepgram STT** → Converts speech to text
5. **Letta Orchestrator** → Processes text, maintains memory, generates response
6. **OpenAI/Cartesia TTS** → Converts response to speech
7. **Livekit Room** → Streams audio back to browser
8. **User hears** → Response plays through speakers

### Key Classes

- `LettaVoiceAssistant` (letta_voice_agent.py:51) - Main voice agent class
- `AgentSession` (letta_voice_agent.py:285) - Livekit session config
- `get_or_create_orchestrator` (letta_voice_agent.py:185) - Letta agent factory

### Memory Persistence

The Letta agent maintains persistent memory across sessions:
- Agent ID saved to: `.letta_agent_id`
- Memory blocks: `role`, `task_history`, `workspace`
- Conversation history preserved in Letta server

## Examples

### Example 1: First Time Setup

User: "I want to talk to my Letta agent"

Workflow:
1. Check all services status
2. Start any missing services (Letta, Livekit, Voice Agent)
3. Generate connection token
4. Provide playground URL and token
5. Guide through browser connection

### Example 2: Quick Voice Session

User: "Start voice chat"

Quick workflow:
```bash
# One-liner to check and connect
ss -tlnp | grep -E "8283|7880" && \
  echo "Services running!" && \
  python3 /home/adamsl/planner/.claude/skills/voice-agent-expert/scripts/generate_token.py
```

### Example 3: Debugging No Audio

User: "I connected but can't hear the agent"

Debug steps:
1. Check voice agent is running and connected to room
2. Verify Deepgram API key is valid
3. Check TTS provider (OpenAI/Cartesia) API key
4. Look for errors in voice agent terminal output
5. Test with text chat to verify Letta is responding

## Key Learnings Summary

### Critical Rules
1. **ALWAYS use `dev` mode, NEVER `start` mode** for local testing
2. **ONLY ONE voice agent process** should be running at a time
3. **Check for duplicates FIRST** when troubleshooting timeouts
4. **Use start_voice_system.sh** after reboots (idempotent)
5. **Use restart_voice_system.sh** when things are broken (nuclear)

### Common Error → Solution Mapping

| Error | Root Cause | Fix |
|-------|------------|-----|
| "room connection has timed out (signal)" | Voice agent in START mode or duplicates | Kill all → restart with DEV mode |
| "Agent joins but no response" | Duplicate voice agents fighting | `pkill -f letta_voice_agent` → restart |
| "Permission denied" / Token errors | Expired token (>6 hours old) | Generate fresh token |
| Can't connect at all | Livekit not running | Check port 7880, restart Livekit |

### Quick Commands Reference

```bash
# Start everything (safe, idempotent)
/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/start_voice_system.sh

# Nuclear restart (when broken)
/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/restart_voice_system.sh

# Check for duplicates (most common issue)
ps aux | grep "letta_voice_agent" | grep -v grep

# Generate fresh token
/home/adamsl/planner/.venv/bin/python3 /home/adamsl/planner/.claude/skills/voice-agent-expert/scripts/generate_token.py

# Diagnostic
/home/adamsl/planner/.venv/bin/python3 /home/adamsl/planner/.claude/skills/voice-agent-expert/scripts/diagnose_voice_system.py
```

## Summary

This skill provides complete guidance for the Letta Voice Agent system:

- **Architecture**: Livekit + Letta + Deepgram + TTS
- **Quick Start**: Use `start_voice_system.sh` (idempotent)
- **Alternative**: Use `chat_with_letta.py` for text-only chat
- **Critical Knowledge**: DEV mode vs START mode difference
- **Most Common Issues**: Duplicate processes, wrong mode, expired tokens

The voice system requires all components running:
1. Letta server (port 8283)
2. Livekit server (port 7880)
3. Voice agent worker **in DEV mode** (not START)
4. Browser with microphone access and fresh token (<6 hours old)
