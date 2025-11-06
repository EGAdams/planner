# Process Management Services

Robust server process management and monitoring system for the Admin Dashboard.

## Architecture Overview

This system uses a layered architecture with three core services and one orchestrator:

```
┌─────────────────────────────────────────┐
│      ServerOrchestrator (API Layer)     │
│  - Unified interface for server mgmt    │
│  - State persistence coordination       │
│  - Event aggregation & forwarding       │
└─────────────────────────────────────────┘
           │            │            │
     ┌─────┘            │            └─────┐
     │                  │                  │
┌────▼─────┐    ┌──────▼──────┐    ┌─────▼────┐
│ Process  │    │  Process    │    │ Process  │
│ Manager  │◄───│  Monitor    │    │  State   │
│          │    │             │    │  Store   │
└──────────┘    └─────────────┘    └──────────┘
```

## Core Services

### 1. ProcessManager
**Purpose**: Core process lifecycle management

**Responsibilities**:
- Spawn processes with proper configuration
- Track PIDs and process states
- Handle clean process termination
- Prevent duplicate process IDs
- Emit events for process state changes

**Key Methods**:
```typescript
spawn(config: SpawnConfig): Promise<ProcessInfo>
kill(id: string): Promise<KillResult>
getProcess(id: string): ProcessInfo | undefined
getAllProcesses(): ProcessInfo[]
isRunning(id: string): boolean
killAll(): Promise<void>
```

**Events Emitted**:
- `processStarted`: When a process successfully spawns
- `processExit`: When a process exits
- `processError`: When a process encounters an error

### 2. ProcessMonitor
**Purpose**: Background health monitoring (independent of UI)

**Responsibilities**:
- Periodic health checks (every ~3 seconds)
- Process liveness verification
- Port connectivity testing
- Process death detection
- Continuous operation even without browser sessions

**Key Methods**:
```typescript
start(intervalMs: number): void
stop(): void
getStatus(id: string): ProcessStatus | undefined
getAllStatuses(): ProcessStatus[]
```

**Events Emitted**:
- `healthCheck`: Periodic health check performed
- `statusChange`: Process health status changed
- `processDied`: Process unexpectedly died

**Monitoring Behavior**:
- Runs independently in the background
- Checks process existence using PID verification
- Tests TCP port connectivity
- Detects hanging or unresponsive processes
- Works even if all browser tabs are closed

### 3. ProcessStateStore
**Purpose**: Persistent state management across restarts

**Responsibilities**:
- Store process information to disk (JSON format)
- Load state on application startup
- Track processes across sessions
- Enable cleanup of orphaned processes
- Handle corrupted/missing state files gracefully

**Key Methods**:
```typescript
load(): Promise<void>
saveProcess(info: StoredProcessInfo): Promise<void>
getProcess(id: string): Promise<StoredProcessInfo | undefined>
removeProcess(id: string): Promise<void>
getAllProcesses(): Promise<StoredProcessInfo[]>
clear(): Promise<void>
```

**Storage Format**:
```json
{
  "server-id": {
    "id": "server-id",
    "pid": 12345,
    "command": "node server.js",
    "cwd": "/path/to/app",
    "startTime": "2025-11-04T12:00:00.000Z",
    "status": "running",
    "ports": [3000, 3001]
  }
}
```

### 4. ServerOrchestrator
**Purpose**: High-level coordination of all services

**Responsibilities**:
- Unified API for server management
- Coordinate between all three services
- Automatic state persistence
- Recovery from crashes
- Orphan process detection
- Event aggregation and forwarding

**Key Methods**:
```typescript
initialize(): Promise<void>
registerServer(id: string, config: ServerConfig): void
registerServers(registry: Record<string, ServerConfig>): void
startServer(serverId: string): Promise<{ success: boolean; message: string }>
stopServer(serverId: string): Promise<{ success: boolean; message: string }>
getServerStatus(currentPorts?): Promise<ServerStatus[]>
killOrphanedProcess(serverId: string, pid: string): Promise<KillResult>
shutdown(): Promise<void>
```

**Events Emitted**:
- `initialized`: Orchestrator initialized and state recovered
- `serverStarted`: Server started successfully
- `serverStopped`: Server stopped successfully
- `orphanKilled`: Orphaned process killed
- Plus forwarded events from ProcessManager and ProcessMonitor

## Usage Examples

### Basic Setup
```typescript
import { ServerOrchestrator, ServerConfig } from './services';

// Define server configurations
const serverRegistry: Record<string, ServerConfig> = {
  'my-api-server': {
    name: 'My API Server',
    command: 'node server.js',
    cwd: '/path/to/app',
    color: '#3B82F6',
    ports: [3000]
  }
};

// Initialize orchestrator
const orchestrator = new ServerOrchestrator('./process-state.json', 3000);
orchestrator.registerServers(serverRegistry);
await orchestrator.initialize();
```

### Starting a Server
```typescript
const result = await orchestrator.startServer('my-api-server');
if (result.success) {
  console.log('Server started:', result.message);
} else {
  console.error('Failed to start server:', result.message);
}
```

### Monitoring Events
```typescript
orchestrator.on('processDied', (data) => {
  console.error(`Process ${data.id} died unexpectedly!`);
  // Could implement auto-restart logic here
});

orchestrator.on('statusChange', (data) => {
  console.log(`Status changed for ${data.id}:`, data.current);
});
```

### Getting Server Status
```typescript
const statuses = await orchestrator.getServerStatus();
for (const status of statuses) {
  console.log(`${status.name}: ${status.running ? 'RUNNING' : 'STOPPED'}`);
  if (status.orphaned) {
    console.log(`  WARNING: Orphaned process detected (PID: ${status.orphanedPid})`);
  }
}
```

### Graceful Shutdown
```typescript
process.on('SIGINT', async () => {
  await orchestrator.shutdown();
  process.exit(0);
});
```

## Testing

The system includes comprehensive unit tests using Jest and TDD methodology.

### Running Tests
```bash
npm test                # Run all tests
npm run test:watch      # Watch mode
npm run test:coverage   # With coverage report
```

### Test Structure
```
backend/__tests__/
├── processManager.test.ts     # Core lifecycle tests
├── processMonitor.test.ts     # Background monitoring tests
└── processStateStore.test.ts  # Persistent storage tests
```

### Test Coverage
- Process spawning and tracking
- Multiple concurrent processes
- Process termination
- Duplicate prevention
- Health checking at intervals
- Process death detection
- Port connectivity verification
- Persistent state storage
- State recovery after restarts
- Graceful handling of corrupted state

## Integration with Existing Server

The `server-integrated.ts` file demonstrates full integration:

1. **Import orchestrator**:
```typescript
import { ServerOrchestrator, ServerConfig } from './services/serverOrchestrator';
```

2. **Initialize with server registry**:
```typescript
const orchestrator = new ServerOrchestrator(stateDbPath, 3000);
orchestrator.registerServers(SERVER_REGISTRY);
await orchestrator.initialize();
```

3. **Wire up API endpoints**:
```typescript
if (action === 'start') {
  result = await orchestrator.startServer(serverId);
} else if (action === 'stop') {
  result = await orchestrator.stopServer(serverId);
}
```

4. **Broadcast updates via SSE**:
```typescript
orchestrator.on('serverStarted', () => broadcastServerUpdate());
orchestrator.on('serverStopped', () => broadcastServerUpdate());
orchestrator.on('processDied', () => broadcastServerUpdate());
```

## Key Features

### Browser-Independent Operation
- Background monitoring continues even with no active browser sessions
- Processes persist across dashboard restarts
- Orphan detection works independently

### Persistent State
- Process information survives application crashes
- State stored in JSON format for easy debugging
- Automatic recovery on restart

### Orphan Process Management
- Detects processes running without dashboard tracking
- Provides API to kill orphaned processes
- Prevents port conflicts

### Event-Driven Architecture
- EventEmitter-based for loose coupling
- Easy to add new listeners for custom behavior
- Comprehensive event coverage for all state changes

### Error Handling
- Graceful handling of missing/corrupted state files
- Proper cleanup on process errors
- Timeout handling for port checks
- Safe signal handling for process termination

## File Locations

```
backend/
├── services/
│   ├── processManager.ts         # Core process lifecycle
│   ├── processMonitor.ts         # Background monitoring
│   ├── processStateStore.ts      # Persistent storage
│   ├── serverOrchestrator.ts     # High-level coordination
│   ├── index.ts                  # Exports
│   └── README.md                 # This file
├── __tests__/
│   ├── processManager.test.ts    # Unit tests
│   ├── processMonitor.test.ts    # Unit tests
│   └── processStateStore.test.ts # Unit tests
├── server.ts                     # Original server (preserved)
└── server-integrated.ts          # Integrated version with orchestrator

process-state.json                # Persistent state (created at runtime)
```

## Migration Guide

To migrate from the old `server.ts` to the new integrated version:

1. **Backup the original**:
```bash
cp backend/server.ts backend/server-original.ts
```

2. **Replace with integrated version**:
```bash
cp backend/server-integrated.ts backend/server.ts
```

3. **Rebuild**:
```bash
npm run build:backend
```

4. **Restart the server**:
```bash
npm start
```

The new system is backward compatible with the existing API endpoints.

## Performance Considerations

- **Memory**: ~1-2MB per tracked process
- **CPU**: Negligible (health checks use signal 0 and TCP probes)
- **Disk I/O**: State file written on each process start/stop (~1KB per process)
- **Network**: Port checks use short-lived TCP connections with 1s timeout

## Security Notes

- Process spawning uses `detached: true` and `stdio: 'ignore'` for proper daemonization
- SIGTERM is tried before SIGKILL for graceful shutdown
- State file contains PIDs and paths but no sensitive credentials
- Port checks only test connectivity, not authentication

## Future Enhancements

Potential improvements for future development:

- [ ] Automatic restart on crash with backoff strategy
- [ ] Log file management and rotation
- [ ] Resource usage tracking (CPU, memory)
- [ ] Process output capture and streaming
- [ ] Webhook notifications for state changes
- [ ] SQLite backend for better query performance
- [ ] Process group management
- [ ] Custom health check endpoints beyond port connectivity

## Support

For issues or questions, check:
- Unit tests for usage examples
- Integration example in `server-integrated.ts`
- Original requirements in project documentation
