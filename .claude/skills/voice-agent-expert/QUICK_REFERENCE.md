# Letta Voice Agent - Quick Reference

## 🚨 MOST COMMON ISSUES

### 1. Timeout Error: "room connection has timed out (signal)"
**Cause**: Voice agent in wrong mode OR duplicate processes

```bash
# Check what's running
ps aux | grep "letta_voice_agent" | grep -v grep

# Should see ONLY ONE with "dev" in command
# If "start" or multiple processes, fix:
pkill -f "letta_voice_agent.py"
/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/start_voice_system.sh
```

### 2. Agent Joins But Doesn't Respond
**Cause**: Duplicate voice agents

```bash
# Kill all duplicates
pkill -f "letta_voice_agent.py"

# Start clean
/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/start_voice_system.sh
```

### 3. Token Expired
**Cause**: Token is >6 hours old

```bash
# Generate fresh token
/home/adamsl/planner/.venv/bin/python3 /home/adamsl/planner/.claude/skills/voice-agent-expert/scripts/generate_token.py
```

## ⚡ Quick Commands

| Task | Command |
|------|---------|
| **Start system** | `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/start_voice_system.sh` |
| **Restart (broken)** | `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/restart_voice_system.sh` |
| **Check status** | `ps aux \| grep "letta_voice_agent" \| grep -v grep` |
| **Generate token** | `/home/adamsl/planner/.venv/bin/python3 /home/adamsl/planner/.claude/skills/voice-agent-expert/scripts/generate_token.py` |
| **Diagnostic** | `/home/adamsl/planner/.venv/bin/python3 /home/adamsl/planner/.claude/skills/voice-agent-expert/scripts/diagnose_voice_system.py` |

## 🎯 Critical Rules

1. ✅ **ALWAYS** use `dev` mode
2. ❌ **NEVER** use `start` mode for local testing
3. 🔍 **CHECK for duplicates FIRST** when troubleshooting
4. 🔄 Use `start_voice_system.sh` after reboots (safe, idempotent)
5. 💥 Use `restart_voice_system.sh` when things are broken (nuclear)

## 📋 Required Services

| Service | Port | Check |
|---------|------|-------|
| Letta | 8283 | `curl http://localhost:8283/` |
| Livekit | 7880 | `curl http://localhost:7880/` |
| Voice Agent | - | `ps aux \| grep "letta_voice_agent.py dev"` |

## 🌐 Browser Connection

1. Open: http://localhost:8888/test-simple.html
2. Click "Connect"
3. Allow microphone
4. Say "Hello!"

## 🆘 Emergency Fix

When nothing works:

```bash
# Kill everything
pkill -f "letta_voice_agent.py"
pkill -f "livekit-server"

# Start fresh
/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/start_voice_system.sh
```

## 📝 Aliases (Add to ~/.bashrc)

```bash
alias start-voice='/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/start_voice_system.sh'
alias restart-voice='/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/restart_voice_system.sh'
alias voice-status='ps aux | grep "letta_voice_agent" | grep -v grep'
```
