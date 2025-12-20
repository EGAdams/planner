# JWT Token Expiration Fix - Summary

## Problem Solved

**Error**: "could not establish signal connection: invalid token" with "token is expired (exp)"

**Root Cause**: The JWT token hardcoded in `voice-agent-selector.html` expired 15.6 hours ago (expired on 2025-12-17 21:41:00).

## Immediate Fix Applied

1. Generated fresh 24-hour JWT token
2. Updated `voice-agent-selector.html` with new token
3. Token now valid until: **2025-12-19 13:20:55** (24 hours from now)

## Quick Fix for Future Token Expiration

When you see "invalid token" or "token is expired" errors:

```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
./update_voice_token.sh
```

This will:
- Generate a fresh 24-hour token
- Update the HTML file automatically
- Back up the old file

Then refresh your browser at http://localhost:9000

## Long-Term Solutions Implemented

### 1. Token Update Script

Created `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/update_voice_token.sh`

This script automates token regeneration and HTML file updates.

### 2. Dynamic Token API

Enhanced CORS proxy server (`cors_proxy_server.py`) with a token generation endpoint:

**Endpoint**: `GET http://localhost:9000/api/token`

**Parameters**:
- `room` (optional, default: "test-room")
- `identity` (optional, default: "user1")
- `ttl` (optional, default: 24 hours)

**Example**:
```bash
curl "http://localhost:9000/api/token?room=my-room&ttl=48"
```

**Response**:
```json
{
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "url": "ws://localhost:7880",
    "room": "my-room",
    "ttl_hours": 48
}
```

### 3. Future Enhancement Option

The frontend can be modified to fetch tokens dynamically instead of using hardcoded tokens:

```javascript
// Before connecting, fetch a fresh token
const response = await fetch(`${PROXY_URL}/api/token?room=test-room&ttl=24`);
const data = await response.json();
const TOKEN = data.token;

await room.connect(LIVEKIT_URL, TOKEN);
```

This ensures tokens are always fresh.

## Files Modified

1. `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/voice-agent-selector.html`
   - Updated TOKEN constant with fresh 24-hour token
   - Added comment with expiration time and regeneration instructions

2. `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/cors_proxy_server.py`
   - Added `/api/token` endpoint for dynamic token generation
   - Loads Livekit credentials from environment
   - Supports configurable TTL via query parameters

## Files Created

1. `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/update_voice_token.sh`
   - Automated token update script
   - Generates fresh 24-hour token
   - Updates HTML file
   - Creates backup

2. `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/JWT_TOKEN_TROUBLESHOOTING.md`
   - Comprehensive troubleshooting guide
   - Token analysis examples
   - Debug checklist
   - Prevention strategies

3. `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/TOKEN_FIX_SUMMARY.md`
   - This summary document

## Verification Steps

To verify the fix is working:

1. **Check token validity**:
   ```bash
   python3 << 'EOF'
   import json, base64, re
   from datetime import datetime
   with open('voice-agent-selector.html') as f:
       content = f.read()
       match = re.search(r"const TOKEN = '([^']+)'", content)
       token = match.group(1)
       parts = token.split('.')
       payload = parts[1]
       padding = len(payload) % 4
       if padding: payload += '=' * (4 - padding)
       data = json.loads(base64.urlsafe_b64decode(payload))
       exp = datetime.fromtimestamp(data['exp'])
       now = datetime.now()
       hours = (exp.timestamp() - now.timestamp()) / 3600
       print(f"Token expires: {exp}")
       print(f"Status: {'VALID' if exp > now else 'EXPIRED'}")
       print(f"Time remaining: {hours:.1f} hours")
   EOF
   ```

2. **Test the web interface**:
   - Open http://localhost:9000
   - Select an agent
   - Click Connect
   - Should connect without "invalid token" error

3. **Test dynamic token API**:
   ```bash
   curl -s "http://localhost:9000/api/token" | jq .
   ```

## Why This Problem Happened

1. **JWT tokens expire**: All JWT tokens have an expiration time for security
2. **Hardcoded token**: The token was hardcoded in the HTML file
3. **No refresh mechanism**: There was no automatic token refresh
4. **Previous token**: Token was generated on 2025-12-17 15:41:00, expired 6 hours later

## Token Details

### Old (Expired) Token
- **Issued**: 2025-12-17 15:41:00
- **Expired**: 2025-12-17 21:41:00
- **Lifetime**: 6.0 hours
- **Status**: EXPIRED (15.6 hours ago)

### New (Current) Token
- **Issued**: 2025-12-18 13:20:55
- **Expires**: 2025-12-19 13:20:55
- **Lifetime**: 24.0 hours
- **Status**: VALID

## Troubleshooting

If you still see token errors:

1. **Hard refresh browser**: Ctrl+Shift+R (clear cache)
2. **Verify CORS proxy is running**: `curl http://localhost:9000/`
3. **Check token in HTML**: `grep "const TOKEN" voice-agent-selector.html`
4. **Generate fresh token**: `./update_voice_token.sh`
5. **Check Livekit server**: `curl http://localhost:7880/`

## Prevention

To avoid this issue in the future:

1. **Use the update script** when tokens expire: `./update_voice_token.sh`
2. **Set up a cron job** to auto-update tokens daily:
   ```bash
   0 0 * * * /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/update_voice_token.sh
   ```
3. **Migrate to dynamic tokens** by modifying the frontend to fetch tokens from `/api/token`
4. **Monitor token expiration** with the health check script in the troubleshooting guide

## Next Steps

### For Immediate Use
- Token is now valid for 24 hours
- Just refresh your browser at http://localhost:9000
- Everything should work

### For Long-Term Reliability
Consider implementing dynamic token fetching:

1. Modify `voice-agent-selector.html` to fetch tokens on demand
2. Remove hardcoded TOKEN constant
3. Call `/api/token` endpoint before each connection
4. Implement token refresh logic for long-running sessions

### Example Implementation

```javascript
// In voice-agent-selector.html, replace hardcoded TOKEN with:

async function getToken(roomName) {
    const response = await fetch(`${PROXY_URL}/api/token?room=${roomName}&ttl=24`);
    const data = await response.json();
    return data.token;
}

// Then in connect function:
window.connect = async function() {
    // ... existing code ...

    const roomName = getRoomName();
    const token = await getToken(roomName);  // Dynamic token!

    await room.connect(LIVEKIT_URL, token, {
        autoSubscribe: true,
    });

    // ... rest of code ...
};
```

This ensures tokens are always fresh and eliminates the need for manual updates.

## Summary

- **Problem**: JWT token expired
- **Immediate Fix**: Updated HTML with fresh 24-hour token
- **Quick Fix Tool**: `./update_voice_token.sh` script
- **Long-Term Fix**: Dynamic token API endpoint at `/api/token`
- **Prevention**: Cron job or migrate to dynamic tokens
- **Documentation**: Complete troubleshooting guide created

The system is now working and you have multiple options for managing tokens going forward.
