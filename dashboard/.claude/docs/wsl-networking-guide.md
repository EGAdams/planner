# WSL Networking Guide for Admin Dashboard

## Overview

The Admin Dashboard runs in Windows Subsystem for Linux (WSL), which creates unique networking considerations. This guide helps you access and manage the dashboard from both WSL and Windows environments.

## Network Architecture

```
┌─────────────────────┐
│   Windows Host      │
│   (Your Computer)   │
│                     │
│  Browser:           │
│  http://172.26.163.131:3030
└──────────┬──────────┘
           │
    WSL Virtual Network
    (172.26.163.0/24)
           │
┌──────────▼──────────┐
│  WSL Linux VM       │
│  (172.26.163.131)   │
│                     │
│  Dashboard Server   │
│  Listening: 0.0.0.0:3030
│  (All interfaces)   │
└─────────────────────┘
```

## Access from Different Locations

### 1. From Windows Browser (Most Common)

**URL**: `http://172.26.163.131:3030`

**Steps**:
1. Open Chrome, Edge, or Firefox on Windows
2. Type: `http://172.26.163.131:3030`
3. Press Enter

**Troubleshooting**:
- If page doesn't load, WSL network connection may be down
- Try: `ipconfig` in Windows PowerShell to verify WSL network

### 2. From WSL Terminal

**URLs** (any of these work):
```bash
http://127.0.0.1:3030
http://localhost:3030
http://172.26.163.131:3030
```

**Test with curl**:
```bash
curl http://127.0.0.1:3030/api/servers
```

### 3. From Windows PowerShell

**Command**:
```powershell
curl.exe http://172.26.163.131:3030/api/servers
```

## Finding Your WSL IP Address

The IP address is typically **172.26.163.131**, but can vary.

### Check WSL IP from Within WSL

```bash
# Get WSL IP address
hostname -I | awk '{print $1}'

# Expected output:
# 172.26.163.131
```

### Check WSL IP from Windows PowerShell

```powershell
# List all WSL instances and IPs
wsl hostname -I

# Or for more detail:
wsl -l -v
```

### Verify Connection from Windows

```powershell
# Test connectivity to WSL
ping 172.26.163.131

# Test specific port
Test-NetConnection -ComputerName 172.26.163.131 -Port 3030 -InformationLevel Detailed
```

## Port Configuration

### Current Configuration

The dashboard is configured to:
- **Listen on**: 0.0.0.0 (all network interfaces)
- **Port**: 3030
- **Accessible from**: Windows host, WSL, and other machines on network

### Change Port

Edit `/home/adamsl/planner/dashboard/.env`:

```ini
# Default
ADMIN_PORT=3030

# Custom port example
ADMIN_PORT=8080
```

Then rebuild and restart:

```bash
npm run build
pkill -f "node backend/dist/server.js"
npm start > dashboard.log 2>&1 &
```

## Common Issues & Solutions

### Issue: "Connection Refused" or "Can't reach server"

**Possible Cause 1**: Dashboard not running
```bash
ps aux | grep "node backend/dist/server.js"
# Should show the process
```

**Fix**: Start the dashboard
```bash
cd /home/adamsl/planner/dashboard
npm start > dashboard.log 2>&1 &
```

**Possible Cause 2**: WSL network issue
```bash
# From WSL, test internal access
curl http://127.0.0.1:3030/api/servers

# If this works, issue is network bridge, not dashboard
```

**Fix**: Restart WSL network
```bash
# From Windows PowerShell (Admin)
Get-Service LxssManager | Restart-Service
```

### Issue: Port 3030 already in use

```bash
# Find what's using the port
lsof -i :3030

# Kill the process
kill -9 <PID>

# Or use a different port in .env
ADMIN_PORT=3031
```

### Issue: Windows can't reach WSL IP (172.26.163.131)

**Possible Cause**: WSL network down

```bash
# From Windows PowerShell
wsl --shutdown    # Shutdown all WSL instances

# Then restart WSL (will auto-start)
# Or manually start:
wsl
```

**Possible Cause**: Firewall blocking

```powershell
# From Windows PowerShell (Admin)
# Allow port 3030 through firewall
netsh advfirewall firewall add rule name="WSL Dashboard" dir=in action=allow protocol=tcp localport=3030
```

## Advanced: WSL Network Debugging

### Check WSL Status

```bash
# From Windows PowerShell
wsl --list --verbose

# Output:
#  NAME      STATE           VERSION
# * Ubuntu   Running         2
```

### Check DNS Resolution

```bash
# From WSL, verify nameserver is configured
cat /etc/resolv.conf

# Check if WSL can resolve Windows host
ping.exe 1.1.1.1
```

### Monitor Network Traffic

```bash
# Monitor port 3030 in WSL
sudo netstat -tulpn | grep 3030
# Or
sudo ss -tulpn | grep 3030
```

### WSL Network Configuration

WSL uses Hyper-V virtual switch for networking. Advanced configuration in `~/.wslconfig`:

```ini
[interop]
enabled=true
appendWindowsPath=true

[network]
generateHosts=true
generateResolvConf=true
```

## API Access Patterns

### Test Dashboard Health

```bash
# From Windows PowerShell
curl.exe http://172.26.163.131:3030/api/servers

# Expected response: JSON array of servers
```

### Monitor Real-time Events

```bash
# Test SSE connection
curl.exe -N http://172.26.163.131:3030/api/events

# Should stream events like:
# event: servers
# data: [...]
```

### Test Server Control

```bash
# Start a server (Pydantic Web Server example)
curl.exe -X POST http://172.26.163.131:3030/api/servers/pydantic-web-server?action=start

# Stop a server
curl.exe -X POST http://172.26.163.131:3030/api/servers/pydantic-web-server?action=stop
```

## WSL vs localhost Differences

| Aspect | 127.0.0.1 | localhost | 172.26.163.131 |
|--------|-----------|-----------|----------------|
| Accessible from WSL | ✅ Yes | ✅ Yes | ✅ Yes |
| Accessible from Windows | ❌ No | ❌ No | ✅ Yes |
| Accessible from network | ❌ No | ❌ No | ✅ Depends on firewall |
| Performance | Fast | Fast | Fast (local network) |
| Preferred use | Testing in WSL | Development | Production, Windows access |

## Production Deployment Notes

### For Production WSL Setup

1. **Firewall Rules**: Allow port 3030 through Windows firewall
2. **Listen Address**: Keep at 0.0.0.0 for Windows host access
3. **SSL/HTTPS**: Consider reverse proxy for HTTPS
4. **Monitoring**: Set up logging and monitoring

### Using a Reverse Proxy (nginx)

If you need SSL or advanced routing:

```bash
# Install nginx in WSL
sudo apt-get install nginx

# Configure to proxy port 3030
# Edit: /etc/nginx/sites-available/default
# Add proxy_pass http://127.0.0.1:3030;
```

## Troubleshooting Checklist

When dashboard isn't accessible:

1. ✅ **Check WSL is running**: `wsl --list --verbose`
2. ✅ **Check dashboard is running**: `ps aux | grep "node backend"`
3. ✅ **Check correct IP**: `hostname -I`
4. ✅ **Check correct port**: Check `.env` ADMIN_PORT
5. ✅ **Test internal access**: `curl http://127.0.0.1:3030/api/servers`
6. ✅ **Test external access**: `curl http://172.26.163.131:3030/api/servers` (from WSL)
7. ✅ **Test from Windows**: Ping WSL IP first: `ping 172.26.163.131`
8. ✅ **Check firewall**: Allow Windows firewall rule for port 3030

## Quick Reference Commands

### In WSL Terminal

```bash
# Start dashboard
npm start > dashboard.log 2>&1 &

# Test from WSL
curl http://127.0.0.1:3030/api/servers

# Get WSL IP
hostname -I | awk '{print $1}'

# Check if port is open
netstat -tulpn | grep 3030
```

### In Windows PowerShell

```powershell
# Test from Windows
curl.exe http://172.26.163.131:3030/api/servers

# Ping WSL
ping 172.26.163.131

# List WSL instances
wsl --list --verbose

# Shutdown WSL
wsl --shutdown
```

## Related Documentation

- [Startup Guide](./startup.md) - Getting started with dashboard
- [Server Registration Skill](./server-registration-skill.md) - Managing servers
- [WSL Official Docs](https://docs.microsoft.com/en-us/windows/wsl/) - Microsoft WSL documentation

---

**Status**: Production Ready ✅
**Last Updated**: 2025-11-13
**WSL Version**: WSL 2 (Hyper-V based)
