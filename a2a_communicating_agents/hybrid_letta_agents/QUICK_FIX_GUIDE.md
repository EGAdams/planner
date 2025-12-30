# QUICK FIX GUIDE - Voice Agent Windows Connectivity

## The Problem (Visual)

```
Windows Browser                  WSL2 Linux
     │                               │
     │  Try: http://localhost:9000   │
     │  ─────────────────────────X   │  CORS Proxy (127.0.0.1:9000)
     │                               │  ❌ Only listening on WSL localhost
     │                               │
     │                               │  Letta Server (127.0.0.1:8283)
     │                               │  ❌ Only listening on WSL localhost
     │                               │
     │                               │  LiveKit Server (:::7880)
     │                               │  ✅ Listening on all interfaces
```

**Result**: Only "Agent Selection" LED is green (client-side JavaScript works)

---

## The Fix (One Command)

```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
./fix_wsl_network.sh
```

This script will:
1. ✅ Update CORS proxy to bind to `0.0.0.0:9000`
2. ✅ Restart Letta server to bind to `0.0.0.0:8283`
3. ✅ Verify network accessibility
4. ✅ Show you the Windows browser URL to use

---

## After Fix

```
Windows Browser                  WSL2 Linux
     │                               │
     │  Use: http://172.26.163.131:9000/debug
     │  ─────────────────────────✅  │  CORS Proxy (0.0.0.0:9000)
     │                               │  ✅ Accessible from Windows
     │                               │
     │  Can access API              │  Letta Server (0.0.0.0:8283)
     │  ─────────────────────────✅  │  ✅ Accessible from Windows
     │                               │
     │  Can connect to LiveKit      │  LiveKit Server (:::7880)
     │  ─────────────────────────✅  │  ✅ Already accessible
```

**Result**: All LEDs turn green, voice chat works!

---

## Test Before Fix

```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
python3 test_network_connectivity.py
```

**Expected Output (Before Fix):**
```
❌ FAIL: cors_proxy_wsl_ip
❌ FAIL: letta_wsl_ip
✅ PASS: livekit_wsl_ip
```

---

## Test After Fix

```bash
python3 test_network_connectivity.py
```

**Expected Output (After Fix):**
```
✅ PASS: cors_proxy_wsl_ip
✅ PASS: letta_wsl_ip
✅ PASS: livekit_wsl_ip
```

---

## Windows Browser Access

**After fix, use this URL from Windows:**

```
http://172.26.163.131:9000/debug
```

**Expected LED States:**
- 🟢 Agent Selection
- 🟢 WebSocket
- 🟢 LiveKit Room
- 🟢 Audio Input (after granting mic permission)
- 🟢 Audio Output
- 🟢 Message Send (after speaking)
- 🟢 Message Receive (after agent responds)

---

## If Still Not Working

### Windows Firewall Issue

Run in PowerShell (as Administrator):

```powershell
New-NetFirewallRule -DisplayName "WSL - CORS Proxy" -Direction Inbound -LocalPort 9000 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "WSL - Letta Server" -Direction Inbound -LocalPort 8283 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "WSL - LiveKit Server" -Direction Inbound -LocalPort 7880 -Protocol TCP -Action Allow
```

### Verify Services Are Running

```bash
# Check if services are running
ps aux | grep -E '(cors_proxy|letta|livekit)'

# Check if ports are bound to 0.0.0.0
netstat -tuln | grep -E '(9000|8283|7880)'
```

Should see:
```
tcp  0.0.0.0:9000  ← CORS Proxy (correct)
tcp  0.0.0.0:8283  ← Letta Server (correct)
tcp  :::7880       ← LiveKit Server (correct)
```

---

## Manual Fix (If Script Fails)

### Step 1: Update CORS Proxy

Edit `/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents/cors_proxy_server.py`

**Line 297 - Change:**
```python
server = http.server.HTTPServer(('localhost', 9000), CORSRequestHandler)
```

**To:**
```python
server = http.server.HTTPServer(('0.0.0.0', 9000), CORSRequestHandler)
```

### Step 2: Restart Services

```bash
# Kill old services
pkill -f cors_proxy_server.py
pkill -f "letta server"

# Start new services
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
python3 cors_proxy_server.py &
letta server --host 0.0.0.0 --port 8283 &
```

---

## Files Created for Diagnosis

| File | Purpose |
|------|---------|
| `test_network_connectivity.py` | Network diagnostic tool |
| `test_voice_agent_wsl.py` | Browser testing with Playwright |
| `fix_wsl_network.sh` | Automated fix script |
| `NETWORK_DIAGNOSIS_REPORT.md` | Detailed technical analysis |
| `TEST_RESULTS_SUMMARY.md` | Complete test results |
| `QUICK_FIX_GUIDE.md` | This guide |
| `screenshot_initial.png` | Browser test screenshot |
| `screenshot_connected.png` | Browser test screenshot |

---

## Summary

**Problem**: Services bound to `localhost` in WSL, unreachable from Windows browser  
**Fix**: Bind to `0.0.0.0` to accept connections from all network interfaces  
**Command**: `./fix_wsl_network.sh`  
**Test**: `http://172.26.163.131:9000/debug` in Windows browser  
**Expected**: All LEDs green, voice chat functional  

**Any questions?** Check `NETWORK_DIAGNOSIS_REPORT.md` for detailed analysis.
