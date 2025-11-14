# Admin Dashboard - Complete Documentation

**Version:** 1.0.0
**Location:** `~/planner/dashboard`
**Port:** 3030
**Purpose:** Real-time system administration and server management interface

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Features](#features)
4. [Installation & Setup](#installation--setup)
5. [Server Registry Configuration](#server-registry-configuration)
6. [API Reference](#api-reference)
7. [Components](#components)
8. [Testing Guide](#testing-guide)
9. [Common Use Cases](#common-use-cases)
10. [Troubleshooting](#troubleshooting)
11. [Development Guide](#development-guide)

---

## Overview

The Admin Dashboard is a TypeScript-based real-time monitoring and management system for servers and system processes. It provides a unified interface for starting/stopping servers, monitoring port usage, and managing system processes.

### Key Capabilities

- **Real-time Port Monitoring**: View all listening ports with live updates every 5 seconds
- **Server Lifecycle Management**: Start/stop registered servers with a single click
- **Process Management**: Kill processes (including orphaned processes) directly from the UI
- **Orphan Detection**: Automatically detects servers running outside dashboard management
- **Live Updates**: Server-Sent Events (SSE) provide real-time updates without page refresh
- **Color-Coded Status**: Visual indicators for different servers and their states

### Current Server Registry

As of the latest configuration, these servers are registered:

| Server ID | Name | Port(s) | Color | Purpose |
|-----------|------|---------|-------|---------|
| `livekit-server` | LiveKit Server | 7880, 7881 | Blue | Voice/video infrastructure |
| `livekit-voice-agent` | LiveKit Voice Agent | None | Green | Voice AI agent |
| `pydantic-web-server` | Pydantic Web Server | 8000 | Purple | Voice agent API & UI |

---

## Architecture

### Technology Stack

- **Backend**: Node.js + TypeScript
- **Frontend**: Web Components + Tailwind CSS
- **Communication**: REST API + Server-Sent Events (SSE)
- **Build System**: TypeScript Compiler + Tailwind CLI

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (Browser)                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ ServerList   │  │ PortMonitor  │  │ProcessKiller │      │
│  │ Component    │  │ Component    │  │  Component   │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │               │
│         └──────────────────┼──────────────────┘              │
│                            │                                  │
│                  ┌─────────▼─────────┐                       │
│                  │    EventBus       │                       │
│                  │  (Pub/Sub System) │                       │
│                  └─────────┬─────────┘                       │
│                            │                                  │
│                  ┌─────────▼─────────┐                       │
│                  │   SSE Manager     │                       │
│                  │ (Real-time Conn)  │                       │
│                  └─────────┬─────────┘                       │
└────────────────────────────┼─────────────────────────────────┘
                             │ HTTP/SSE
┌────────────────────────────▼─────────────────────────────────┐
│                    Backend (Node.js Server)                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────────────────────────────────────────┐   │
│  │             server.ts (Main Server)                   │   │
│  │                                                        │   │
│  │  • REST API Endpoints                                 │   │
│  │  • SSE Event Broadcasting                             │   │
│  │  • Server Process Management                          │   │
│  │  • Port Monitoring (via ss/netstat)                   │   │
│  │  • Process Killing (via kill -9)                      │   │
│  └──────────────────────────────────────────────────────┘   │
│                            │                                  │
│                  ┌─────────▼─────────┐                       │
│                  │ SERVER_REGISTRY   │                       │
│                  │  (Configuration)  │                       │
│                  └───────────────────┘                       │
└─────────────────────────────────────────────────────────────┘
```

### Design Principles

1. **Single Responsibility**: Each component has one clear purpose
2. **Event-Driven**: Components communicate via the EventBus (no tight coupling)
3. **Web Components**: Encapsulated, reusable UI elements with Shadow DOM
4. **Real-time Updates**: SSE pushes updates to all connected clients every 5 seconds
5. **ES Module Singletons**: EventBus and SSEManager are module-level singletons

---

## Features

### 1. Server Management

**Visual Status Indicators:**
- 🟢 Green dot = Server running and managed by dashboard
- 🔴 Red dot = Server stopped
- 🟥 Red background = Orphaned (running but not managed by dashboard)

**Actions:**
- **Start Server**: Spawns process with configured command and working directory
- **Stop Server**: Gracefully kills the managed process
- **Kill Orphaned**: Force kills orphaned processes with sudo privileges

**Server Cards Display:**
```
┌──────────────────────────────────────────────┐
│ 🟢 LiveKit Server                [Stop]      │
│    livekit-server                            │
└──────────────────────────────────────────────┘

┌──────────────────────────────────────────────┐
│ 🔴 Pydantic Web Server           [Start]     │
│    pydantic-web-server                       │
└──────────────────────────────────────────────┘
```

### 2. Port Monitoring

**Information Displayed:**
- Port number
- Protocol (tcp/tcp6/udp)
- Process ID (PID)
- Program name
- Full command line
- Color-coded by server (if registered)

**Orphan Detection:**
- Processes using registered ports but not started by dashboard are marked "ORPHANED"
- Red background highlights orphaned processes
- "Force Kill" button for immediate termination

**Example Display:**
```
┌──────┬──────────┬─────┬─────────┬─────────────────┬─────────┐
│ Port │ Protocol │ PID │ Program │ Command         │ Actions │
├──────┼──────────┼─────┼─────────┼─────────────────┼─────────┤
│ 7880 │ TCP6     │1234 │ livekit │ ./livekit-...   │ [Kill]  │
│ 8000 │ TCP6     │5678 │ python3 │ python pyda...  │ [Kill]  │
│ 3030 │ TCP6     │9012 │ node    │ node backend... │ [Kill]  │
└──────┴──────────┴─────┴─────────┴─────────────────┴─────────┘
```

### 3. Real-time Updates

**Server-Sent Events (SSE) Stream:**
- **Frequency**: Updates every 5 seconds
- **Events**: `ports-updated`, `servers-updated`
- **Auto-reconnect**: Handles connection drops gracefully
- **Visual Indicator**: Pulsing green dot shows live connection

**Update Flow:**
1. Backend polls system every 5 seconds
2. Detects changes in ports/servers
3. Broadcasts via SSE to all connected clients
4. Components update UI automatically

### 4. Process Management

**Kill Operations:**
- **Regular Kill**: `kill -9 <pid>` for user-owned processes
- **Sudo Kill**: `echo "password" | sudo -S kill -9 <pid>` for privileged processes
- **Port-based Kill**: Automatically finds and kills process on specific port

**Safety Features:**
- Confirmation dialogs before killing (implemented in process-killer component)
- Success/failure notifications
- Automatic UI refresh after kill operations

---

## Installation & Setup

### 1. Prerequisites

```bash
# Required software
node --version    # v14+ required
npm --version     # v6+ required
```

### 2. Initial Setup

```bash
cd ~/planner/dashboard

# Install dependencies
npm install

# Configure environment
cp .env.example .env
nano .env
```

### 3. Environment Configuration

Edit `.env` file:

```bash
# Sudo password for killing privileged processes
SUDO_PASSWORD=your_actual_password

# Admin dashboard port (default: 3030)
ADMIN_PORT=3030
```

**⚠️ SECURITY WARNING:**
- The `.env` file contains your sudo password
- Never commit `.env` to git (it's in `.gitignore`)
- Restrict file permissions: `chmod 600 .env`

### 4. Build the Project

```bash
# Build everything (components + backend + CSS)
npm run build

# Or build individually:
npm run build:components   # Compile TypeScript components
npm run build:backend      # Compile backend server
npm run build:css          # Build Tailwind CSS
```

### 5. Start the Dashboard

```bash
# Production mode
npm start

# Or run directly
node backend/dist/server.js

# Run in background
npm start > dashboard.log 2>&1 &
```

### 6. Access the Dashboard

Open browser to: **http://localhost:3030**

---

## Server Registry Configuration

### Adding a New Server

Edit `backend/server.ts` and add to `SERVER_REGISTRY`:

```typescript
const SERVER_REGISTRY: Record<string, ServerConfig> = {
  // ... existing servers ...

  'my-new-server': {
    name: 'My New Server',                    // Display name
    command: 'npm run dev',                   // Start command
    cwd: '/home/adamsl/my-project',          // Working directory
    color: '#FEF3C7',                         // Background color (hex)
    ports: [4000],                            // Monitored ports
    env: {                                    // Optional environment vars
      NODE_ENV: 'development',
      PORT: '4000'
    }
  },
};
```

### ServerConfig Interface

```typescript
interface ServerConfig {
  name: string;           // Human-readable name shown in UI
  command: string;        // Shell command to start server
  cwd: string;           // Working directory (absolute path)
  color: string;         // Hex color for visual identification
  ports: number[];       // Array of ports this server uses
  env?: Record<string, string>;  // Optional environment variables
}
```

### Color Coding Guidelines

**Recommended color palette:**
- `#DBEAFE` - Blue (infrastructure services)
- `#AEEAE5` - Green (application servers)
- `#E9D5FF` - Purple (API services)
- `#FEF3C7` - Yellow (monitoring/utilities)
- `#FED7AA` - Orange (databases)

### Port Configuration

**Important Notes:**
- Only specify TCP ports (UDP ports are dynamic and can't be reliably tracked)
- Multiple ports are supported: `ports: [8000, 8001, 8002]`
- Empty array `[]` means no port monitoring (agent-type processes)
- Port monitoring enables orphan detection

### After Adding a Server

1. Rebuild the backend: `npm run build:backend`
2. Restart the dashboard: `pkill -f "node backend/dist/server.js" && npm start &`
3. Refresh browser to see the new server

---

## API Reference

### Base URL

```
http://localhost:3030
```

### Endpoints

#### GET /api/ports

Get all listening ports and their associated processes.

**Response:**
```json
[
  {
    "pid": "1234",
    "port": "7880",
    "protocol": "tcp6",
    "program": "livekit-server",
    "command": "./livekit-server --dev --bind 0.0.0.0",
    "color": "#DBEAFE",
    "serverId": "livekit-server",
    "orphaned": false
  }
]
```

#### GET /api/servers

Get all registered servers and their status.

**Response:**
```json
[
  {
    "id": "livekit-server",
    "name": "LiveKit Server",
    "running": true,
    "orphaned": false,
    "orphanedPid": null,
    "color": "#DBEAFE"
  }
]
```

#### POST /api/servers/:serverId?action=start|stop

Start or stop a registered server.

**Parameters:**
- `serverId` (path): Server ID from SERVER_REGISTRY
- `action` (query): Either `start` or `stop`

**Examples:**
```bash
# Start a server
curl -X POST http://localhost:3030/api/servers/livekit-server?action=start

# Stop a server
curl -X POST http://localhost:3030/api/servers/livekit-server?action=stop
```

**Response:**
```json
{
  "success": true,
  "message": "Server livekit-server started successfully"
}
```

#### DELETE /api/kill

Kill a process by PID or port.

**Request Body:**
```json
{
  "pid": "1234"
}
```

Or:

```json
{
  "port": "8000"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Process 1234 killed successfully"
}
```

**Example:**
```bash
# Kill by PID
curl -X DELETE http://localhost:3030/api/kill \
  -H "Content-Type: application/json" \
  -d '{"pid": "1234"}'

# Kill by port
curl -X DELETE http://localhost:3030/api/kill \
  -H "Content-Type: application/json" \
  -d '{"port": "8000"}'
```

#### GET /api/events

Server-Sent Events (SSE) endpoint for real-time updates.

**Response:** Event stream with updates every 5 seconds

**Events:**
- `ports` - Updated list of listening ports
- `servers` - Updated server status

**Example (JavaScript):**
```javascript
const eventSource = new EventSource('http://localhost:3030/api/events');

eventSource.addEventListener('ports', (event) => {
  const ports = JSON.parse(event.data);
  console.log('Ports updated:', ports);
});

eventSource.addEventListener('servers', (event) => {
  const servers = JSON.parse(event.data);
  console.log('Servers updated:', servers);
});
```

---

## Components

### EventBus (event-bus/event-bus.ts)

**Purpose:** Global pub/sub event system for component communication

**Pattern:** ES Module Singleton

**Usage:**
```typescript
import { eventBus } from '../event-bus/event-bus.js';

// Subscribe to events
const unsubscribe = eventBus.on('ports-updated', (data) => {
  console.log('Ports:', data);
});

// Emit events
eventBus.emit('kill-process', { pid: '1234', port: '8000' });

// Unsubscribe
unsubscribe();
```

**API Methods:**
- `on(event, callback)` - Subscribe to event, returns unsubscribe function
- `emit(event, data)` - Emit event with optional data
- `off(event, callback)` - Unsubscribe from event
- `once(event, callback)` - Subscribe for single event
- `clear(event?)` - Clear all subscribers for event or all events
- `listenerCount(event)` - Get number of subscribers

### SSEManager (event-bus/sse-manager.ts)

**Purpose:** Manage Server-Sent Events connection

**Features:**
- Automatic connection management
- Event-driven architecture
- Graceful reconnection

**Usage:**
```typescript
import { sseManager } from '../event-bus/sse-manager.js';

// Connection will start automatically
// Events are automatically forwarded to EventBus
```

### PortMonitor (port-monitor/port-monitor.ts)

**Purpose:** Display all listening ports and processes

**Features:**
- Real-time port list updates
- Color-coding by server
- Orphan detection and highlighting
- Kill process buttons
- Command tooltips

**Custom Element:** `<port-monitor></port-monitor>`

**Events Consumed:**
- `ports-updated` - Updates display with new port data

**Events Emitted:**
- `kill-process` - Request to kill a process

### ServerList (server-list/server-list.ts)

**Purpose:** Display all registered servers with status

**Features:**
- Server status indicators (running/stopped)
- Orphan detection
- Color-coded server cards
- Embedded server-controller for each server

**Custom Element:** `<server-list></server-list>`

**Events Consumed:**
- `servers-updated` - Updates display with new server data

### ServerController (server-controller/server-controller.ts)

**Purpose:** Start/stop controls for individual server

**Features:**
- Start button (when stopped)
- Stop button (when running)
- Kill button (when orphaned)
- Loading states

**Custom Element:** `<server-controller server-id="server-id"></server-controller>`

**Attributes:**
- `server-id` - ID of server to control

### ProcessKiller (process-killer/process-killer.ts)

**Purpose:** Handle process termination with notifications

**Features:**
- Confirmation dialogs
- Success/failure notifications
- API communication
- Toast-style notifications

**Custom Element:** `<process-killer api-url="http://localhost:3030"></process-killer>`

**Events Consumed:**
- `kill-process` - Triggers kill operation

---

## Testing Guide

### Manual Testing Checklist

#### 1. Server Lifecycle Testing

```bash
# Test: Start a server from UI
1. Open dashboard at http://localhost:3030
2. Find a stopped server (red indicator)
3. Click [Start] button
4. ✓ Verify green indicator appears
5. ✓ Verify port appears in Port Monitor
6. ✓ Verify background color matches server

# Test: Stop a server from UI
1. Find a running server (green indicator)
2. Click [Stop] button
3. ✓ Verify red indicator appears
4. ✓ Verify port disappears from Port Monitor
```

#### 2. Orphan Detection Testing

```bash
# Test: Start server outside dashboard
1. Open terminal
2. Start a server manually:
   cd ~/ottomator-agents/livekit-agent
   uv run python pydantic_web_server.py &
3. Return to dashboard
4. Within 5 seconds:
   ✓ Verify server card shows ORPHANED badge
   ✓ Verify red background on server card
   ✓ Verify port shows ORPHANED badge
   ✓ Verify "Force Kill" button available

# Test: Kill orphaned process
1. Click [Kill Orphaned] button on server card
   OR click [Force Kill] button in Port Monitor
2. ✓ Verify process terminates
3. ✓ Verify ORPHANED badges disappear
4. ✓ Verify server shows as stopped
```

#### 3. Port Monitoring Testing

```bash
# Test: Port discovery
1. Start multiple servers (dashboard and manually)
2. Check Port Monitor table
   ✓ Verify all listening ports appear
   ✓ Verify correct PIDs shown
   ✓ Verify correct programs shown
   ✓ Verify full commands visible (hover tooltip)

# Test: Color coding
1. Verify managed server ports have background colors
2. Verify colors match SERVER_REGISTRY configuration
3. Verify orphaned processes show red background
```

#### 4. Real-time Updates Testing

```bash
# Test: SSE connection
1. Open dashboard
2. Open browser console
3. Look for connection status message
   ✓ Verify "SSE connected" or similar
4. Watch for pulsing green dot in Port Monitor header

# Test: Live updates
1. In terminal, start a server:
   ./livekit-server --dev &
2. Keep dashboard visible
3. Within 5 seconds:
   ✓ Verify new port appears
   ✓ Verify server status updates
4. Kill the server:
   pkill livekit-server
5. Within 5 seconds:
   ✓ Verify port disappears
   ✓ Verify server status updates
```

#### 5. Process Management Testing

```bash
# Test: Kill by PID
1. Identify a process PID in Port Monitor
2. Click [Kill] button
3. ✓ Verify success notification appears
4. ✓ Verify process terminates (check with ps)
5. ✓ Verify port disappears from list

# Test: Kill by port
curl -X DELETE http://localhost:3030/api/kill \
  -H "Content-Type: application/json" \
  -d '{"port": "8000"}'
✓ Verify returns success
✓ Verify process on port 8000 terminates
```

### Automated Testing

```bash
# Test: API endpoints
cd ~/planner/dashboard

# Test GET /api/ports
curl http://localhost:3030/api/ports | jq '.'
✓ Verify returns array of port objects

# Test GET /api/servers
curl http://localhost:3030/api/servers | jq '.'
✓ Verify returns array of server objects

# Test POST /api/servers/:id?action=start
curl -X POST http://localhost:3030/api/servers/livekit-server?action=start
✓ Verify returns success:true
✓ Verify server actually starts (check with ps)

# Test POST /api/servers/:id?action=stop
curl -X POST http://localhost:3030/api/servers/livekit-server?action=stop
✓ Verify returns success:true
✓ Verify server actually stops

# Test SSE connection
curl -N http://localhost:3030/api/events
✓ Verify receives event: ports
✓ Verify receives event: servers
✓ Verify updates continue every 5 seconds
```

### Performance Testing

```bash
# Test: Multiple clients
1. Open dashboard in 3 different browser tabs
2. Start/stop servers from one tab
3. ✓ Verify all tabs update simultaneously
4. ✓ Verify no lag or connection drops

# Test: Long-running connection
1. Open dashboard
2. Leave open for 1+ hours
3. ✓ Verify updates continue
4. ✓ Verify no memory leaks in browser
5. ✓ Check SSE connection remains stable
```

---

## Common Use Cases

### Use Case 1: Starting the Development Environment

**Scenario:** You're beginning work and need all services running

**Steps:**
1. Open dashboard: http://localhost:3030
2. Identify stopped servers (red indicators)
3. Click [Start] for each required server:
   - LiveKit Server (for voice infrastructure)
   - LiveKit Voice Agent (for voice AI)
   - Pydantic Web Server (for API)
4. Wait for green indicators
5. Verify all ports are listening in Port Monitor

**Expected State:**
```
✓ LiveKit Server - Running on 7880, 7881
✓ LiveKit Voice Agent - Running (no port)
✓ Pydantic Web Server - Running on 8000
✓ Admin Dashboard - Running on 3030
```

### Use Case 2: Cleaning Up Orphaned Processes

**Scenario:** Servers were started manually and are hogging ports

**Steps:**
1. Open dashboard
2. Look for red ORPHANED badges
3. Option A: Click [Kill Orphaned] on server card
4. Option B: Click [Force Kill] in Port Monitor
5. Confirm in dialog
6. Wait for green "Success" notification

**Indicators:**
- Red background on server cards = Orphaned
- ORPHANED badge in Port Monitor = Process not managed by dashboard

### Use Case 3: Debugging Port Conflicts

**Scenario:** A server won't start due to "port already in use"

**Steps:**
1. Open dashboard
2. Go to Port Monitor section
3. Find the conflicting port
4. Check the "Program" column to identify what's using it
5. Hover over "Command" to see full command
6. Click [Kill] to free the port
7. Return to Server Management and click [Start]

**Example:**
```
Port 8000 is in use by python3 (orphaned)
Command: python pydantic_web_server.py
→ Kill this process
→ Start Pydantic Web Server from dashboard
```

### Use Case 4: Monitoring System Health

**Scenario:** Checking if all services are healthy during testing

**Steps:**
1. Open dashboard
2. Check Server Management section:
   - All expected servers should have green indicators
   - No orphaned badges should appear
3. Check Port Monitor section:
   - All expected ports should be present
   - Color coding should match servers
   - No unexpected processes

**Health Indicators:**
- 🟢 Green dots = Healthy
- 🟥 Red background = Needs attention
- Missing ports = Service may be down
- Extra ports = Unexpected process running

### Use Case 5: Testing Voice Agent Integration

**Scenario:** Testing the full LiveKit voice stack

**Prerequisites:**
1. All voice-related servers must be running
2. No orphaned processes

**Steps:**
1. Open dashboard: http://localhost:3030
2. Verify green indicators for:
   - LiveKit Server
   - LiveKit Voice Agent
   - Pydantic Web Server
3. Open voice UI: http://localhost:8000/talk
4. Click "Connect Voice"
5. Speak to test the agent
6. Return to dashboard to monitor:
   - Port 7880, 7881 (LiveKit)
   - Port 8000 (Web Server)
   - Check for any errors or orphaned processes

**Troubleshooting with Dashboard:**
- If voice doesn't work, check Port Monitor for missing ports
- Look for orphaned processes that might conflict
- Restart services using dashboard controls

### Use Case 6: Shutting Down for the Day

**Scenario:** Stopping all services cleanly

**Steps:**
1. Open dashboard
2. For each running server (green indicator):
   - Click [Stop] button
   - Wait for red indicator
3. Verify Port Monitor is empty (except port 3030)
4. Stop dashboard itself:
   ```bash
   pkill -f "node backend/dist/server.js"
   ```

**Best Practice:** Always use dashboard to stop servers (not manual kill) to ensure clean shutdown.

---

## Troubleshooting

### Dashboard Won't Start

**Symptom:** `npm start` fails or dashboard doesn't respond

**Checks:**
1. Port 3030 already in use:
   ```bash
   netstat -tlnp | grep 3030
   # Kill existing process if found
   ```

2. Build not completed:
   ```bash
   cd ~/planner/dashboard
   npm run build
   ```

3. Dependencies not installed:
   ```bash
   npm install
   ```

4. Node.js version:
   ```bash
   node --version  # Must be v14+
   ```

**Logs:**
```bash
# Check for errors
cat ~/planner/dashboard/dashboard.log

# Run in foreground to see errors
node backend/dist/server.js
```

### Can't Kill Processes

**Symptom:** [Kill] button fails with error notification

**Causes:**
1. **Insufficient permissions:**
   - Check `.env` has correct `SUDO_PASSWORD`
   - Verify user has sudo privileges:
     ```bash
     sudo -v  # Test sudo access
     ```

2. **System processes:**
   - Some processes (owned by root) cannot be killed
   - System-critical processes are protected

3. **Process already terminated:**
   - Race condition: process died between display and kill
   - Refresh dashboard (it updates every 5 seconds)

**Solution:**
```bash
# Manual kill if dashboard fails
sudo kill -9 <PID>

# Verify process is gone
ps aux | grep <PID>
```

### Servers Show as Orphaned

**Symptom:** Green indicator but ORPHANED badge present

**Cause:** Server was started outside dashboard control

**Solutions:**
1. **Recommended:** Kill orphaned process, restart from dashboard
   ```
   Click [Kill Orphaned] → Wait → Click [Start]
   ```

2. **Alternative:** Accept orphaned state (dashboard will monitor but not manage)

**Prevention:**
- Always use dashboard to start servers
- Add alias to prevent manual starts:
  ```bash
  alias livekit="echo 'Use dashboard to start LiveKit!'"
  ```

### Real-time Updates Stopped

**Symptom:** Dashboard shows old data, no pulsing green dot

**Checks:**
1. **SSE connection dropped:**
   - Check browser console for errors
   - Refresh page to reconnect
   - Check if backend is still running:
     ```bash
     ps aux | grep "node backend/dist/server.js"
     ```

2. **Network issues:**
   - Test API manually:
     ```bash
     curl http://localhost:3030/api/ports
     ```

3. **Backend crashed:**
   ```bash
   # Check logs
   tail -50 ~/planner/dashboard/dashboard.log

   # Restart dashboard
   pkill -f "node backend/dist/server.js"
   npm start &
   ```

### Port Not Showing in Monitor

**Symptom:** Server is running but port not visible

**Causes:**
1. **UDP ports:** Dashboard only tracks TCP ports
   - Solution: Add TCP port to SERVER_REGISTRY

2. **Binding to specific interface:**
   - Server bound to 127.0.0.1 only (localhost)
   - Solution: Bind to 0.0.0.0 to appear in netstat

3. **Update delay:**
   - Updates happen every 5 seconds
   - Solution: Wait for next update cycle

**Verification:**
```bash
# Check if port is actually listening
ss -tlnp | grep <PORT>

# Or
netstat -tlnp | grep <PORT>
```

### Server Won't Start from Dashboard

**Symptom:** Click [Start], nothing happens or fails immediately

**Checks:**
1. **Command is correct:**
   - Verify `command` in SERVER_REGISTRY
   - Test command manually in terminal:
     ```bash
     cd /path/from/registry
     ./command-from-registry
     ```

2. **Working directory exists:**
   - Verify `cwd` path in SERVER_REGISTRY:
     ```bash
     ls -la /path/from/registry
     ```

3. **Missing dependencies:**
   - Server may fail due to missing Python/Node modules
   - Check server's own logs

4. **Environment variables:**
   - Verify `env` section in SERVER_REGISTRY
   - Check if `.env` file exists in server's directory

**Debug:**
```bash
# Start server manually to see errors
cd ~/ottomator-agents/livekit-agent
uv run python livekit_mcp_agent.py dev

# Check for error messages
```

### Colors Not Showing

**Symptom:** All ports/servers are white/gray, no color coding

**Cause:** Server colors not configured in SERVER_REGISTRY

**Solution:**
1. Edit `backend/server.ts`
2. Add/update `color` field for each server:
   ```typescript
   'my-server': {
     // ...
     color: '#DBEAFE',  // Add this
     // ...
   }
   ```
3. Rebuild and restart:
   ```bash
   npm run build:backend
   pkill -f "node backend/dist/server.js"
   npm start &
   ```

---

## Development Guide

### Project Structure

```
dashboard/
├── backend/                 # Node.js backend server
│   ├── server.ts           # Main server implementation
│   └── dist/               # Compiled JavaScript (generated)
│
├── event-bus/              # Event system
│   ├── event-bus.ts        # Pub/sub EventBus
│   └── sse-manager.ts      # SSE connection manager
│
├── port-monitor/           # Port monitoring component
│   └── port-monitor.ts
│
├── server-list/            # Server list component
│   └── server-list.ts
│
├── server-controller/      # Server start/stop controls
│   └── server-controller.ts
│
├── process-killer/         # Process termination component
│   └── process-killer.ts
│
├── public/                 # Static files
│   ├── index.html         # Main HTML
│   ├── styles/            # CSS files
│   │   ├── input.css      # Tailwind input
│   │   └── output.css     # Compiled CSS (generated)
│   └── dist/              # Compiled components (generated)
│
├── main.ts                # Main app entry point
├── package.json           # NPM dependencies
├── tsconfig.json          # TypeScript config (components)
├── tsconfig.backend.json  # TypeScript config (backend)
├── tailwind.config.js     # Tailwind CSS config
├── .env                   # Environment variables (DO NOT COMMIT)
├── .env.example           # Environment template
└── README.md              # Documentation
```

### Development Workflow

#### 1. Making Changes to Components

```bash
# Edit component files
nano port-monitor/port-monitor.ts

# Rebuild components
npm run build:components

# Components are automatically loaded by browser (no server restart needed)
# Just refresh the page
```

#### 2. Making Changes to Backend

```bash
# Edit backend
nano backend/server.ts

# Rebuild backend
npm run build:backend

# Restart server
pkill -f "node backend/dist/server.js"
npm start &

# Or restart in foreground for debugging
node backend/dist/server.js
```

#### 3. Making Changes to Styles

```bash
# Edit Tailwind classes in components or HTML
nano public/index.html

# Rebuild CSS
npm run build:css

# Or use watch mode during development
npm run dev:css
# (Leave this running in separate terminal)
```

#### 4. Adding a New Component

```bash
# 1. Create component directory
mkdir dashboard/my-component

# 2. Create TypeScript file
cat > dashboard/my-component/my-component.ts << 'EOF'
import { eventBus } from '../event-bus/event-bus.js';

export class MyComponent extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  connectedCallback() {
    this.render();
  }

  private render() {
    if (!this.shadowRoot) return;
    this.shadowRoot.innerHTML = `
      <style>
        /* Component styles */
      </style>
      <div>My Component Content</div>
    `;
  }
}

customElements.define('my-component', MyComponent);
EOF

# 3. Update tsconfig.json
# Add to "include" array:
# "my-component/**/*"

# 4. Build
npm run build:components

# 5. Add to HTML
# Edit public/index.html:
# <my-component></my-component>
# <script type="module" src="/dist/my-component/my-component.js"></script>
```

### Build Commands Reference

```bash
# Build everything
npm run build

# Build components only
npm run build:components

# Build backend only
npm run build:backend

# Build CSS only
npm run build:css

# Watch CSS for changes
npm run dev:css

# Start production server
npm start

# Run backend with output (debugging)
npm run dev:backend
```

### TypeScript Configuration

**Components (`tsconfig.json`):**
- Target: ES2020
- Module: ES2020 (ES modules)
- Output: `public/dist/`
- Source maps: Yes

**Backend (`tsconfig.backend.json`):**
- Target: ES2020
- Module: CommonJS
- Output: `backend/dist/`
- Source maps: Yes

### Adding New API Endpoints

Edit `backend/server.ts`:

```typescript
// Add after existing routes
if (pathname === '/api/my-endpoint' && req.method === 'GET') {
  // Your logic here
  const data = { message: 'Hello' };

  res.writeHead(200, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify(data));
  return;
}
```

Rebuild and restart:
```bash
npm run build:backend
pkill -f "node backend/dist/server.js" && npm start &
```

### EventBus Communication Pattern

**Publishing events (any component):**
```typescript
import { eventBus } from '../event-bus/event-bus.js';

eventBus.emit('my-event', { data: 'value' });
```

**Subscribing to events (any component):**
```typescript
import { eventBus } from '../event-bus/event-bus.js';

class MyComponent extends HTMLElement {
  private unsubscribe: (() => void) | null = null;

  connectedCallback() {
    this.unsubscribe = eventBus.on('my-event', (data) => {
      console.log('Received:', data);
    });
  }

  disconnectedCallback() {
    // IMPORTANT: Always clean up subscriptions
    if (this.unsubscribe) {
      this.unsubscribe();
    }
  }
}
```

### Debugging Tips

**Frontend (Browser):**
```javascript
// Check EventBus subscriptions
eventBus.listenerCount('ports-updated')

// Manual event emission
eventBus.emit('test-event', { foo: 'bar' })

// Check SSE connection
// Open DevTools → Network tab → EventStream
```

**Backend (Server):**
```typescript
// Add console.log statements
console.log('[DEBUG] Server status:', runningServers.keys());

// Check SSE clients
console.log('[DEBUG] Connected clients:', sseClients.length);
```

**System-level:**
```bash
# Watch processes
watch -n 1 'ps aux | grep -E "(livekit|python|node)"'

# Monitor ports
watch -n 1 'ss -tlnp'

# Monitor dashboard
tail -f ~/planner/dashboard/dashboard.log
```

---

## Best Practices

### For Team Members

1. **Always use the dashboard to start/stop servers**
   - Don't use manual commands unless absolutely necessary
   - Prevents orphaned processes
   - Ensures consistent environment

2. **Check dashboard before debugging**
   - Port conflicts? Check Port Monitor first
   - Service not responding? Check server status
   - Save time troubleshooting

3. **Keep SERVER_REGISTRY updated**
   - Add new services immediately
   - Document port numbers
   - Use descriptive names

4. **Monitor for orphaned processes**
   - Red badges = potential issues
   - Clean up orphans before testing
   - Report orphan patterns to team

5. **Use dashboard for testing workflows**
   - Simulates prod environment
   - Tests service dependencies
   - Validates port assignments

### For Developers

1. **Component development**
   - Keep components small and focused
   - Use Shadow DOM for encapsulation
   - Always unsubscribe from EventBus in disconnectedCallback()

2. **Backend changes**
   - Test API endpoints with curl first
   - Add console.log for debugging
   - Broadcast SSE updates after state changes

3. **Server registry**
   - Choose unique, descriptive IDs
   - Use full absolute paths for cwd
   - Test commands manually before adding

4. **Security**
   - Never commit .env file
   - Use sudo only when necessary
   - Validate all user input

---

## Appendix

### Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SUDO_PASSWORD` | Yes | None | Password for sudo commands (killing privileged processes) |
| `ADMIN_PORT` | No | 3030 | Port for dashboard server |

### Port Registry

| Port | Service | Protocol | Purpose |
|------|---------|----------|---------|
| 3030 | Admin Dashboard | HTTP | Dashboard web interface |
| 7880 | LiveKit Server | WebSocket | LiveKit signaling |
| 7881 | LiveKit Server | TCP | LiveKit RTC |
| 8000 | Pydantic Web | HTTP | Voice agent API & UI |

### Color Palette Reference

| Color | Hex | RGB | Use Case |
|-------|-----|-----|----------|
| Blue | #DBEAFE | rgb(219,234,254) | Infrastructure |
| Green | #D1FAE5 | rgb(209,250,229) | Applications |
| Purple | #E9D5FF | rgb(233,213,255) | APIs |
| Yellow | #FEF3C7 | rgb(254,243,199) | Utilities |
| Orange | #FED7AA | rgb(254,215,170) | Databases |
| Red | #FEE2E2 | rgb(254,226,226) | Orphaned/Errors |

### Keyboard Shortcuts

(Currently none - consider adding in future versions)

### Future Enhancements

Potential features for consideration:

- [ ] Log viewer integration
- [ ] Resource usage monitoring (CPU/memory)
- [ ] Server health checks (ping/http)
- [ ] Automatic orphan cleanup
- [ ] Server dependency management
- [ ] Configuration backup/restore
- [ ] Mobile-responsive design
- [ ] Dark mode
- [ ] Keyboard shortcuts
- [ ] Export metrics to CSV
- [ ] Alerts/notifications system
- [ ] Multi-user permissions
- [ ] HTTPS support
- [ ] Container/Docker support

---

## Quick Reference Card

### Essential Commands

```bash
# Start dashboard
cd ~/planner/dashboard && npm start &

# Stop dashboard
pkill -f "node backend/dist/server.js"

# Rebuild everything
npm run build

# Check if running
netstat -tlnp | grep 3030

# View logs
tail -f ~/planner/dashboard/dashboard.log
```

### Essential URLs

- Dashboard: http://localhost:3030
- API Ports: http://localhost:3030/api/ports
- API Servers: http://localhost:3030/api/servers
- SSE Stream: http://localhost:3030/api/events

### Common Troubleshooting

```bash
# Can't start dashboard (port in use)
pkill -f "node backend/dist/server.js"

# Orphaned processes everywhere
# Use dashboard to kill all, then restart from dashboard

# Server won't start
# Check command works: cd <cwd> && <command>

# Updates not working
# Refresh page, check browser console
```

---

**Last Updated:** 2025-10-11
**Maintained By:** Development Team
**Dashboard Version:** 1.0.0
**Location:** ~/planner/dashboard
**Questions?** Check troubleshooting section or ask team
