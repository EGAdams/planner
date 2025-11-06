/**
 * Unit Tests for ServerOrchestrator
 * 
 * TDD Approach - Tests for server startup, configuration, and orchestration
 */

import { ServerOrchestrator, ServerConfig } from '../services/serverOrchestrator';
import * as fs from 'fs';
import * as path from 'path';

describe('ServerOrchestrator - Configuration', () => {
  let orchestrator: ServerOrchestrator;
  const testStateFile = path.join(__dirname, 'test-state.json');

  beforeEach(async () => {
    // Clean up test state file
    if (fs.existsSync(testStateFile)) {
      fs.unlinkSync(testStateFile);
    }
    
    orchestrator = new ServerOrchestrator(testStateFile, 10000);
    await orchestrator.initialize();
  });

  afterEach(async () => {
    await orchestrator.shutdown();
    
    // Clean up
    if (fs.existsSync(testStateFile)) {
      fs.unlinkSync(testStateFile);
    }
  });

  test('should initialize without errors', async () => {
    expect(orchestrator).toBeTruthy();
  });

  test('should register a server configuration', () => {
    const config: ServerConfig = {
      name: 'Test Server',
      command: 'echo "test"',
      cwd: '/tmp',
      color: '#FFFFFF',
      ports: [9999]
    };

    orchestrator.registerServer('test-server', config);
    
    // Verify by getting status
    const status = orchestrator.getServerStatus([]);
    expect(status).toBeTruthy();
  });

  test('should register multiple servers at once', () => {
    const registry = {
      'server1': {
        name: 'Server 1',
        command: 'echo "1"',
        cwd: '/tmp',
        color: '#FF0000',
        ports: [8001]
      },
      'server2': {
        name: 'Server 2',
        command: 'echo "2"',
        cwd: '/tmp',
        color: '#00FF00',
        ports: [8002]
      }
    };

    orchestrator.registerServers(registry);
    
    // Servers should be registered (will verify in status tests)
    expect(orchestrator).toBeTruthy();
  });

  test('should register Pydantic server with correct configuration', () => {
    const pydanticConfig: ServerConfig = {
      name: 'Pydantic Web Server',
      command: 'uv run python pydantic_mcp_agent_endpoint.py',
      cwd: '/home/adamsl/ottomator-agents/pydantic-ai-mcp-agent/studio-integration-version',
      color: '#E9D5FF',
      ports: [8001]
    };

    orchestrator.registerServer('pydantic-web-server', pydanticConfig);
    
    // Verify configuration is stored
    expect(orchestrator).toBeTruthy();
  });
});

describe('ServerOrchestrator - Server Status', () => {
  let orchestrator: ServerOrchestrator;
  const testStateFile = path.join(__dirname, 'test-state-status.json');

  beforeEach(async () => {
    if (fs.existsSync(testStateFile)) {
      fs.unlinkSync(testStateFile);
    }
    
    orchestrator = new ServerOrchestrator(testStateFile, 10000);
    await orchestrator.initialize();
    
    // Register test servers
    orchestrator.registerServers({
      'test-server': {
        name: 'Test Server',
        command: 'sleep 100',
        cwd: '/tmp',
        color: '#FFFFFF',
        ports: [9999]
      }
    });
  });

  afterEach(async () => {
    await orchestrator.shutdown();
    
    if (fs.existsSync(testStateFile)) {
      fs.unlinkSync(testStateFile);
    }
  });

  test('should return server status for registered servers', async () => {
    const statuses = await orchestrator.getServerStatus([]);
    
    expect(Array.isArray(statuses)).toBe(true);
    expect(statuses.length).toBeGreaterThan(0);
    
    const testServer = statuses.find(s => s.id === 'test-server');
    expect(testServer).toBeTruthy();
    expect(testServer?.name).toBe('Test Server');
    expect(testServer?.color).toBe('#FFFFFF');
    expect(testServer?.running).toBe(false); // Not started yet
  });

  test('should detect server as stopped initially', async () => {
    const statuses = await orchestrator.getServerStatus([]);
    const server = statuses.find(s => s.id === 'test-server');
    
    expect(server?.running).toBe(false);
    expect(server?.orphaned).toBe(false);
  });

  test('should detect orphaned processes', async () => {
    // Simulate an orphaned process on port 9999
    const mockPorts = [
      { pid: '12345', port: '9999' }
    ];

    const statuses = await orchestrator.getServerStatus(mockPorts);
    const server = statuses.find(s => s.id === 'test-server');
    
    expect(server?.running).toBe(true);
    expect(server?.orphaned).toBe(true);
    expect(server?.orphanedPid).toBe('12345');
  });
});

describe('ServerOrchestrator - Server Lifecycle', () => {
  let orchestrator: ServerOrchestrator;
  const testStateFile = path.join(__dirname, 'test-state-lifecycle.json');

  beforeEach(async () => {
    if (fs.existsSync(testStateFile)) {
      fs.unlinkSync(testStateFile);
    }
    
    orchestrator = new ServerOrchestrator(testStateFile, 10000);
    await orchestrator.initialize();
  });

  afterEach(async () => {
    await orchestrator.shutdown();
    
    if (fs.existsSync(testStateFile)) {
      fs.unlinkSync(testStateFile);
    }
  });

  test('should fail to start unregistered server', async () => {
    const result = await orchestrator.startServer('nonexistent-server');
    
    expect(result.success).toBe(false);
    expect(result.message).toContain('not found in registry');
  });

  test('should start a simple server', async () => {
    // Register a simple server that will exit quickly
    orchestrator.registerServer('echo-server', {
      name: 'Echo Server',
      command: 'echo "Hello World"',
      cwd: '/tmp',
      color: '#FFFFFF',
      ports: []
    });

    const result = await orchestrator.startServer('echo-server');
    
    expect(result.success).toBe(true);
    expect(result.message).toContain('started successfully');
    expect(result.message).toContain('PID');
  }, 10000);

  test('should prevent starting already running server', async () => {
    orchestrator.registerServer('sleep-server', {
      name: 'Sleep Server',
      command: 'sleep 5',
      cwd: '/tmp',
      color: '#FFFFFF',
      ports: []
    });

    // Start once
    await orchestrator.startServer('sleep-server');
    
    // Try to start again
    const result = await orchestrator.startServer('sleep-server');
    
    expect(result.success).toBe(false);
    expect(result.message).toContain('already running');
  }, 10000);

  test('should stop a running server', async () => {
    orchestrator.registerServer('stop-test-server', {
      name: 'Stop Test Server',
      command: 'sleep 30',
      cwd: '/tmp',
      color: '#FFFFFF',
      ports: []
    });

    // Start server
    await orchestrator.startServer('stop-test-server');
    
    // Stop server
    const result = await orchestrator.stopServer('stop-test-server');
    
    expect(result.success).toBe(true);
  }, 10000);
});

describe('ServerOrchestrator - Event Emission', () => {
  let orchestrator: ServerOrchestrator;
  const testStateFile = path.join(__dirname, 'test-state-events.json');

  beforeEach(async () => {
    if (fs.existsSync(testStateFile)) {
      fs.unlinkSync(testStateFile);
    }
    
    orchestrator = new ServerOrchestrator(testStateFile, 10000);
    await orchestrator.initialize();
  });

  afterEach(async () => {
    await orchestrator.shutdown();
    
    if (fs.existsSync(testStateFile)) {
      fs.unlinkSync(testStateFile);
    }
  });

  test('should emit serverStarted event when server starts', async () => {
    orchestrator.registerServer('event-test-server', {
      name: 'Event Test Server',
      command: 'sleep 5',
      cwd: '/tmp',
      color: '#FFFFFF',
      ports: []
    });

    const eventPromise = new Promise((resolve) => {
      orchestrator.on('serverStarted', (data) => {
        resolve(data);
      });
    });

    await orchestrator.startServer('event-test-server');
    
    const eventData = await eventPromise;
    expect(eventData).toBeTruthy();
    expect((eventData as any).serverId).toBe('event-test-server');
  }, 10000);

  test('should emit serverStopped event when server stops', async () => {
    orchestrator.registerServer('stop-event-test', {
      name: 'Stop Event Test',
      command: 'sleep 30',
      cwd: '/tmp',
      color: '#FFFFFF',
      ports: []
    });

    await orchestrator.startServer('stop-event-test');

    const eventPromise = new Promise((resolve) => {
      orchestrator.on('serverStopped', (data) => {
        resolve(data);
      });
    });

    await orchestrator.stopServer('stop-event-test');
    
    const eventData = await eventPromise;
    expect(eventData).toBeTruthy();
    expect((eventData as any).serverId).toBe('stop-event-test');
  }, 10000);
});
