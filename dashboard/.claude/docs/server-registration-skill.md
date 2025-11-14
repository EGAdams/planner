# Server Registration Management Skill

This skill guides you through registering, modifying, and managing servers in the Admin Dashboard.

## Overview

The Admin Dashboard uses a **Server Registry** pattern to manage which servers are available for monitoring and control. This skill provides commands and guidance for:

- ✅ Registering new servers
- ✅ Modifying existing server configurations
- ✅ Removing servers from management
- ✅ Verifying server registration
- ✅ Testing server connectivity

## Quick Reference

### View Current Servers

**From WSL**:
```bash
curl http://127.0.0.1:3030/api/servers
```

**From Windows**:
```powershell
curl.exe http://172.26.163.131:3030/api/servers
```

For detailed WSL networking info, see [WSL Networking Guide](./wsl-networking-guide.md)

### Verify SSE Connection
Open browser console: `F12` → Console tab
Look for: "SSE connection established"

### Check Server Registry
```bash
grep -A 50 "const SERVER_REGISTRY" /home/adamsl/planner/dashboard/backend/server.ts
```

## Step-by-Step: Add a New Server

### 1. Prepare Server Information

Before registering, gather:
- **Server ID**: Unique identifier (e.g., 'my-server')
- **Server Name**: Display name (e.g., 'My Custom Server')
- **Command**: Full startup command with arguments
- **Working Directory**: Where the server should start from
- **Ports**: Array of ports to monitor (e.g., [3000, 5000])
- **Color**: Hex color for UI display (e.g., '#FF5733')

### 2. Edit Server Registry

Open: `backend/server.ts`

Find the `SERVER_REGISTRY` object (around line 35):

```typescript
const SERVER_REGISTRY: Record<string, ServerConfig> = {
  'livekit-server': { ... },
  'livekit-voice-agent': { ... },
  'pydantic-web-server': { ... },
  // ADD YOUR SERVER HERE
};
```

Add your server entry:

```typescript
  'my-custom-server': {
    name: 'My Custom Server',
    command: '/usr/bin/python /path/to/my_server.py --arg value',
    cwd: '/path/to/server/directory',
    color: '#00AA55',
    ports: [3000],
  },
```

### 3. Rebuild & Restart

```bash
cd /home/adamsl/planner/dashboard
npm run build
pkill -f "node backend/dist/server.js"
npm start > dashboard.log 2>&1 &
```

### 4. Verify Registration

```bash
# Check API response includes new server
curl http://127.0.0.1:3030/api/servers | grep my-custom-server

# Check dashboard displays the server
open http://127.0.0.1:3030  # In browser
```

## Step-by-Step: Modify Existing Server

### 1. Identify the Server
```bash
grep "'server-id'" /home/adamsl/planner/dashboard/backend/server.ts
```

### 2. Update Configuration

Edit the registry entry in `backend/server.ts`. You can modify:
- `name` - Display name
- `command` - Startup command
- `cwd` - Working directory
- `ports` - Monitored ports array
- `color` - UI color hex code

Example: Change Pydantic Web Server ports from [8001] to [8001, 8002]:

```typescript
  'pydantic-web-server': {
    name: 'Pydantic Web Server',
    command: '/home/adamsl/planner/venv/bin/python pydantic_mcp_agent_endpoint.py',
    cwd: '/home/adamsl/ottomator-agents/pydantic-ai-mcp-agent/studio-integration-version',
    color: '#E9D5FF',
    ports: [8001, 8002],  // ← CHANGED
  },
```

### 3. Rebuild & Restart

Same as "Add New Server" step 3.

## Step-by-Step: Remove a Server

### 1. Edit Server Registry

Open: `backend/server.ts`

Delete the entire server entry from the `SERVER_REGISTRY` object.

Example - Remove 'livekit-voice-agent':

```typescript
const SERVER_REGISTRY: Record<string, ServerConfig> = {
  'livekit-server': { ... },
  // 'livekit-voice-agent': DELETED,
  'pydantic-web-server': { ... },
};
```

### 2. Rebuild & Restart

```bash
cd /home/adamsl/planner/dashboard
npm run build
pkill -f "node backend/dist/server.js"
npm start > dashboard.log 2>&1 &
```

### 3. Verify Removal

```bash
curl http://127.0.0.1:3030/api/servers | grep -v livekit-voice-agent
```

## Troubleshooting Registration Issues

### Servers Don't Appear in Dashboard

**Check 1**: API returns servers
```bash
curl http://127.0.0.1:3030/api/servers
```

**Check 2**: Browser console shows SSE connection
```
F12 → Console → Look for "SSE connection established"
```

**Check 3**: Server registry is valid TypeScript
```bash
npm run build:backend
# Should complete without errors
```

**Check 4**: Dashboard is restarted
```bash
ps aux | grep "node backend/dist/server.js"
# Should show the process
```

### Server Appears But Won't Start

**Check 1**: Server command exists
```bash
which <server-command>
# Or test the path
ls -la <path-to-server>
```

**Check 2**: Working directory exists
```bash
ls -la <cwd>
```

**Check 3**: Check dashboard logs
```bash
tail -50 /home/adamsl/planner/dashboard/dashboard.log
```

### Server Registration Failed to Parse

**Check**: TypeScript compilation errors
```bash
cd /home/adamsl/planner/dashboard
npm run build:backend
# Look for syntax errors
```

**Fix**: Verify JSON/TypeScript syntax
- Trailing commas after last entry cause errors
- Quotes must be double (not single in config)
- Arrays use square brackets: `[8000, 8001]`

## Advanced: Server Configuration Options

### ServerConfig Interface

```typescript
interface ServerConfig {
  name: string;           // Display name in UI
  command: string;        // Full startup command
  cwd: string;            // Working directory
  color: string;          // Hex color (#RRGGBB)
  ports: number[];        // Ports to monitor
}
```

### Color Selection

Colors are displayed in the dashboard UI card. Popular choices:
- `#DBEAFE` - Light Blue (LiveKit)
- `#D1FAE5` - Light Green (Voice Agent)
- `#E9D5FF` - Light Purple (Pydantic)
- `#FEE2E2` - Light Red (Critical services)
- `#FEF3C7` - Light Yellow (Monitoring)

### Port Monitoring

Ports are checked every 3 seconds:
- Dashboard shows "In Use" if port is open
- Shows "Available" if port is free
- Multiple ports can be monitored per server

Example: Monitor main port + debug port
```typescript
ports: [8000, 8001]  // Check both ports
```

## Verification Checklist

After registering a server, verify:

- [ ] Server appears in API response
- [ ] Server appears in dashboard UI
- [ ] "Start" button is clickable
- [ ] Clicking "Start" launches the process
- [ ] Ports show as "In Use" when running
- [ ] "Stop" button stops the process
- [ ] Ports show as "Available" when stopped

## Integration Points

The server registration system integrates with:

1. **Backend API** - `/api/servers` endpoint
2. **SSE Stream** - Real-time `servers` event
3. **ProcessOrchestrator** - Server lifecycle management
4. **ProcessStateStore** - Persistent process state (JSON)
5. **Frontend UI** - ServerList web component displays servers

## FAQ

**Q: Can I register a server that's already running?**
A: Yes! The dashboard will detect the orphaned process and show "Orphaned" status. You can then kill it or adopt it into management.

**Q: Do I need to stop all servers before registering a new one?**
A: No, you can add new servers while others are running. Just rebuild and restart the dashboard.

**Q: Can multiple dashboards manage the same servers?**
A: Not recommended. Only one dashboard should manage a server registry. Multiple dashboards will conflict on process state.

**Q: What happens to running processes if I remove the server from registry?**
A: The processes will keep running (orphaned), but the dashboard won't manage them. You'll need to kill them manually.

**Q: Can I change a server's command while it's running?**
A: Changes only take effect on the next start. The current process continues running.

## Common Patterns

### Pattern 1: Python Server
```typescript
'my-python-service': {
  name: 'My Python Service',
  command: '/home/adamsl/planner/venv/bin/python main.py',
  cwd: '/path/to/python/project',
  color: '#3B82F6',
  ports: [5000],
},
```

### Pattern 2: Node.js Server
```typescript
'my-node-service': {
  name: 'My Node Service',
  command: '/usr/bin/node index.js',
  cwd: '/path/to/node/project',
  color: '#10B981',
  ports: [3000],
},
```

### Pattern 3: Binary/Executable
```typescript
'my-custom-binary': {
  name: 'Custom Binary',
  command: '/path/to/binary --flag value',
  cwd: '/path/to/binary/directory',
  color: '#F59E0B',
  ports: [9000],
},
```

### Pattern 4: Multi-Port Service
```typescript
'database-cluster': {
  name: 'Database Cluster',
  command: '/usr/bin/database-server --replicas 3',
  cwd: '/var/database',
  color: '#EF4444',
  ports: [5432, 5433, 5434],  // Monitor all replicas
},
```

## Next Steps

1. ✅ Understand server registration
2. 📋 Identify servers you want to manage
3. 🔧 Edit `backend/server.ts`
4. 🔨 Rebuild with `npm run build`
5. 🚀 Restart dashboard
6. ✓ Verify servers appear in UI

---

**Status**: Production Ready ✅
**Last Updated**: 2025-11-13
**Requires**: Node.js 18+, npm
