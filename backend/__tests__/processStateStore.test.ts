/**
 * Process State Store Tests - TDD RED Phase
 *
 * Testing persistent state management:
 * 1. Storing process information
 * 2. Surviving app restarts
 * 3. Tracking across sessions
 * 4. Cleanup capabilities
 * 5. Data integrity
 */

import { ProcessStateStore } from '../services/processStateStore';
import * as fs from 'fs/promises';
import * as path from 'path';

describe('ProcessStateStore - Persistent Storage', () => {
  const testDbPath = path.join(__dirname, '../../test-process-state.json');
  let stateStore: ProcessStateStore;

  beforeEach(async () => {
    // Clean up any existing test database
    try {
      await fs.unlink(testDbPath);
    } catch {
      // Ignore if file doesn't exist
    }
    stateStore = new ProcessStateStore(testDbPath);
  });

  afterEach(async () => {
    // Clean up test database
    try {
      await fs.unlink(testDbPath);
    } catch {
      // Ignore if file doesn't exist
    }
  });

  test('should save process state to disk', async () => {
    await stateStore.saveProcess({
      id: 'test-server-1',
      pid: 12345,
      command: 'node server.js',
      cwd: '/app',
      startTime: new Date(),
      status: 'running'
    });

    // Verify file was created
    const fileExists = await fs.access(testDbPath).then(() => true).catch(() => false);
    expect(fileExists).toBe(true);

    // Verify content
    const content = await fs.readFile(testDbPath, 'utf-8');
    const data = JSON.parse(content);
    expect(data['test-server-1']).toBeDefined();
    expect(data['test-server-1'].pid).toBe(12345);
  });

  test('should load process state from disk', async () => {
    // Manually create a state file
    await fs.writeFile(testDbPath, JSON.stringify({
      'test-server-1': {
        id: 'test-server-1',
        pid: 12345,
        command: 'node server.js',
        cwd: '/app',
        startTime: new Date().toISOString(),
        status: 'running'
      }
    }));

    // Create new store instance to load from disk
    const newStore = new ProcessStateStore(testDbPath);
    await newStore.load();

    const process = await newStore.getProcess('test-server-1');
    expect(process).toBeDefined();
    expect(process?.pid).toBe(12345);
    expect(process?.status).toBe('running');
  });

  test('should persist state across store instances (simulating app restart)', async () => {
    // First instance saves data
    const store1 = new ProcessStateStore(testDbPath);
    await store1.saveProcess({
      id: 'test-server-1',
      pid: 12345,
      command: 'node server.js',
      cwd: '/app',
      startTime: new Date(),
      status: 'running'
    });

    // Second instance should load the data
    const store2 = new ProcessStateStore(testDbPath);
    await store2.load();
    const process = await store2.getProcess('test-server-1');

    expect(process).toBeDefined();
    expect(process?.pid).toBe(12345);
  });

  test('should remove process from state', async () => {
    await stateStore.saveProcess({
      id: 'test-server-1',
      pid: 12345,
      command: 'node server.js',
      cwd: '/app',
      startTime: new Date(),
      status: 'running'
    });

    await stateStore.removeProcess('test-server-1');

    const process = await stateStore.getProcess('test-server-1');
    expect(process).toBeUndefined();
  });

  test('should list all stored processes', async () => {
    await stateStore.saveProcess({
      id: 'test-server-1',
      pid: 12345,
      command: 'node server.js',
      cwd: '/app',
      startTime: new Date(),
      status: 'running'
    });

    await stateStore.saveProcess({
      id: 'test-server-2',
      pid: 67890,
      command: 'python app.py',
      cwd: '/app',
      startTime: new Date(),
      status: 'running'
    });

    const allProcesses = await stateStore.getAllProcesses();
    expect(allProcesses).toHaveLength(2);
    expect(allProcesses.map(p => p.id)).toContain('test-server-1');
    expect(allProcesses.map(p => p.id)).toContain('test-server-2');
  });

  test('should handle missing or corrupted state file gracefully', async () => {
    // Try to load from non-existent file
    const newStore = new ProcessStateStore(testDbPath);
    await expect(newStore.load()).resolves.not.toThrow();

    const allProcesses = await newStore.getAllProcesses();
    expect(allProcesses).toHaveLength(0);
  });
});
