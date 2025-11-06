/**
 * Process Monitor Tests - TDD RED Phase
 *
 * Testing background monitoring:
 * 1. Health checking at intervals
 * 2. Port connectivity verification
 * 3. Hang/timeout detection
 * 4. Independent of UI/browser
 * 5. Event emission for state changes
 */

import { ProcessMonitor } from '../services/processMonitor';
import { ProcessManager } from '../services/processManager';
import { EventEmitter } from 'events';

describe('ProcessMonitor - Background Monitoring', () => {
  let processManager: ProcessManager;
  let processMonitor: ProcessMonitor;

  beforeEach(() => {
    processManager = new ProcessManager();
    processMonitor = new ProcessMonitor(processManager);
  });

  afterEach(async () => {
    processMonitor.stop();
    await processManager.killAll();
  });

  test('should start monitoring and check health periodically', async () => {
    const healthCheckSpy = jest.fn();
    processMonitor.on('healthCheck', healthCheckSpy);

    processMonitor.start(1000); // Check every 1 second

    // Wait for at least 2 health checks
    await new Promise(resolve => setTimeout(resolve, 2500));

    // Should have been called at least 2 times (initial + periodic checks)
    expect(healthCheckSpy.mock.calls.length).toBeGreaterThanOrEqual(2);
  });

  test('should detect when a process is still running', async () => {
    await processManager.spawn({
      id: 'test-server-1',
      command: 'node',
      args: ['-e', 'setInterval(() => {}, 1000)'],
      cwd: '/tmp'
    });

    const statusSpy = jest.fn();
    processMonitor.on('statusChange', statusSpy);
    processMonitor.start(1000);

    await new Promise(resolve => setTimeout(resolve, 1500));

    const status = processMonitor.getStatus('test-server-1');
    expect(status).toBeDefined();
    expect(status?.isHealthy).toBe(true);
    expect(status?.isRunning).toBe(true);
  });

  test('should detect when a process dies unexpectedly', async () => {
    const proc = await processManager.spawn({
      id: 'test-server-1',
      command: 'node',
      args: ['-e', 'setTimeout(() => process.exit(1), 1000)'], // Exit after 1 second
      cwd: '/tmp'
    });

    const deathSpy = jest.fn();
    processMonitor.on('processDied', deathSpy);
    processMonitor.start(500);

    // Wait for process to die and be detected
    await new Promise(resolve => setTimeout(resolve, 2000));

    expect(deathSpy).toHaveBeenCalledWith(
      expect.objectContaining({
        id: 'test-server-1'
      })
    );
  });

  test('should verify port connectivity when ports are specified', async () => {
    // Spawn a simple HTTP server
    await processManager.spawn({
      id: 'test-http-server',
      command: 'node',
      args: ['-e', 'require("http").createServer().listen(8888)'],
      cwd: '/tmp',
      ports: [8888]
    });

    processMonitor.start(1000);

    // Wait for monitoring to check
    await new Promise(resolve => setTimeout(resolve, 2000));

    const status = processMonitor.getStatus('test-http-server');
    expect(status?.portConnectivity?.[8888]).toBe(true);
  });

  test('should continue monitoring even without active sessions', async () => {
    await processManager.spawn({
      id: 'test-server-1',
      command: 'node',
      args: ['-e', 'setInterval(() => {}, 1000)'],
      cwd: '/tmp'
    });

    const checkCount = jest.fn();
    processMonitor.on('healthCheck', checkCount);
    processMonitor.start(500);

    // Simulate no UI/browser sessions
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Monitor should still be running
    expect(checkCount.mock.calls.length).toBeGreaterThanOrEqual(3);
  });
});
