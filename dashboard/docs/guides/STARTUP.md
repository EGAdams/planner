# Dashboard Startup Guide

## ⚠️ WSL Environment Notice

This dashboard runs in Windows Subsystem for Linux (WSL). Key networking details:

- **WSL IP Address**: 172.26.163.131 (for Windows host access)
- **Dashboard Port**: 3030 (configurable via .env)
- **Listen Address**: 0.0.0.0 (all interfaces)
- **Access from Windows**: http://172.26.163.131:3030
- **Access from WSL**: http://127.0.0.1:3030 or http://localhost:3030

## Quick Start

This guide walks through setting up and running the Admin Dashboard for server management.

## System Architecture

The Admin Dashboard manages three managed servers:

```
┌─────────────────────────────────────────────────────┐
│          Admin Dashboard (Port 3030)                │
├─────────────────────────────────────────────────────┤
│  • Browser UI for managing servers                  │
│  • HTTP API for server control                      │
│  • Real-time SSE updates                            │
└─────────────────┬───────────────────────────────────┘
                  │
        ┌─────────┴────────┬──────────────┐
        │                  │              │
    ┌───▼───────┐  ┌───────▼────┐  ┌──────▼─────┐
    │ LiveKit   │  │ LiveKit    │  │ Pydantic   │
    │ Server    │  │Voice Agent │  │ Web Server │
    │(7880,7881)   │            │  │ (8001)     │
    └───────────┘  └────────────┘  └────────────┘
```

## Prerequisites

- Node.js 18+ with npm
- Python 3.8+ with venv at `/home/adamsl/planner/venv`
- Access to source directories for managed servers
- Port 3030 available for the dashboard (configurable in .env)

## Step 1: Environment Setup

The dashboard uses the `.env` file for configuration:

```ini
ADMIN_PORT=3030                    # Dashboard server port
ADMIN_HOST=127.0.0.1               # Dashboard server host
SUDO_PASSWORD=             # Password for privileged operations
```

**Status**: ✅ Already configured

## Step 2: Build the Dashboard

Compile TypeScript and Tailwind CSS:

```bash
cd /home/adamsl/planner/dashboard
npm run build
```

This runs three build steps:
- `build:components` - Compile TypeScript to JavaScript
- `build:backend` - Build backend services
- `build:css` - Compile Tailwind CSS

**Expected output**: No errors, `backend/dist/` folder created with compiled files

## Step 3: Server Registration

### What is Server Registration?

Server registration is the process of telling the dashboard which servers it should manage. All managed servers are defined in a **Server Registry** in the backend code.

### Server Registry Configuration

The dashboard manages servers defined in `backend/server.ts` (lines 35-57). The registry maps server IDs to their configuration:

```typescript
const SERVER_REGISTRY: Record<string, ServerConfig> = {
  'livekit-server': { ... },
  'livekit-voice-agent': { ... },
  'pydantic-web-server': { ... }
};

// Register all servers
orchestrator.registerServers(SERVER_REGISTRY);
```

**Status**: ✅ All three servers are already registered

### How Server Registration Works

1. **Backend Registration** (`backend/server.ts:64`)
   - ServerRegistry defines all managed servers
   - `orchestrator.registerServers()` loads them into memory
   - Servers become available via `/api/servers` endpoint

2. **Frontend Discovery** (browser)
   - Dashboard fetches servers from `/api/servers`
   - SSE stream sends real-time updates via `servers` event
   - UI displays all registered servers

3. **Verification**
   - Access http://127.0.0.1:3030
   - Check browser console (F12) for connection status
   - All 3 servers should appear in "Server Management" section

### Adding New Servers

To add a new managed server:

1. **Edit** `backend/server.ts` lines 35-57
2. **Add** new entry to SERVER_REGISTRY:
   ```typescript
   'my-new-server': {
     name: 'My New Server',
     command: '/path/to/command arg1 arg2',
     cwd: '/path/to/working/directory',
     color: '#RRGGBB',    // Hex color for UI
     ports: [8080, 8081], // Ports to monitor
   }
   ```
3. **Rebuild**: `npm run build`
4. **Restart**: Dashboard will auto-load new server

### Understanding the Managed Servers

The dashboard manages servers defined in the Server Registry:

#### 1. **LiveKit Server**
- **Location**: `/home/adamsl/ottomator-agents/livekit-agent`
- **Command**: `./livekit-server --dev --bind 0.0.0.0`
- **Ports**: 7880 (TCP), 7881
- **Status**: Not managed by dashboard (requires external installation)
- **Note**: Must be started separately if needed

#### 2. **LiveKit Voice Agent**
- **Location**: `/home/adamsl/ottomator-agents/livekit-agent`
- **Command**: `/home/adamsl/planner/venv/bin/python livekit_mcp_agent.py dev`
- **Ports**: None (runs as background worker)
- **Status**: Dashboard can start/stop

#### 3. **Pydantic Web Server**
- **Location**: `/home/adamsl/ottomator-agents/pydantic-ai-mcp-agent/studio-integration-version`
- **Command**: `/home/adamsl/planner/venv/bin/python pydantic_mcp_agent_endpoint.py`
- **Ports**: 8001
- **Status**: Dashboard can start/stop

## Step 4: Start the Dashboard Server

### Option A: Foreground (Development)

```bash
cd /home/adamsl/planner/dashboard
npm start
```

**Output**: Server logs visible in terminal

```
Server orchestrator initialized
[timestamps with event logs]
Admin dashboard listening on http://127.0.0.1:3030
```

**Access**: Open http://127.0.0.1:3030 in your browser

### Option B: Background (Production)

```bash
cd /home/adamsl/planner/dashboard
npm start > dashboard.log 2>&1 &
```

**Verify running**:
```bash
ps aux | grep "node backend/dist/server.js"
curl http://127.0.0.1:3030
```

## Step 5: Access the Dashboard

### From WSL Terminal (Linux)
```bash
http://127.0.0.1:3030
```

### From Windows Host (Browser)
```
http://172.26.163.131:3030
```

**Note**: WSL uses IP **172.26.163.131** to communicate with the Windows host. This address may vary - check with:
```bash
hostname -I | awk '{print $1}'
```

### Quick Test

```bash
# From WSL terminal
curl http://172.26.163.131:3030/api/servers

# From Windows PowerShell
curl.exe http://172.26.163.131:3030/api/servers
```

Navigate to: **http://172.26.163.131:3030** in your Windows browser

### Dashboard Features

**Server Status Panel**
- Shows all managed servers
- Real-time status (Running/Stopped)
- Port availability indicators
- Orphan process detection

**Server Controls**
- Start/Stop buttons for each server
- Kill orphan processes
- View process PIDs
- Monitor startup/shutdown events

**System Information**
- Active processes
- Ports in use
- System resource status
- Event log stream

## Step 6: Testing Server Management

### Test Starting a Server

1. Click **Start** on "Pydantic Web Server"
2. Monitor the dashboard for:
   - Status changes to "Running"
   - Port 8001 shows as "In Use"
   - Event log shows "Server started"
3. Verify: `curl http://127.0.0.1:8001`

### Test Stopping a Server

1. Click **Stop** on the running server
2. Monitor the dashboard for:
   - Status changes to "Stopped"
   - Port shows as "Available"
   - Event log shows "Server stopped"

### Test Orphan Process Detection

If a server crashes or is killed externally:

1. In dashboard, port still shows "In Use" (orphaned)
2. Dashboard shows "Orphaned Process" indicator
3. Click **Kill Orphan** to clean up
4. Verify port becomes "Available"

## Development Workflow

### Code Changes

1. **Edit TypeScript files** in `backend/services/` or `backend/server.ts`
2. **Rebuild**: `npm run build`
3. **Restart server**: Stop and run `npm start` again

### File Organization

```
dashboard/
├── backend/
│   ├── services/
│   │   ├── processManager.ts      # Process spawning/killing
│   │   ├── processMonitor.ts      # Health monitoring
│   │   ├── processStateStore.ts   # State persistence
│   │   └── serverOrchestrator.ts  # High-level coordination
│   ├── __tests__/                 # Jest unit tests
│   ├── server.ts                  # Main HTTP server
│   └── dist/                       # Compiled JavaScript
├── public/
│   ├── index.html                 # Dashboard UI
│   ├── styles/                    # Tailwind CSS
│   └── js/                        # Frontend scripts
├── process-state.json             # Runtime process state
└── package.json
```

### Running Tests

```bash
# Run all tests
npm test

# Watch mode
npm test:watch

# Coverage report
npm test:coverage
```

**Expected**: All 16 unit tests passing

## Monitoring & Logging

### Dashboard Logs

View real-time logs in the terminal where dashboard is running:

```
[Timestamp] ProcessManager: Process 'pydantic-web-server' started (PID: 12345)
[Timestamp] ProcessMonitor: Health check completed (3 processes)
[Timestamp] orchestrator.on('serverStarted'): Pydantic Web Server
```

### State Persistence

The dashboard maintains persistent state in `process-state.json`:

```json
{
  "pydantic-web-server": {
    "pid": "12345",
    "command": "/home/adamsl/planner/venv/bin/python ...",
    "startTime": "2025-11-13T19:30:00Z"
  }
}
```

**Key behaviors**:
- Automatically created on first run
- Updated when processes start/stop
- Cleaned up when processes exit
- Persists across dashboard restarts

### Event Stream (SSE)

The dashboard streams real-time events to the browser via Server-Sent Events (SSE):

```javascript
// Browser endpoint
GET /api/events

// Events received
event: server-update
data: {"servers": [...]}

event: health-check
data: {"timestamp": "...", "healthy": true}
```

## Troubleshooting

### Port 3030 Already in Use

```bash
# Find process on port 3030
lsof -i :3030

# Kill the process
kill -9 <PID>

# Or change port in .env
ADMIN_PORT=3031
```

### Dashboard Won't Start

**Check**: Node.js is installed
```bash
node --version
```

**Check**: Dependencies are installed
```bash
npm install
```

**Check**: Build succeeded
```bash
npm run build
```

### Servers Won't Start

**Check**: Source directories exist
```bash
ls -la /home/adamsl/ottomator-agents/livekit-agent
ls -la /home/adamsl/ottomator-agents/pydantic-ai-mcp-agent/studio-integration-version
```

**Check**: Python venv is available
```bash
/home/adamsl/planner/venv/bin/python --version
```

**Check**: Dashboard has permissions
```bash
chmod +x /home/adamsl/ottomator-agents/livekit-agent/livekit-server
```

### Orphaned Process Stuck

If you can't kill an orphan process:

```bash
# Find the process manually
ps aux | grep "livekit\|pydantic"

# Kill with SIGKILL
kill -9 <PID>

# Or use the dashboard's Kill Orphan button
```

## Production Deployment

### Systemd Service (Optional)

Create `/etc/systemd/system/admin-dashboard.service`:

```ini
[Unit]
Description=Admin Dashboard Server
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/adamsl/planner/dashboard
ExecStart=/usr/bin/node backend/dist/server.js
Restart=on-failure
RestartSec=10
User=adamsl
Environment="ADMIN_PORT=3030"

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable admin-dashboard
sudo systemctl start admin-dashboard
sudo systemctl status admin-dashboard
```

### PM2 Management (Alternative)

```bash
# Install PM2 globally
npm install -g pm2

# Start dashboard
pm2 start "npm start" --name "admin-dashboard" --cwd /home/adamsl/planner/dashboard

# Monitor
pm2 monit

# Logs
pm2 logs admin-dashboard
```

## Security Considerations

⚠️ **Important**: The `.env` file contains a sudo password. Keep it secure:

```bash
# Restrict permissions
chmod 600 /home/adamsl/planner/dashboard/.env

# Don't commit to version control
# Already in .gitignore
```

## Next Steps

1. ✅ Start the dashboard server
2. ✅ Access the UI at http://127.0.0.1:3030
3. ✅ Test starting/stopping managed servers
4. ✅ Monitor process state and logs
5. 📋 (Optional) Set up systemd service for auto-start
6. 📋 (Optional) Configure monitoring alerts

## Quick Commands Reference

```bash
# Build
npm run build

# Start (foreground)
npm start

# Start (background)
npm start > dashboard.log 2>&1 &

# Tests
npm test
npm test:watch
npm test:coverage

# View logs
tail -f dashboard.log

# Kill dashboard
pkill -f "node backend/dist/server.js"

# Check port
lsof -i :3030

# Curl API
curl http://127.0.0.1:3030/api/servers
curl http://127.0.0.1:3030/api/events
```

## Resources

- **ARCHITECTURE.md** - System design and data flow
- **README_TESTING.md** - Testing procedures
- **RESTART_INSTRUCTIONS.md** - Recovery procedures
- **START_SERVER_GUIDE.md** - Basic startup instructions

---

**Last Updated**: 2025-11-13
**Dashboard Status**: Production Ready ✅
**Test Coverage**: 100% of core services
