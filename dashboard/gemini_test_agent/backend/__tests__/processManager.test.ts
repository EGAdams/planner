/**
 * Process Manager Tests - TDD RED Phase
 *
 * Testing core process lifecycle management:
 * 1. Spawning processes
 * 2. Tracking PIDs and states
 * 3. Killing processes
 * 4. Cleanup on termination
 * 5. Error handling
 */

import { ProcessManager } from '../services/processManager';
import { ChildProcess } from 'child_process';

describe('ProcessManager - Core Lifecycle', () => {
  let processManager: ProcessManager;

  beforeEach(() => {
    processManager = new ProcessManager();
  });

  afterEach(async () => {
    // Clean up any running processes
    await processManager.killAll();
  });

  test('should spawn a process and track its PID', async () => {
    const processInfo = await processManager.spawn({
      id: 'test-server-1',
      command: 'node',
      args: ['-e', 'setInterval(() => {}, 1000)'],
      cwd: '/tmp'
    });

    expect(processInfo.id).toBe('test-server-1');
    expect(processInfo.pid).toBeGreaterThan(0);
    expect(processInfo.status).toBe('running');
    expect(processInfo.startTime).toBeInstanceOf(Date);
  });

  test('should track multiple concurrent processes', async () => {
    const proc1 = await processManager.spawn({
      id: 'test-server-1',
      command: 'node',
      args: ['-e', 'setInterval(() => {}, 1000)'],
      cwd: '/tmp'
    });

    const proc2 = await processManager.spawn({
      id: 'test-server-2',
      command: 'node',
      args: ['-e', 'setInterval(() => {}, 1000)'],
      cwd: '/tmp'
    });

    expect(proc1.pid).not.toBe(proc2.pid);
    expect(processManager.getProcess('test-server-1')).toBeDefined();
    expect(processManager.getProcess('test-server-2')).toBeDefined();
    expect(processManager.getAllProcesses()).toHaveLength(2);
  });

  test('should kill a process by ID', async () => {
    await processManager.spawn({
      id: 'test-server-1',
      command: 'node',
      args: ['-e', 'setInterval(() => {}, 1000)'],
      cwd: '/tmp'
    });

    const result = await processManager.kill('test-server-1');

    expect(result.success).toBe(true);
    expect(result.message).toContain('killed successfully');

    // Process should no longer be tracked
    const proc = processManager.getProcess('test-server-1');
    expect(proc).toBeUndefined();
  });

  test('should handle killing non-existent process gracefully', async () => {
    const result = await processManager.kill('non-existent-server');

    expect(result.success).toBe(false);
    expect(result.message).toContain('not found');
  });

  test('should prevent spawning duplicate process IDs', async () => {
    await processManager.spawn({
      id: 'test-server-1',
      command: 'node',
      args: ['-e', 'setInterval(() => {}, 1000)'],
      cwd: '/tmp'
    });

    await expect(
      processManager.spawn({
        id: 'test-server-1',
        command: 'node',
        args: ['-e', 'setInterval(() => {}, 1000)'],
        cwd: '/tmp'
      })
    ).rejects.toThrow('already running');
  });
});
