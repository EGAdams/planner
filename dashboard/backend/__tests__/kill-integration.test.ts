/**
 * Kill Endpoint Integration Tests
 *
 * These tests verify the kill endpoint works with real HTTP requests
 * against the running server.
 */

import * as http from 'http';

const API_URL = 'http://localhost:3030';

interface KillResponse {
  success: boolean;
  message: string;
}

/**
 * Make HTTP DELETE request to kill endpoint
 */
function makeKillRequest(body: any): Promise<{ status: number; data: KillResponse }> {
  return new Promise((resolve, reject) => {
    const bodyStr = JSON.stringify(body);

    const options: http.RequestOptions = {
      hostname: 'localhost',
      port: 3030,
      path: '/api/kill',
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(bodyStr),
      },
    };

    const req = http.request(options, (res) => {
      let data = '';
      res.on('data', (chunk) => (data += chunk));
      res.on('end', () => {
        try {
          resolve({
            status: res.statusCode || 500,
            data: JSON.parse(data),
          });
        } catch (error) {
          reject(new Error(`Failed to parse response: ${data}`));
        }
      });
    });

    req.on('error', (error) => {
      reject(error);
    });

    req.write(bodyStr);
    req.end();
  });
}

/**
 * Spawn a test process that listens on a port
 */
function spawnTestProcess(port: number): Promise<number> {
  return new Promise((resolve, reject) => {
    const { spawn } = require('child_process');

    // Start a simple HTTP server on the specified port
    const proc = spawn('node', [
      '-e',
      `require('http').createServer((req, res) => res.end('test')).listen(${port}, () => console.log('Server started'))`,
    ]);

    let started = false;
    proc.stdout.on('data', () => {
      if (!started) {
        started = true;
        resolve(proc.pid);
      }
    });

    proc.on('error', reject);

    // Timeout after 5 seconds
    setTimeout(() => {
      if (!started) {
        proc.kill();
        reject(new Error('Test process failed to start'));
      }
    }, 5000);
  });
}

describe('Kill Endpoint Integration Tests', () => {
  describe('Validation Tests', () => {
    test('should reject request with no pid or port', async () => {
      const response = await makeKillRequest({});

      expect(response.status).toBe(400);
      expect(response.data.success).toBe(false);
      expect(response.data.message).toContain('pid or port is required');
    });

    test('should reject invalid PID format', async () => {
      const response = await makeKillRequest({ pid: 'invalid' });

      expect(response.status).toBe(400);
      expect(response.data.success).toBe(false);
      expect(response.data.message).toContain('Invalid PID format');
    });

    test('should reject negative PID', async () => {
      const response = await makeKillRequest({ pid: '-1' });

      expect(response.status).toBe(400);
      expect(response.data.success).toBe(false);
    });

    test('should reject invalid port number', async () => {
      const response = await makeKillRequest({ port: '99999' });

      expect(response.status).toBe(400);
      expect(response.data.success).toBe(false);
      expect(response.data.message).toContain('Invalid port number');
    });

    test('should reject system process PID (< 1000)', async () => {
      const response = await makeKillRequest({ pid: '999' });

      expect(response.status).toBe(403);
      expect(response.data.success).toBe(false);
      expect(response.data.message).toContain('system processes');
    });
  });

  describe('Process Termination Tests', () => {
    let testPid: number;
    const testPort = 44444;

    beforeEach(async () => {
      // Spawn a test process we can safely kill
      testPid = await spawnTestProcess(testPort);
      // Wait for process to be fully started
      await new Promise(resolve => setTimeout(resolve, 1000));
    });

    afterEach(() => {
      // Clean up test process if it still exists
      try {
        process.kill(testPid, 'SIGKILL');
      } catch {
        // Process already killed, that's fine
      }
    });

    test('should kill process by PID', async () => {
      const response = await makeKillRequest({ pid: testPid.toString() });

      expect(response.status).toBe(200);
      expect(response.data.success).toBe(true);
      expect(response.data.message).toContain('killed successfully');

      // Verify process is actually dead
      await new Promise(resolve => setTimeout(resolve, 500));
      let processExists = true;
      try {
        process.kill(testPid, 0); // Signal 0 checks if process exists
      } catch {
        processExists = false;
      }
      expect(processExists).toBe(false);
    });

    test('should kill process by port', async () => {
      const response = await makeKillRequest({ port: testPort.toString() });

      expect(response.status).toBe(200);
      expect(response.data.success).toBe(true);
      expect(response.data.message).toContain('killed successfully');

      // Verify process is actually dead
      await new Promise(resolve => setTimeout(resolve, 500));
      let processExists = true;
      try {
        process.kill(testPid, 0);
      } catch {
        processExists = false;
      }
      expect(processExists).toBe(false);
    });

    test('should handle non-existent PID gracefully', async () => {
      const response = await makeKillRequest({ pid: '999999' });

      expect(response.status).toBe(200);
      expect(response.data).toHaveProperty('success');
      expect(response.data).toHaveProperty('message');
    });

    test('should handle non-existent port gracefully', async () => {
      const response = await makeKillRequest({ port: '54321' });

      expect(response.status).toBe(200);
      expect(response.data.success).toBe(false);
      expect(response.data.message).toContain('No process found');
    });
  });
});
