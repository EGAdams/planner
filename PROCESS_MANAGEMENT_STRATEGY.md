# Process Management Strategy

Comprehensive guide for managing dashboard startup, service orchestration, and system automation.

## Quick Reference

### Start Dashboard
```bash
/home/adamsl/planner/start_sys_admin_dash.sh
```

### Stop All Services
```bash
kill $(lsof -t -i:3000)  # Dashboard
kill $(lsof -t -i:7880) # LiveKit server
kill $(lsof -t -i:8001) # Pydantic server
```

### Check Status
```bash
lsof -i :3000 -i :7880 -i :7881 -i :8001
```

### View Logs
```bash
tail -f /home/adamsl/planner/dashboard-startup.log
```

## Startup Process Flow

### Automated Startup Script (`start_sys_admin_dash.sh`)

**Purpose**: Reliably start the dashboard with all proper configurations.

**Process**:
```
1. Explicit Environment Variable Override
   └─ env ADMIN_PORT=3000 (prevents system interference)

2. Working Directory Setup
   └─ cd /home/adamsl/planner/dashboard

3. Background Execution
   └─ nohup npm start >> "$LOG_FILE" 2>&1 &

4. Initialization Wait
   └─ sleep 3 (allows server to bind port)

5. Startup Verification
   └─ lsof check on port 3000

6. Status Output
   └─ Success/failure message
```

**Why This Matters**:
- `env ADMIN_PORT=3000`: Ensures explicit port override
- `nohup`: Prevents termination when shell closes
- `>> "$LOG_FILE" 2>&1`: Captures all output for debugging
- `&`: Runs in background
- Verification: Confirms successful startup

### Manual Startup (For Debugging)

When automated startup fails:
```bash
cd /home/adamsl/planner/dashboard
env ADMIN_PORT=3000 npm start
```

This shows real-time output for troubleshooting.

## Service Orchestration

### Managed Services Overview

The dashboard manages three services through ServerOrchestrator:

#### 1. LiveKit Server
- **Status**: Core dependency for voice/video
- **Port**: 7880 (media), 7881 (signaling)
- **Location**: `/home/adamsl/ottomator-agents/livekit-agent`
- **Command**: `./livekit-server --dev --bind 0.0.0.0`
- **Management**: Can start/stop via dashboard API

#### 2. LiveKit Voice Agent
- **Status**: Voice interaction service
- **Port**: Dynamic (assigned by system)
- **Location**: `/home/adamsl/ottomator-agents/livekit-agent`
- **Command**: `/home/adamsl/planner/venv/bin/python livekit_mcp_agent.py dev`
- **Dependency**: Requires livekit-server running
- **Management**: Can start/stop via dashboard API

#### 3. Pydantic Web Server
- **Status**: AI agent endpoint
- **Port**: 8001
- **Location**: `/home/adamsl/ottomator-agents/pydantic-ai-mcp-agent/studio-integration-version`
- **Command**: `/home/adamsl/planner/venv/bin/python pydantic_mcp_agent_endpoint.py`
- **Management**: Can start/stop via dashboard API

### Service Management API

#### Get All Services
```bash
curl http://localhost:3000/api/servers
```

Response:
```json
{
  "livekit-server": {
    "running": true,
    "pid": 12345,
    "port": 7880,
    "uptime": 3600
  },
  "livekit-voice-agent": {
    "running": true,
    "pid": 12346,
    "uptime": 3550
  },
  "pydantic-web-server": {
    "running": false,
    "error": "Process exited with code 1"
  }
}
```

#### Start a Service
```bash
curl -X POST http://localhost:3000/api/servers/livekit-server/start
```

#### Stop a Service
```bash
curl -X POST http://localhost:3000/api/servers/livekit-server/stop
```

#### Restart a Service
```bash
curl -X POST http://localhost:3000/api/servers/livekit-server/restart
```

## Startup Automation

### Option 1: Windows Startup (Recommended for WSL2)

**File**: `start-dashboard.bat` (in Windows Startup folder)

**Setup Steps**:
1. Copy `start-dashboard.bat` to Windows clipboard
2. Press `Win + R`, type `shell:startup`, press Enter
3. Right-click → New → Text Document
4. Name it `StartDashboard.bat`
5. Paste content and save
6. Restart Windows to test

**What It Does**:
- Launches WSL2
- Runs bash startup script
- Waits for initialization
- Opens browser to dashboard

### Option 2: WSL2 Profile Startup

**Setup**:
Add to `~/.bashrc`:
```bash
# Auto-start Dashboard on WSL2 startup (optional)
if [ ! -e /tmp/dashboard_started ]; then
    /home/adamsl/planner/start_sys_admin_dash.sh
    touch /tmp/dashboard_started
fi
```

**Pros**: Automatic whenever WSL2 terminal opens
**Cons**: Only works if you open WSL2 terminal

### Option 3: systemd Service (Advanced)

For full system integration, create systemd services:

**File**: `/etc/systemd/system/admin-dashboard.service`
```ini
[Unit]
Description=Admin Dashboard Server
After=network.target

[Service]
Type=simple
User=adamsl
WorkingDirectory=/home/adamsl/planner/dashboard
Environment="ADMIN_PORT=3000"
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10
StandardOutput=append:/home/adamsl/planner/dashboard-startup.log
StandardError=append:/home/adamsl/planner/dashboard-startup.log

[Install]
WantedBy=multi-user.target
```

**Setup**:
```bash
sudo systemctl daemon-reload
sudo systemctl enable admin-dashboard.service
sudo systemctl start admin-dashboard.service
```

**Management**:
```bash
sudo systemctl status admin-dashboard.service
sudo systemctl restart admin-dashboard.service
sudo systemctl stop admin-dashboard.service
```

## Process Management Commands

### Check Running Services

**Dashboard**:
```bash
lsof -i :3000
```

**All Dashboard Services**:
```bash
lsof -i :3000 -i :7880 -i :7881 -i :8001
```

**More Detail**:
```bash
ps aux | grep -E 'node|npm|python' | grep -v grep
```

### Stop Services

**Single Service** (by port):
```bash
kill $(lsof -t -i:3000)
```

**Multiple Services**:
```bash
# Kill by port
kill $(lsof -t -i:3000) $(lsof -t -i:7880) $(lsof -t -i:8001)

# Kill by process name
pkill -f "npm start"
pkill -f "livekit-server"
pkill -f "pydantic_mcp_agent"
```

**Force Kill** (if graceful kill doesn't work):
```bash
kill -9 $(lsof -t -i:3000)
```

### Restart Services

**Dashboard Only**:
```bash
# Stop
kill $(lsof -t -i:3000) 2>/dev/null
# Wait
sleep 2
# Start
/home/adamsl/planner/start_sys_admin_dash.sh
```

**All Services** (using dashboard API):
```bash
# Via dashboard UI: manually restart each
# Via curl:
for service in livekit-server livekit-voice-agent pydantic-web-server; do
  curl -X POST http://localhost:3000/api/servers/$service/stop
  sleep 1
  curl -X POST http://localhost:3000/api/servers/$service/start
done
```

## Log Management

### Log Locations

**Dashboard Startup Log**:
```bash
/home/adamsl/planner/dashboard-startup.log
```

**Real-time Monitoring**:
```bash
tail -f /home/adamsl/planner/dashboard-startup.log
```

**View Last 50 Lines**:
```bash
tail -50 /home/adamsl/planner/dashboard-startup.log
```

### Log Rotation

Current logs grow indefinitely. For production, implement rotation:

**Option 1: Manual Cleanup**
```bash
# Archive old log
mv dashboard-startup.log dashboard-startup.log.old

# Start fresh
/home/adamsl/planner/start_sys_admin_dash.sh
```

**Option 2: Automatic Rotation with logrotate**

Create `/etc/logrotate.d/admin-dashboard`:
```
/home/adamsl/planner/dashboard-startup.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    create 0644 adamsl adamsl
    sharedscripts
    postrotate
        systemctl reload admin-dashboard.service > /dev/null 2>&1 || true
    endscript
}
```

Then run:
```bash
sudo logrotate /etc/logrotate.d/admin-dashboard
```

## Troubleshooting Process Issues

### Dashboard Won't Start

**Symptom**: `start_sys_admin_dash.sh` completes but server doesn't run

**Investigation**:
```bash
# Check logs
tail -20 /home/adamsl/planner/dashboard-startup.log

# Check for port conflicts
lsof -i :3000

# Try manual start for detailed error
cd /home/adamsl/planner/dashboard
npm start
```

**Solutions**:
1. **Port already in use**:
   ```bash
   kill -9 $(lsof -t -i:3000)
   sleep 2
   /home/adamsl/planner/start_sys_admin_dash.sh
   ```

2. **npm not found**:
   ```bash
   # Check npm location
   which npm
   # Update PATH in startup script if needed
   ```

3. **Dependencies missing**:
   ```bash
   cd /home/adamsl/planner/dashboard
   npm install
   ```

### Managed Services Won't Start

**Symptom**: Dashboard shows services as "stopped" when trying to start

**Investigation**:
```bash
# Check service command exists
which livekit-server
ls /home/adamsl/planner/venv/bin/python

# Try running command manually
cd /home/adamsl/ottomator-agents/livekit-agent
./livekit-server --dev --bind 0.0.0.0
```

**Solutions**:
1. **Missing executable**:
   - Install service: `apt install livekit-server`
   - Or update command in ServerOrchestrator configuration

2. **Working directory doesn't exist**:
   - Create directory: `mkdir -p /home/adamsl/ottomator-agents/livekit-agent`
   - Or update path in configuration

3. **Python venv not active**:
   - Create/activate venv in dashboard directory
   - Or use full path: `/home/adamsl/planner/venv/bin/python`

### Environment Variable Conflicts

**Symptom**: Server binds to port 3030 instead of 3000

**Cause**: System environment variable `ADMIN_PORT=3030`

**Check**:
```bash
printenv | grep ADMIN_PORT
```

**Fix**:
```bash
# Unset conflicting variable
unset ADMIN_PORT

# Export correct value
export ADMIN_PORT=3000

# Restart dashboard
/home/adamsl/planner/start_sys_admin_dash.sh
```

### Performance Issues

**Symptom**: Dashboard slow or unresponsive

**Investigation**:
```bash
# Check system resources
top
free -h
df -h

# Check Node.js memory usage
ps aux | grep node

# Check network connections
netstat -an | grep 3000
```

**Solutions**:
1. **Restart dashboard**: `kill -9 $(lsof -t -i:3000) && sleep 2 && /home/adamsl/planner/start_sys_admin_dash.sh`
2. **Clean up logs**: `truncate -s 0 /home/adamsl/planner/dashboard-startup.log`
3. **Restart managed services**: Use dashboard API to restart hung services

## Monitoring & Health Checks

### Health Check Endpoint
```bash
curl -s http://localhost:3000/api/servers | python -m json.tool
```

### Monitoring Script

Create `/usr/local/bin/check-dashboard.sh`:
```bash
#!/bin/bash
PORT=3000
TIMEOUT=5

if timeout $TIMEOUT bash -c "echo >/dev/tcp/localhost/$PORT" 2>/dev/null; then
    echo "✓ Dashboard is running on port $PORT"
    exit 0
else
    echo "✗ Dashboard is NOT responding on port $PORT"
    exit 1
fi
```

Make executable:
```bash
chmod +x /usr/local/bin/check-dashboard.sh
```

### Cron Job for Monitoring

Add to crontab (`crontab -e`):
```bash
# Check dashboard every 5 minutes, restart if down
*/5 * * * * /usr/local/bin/check-dashboard.sh || /home/adamsl/planner/start_sys_admin_dash.sh
```

## Best Practices

### Startup
- ✅ Use automated startup script for consistency
- ✅ Always verify startup with logs
- ✅ Test after system updates or config changes
- ❌ Don't start multiple instances on same port
- ❌ Don't rely on manual terminal startup in production

### Service Management
- ✅ Use API endpoints for service control
- ✅ Check logs when service fails
- ✅ Monitor port availability before starting
- ✅ Document service dependencies
- ❌ Don't kill -9 unless necessary
- ❌ Don't manually edit service configuration files while running

### Monitoring
- ✅ Set up automated health checks
- ✅ Monitor logs regularly
- ✅ Track service uptime
- ✅ Alert on port binding failures
- ❌ Don't ignore startup errors
- ❌ Don't let logs grow unbounded

### Maintenance
- ✅ Rotate logs regularly
- ✅ Test restarts periodically
- ✅ Document service changes
- ✅ Keep backup of working configuration
- ❌ Don't modify .env files while server is running
- ❌ Don't change ports without updating scripts

---

**Process Management Status**: Production Ready
**Last Updated**: November 6, 2025
