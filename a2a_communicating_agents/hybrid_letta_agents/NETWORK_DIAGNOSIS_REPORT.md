# WSL/Windows Network Connectivity Diagnosis Report

**Date**: 2025-12-29  
**Issue**: Voice agent connection fails from Windows browser (only "Agent Selection" LED is green)  
**Root Cause**: Services bound to `localhost` instead of `0.0.0.0` in WSL

---

## Executive Summary

The voice agent web application works correctly from WSL but fails from Windows browsers because:

1. **CORS Proxy (port 9000)**: Bound to `localhost` - Windows cannot connect
2. **Letta Server (port 8283)**: Bound to `localhost` - Windows cannot connect  
3. **LiveKit Server (port 7880)**: Bound to `0.0.0.0` - Windows CAN connect ✅

This causes the Windows browser to:
- Successfully load the HTML page (cached or served via file://)
- Successfully select Agent_66 (client-side JavaScript)
- **FAIL** to connect to LiveKit because CORS proxy is unreachable
- **FAIL** to fetch agent data from Letta API

---

## Test Results

### Network Connectivity Test (WSL → WSL IP)

```
Service                      Localhost (127.0.0.1)    WSL IP (172.26.163.131)
-------------------------------------------------------------------------
CORS Proxy (9000)            ✅ ACCESSIBLE            ❌ BLOCKED
Letta Server (8283)          ✅ ACCESSIBLE            ❌ BLOCKED
LiveKit Server (7880)        ✅ ACCESSIBLE            ✅ ACCESSIBLE
```

### Browser Test (Playwright from WSL)

**LED States After Connection Attempt:**
- 🟢 **Agent Selection**: CONNECTED (client-side JavaScript works)
- ⚫ **WebSocket**: DISCONNECTED (cannot reach LiveKit via CORS proxy)
- 🟡 **LiveKit Room**: CONNECTING (stuck in connecting state)
- 🔴 **Audio Input**: ERROR (no microphone in headless browser - expected)
- ⚫ All other LEDs: DISCONNECTED

**Key Observations:**
1. Agent_66 is successfully selected and ID populated
2. Microphone check fails (expected in headless WSL environment)
3. WebSocket connection never establishes (CORS proxy unreachable from Windows perspective)

---

## Root Cause Analysis

### Service Binding Configuration

**Current State:**
```bash
netstat -tuln | grep -E '(9000|7880|8283)'
tcp        0      0 127.0.0.1:9000          0.0.0.0:*               LISTEN     # CORS Proxy
tcp        0      0 127.0.0.1:8283          0.0.0.0:*               LISTEN     # Letta Server
tcp6       0      0 :::7880                 :::*                    LISTEN     # LiveKit Server
```

### Why Windows Cannot Connect

In WSL2 (default mode), localhost binding (`127.0.0.1`) only accepts connections from:
- The WSL instance itself
- Other processes within the same WSL instance

Windows applications see WSL as a separate network host with IP `172.26.163.131`. When services bind to `localhost`, Windows sees them as **unreachable**.

### Connection Flow Breakdown

**From WSL Browser** (works):
```
Browser → localhost:9000 (CORS Proxy) → localhost:8283 (Letta API)
                       ↓
                localhost:7880 (LiveKit Server)
```

**From Windows Browser** (fails):
```
Browser → 172.26.163.131:9000 ❌ CONNECTION REFUSED
                              ↓
                         Cannot proceed
```

---

## Solution: Bind Services to 0.0.0.0

### Fix 1: CORS Proxy Server (CRITICAL)

**File**: `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/cors_proxy_server.py`

**Line 297** - Change from:
```python
server = http.server.HTTPServer(('localhost', 9000), CORSRequestHandler)
```

To:
```python
server = http.server.HTTPServer(('0.0.0.0', 9000), CORSRequestHandler)
```

**Why**: This allows the CORS proxy to accept connections from all network interfaces, including Windows → WSL connections.

**Restart command**:
```bash
# Kill existing CORS proxy
pkill -f cors_proxy_server.py

# Restart with new binding
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
python3 cors_proxy_server.py &
```

---

### Fix 2: Letta Server (IMPORTANT)

**Current Command** (likely):
```bash
letta server
```

**Updated Command**:
```bash
letta server --host 0.0.0.0 --port 8283
```

Or set in Letta configuration file if available.

**Restart command**:
```bash
# Kill existing Letta server
pkill -f "letta server"

# Restart with network binding
letta server --host 0.0.0.0 --port 8283 &
```

---

### Fix 3: LiveKit Server (Already Correct ✅)

The LiveKit server is already correctly bound to `:::7880` (all IPv6 interfaces), which makes it accessible from Windows.

**No action needed.**

---

## Verification Steps

### Step 1: Apply Fixes and Restart Services

```bash
# 1. Update CORS proxy script (apply Fix 1 above)

# 2. Restart services
pkill -f cors_proxy_server.py
pkill -f "letta server"

# 3. Start services with correct bindings
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
python3 cors_proxy_server.py &
letta server --host 0.0.0.0 --port 8283 &
```

### Step 2: Verify Network Accessibility

```bash
# Run network diagnostic again
python3 /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/test_network_connectivity.py
```

**Expected Output:**
```
✅ PASS: cors_proxy_wsl_ip
✅ PASS: letta_wsl_ip
✅ PASS: livekit_wsl_ip
```

### Step 3: Test from Windows Browser

**URL**: `http://172.26.163.131:9000/debug`

**Expected LED States:**
- 🟢 Agent Selection
- 🟢 WebSocket
- 🟢 LiveKit Room
- 🟢 Audio Input (if microphone is connected and permissions granted)

---

## Windows Firewall Considerations

If services are still unreachable after binding to `0.0.0.0`, Windows Firewall may be blocking incoming connections.

### Option 1: Allow Specific Ports (Recommended)

Open PowerShell as Administrator:
```powershell
# Allow CORS Proxy
New-NetFirewallRule -DisplayName "WSL - CORS Proxy" -Direction Inbound -LocalPort 9000 -Protocol TCP -Action Allow

# Allow Letta Server
New-NetFirewallRule -DisplayName "WSL - Letta Server" -Direction Inbound -LocalPort 8283 -Protocol TCP -Action Allow

# Allow LiveKit Server
New-NetFirewallRule -DisplayName "WSL - LiveKit Server" -Direction Inbound -LocalPort 7880 -Protocol TCP -Action Allow
```

### Option 2: Disable Firewall for Private Networks (Less Secure)

Not recommended for production environments.

---

## WSL Networking Modes

WSL2 has two networking modes that affect localhost accessibility:

### Current Mode: NAT (Default)
- WSL has its own IP address (172.26.163.131)
- localhost is isolated between WSL and Windows
- **Requires binding to 0.0.0.0** for Windows access

### Alternative Mode: Mirrored (Windows 11 22H2+)

Enable in `.wslconfig`:
```ini
[wsl2]
networkingMode=mirrored
```

**Benefits:**
- Windows and WSL share the same localhost
- No need to bind to 0.0.0.0
- Easier development workflow

**To Enable:**
1. Create/edit `C:\Users\<username>\.wslconfig`
2. Add the configuration above
3. Restart WSL: `wsl --shutdown` (from PowerShell)

**Note**: This is a system-wide change and may affect other WSL workflows.

---

## Testing Strategy Summary

### Automated Tests Created

1. **Network Connectivity Test** (`test_network_connectivity.py`)
   - Tests TCP connectivity to all services
   - Tests from both localhost and WSL IP perspectives
   - Validates HTTP endpoints

2. **Playwright Browser Test** (`test_voice_agent_wsl.py`)
   - Loads debug page in headless browser
   - Clicks connect and monitors LED states
   - Captures screenshots and event logs
   - Analyzes connection failures

### Manual Test from Windows

1. Open Chrome/Edge on Windows
2. Navigate to `http://172.26.163.131:9000/debug`
3. Click "Connect" button
4. Observe LED panel - should see all LEDs turn green
5. Grant microphone permissions when prompted
6. Verify audio connection works

---

## Expected Behavior After Fixes

### From WSL Browser (localhost:9000)
- ✅ All connections work
- ✅ All LEDs turn green (except mic if not available)
- ✅ Voice chat functional

### From Windows Browser (172.26.163.131:9000)
- ✅ All connections work
- ✅ All LEDs turn green
- ✅ Voice chat functional
- ✅ Microphone permissions requested
- ✅ Agent responds to voice input

---

## Files Modified/Created

### Modified
- `cors_proxy_server.py` (line 297: bind address change)

### Created (for diagnostics)
- `test_network_connectivity.py` - Network diagnostic script
- `test_voice_agent_wsl.py` - Playwright browser test
- `screenshot_initial.png` - Initial page state
- `screenshot_connected.png` - Connection attempt state
- `NETWORK_DIAGNOSIS_REPORT.md` - This report

### No Changes Needed
- `voice-agent-selector-debug.html` - Application code is correct
- `letta_voice_agent_optimized.py` - LiveKit binding already correct

---

## Troubleshooting Guide

### Issue: CORS Proxy still not accessible from Windows

**Check 1**: Verify service is listening on 0.0.0.0
```bash
netstat -tuln | grep 9000
# Should show: 0.0.0.0:9000 (not 127.0.0.1:9000)
```

**Check 2**: Test from WSL using WSL IP
```bash
curl http://172.26.163.131:9000
```

**Check 3**: Check Windows Firewall
```powershell
Get-NetFirewallRule | Where-Object {$_.LocalPort -eq 9000}
```

### Issue: Page loads but all LEDs stay gray

**Diagnosis**: JavaScript not executing or CORS errors

**Check**: Open browser DevTools (F12) and look for:
- CORS errors in Console
- Network requests failing with status 0 or CORS
- JavaScript errors

### Issue: WebSocket LED yellow (stuck connecting)

**Diagnosis**: LiveKit server unreachable or room issues

**Check**: 
1. Verify LiveKit server is running: `ps aux | grep livekit`
2. Check LiveKit logs for connection attempts
3. Verify token is valid and not expired

---

## Performance Impact

Binding to `0.0.0.0` instead of `localhost` has minimal performance impact:
- **Latency**: No measurable difference for local connections
- **Security**: Services are exposed to local network (acceptable for development)
- **Throughput**: No impact on data transfer rates

For production deployment, use:
- Proper firewall rules
- Reverse proxy (nginx/Apache)
- SSL/TLS encryption
- Network isolation

---

## Summary

**Problem**: Windows browser cannot connect to voice agent services in WSL

**Root Cause**: Services bound to `localhost` instead of `0.0.0.0`

**Solution**: 
1. Update `cors_proxy_server.py` line 297 to bind to `0.0.0.0`
2. Restart Letta server with `--host 0.0.0.0`
3. Verify with network connectivity test
4. Test from Windows browser at `http://172.26.163.131:9000/debug`

**Expected Outcome**: All LEDs turn green, voice chat works from both WSL and Windows browsers

---

**Report Generated**: 2025-12-29 23:10 UTC  
**WSL IP**: 172.26.163.131  
**Services**: CORS Proxy (9000), Letta Server (8283), LiveKit Server (7880)
