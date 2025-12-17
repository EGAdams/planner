# Voice Agent Expert Skill

Expert troubleshooting and debugging for LiveKit-based voice agents with Letta integration.

## Critical Architecture Knowledge

### LiveKit Agent Override Methods

**CRITICAL**: The LiveKit `Agent` base class does NOT have a `generate_reply` method. To intercept LLM calls and route through Letta, you must override:

```python
async def llm_node(self, chat_ctx, tools, model_settings):
    """
    This is the actual method called by LiveKit framework.
    Override this to route through Letta instead of using the session's LLM.
    """
    user_message = chat_ctx.messages[-1].content if chat_ctx.messages else ""
    # Route to Letta here
    return response_text
```

**Wrong approach** (doesn't work):
```python
async def generate_reply(self, chat_ctx):  # ❌ This method doesn't exist in base class
    # Framework never calls this!
```

### Agent Process Management

**Multiple processes prevent new agents from joining rooms!**
- Only ONE voice agent process should run at a time
- Kill all processes before restarting: `pkill -9 -f letta_voice_agent.py`
- Check for duplicates: `ps aux | grep letta_voice_agent | grep -v grep`

### Code Changes Require Restart

**Code changes don't apply to running processes**
- Voice agent loads code at startup
- Must kill and restart process after ANY code changes
- Use `pkill -f letta_voice_agent.py && python3 letta_voice_agent.py dev`

## Common Issues and Solutions

### 1. Connection Timeout Errors

**Symptoms:**
- Browser console shows: `ConnectionError: could not establish signal connection: room connection has timed out`
- Or: `Connection timeout after 15s`
- Or: `Failed to fetch` / `ERR_CONNECTION_REFUSED`

**Root Cause:**
- LiveKit server process is stuck or unresponsive
- Server listening but not responding to WebSocket/HTTP requests
- Port conflicts on UDP port 7882 (media) or TCP port 7880 (signaling)

**Solution (Automated):**
```bash
# Use the restart script (recommended)
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
./restart_voice_system.sh
```

**Solution (Manual):**
```bash
# 1. Check if server is stuck
ps aux | grep livekit-server | grep -v grep
# Look for "Tl" status which indicates stopped/traced state

# 2. Force kill old server
pkill -f livekit-server

# 3. Restart fresh server
cd /home/adamsl/ottomator-agents/livekit-agent
nohup ./livekit-server --dev --bind 0.0.0.0 > /tmp/livekit.log 2>&1 &

# 4. Verify startup
tail -f /tmp/livekit.log
# Should see: "starting in development mode"
# Should NOT see: "bind: address already in use"

# 5. Test connectivity
curl -v http://localhost:7880/ 2>&1 | head -20
# Should get HTTP response, not timeout
```

### 2. WebSocket Double Slash Issue

**Symptoms:**
- Browser tries to connect to `ws://127.0.0.1:7880//rtc` (double slash)

**Solution:**
- Use `ws://localhost:7880` (NOT `ws://127.0.0.1:7880`)
- LiveKit client adds `/rtc` path automatically

### 3. Messages Not Being Saved to Letta

**Symptoms:**
- Voice agent responds but no conversation history in Letta Desktop
- Letta Desktop shows no new messages for the agent
- No `🎤 User message` logs appearing

**Root Causes:**
1. **Wrong method overridden** - Using `generate_reply` instead of `llm_node`
2. **Old process running** - Code changes not applied because process wasn't restarted
3. **Session LLM bypassing Letta** - Framework using `openai.LLM(model="gpt-5-mini")` directly

**Solution:**
```bash
# 1. Verify the code has llm_node override
grep -A5 "def llm_node" letta_voice_agent.py

# 2. Kill ALL voice agent processes
pkill -9 -f letta_voice_agent.py
sleep 2

# 3. Start fresh with updated code
python3 letta_voice_agent.py dev > /tmp/letta_voice_agent.log 2>&1 &

# 4. Monitor for the 🎤 emoji (proves llm_node is being called)
tail -f /tmp/letta_voice_agent.log | grep "🎤"
```

### 4. Agent Won't Join Room

**Symptoms:**
- Browser shows "Waiting for agent to join..."
- No "Voice agent starting in room" in logs
- LiveKit shows old agent participant still in room

**Root Causes:**
1. Multiple voice agent processes running
2. Old agent ghost stuck in room
3. Agent registered but not dispatching to rooms

**Solution:**
```bash
# 1. Kill ALL voice agent processes (including background tails)
pkill -9 -f letta_voice_agent
ps aux | grep letta_voice_agent  # Verify all killed

# 2. Start ONE fresh process
python3 letta_voice_agent.py dev > /tmp/letta_voice_agent.log 2>&1 &

# 3. Close browser tab completely (not just disconnect)
# 4. Wait 5 seconds
# 5. Open fresh browser tab and reconnect
```

### 5. Expired JWT Tokens

**Symptoms:**
- Unauthorized or authentication errors

**Solution:**
```bash
# Generate fresh token using Python
cd /home/adamsl/planner && source .venv/bin/activate
python3 << 'EOF'
from livekit import api
import os
from dotenv import load_dotenv

load_dotenv('/home/adamsl/planner/.env')
load_dotenv('/home/adamsl/ottomator-agents/livekit-agent/.env')

token = api.AccessToken(
    api_key=os.getenv('LIVEKIT_API_KEY', 'devkey'),
    api_secret=os.getenv('LIVEKIT_API_SECRET', 'secret')
)

token.with_identity('test-user').with_name('Test User').with_grants(
    api.VideoGrants(
        room_join=True,
        room='test-room',
        can_publish=True,
        can_subscribe=True,
        can_publish_data=True,
    )
)

print(token.to_jwt())
EOF
```

## Key Files and Locations

### LiveKit Configuration
- **Server binary**: `/home/adamsl/ottomator-agents/livekit-agent/livekit-server`
- **Server logs**: `/tmp/livekit.log` (or `livekit-server.log` if started manually)
- **Environment**: `/home/adamsl/ottomator-agents/livekit-agent/.env`
- **Test page**: `/home/adamsl/ottomator-agents/livekit-agent/test-simple.html` (served on port 8888 or 8899)
- **HTTP server log**: `/tmp/livekit_http_server.log`

### Letta Voice Agent
- **Agent code**: `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/letta_voice_agent.py`
- **Agent logs**: `/tmp/letta_voice_agent.log`
- **Python venv**: `/home/adamsl/planner/.venv`
- **Start script**: `./start_voice_system.sh` (automated)
- **Restart script**: `./restart_voice_system.sh` (automated)

### Letta Server
- **Server logs**: `/home/adamsl/planner/logs/letta.log`
- **Server URL**: `http://localhost:8283`
- **Environment**: `/home/adamsl/planner/.env`

## Diagnostic Commands

### Check Service Status
```bash
# LiveKit server
ps aux | grep livekit-server | grep -v grep
lsof -i :7880
netstat -tlnp | grep 7880

# Letta voice agent
ps aux | grep letta_voice_agent | grep -v grep
lsof -i :7880 | grep python  # Check agent connection

# Web server for test page
lsof -i :8888
```

### Check Logs
```bash
# LiveKit server logs
tail -f /tmp/livekit.log

# Letta voice agent logs
tail -f /tmp/letta_voice_agent.log

# Letta server logs
tail -f /home/adamsl/planner/logs/letta.log

# HTTP demo server logs
tail -f /tmp/livekit_http_server.log

# Look for in LiveKit logs:
# - "starting in development mode" = good
# - "bind: address already in use" = port conflict
# - Ping requests with participant info = client connected
```

### Test Connectivity
```bash
# Test HTTP endpoint (should respond quickly)
curl -v http://localhost:7880/ 2>&1 | head -20

# Test WebSocket upgrade (for debugging only)
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: test" \
  http://localhost:7880/
```

## Typical Workflow

### Automated Startup (Recommended)

Use the automated scripts for complete system startup:

```bash
# Start everything from scratch (checks if services are running)
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
./start_voice_system.sh

# Or restart just voice components (keeps Letta running)
./restart_voice_system.sh
```

These scripts will:
1. Check/start Letta server (port 8283)
2. Check/start LiveKit server (port 7880)
3. Start voice agent in DEV mode
4. Start HTTP demo server (port 8888 or 8899)
5. Generate a fresh connection token

### Manual Startup (Fallback)

If you need to start services individually:

#### 1. Start LiveKit Server
```bash
cd /home/adamsl/ottomator-agents/livekit-agent
./livekit-server --dev --bind 0.0.0.0
# Or in background:
nohup ./livekit-server --dev --bind 0.0.0.0 > /tmp/livekit.log 2>&1 &
```

#### 2. Start Letta Voice Agent
```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
source /home/adamsl/planner/.venv/bin/activate
python3 letta_voice_agent.py dev > /tmp/letta_voice_agent.log 2>&1 &
```

#### 3. Start Web Server for Test Page
```bash
cd /home/adamsl/ottomator-agents/livekit-agent
python3 -m http.server 8888
```

#### 4. Test in Browser
- Navigate to `http://localhost:8888/test-simple.html`
- Click "Connect"
- Paste the connection token
- Allow microphone access
- Say "Hello!"

## Architecture

```
Browser (test-simple.html)
    ↓ WebSocket
LiveKit Server (port 7880)
    ↓ Agent Protocol
Letta Voice Agent (letta_voice_agent.py)
    ↓ HTTP
Letta Server (port 8283)
```

## Environment Variables

Required in `/home/adamsl/ottomator-agents/livekit-agent/.env`:
```bash
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
OPENAI_API_KEY=sk-...
DEEPGRAM_API_KEY=...
```

Optional:
```bash
CARTESIA_API_KEY=...  # For TTS
TTS_PROVIDER=openai   # or "cartesia"
```

## Troubleshooting Checklist

When debugging connection issues:

1. ✅ **Check LiveKit server is running and healthy**
   - `ps aux | grep livekit-server`
   - Check process status is NOT "Tl" (traced/stopped)

2. ✅ **Check LiveKit server is responding**
   - `curl http://localhost:7880/` should respond quickly
   - If timeout = restart server

3. ✅ **Check no port conflicts**
   - Port 7880 (TCP) for signaling
   - Port 7882 (UDP) for media

4. ✅ **Check ONLY ONE voice agent process is running**
   - `ps aux | grep letta_voice_agent | grep -v grep | wc -l` should return 1
   - If > 1, kill all and start fresh

5. ✅ **Verify code changes were applied**
   - Check file modification time vs process start time
   - Restart process after ANY code changes

6. ✅ **Check token is fresh**
   - Tokens expire in 6 hours by default
   - Generate new token if expired

7. ✅ **Monitor for 🎤 emoji in logs**
   - `tail -f /tmp/letta_voice_agent.log | grep "🎤"`
   - If you speak but see nothing, `llm_node` is NOT being called

8. ✅ **Check browser console for detailed errors**
   - Connection state changes
   - WebSocket URL (check for double slashes)
   - Full error stack traces

9. ✅ **Verify Letta server is running**
   - `curl -s http://localhost:8283/ > /dev/null && echo "OK" || echo "DOWN"`

10. ✅ **Check for agent ghosts in room**
   - `tail -20 /tmp/livekit.log | grep agent`
   - If old agent still present, close browser tab completely and reconnect

## Success Indicators

When everything is working:

- **LiveKit server logs**: Shows ping requests every 5 seconds
- **Browser console**: Shows "✅ Signal connection established" → "✅ Room connected successfully"
- **Browser status**: Changes to "Connected! Waiting for agent..."
- **Agent logs**: Shows "Voice agent starting in room: test-room"
- **Audio**: Agent joins and speaks greeting

## Quick Reference Scripts

### Start Everything
```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
./start_voice_system.sh
```

### Restart Voice Components Only
```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
./restart_voice_system.sh
```

### Stop Everything
```bash
# Stop ALL voice agent processes (critical!)
pkill -9 -f letta_voice_agent

# Stop LiveKit
pkill -f livekit-server

# Stop Letta server (if needed)
pkill -f "letta server"
```

### Emergency Full Reset
```bash
# When nothing works - nuclear option
pkill -9 -f letta_voice_agent
pkill -9 -f livekit-server
sleep 3

# Start LiveKit
cd /home/adamsl/ottomator-agents/livekit-agent
./livekit-server --dev --bind 0.0.0.0 > /tmp/livekit.log 2>&1 &
sleep 2

# Start voice agent with fresh log
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
/home/adamsl/planner/.venv/bin/python3 letta_voice_agent.py dev > /tmp/letta_voice_agent.log 2>&1 &
sleep 5

# Verify
ps aux | grep -E "(livekit-server|letta_voice_agent)" | grep -v grep
tail -20 /tmp/letta_voice_agent.log | grep "registered"

# Generate fresh token
/home/adamsl/planner/.venv/bin/python3 << 'EOF'
from livekit import api
import os
from dotenv import load_dotenv
load_dotenv('/home/adamsl/ottomator-agents/livekit-agent/.env')
token = api.AccessToken(os.environ['LIVEKIT_API_KEY'], os.environ['LIVEKIT_API_SECRET']) \
    .with_identity('test-user').with_name('Test User') \
    .with_grants(api.VideoGrants(room_join=True, room='test-room'))
print("\n" + "="*60)
print("TOKEN:", token.to_jwt())
print("="*60 + "\n")
EOF
```

## Development Tips

### Verify Letta Integration is Working

After speaking to the agent, immediately check:

```bash
# 1. Did llm_node get called?
tail -100 /tmp/letta_voice_agent.log | grep "🎤 User message"

# 2. Was message sent to Letta?
tail -100 /tmp/letta_voice_agent.log | grep "POST.*8283.*messages"

# 3. Check Letta for the message
curl -s "http://localhost:8283/v1/agents/agent-e8f31f19-9eed-4a57-9042-afa52f85d71a/messages?limit=1" | \
  python3 -m json.tool | grep -E "(date|content)" | head -4
```

### Monitor Live Interaction

```bash
# Terminal 1: Watch for voice input
tail -f /tmp/letta_voice_agent.log | grep --line-buffered "🎤"

# Terminal 2: Watch LiveKit activity
tail -f /tmp/livekit.log | grep --line-buffered "participant"

# Terminal 3: Monitor agent process
watch -n 1 'ps aux | grep letta_voice_agent | grep -v grep'
```

---

**Version**: 1.2
**Last Updated**: 2025-12-16
**Author**: Voice Agent Deep Debugging Session
**Key Fix**: Override `llm_node` not `generate_reply`
