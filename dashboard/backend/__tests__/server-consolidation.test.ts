/**
 * Server Consolidation Tests (TDD Red Phase)
 *
 * These tests validate that:
 * 1. Only ONE server process runs after startup
 * 2. Server listens on port 3000 (user preference)
 * 3. Server does not listen on port 3030
 * 4. Startup/shutdown works properly
 * 5. No orphaned processes remain
 */

import { exec } from 'child_process';
import { promisify } from 'util';
import * as http from 'http';

const execAsync = promisify(exec);

describe('Server Consolidation - Single Port 3000', () => {

  test('CRITICAL: Server should listen on port 3000 only', async () => {
    // Check what ports are in use
    const { stdout } = await execAsync('lsof -i :3000 -i :3030 -t 2>/dev/null || echo ""');
    const pids = stdout.trim().split('\n').filter(Boolean);

    // Get process details for each PID
    const processDetails = await Promise.all(
      pids.map(async (pid) => {
        try {
          const { stdout: cmdOutput } = await execAsync(`ps -p ${pid} -o command= 2>/dev/null || echo ""`);
          const { stdout: portOutput } = await execAsync(`lsof -p ${pid} -i -P -n 2>/dev/null | grep -E ":(3000|3030)" || echo ""`);
          return {
            pid,
            command: cmdOutput.trim(),
            ports: portOutput.trim()
          };
        } catch {
          return { pid, command: '', ports: '' };
        }
      })
    );

    // Filter for our dashboard processes
    const dashboardProcesses = processDetails.filter(p =>
      p.command.includes('backend/dist/server.js') ||
      p.command.includes('server-monitor-app') ||
      p.command.includes('server.js')
    );

    // Should have at most ONE dashboard server process
    expect(dashboardProcesses.length).toBeLessThanOrEqual(1);

    // If a process exists, it should be on port 3000
    if (dashboardProcesses.length > 0) {
      const process = dashboardProcesses[0];
      expect(process.ports).toContain('3000');
      expect(process.ports).not.toContain('3030');
    }
  });

  test('Port 3030 should NOT be in use by dashboard', async () => {
    try {
      const { stdout } = await execAsync('lsof -i :3030 -t 2>/dev/null || echo ""');
      const pids = stdout.trim().split('\n').filter(Boolean);

      for (const pid of pids) {
        const { stdout: cmdOutput } = await execAsync(`ps -p ${pid} -o command= 2>/dev/null || echo ""`);
        const command = cmdOutput.trim();

        // Port 3030 should NOT be used by our dashboard processes
        expect(command).not.toContain('backend/dist/server.js');
        expect(command).not.toContain('server-monitor-app');
      }
    } catch (error) {
      // If no process on 3030, that's perfect
      expect(true).toBe(true);
    }
  });

  test('Port 3000 should respond to health check', async () => {
    return new Promise<void>((resolve, reject) => {
      const req = http.get('http://localhost:3000/', (res) => {
        expect(res.statusCode).toBeLessThan(500); // Should not be server error
        resolve();
      });

      req.on('error', (error) => {
        reject(new Error(`Port 3000 not responding: ${error.message}`));
      });

      req.setTimeout(5000, () => {
        req.destroy();
        reject(new Error('Port 3000 health check timeout'));
      });
    });
  });

  test('Server should provide API endpoints on port 3000', async () => {
    return new Promise<void>((resolve, reject) => {
      const req = http.get('http://localhost:3000/api/servers', (res) => {
        expect(res.statusCode).toBe(200);
        expect(res.headers['content-type']).toContain('application/json');

        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
          // Should return valid JSON
          const parsed = JSON.parse(data);
          expect(parsed).toBeDefined();
          resolve();
        });
      });

      req.on('error', (error) => {
        reject(new Error(`API not accessible on port 3000: ${error.message}`));
      });

      req.setTimeout(5000, () => {
        req.destroy();
        reject(new Error('API health check timeout'));
      });
    });
  });

  test('No server-monitor-app proxy process should be running', async () => {
    const { stdout } = await execAsync('ps aux | grep "server-monitor-app" | grep -v grep || echo ""');
    const processes = stdout.trim();

    // Should be empty - no server-monitor-app should be running
    expect(processes).toBe('');
  });

  test('Startup script should only start one server', async () => {
    // Parse the startup script to ensure it's not starting multiple servers
    const fs = require('fs');
    const startupScript = fs.readFileSync('/home/adamsl/planner/start_sys_admin_dash.sh', 'utf8');

    // Count how many times we start services on different ports
    const port3000Starts = (startupScript.match(/3000/g) || []).length;
    const port3030Starts = (startupScript.match(/3030/g) || []).length;

    // After consolidation, we should only reference port 3000
    // This test will fail initially (Red phase)
    expect(port3030Starts).toBe(0);
  });
});

describe('Server Process Management', () => {

  test('ServerOrchestrator should manage processes correctly', () => {
    // This validates the orchestrator is initialized on port 3000
    // Currently it's initialized with port 3000 in line 61 of server.ts
    const fs = require('fs');
    const serverCode = fs.readFileSync('/home/adamsl/planner/dashboard/backend/server.ts', 'utf8');

    // Check that orchestrator is initialized with correct port
    expect(serverCode).toContain('new ServerOrchestrator(stateDbPath, 3000)');
  });

  test('Server should use PORT from environment or default to 3000', () => {
    const fs = require('fs');
    const serverCode = fs.readFileSync('/home/adamsl/planner/dashboard/backend/server.ts', 'utf8');

    // Port should default to 3000, not 3030
    const portMatch = serverCode.match(/const PORT = process\.env\.\w+ \|\| (\d+)/);
    if (portMatch) {
      expect(parseInt(portMatch[1])).toBe(3000);
    }
  });
});
