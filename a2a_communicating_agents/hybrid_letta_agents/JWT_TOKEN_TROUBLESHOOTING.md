# JWT Token Troubleshooting Guide

## Problem: "invalid token" or "token is expired (exp)" Error

### Quick Fix (Recommended)

Run the token update script:

```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
./update_voice_token.sh
```

Then refresh your browser at http://localhost:9000

### Understanding the Issue

**Root Cause**: The JWT token hardcoded in `voice-agent-selector.html` has expired.

Livekit JWT tokens have an expiration time (exp claim). By default, tokens are valid for 6 hours. Once expired, Livekit server rejects the connection with:

```
could not establish signal connection: invalid token
Error: go-jose/go-jose/jwt: validation failed, token is expired (exp)
```

### Token Lifecycle

1. **Token Generated**: Created with a specific TTL (Time To Live)
2. **Token Valid**: Can be used to connect to Livekit rooms
3. **Token Expired**: After TTL expires, Livekit rejects the token
4. **Need New Token**: Must generate and update with fresh token

### Analyzing a Token

To check if a token is expired:

```bash
python3 << 'EOF'
import json
import base64
from datetime import datetime

# Your token (just the payload part, or full JWT)
token = "YOUR_TOKEN_HERE"

# Decode
parts = token.split('.')
payload = parts[1] if len(parts) > 1 else token
padding = len(payload) % 4
if padding:
    payload += '=' * (4 - padding)

data = json.loads(base64.urlsafe_b64decode(payload))

print(f"Issued: {datetime.fromtimestamp(data['nbf'])}")
print(f"Expires: {datetime.fromtimestamp(data['exp'])}")
print(f"Current: {datetime.now()}")
print(f"Status: {'EXPIRED' if datetime.now().timestamp() > data['exp'] else 'VALID'}")
EOF
```

### Solutions

#### Option 1: Quick Update (24-hour token)

Use the automated script:

```bash
./update_voice_token.sh
```

This updates the HTML file with a fresh 24-hour token.

#### Option 2: Manual Token Generation

Generate a token manually:

```bash
/home/adamsl/planner/.venv/bin/python3 /home/adamsl/planner/.claude/skills/voice-agent-expert/scripts/generate_token.py
```

Then manually update the `TOKEN` constant in `voice-agent-selector.html` (line ~13).

#### Option 3: Use Dynamic Token API (Best for Production)

The CORS proxy server now has a token generation endpoint. Modify your frontend to fetch tokens dynamically:

```javascript
// Instead of hardcoded token:
const response = await fetch('http://localhost:9000/api/token?room=test-room&ttl=24');
const data = await response.json();
const TOKEN = data.token;
```

This ensures tokens are always fresh when connecting.

### Preventing Token Expiration

#### For Development

Use longer TTL tokens:

```bash
# Generate 7-day token
curl "http://localhost:9000/api/token?room=test-room&ttl=168"
```

#### For Production

Implement automatic token refresh:

```javascript
async function getOrRefreshToken() {
    const response = await fetch(`${PROXY_URL}/api/token?room=test-room&ttl=24`);
    const data = await response.json();
    return data.token;
}

// Use before connecting
const freshToken = await getOrRefreshToken();
await room.connect(LIVEKIT_URL, freshToken);
```

### Token Generation Endpoint

The CORS proxy server (`cors_proxy_server.py`) provides a token generation endpoint:

**Endpoint**: `GET /api/token`

**Parameters**:
- `room` (optional): Room name (default: "test-room")
- `identity` (optional): User identity (default: "user1")
- `ttl` (optional): Token lifetime in hours (default: 24)

**Examples**:

```bash
# Default 24-hour token
curl "http://localhost:9000/api/token"

# 7-day token for specific room
curl "http://localhost:9000/api/token?room=my-room&ttl=168"

# Custom identity
curl "http://localhost:9000/api/token?identity=alice&room=meeting-room&ttl=12"
```

**Response**:

```json
{
    "token": "eyJhbGci...",
    "url": "ws://localhost:7880",
    "room": "test-room",
    "ttl_hours": 24
}
```

### Verification Steps

After updating the token, verify it's working:

1. **Check token is valid**:
   ```bash
   curl -s "http://localhost:9000/api/token" | jq '.token' | xargs -I {} python3 -c "
   import json, base64, sys
   from datetime import datetime
   token = sys.argv[1].split('.')[1]
   padding = len(token) % 4
   if padding: token += '=' * (4 - padding)
   data = json.loads(base64.urlsafe_b64decode(token))
   print(f'Valid until: {datetime.fromtimestamp(data[\"exp\"])}')
   " {}
   ```

2. **Check HTML is updated**:
   ```bash
   grep "const TOKEN" voice-agent-selector.html
   ```

3. **Test connection**:
   - Open http://localhost:9000 in browser
   - Open browser console (F12)
   - Select an agent
   - Click Connect
   - Should connect without "invalid token" error

### Common Mistakes

1. **Browser cache**: Hard refresh (Ctrl+Shift+R) after updating token
2. **Wrong file**: Make sure you're editing the right HTML file
3. **CORS proxy not restarted**: The proxy serves cached HTML - restart it:
   ```bash
   pkill -f cors_proxy_server
   /home/adamsl/planner/.venv/bin/python3 cors_proxy_server.py &
   ```

### Files Involved

- **HTML with token**: `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/voice-agent-selector.html`
- **Token update script**: `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/update_voice_token.sh`
- **CORS proxy server**: `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/cors_proxy_server.py`
- **Token generator**: `/home/adamsl/planner/.claude/skills/voice-agent-expert/scripts/generate_token.py`
- **Livekit credentials**: `/home/adamsl/ottomator-agents/livekit-agent/.env`

### Debug Checklist

When you get token errors:

- [ ] Check current time vs token expiration
- [ ] Verify LIVEKIT_API_KEY and LIVEKIT_API_SECRET are set in .env
- [ ] Generate fresh token
- [ ] Update HTML file or use dynamic token API
- [ ] Hard refresh browser (clear cache)
- [ ] Check browser console for detailed error messages
- [ ] Verify Livekit server is running: `curl http://localhost:7880/`

### Automation Ideas

#### Cron Job for Daily Token Updates

```bash
# Add to crontab: update token daily at midnight
0 0 * * * /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/update_voice_token.sh
```

#### Health Check Script

```bash
#!/bin/bash
# Check if token will expire in next hour
python3 << 'EOF'
import re, base64, json
from datetime import datetime

with open('voice-agent-selector.html') as f:
    content = f.read()
    match = re.search(r"const TOKEN = '([^']+)'", content)
    if match:
        token = match.group(1)
        parts = token.split('.')
        payload = parts[1]
        padding = len(payload) % 4
        if padding: payload += '=' * (4 - padding)
        data = json.loads(base64.urlsafe_b64decode(payload))
        exp = data['exp']
        now = datetime.now().timestamp()
        hours_left = (exp - now) / 3600

        if hours_left < 1:
            print(f"WARNING: Token expires in {hours_left:.1f} hours!")
            exit(1)
        else:
            print(f"OK: Token valid for {hours_left:.1f} more hours")
            exit(0)
EOF
```

## Summary

- **Quick Fix**: Run `./update_voice_token.sh`
- **Root Cause**: JWT tokens expire after their TTL (default 6-24 hours)
- **Best Practice**: Use dynamic token generation API endpoint
- **Prevention**: Implement token refresh logic or use longer TTL for development
