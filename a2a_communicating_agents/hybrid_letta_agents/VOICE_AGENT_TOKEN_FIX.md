# Voice Agent JWT Token Fix - Complete Guide

## Problem Solved

Your JWT token had expired, preventing connection to Livekit with the error:
```
Error: could not establish signal connection: invalid token
error: go-jose/go-jose/jwt: validation failed, token is expired (exp)
```

## Immediate Fix Applied

1. Generated fresh 24-hour JWT token
2. Updated `voice-agent-selector.html` with new token
3. Restarted CORS proxy server to serve updated HTML
4. Token now valid until: **2025-12-20 17:51:58 UTC** (24 hours)

## Quick Fix Commands

### When Token Expires Again

```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents

# Option 1: Use automated script (RECOMMENDED)
./update_voice_token.sh

# Option 2: Manual verification first
./verify_token.py

# Option 3: Generate token via API
curl -s http://localhost:9000/api/token | python3 -c "import json,sys; print(json.load(sys.stdin)['token'])"
```

After updating, refresh your browser at http://localhost:9000 (Ctrl+Shift+R to hard refresh).

## Files Created/Updated

### New Tools

1. **`verify_token.py`** - Verify token validity
   ```bash
   ./verify_token.py              # Check token in HTML file
   ./verify_token.py <token>      # Check specific token
   ```

2. **`update_voice_token.sh`** - Auto-update token (already existed, now verified working)
   - Generates fresh 24-hour token
   - Updates HTML file
   - Creates backup
   - Shows expiration time

3. **CORS proxy token API** - Dynamic token generation at `http://localhost:9000/api/token`
   ```bash
   # Get token for default room (24 hours)
   curl "http://localhost:9000/api/token"

   # Custom room with 48-hour validity
   curl "http://localhost:9000/api/token?room=my-room&ttl=48"

   # Different user identity
   curl "http://localhost:9000/api/token?identity=alice&room=test-room&ttl=12"
   ```

## Long-Term Solution Options

### Option 1: Use Automation Script (Quick)

Set up a daily cron job to auto-refresh tokens:

```bash
# Edit crontab
crontab -e

# Add this line to regenerate token daily at midnight
0 0 * * * cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents && ./update_voice_token.sh >> /tmp/token_update.log 2>&1
```

**Pros**: No code changes, automatic updates
**Cons**: Still uses hardcoded tokens, 24-hour windows

### Option 2: Dynamic Token Fetching (Best Practice)

Modify `voice-agent-selector.html` to fetch tokens on-demand from the API:

```javascript
// Add this helper function near the top of the script
async function getFreshToken(roomName) {
    try {
        const response = await fetch(`${PROXY_URL}/api/token?room=${roomName}&ttl=24`);
        const data = await response.json();
        console.log('🎟️ Generated fresh token for room:', roomName);
        return data.token;
    } catch (error) {
        console.error('❌ Failed to get token:', error);
        throw error;
    }
}

// Modify the connect function (around line 225)
// BEFORE:
await room.connect(LIVEKIT_URL, TOKEN, roomName, { autoSubscribe: true });

// AFTER:
const freshToken = await getFreshToken(roomName);
await room.connect(LIVEKIT_URL, freshToken, roomName, { autoSubscribe: true });

// Remove or comment out the hardcoded TOKEN constant (line 14)
// const TOKEN = '...';  // No longer needed
```

**Pros**: Always fresh tokens, no expiration issues, production-ready
**Cons**: Requires small code change

### Option 3: Extended Token Lifetime (Development)

For development purposes, generate longer-lived tokens:

```bash
# Generate 7-day token (168 hours)
curl "http://localhost:9000/api/token?ttl=168" | python3 -c "import json,sys; data=json.load(sys.stdin); print('Token:', data['token'][:50]+'...'); print('Valid for:', data['ttl_hours'], 'hours')"

# Then manually update HTML file or use update script with modifications
```

**Pros**: Less frequent updates needed
**Cons**: Not suitable for production, still requires manual updates

## System Status Verification

### Check Everything is Working

```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents

# 1. Verify token validity
./verify_token.py

# 2. Check Livekit server is running
curl http://localhost:7880/

# 3. Check CORS proxy is running
ps aux | grep cors_proxy_server

# 4. Check token API works
curl -s http://localhost:9000/api/token | head -c 100

# 5. Test web interface
curl -I http://localhost:9000/
```

### Manual Token Inspection

To decode and inspect any JWT token:

```bash
python3 << 'EOF'
import json, base64
token = "YOUR_TOKEN_HERE"  # Replace with actual token
parts = token.split('.')
payload = parts[1]
padding = len(payload) % 4
if padding: payload += '=' * (4 - padding)
data = json.loads(base64.urlsafe_b64decode(payload))
print(json.dumps(data, indent=2))
EOF
```

## Troubleshooting Guide

### Issue: Token Still Shows as Expired

**Symptoms**: `verify_token.py` shows "EXPIRED" after running update script

**Solutions**:
1. Verify update script ran successfully: `./update_voice_token.sh`
2. Check HTML was actually updated: `grep "const TOKEN" voice-agent-selector.html | head -1`
3. Hard refresh browser: Ctrl+Shift+R (Chrome/Edge) or Cmd+Shift+R (Mac)
4. Restart CORS proxy: `pkill -f cors_proxy_server && /home/adamsl/planner/.venv/bin/python3 cors_proxy_server.py &`

### Issue: CORS Proxy Not Running

**Symptoms**: `curl http://localhost:9000/` fails with connection refused

**Solutions**:
```bash
# Check if running
ps aux | grep cors_proxy_server

# Start it
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
/home/adamsl/planner/.venv/bin/python3 cors_proxy_server.py &

# Or use the system scripts
./start_voice_system.sh
```

### Issue: Livekit Server Not Running

**Symptoms**: `curl http://localhost:7880/` fails

**Solutions**:
```bash
# Check if running
ps aux | grep livekit-server

# Check systemd service
systemctl --user status livekit

# Start/restart if needed
systemctl --user start livekit
# or
./start_voice_system.sh
```

### Issue: Update Script Fails

**Symptoms**: `update_voice_token.sh` exits with error

**Solutions**:
1. Check Python virtual environment exists: `ls /home/adamsl/planner/.venv/bin/python3`
2. Check livekit package is installed: `/home/adamsl/planner/.venv/bin/python3 -c "import livekit; print('OK')"`
3. Verify .env file exists: `ls /home/adamsl/ottomator-agents/livekit-agent/.env`
4. Check environment variables: `grep LIVEKIT /home/adamsl/ottomator-agents/livekit-agent/.env`

### Issue: Browser Shows "Invalid Token" After Update

**Symptoms**: Updated token but browser still shows error

**Solutions**:
1. Hard refresh browser cache: Ctrl+Shift+R
2. Clear browser cache completely
3. Open in incognito/private window
4. Restart CORS proxy server (it serves the HTML)
5. Verify HTML file was actually updated

## Prevention Strategies

### 1. Monitoring (Recommended for Production)

Create a health check script:

```bash
#!/bin/bash
# File: /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/check_token_health.sh

cd "$(dirname "$0")"

# Check token validity
if ! ./verify_token.py 2>&1 | grep -q "VALID"; then
    echo "WARNING: Token is expired or invalid!"
    echo "Regenerating token..."
    ./update_voice_token.sh
    exit 1
fi

echo "Token is valid"
exit 0
```

Run hourly via cron:
```bash
0 * * * * /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/check_token_health.sh
```

### 2. Alerting

Get notified before tokens expire:

```bash
#!/bin/bash
# Alert if token expires in < 2 hours
./verify_token.py 2>&1 | grep "expires in" | awk '{if ($4 < 2) print "WARNING: Token expires soon!"}'
```

### 3. Migrate to Dynamic Tokens (Best)

See Option 2 in Long-Term Solutions above.

## Technical Details

### Token Structure

JWT tokens contain three parts (separated by `.`):
1. **Header**: Algorithm and token type
2. **Payload**: Claims (user, expiration, permissions)
3. **Signature**: Verification using secret key

Example payload:
```json
{
  "name": "User",
  "video": {
    "roomJoin": true,
    "room": "test-room",
    "canPublish": true,
    "canSubscribe": true,
    "canPublishData": true
  },
  "sub": "user1",
  "iss": "devkey",
  "nbf": 1766184718,     // Not Before (Unix timestamp)
  "exp": 1766271118      // Expiration (Unix timestamp)
}
```

### Token Expiration Calculation

- Token lifetime (TTL) defaults to 24 hours in `update_voice_token.sh`
- `nbf` (not before): Token issue time
- `exp` (expiration): `nbf` + TTL
- Current time must be between `nbf` and `exp` for token to be valid

### Why Tokens Expire

Security best practice:
- Limits damage from stolen tokens
- Forces periodic re-authentication
- Allows permission revocation
- Reduces token replay attack window

## Files Reference

### Configuration
- **Livekit credentials**: `/home/adamsl/ottomator-agents/livekit-agent/.env`
- **HTML with token**: `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/voice-agent-selector.html`

### Scripts
- **Update token**: `./update_voice_token.sh`
- **Verify token**: `./verify_token.py`
- **CORS proxy**: `./cors_proxy_server.py`
- **Start system**: `./start_voice_system.sh`
- **Stop system**: `./stop_voice_system.sh`

### Documentation
- **This guide**: `VOICE_AGENT_TOKEN_FIX.md`
- **JWT troubleshooting**: `JWT_TOKEN_TROUBLESHOOTING.md`
- **Token fix summary**: `TOKEN_FIX_SUMMARY.md`

## Summary

### What Happened
- JWT token expired after 24 hours (security feature)
- Livekit server rejected the expired token
- Connection failed with "token is expired (exp)" error

### What Was Fixed
- Generated fresh 24-hour token
- Updated HTML file automatically
- Restarted CORS proxy to serve new HTML
- Created verification tool

### What To Do Next Time
```bash
# Quick fix (30 seconds)
./update_voice_token.sh

# Verify it worked
./verify_token.py

# Restart browser
# Open http://localhost:9000
```

### Best Long-Term Solution
Implement dynamic token fetching (Option 2) to eliminate manual updates forever.

## Questions?

- Check token status: `./verify_token.py`
- Read detailed troubleshooting: `JWT_TOKEN_TROUBLESHOOTING.md`
- Generate new token: `./update_voice_token.sh`
- Get token via API: `curl http://localhost:9000/api/token`

The voice agent system is now working with a fresh token valid for 24 hours!
