/**
 * Admin Dashboard Server - Integrated with Process Management Services
 *
 * This version integrates the new process management system with the existing dashboard.
 */

import * as http from 'http';
import * as url from 'url';
import * as path from 'path';
import * as fs from 'fs';
import { exec } from 'child_process';
import { promisify } from 'util';
import * as dotenv from 'dotenv';
import { ServerOrchestrator, ServerConfig } from './services/serverOrchestrator';

dotenv.config({ path: path.join(__dirname, '../../.env') });

const execAsync = promisify(exec);
const PORT = process.env.ADMIN_PORT || 3030;
const HOST = process.env.ADMIN_HOST || '0.0.0.0';
const SUDO_PASSWORD = process.env.SUDO_PASSWORD || '';

interface ProcessInfo {
  pid: string;
  port: string;
  protocol: string;
  program: string;
  command: string;
  color?: string;
  serverId?: string;
  orphaned?: boolean;
}

// Server registry - define all servers that can be managed
const SERVER_REGISTRY: Record<string, ServerConfig> = {
  'livekit-server': {
    name: 'LiveKit Server',
    command: './livekit-server --dev --bind 0.0.0.0',
    cwd: '/home/adamsl/ottomator-agents/livekit-agent',
    color: '#DBEAFE',
    ports: [7880, 7881], // Only track main TCP ports; UDP ports are dynamic
  },
  'livekit-voice-agent': {
    name: 'LiveKit Voice Agent',
    command: '/home/adamsl/planner/venv/bin/python livekit_mcp_agent.py dev',
    cwd: '/home/adamsl/ottomator-agents/livekit-agent',
    color: '#D1FAE5',
    ports: [],
  },
  'pydantic-web-server': {
    name: 'Pydantic Web Server',
    command: '/home/adamsl/planner/venv/bin/python pydantic_mcp_agent_endpoint.py',
    cwd: '/home/adamsl/ottomator-agents/pydantic-ai-mcp-agent/studio-integration-version',
    color: '#E9D5FF',
    ports: [8001],
  },
};

// Initialize orchestrator
const stateDbPath = path.join(__dirname, '../process-state.json');
const orchestrator = new ServerOrchestrator(stateDbPath, 3000);

// Register all servers
orchestrator.registerServers(SERVER_REGISTRY);

// Initialize and recover state
orchestrator.initialize().then(() => {
  console.log('Server orchestrator initialized');
}).catch(err => {
  console.error('Failed to initialize orchestrator:', err);
});

// Listen for orchestrator events
orchestrator.on('serverStarted', (data) => {
  console.log(`Server ${data.serverId} started with PID ${data.pid}`);
  broadcastServerUpdate();
});

orchestrator.on('serverStopped', (data) => {
  console.log(`Server ${data.serverId} stopped`);
  broadcastServerUpdate();
});

orchestrator.on('processDied', (data) => {
  console.log(`Process ${data.id} died unexpectedly`);
  broadcastServerUpdate();
});

function getServerByPort(port: string): { serverId: string; color: string } | null {
  const portNum = parseInt(port, 10);
  for (const [serverId, config] of Object.entries(SERVER_REGISTRY)) {
    if (config.ports.includes(portNum)) {
      return { serverId, color: config.color };
    }
  }
  return null;
}

function getServerByProgramName(programName: string): { serverId: string; color: string } | null {
  // Normalize program name (remove path, extension, etc.)
  const normalizedProgram = programName.toLowerCase().trim();

  for (const [serverId, config] of Object.entries(SERVER_REGISTRY)) {
    // Check if the program name contains the server ID or command name
    if (normalizedProgram.includes(serverId.toLowerCase()) ||
        config.command.toLowerCase().includes(normalizedProgram)) {
      return { serverId, color: config.color };
    }
  }
  return null;
}

async function getListeningPorts(): Promise<ProcessInfo[]> {
  try {
    const { stdout } = await execAsync('ss -tulpn 2>/dev/null || netstat -tulpn 2>/dev/null');
    const lines = stdout.split('\n').slice(1); // Skip header
    const processes: ProcessInfo[] = [];

    for (const line of lines) {
      if (!line.trim()) continue;

      const parts = line.trim().split(/\s+/);  // Trim line to remove trailing spaces
      if (parts.length < 6) continue;

      const localAddress = parts[4] || '';
      const programInfo = parts[parts.length - 1] || '';

      const portMatch = localAddress.match(/:(\d+)$/);

      // Handle both netstat format (123/program) and ss format (users:(("program",pid=123,fd=N)))
      let pidMatch = programInfo.match(/(\d+)\//);  // netstat format
      if (!pidMatch) {
        pidMatch = programInfo.match(/pid=(\d+)/);  // ss format
      }

      let programMatch = programInfo.match(/\/(.+)$/);  // netstat format
      if (!programMatch) {
        programMatch = programInfo.match(/\(\("(.+?)",pid=/);  // ss format
      }

      if (portMatch && pidMatch) {
        const programName = programMatch ? programMatch[1] : 'unknown';

        // Try to match by port first, then fall back to program name
        let serverInfo = getServerByPort(portMatch[1]);
        if (!serverInfo) {
          serverInfo = getServerByProgramName(programName);
        }

        processes.push({
          pid: pidMatch[1],
          port: portMatch[1],
          protocol: parts[0] || '',
          program: programName,
          command: await getCommandForPid(pidMatch[1]),
          color: serverInfo?.color,
          serverId: serverInfo?.serverId,
        });
      }
    }

    return processes;
  } catch (error) {
    console.error('Error getting listening ports:', error);
    return [];
  }
}

async function getCommandForPid(pid: string): Promise<string> {
  try {
    const { stdout } = await execAsync(`ps -p ${pid} -o command=`);
    return stdout.trim();
  } catch {
    return 'unknown';
  }
}

async function killProcess(pid: string, useSudo: boolean = false): Promise<{ success: boolean; message: string }> {
  try {
    const killCmd = useSudo && SUDO_PASSWORD
      ? `echo "${SUDO_PASSWORD}" | sudo -S kill -9 ${pid}`
      : `kill -9 ${pid}`;

    await execAsync(killCmd);
    return { success: true, message: `Process ${pid} killed successfully` };
  } catch (error: any) {
    return { success: false, message: error.message };
  }
}

async function killProcessOnPort(port: string): Promise<{ success: boolean; message: string }> {
  try {
    const processes = await getListeningPorts();
    const process = processes.find(p => p.port === port);

    if (!process) {
      return { success: false, message: `No process found on port ${port}` };
    }

    return await killProcess(process.pid, true);
  } catch (error: any) {
    return { success: false, message: error.message };
  }
}

// SSE clients for real-time updates
const sseClients: http.ServerResponse[] = [];

function broadcastUpdate(event: string, data: any) {
  const message = `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
  sseClients.forEach(client => {
    try {
      client.write(message);
    } catch (error) {
      console.error('Error broadcasting to client:', error);
    }
  });
}

async function broadcastServerUpdate() {
  const ports = await getListeningPorts();
  broadcastUpdate('ports', ports);

  const servers = await orchestrator.getServerStatus(ports);
  broadcastUpdate('servers', servers);
}

// Periodic updates
setInterval(async () => {
  await broadcastServerUpdate();
}, 5000);

const server = http.createServer(async (req, res) => {
  const parsedUrl = url.parse(req.url || '', true);
  const pathname = parsedUrl.pathname || '/';

  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }

  // API Routes
  if (pathname === '/api/ports' && req.method === 'GET') {
    const ports = await getListeningPorts();
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(ports));
    return;
  }

  if (pathname === '/api/servers' && req.method === 'GET') {
    const ports = await getListeningPorts();
    const servers = await orchestrator.getServerStatus(ports);
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(servers));
    return;
  }

  if (pathname === '/api/docling-report' && req.method === 'POST') {
    try {
      const repoRoot = path.join(__dirname, '../../..');
      const scriptPath = path.join(repoRoot, 'docling', 'test_january_statement.py');
      const pythonCandidates = [
        path.join(repoRoot, 'venv', 'bin', 'python'),
        path.join(repoRoot, 'venv', 'bin', 'python3'),
        path.join(repoRoot, 'venv', 'Scripts', 'python.exe'),
        'python3',
        'python'
      ];

      const pythonExecutable = pythonCandidates.find(candidate =>
        candidate.startsWith('python') ? true : fs.existsSync(candidate)
      );

      if (!pythonExecutable) {
        throw new Error('Unable to locate Python executable for Docling report.');
      }

      const command = pythonExecutable.startsWith('python')
        ? `${pythonExecutable} "${scriptPath}"`
        : `"${pythonExecutable}" "${scriptPath}"`;

      const { stdout } = await execAsync(command, {
        cwd: repoRoot,
        maxBuffer: 10 * 1024 * 1024
      });

      const trimmed = stdout.trim();
      const payload = JSON.parse(trimmed);

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(payload));
    } catch (error: any) {
      console.error('Docling report error:', error);

      const message = error?.stderr?.toString() || error?.message || 'Unknown error';

      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        success: false,
        message: 'Failed to generate Docling report',
        details: message
      }));
    }
    return;
  }

  if (pathname.startsWith('/api/servers/') && req.method === 'POST') {
    const serverId = pathname.split('/')[3];
    const action = parsedUrl.query.action as string;

    let result;
    if (action === 'start') {
      result = await orchestrator.startServer(serverId);
    } else if (action === 'stop') {
      result = await orchestrator.stopServer(serverId);
    } else {
      res.writeHead(400, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ success: false, message: 'Invalid action' }));
      return;
    }

    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(result));

    // Broadcast update after action
    await broadcastServerUpdate();
    return;
  }

  if (pathname === '/api/kill' && req.method === 'DELETE') {
    let body = '';
    req.on('data', chunk => body += chunk.toString());
    req.on('end', async () => {
      const { pid, port } = JSON.parse(body);

      let result;
      if (pid) {
        result = await killProcess(pid, true);
      } else if (port) {
        result = await killProcessOnPort(port);
      } else {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ success: false, message: 'Either pid or port is required' }));
        return;
      }

      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(result));

      if (result.success) {
        await broadcastServerUpdate();
      }
    });
    return;
  }

  if (pathname === '/api/events' && req.method === 'GET') {
    res.writeHead(200, {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive'
    });

    sseClients.push(res);

    // Send initial data
    const ports = await getListeningPorts();
    const servers = await orchestrator.getServerStatus(ports);
    res.write(`event: ports\ndata: ${JSON.stringify(ports)}\n\n`);
    res.write(`event: servers\ndata: ${JSON.stringify(servers)}\n\n`);

    req.on('close', () => {
      const index = sseClients.indexOf(res);
      if (index !== -1) {
        sseClients.splice(index, 1);
      }
    });
    return;
  }

  // Static file serving
  const publicDir = path.join(__dirname, '../../public');
  let filePath = pathname === '/' ? '/index.html' : pathname;
  filePath = path.join(publicDir, filePath);

  const extname = path.extname(filePath);
  const contentTypes: Record<string, string> = {
    '.html': 'text/html',
    '.js': 'text/javascript',
    '.css': 'text/css',
    '.json': 'application/json',
    '.png': 'image/png',
    '.jpg': 'image/jpg',
    '.svg': 'image/svg+xml',
  };

  const contentType = contentTypes[extname] || 'text/plain';

  fs.readFile(filePath, (error, content) => {
    if (error) {
      if (error.code === 'ENOENT') {
        res.writeHead(404);
        res.end('404 Not Found');
      } else {
        res.writeHead(500);
        res.end('500 Internal Server Error');
      }
    } else {
      res.writeHead(200, { 'Content-Type': contentType });
      res.end(content);
    }
  });
});

// Graceful shutdown
process.on('SIGINT', async () => {
  console.log('\nShutting down gracefully...');
  await orchestrator.shutdown();
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});

process.on('SIGTERM', async () => {
  console.log('\nShutting down gracefully...');
  await orchestrator.shutdown();
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});

server.listen(Number(PORT), HOST, () => {
  console.log(`Admin dashboard server running on http://${HOST}:${PORT}`);
  console.log(`Process management enabled with persistent state`);
});
