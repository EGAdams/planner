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
const HOST = process.env.ADMIN_HOST || '127.0.0.1';
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
    command: 'uv run python livekit_mcp_agent.py dev',
    cwd: '/home/adamsl/ottomator-agents/livekit-agent',
    color: '#D1FAE5',
    ports: [],
  },
  'pydantic-web-server': {
    name: 'Pydantic Web Server',
    command: '.venv/bin/python pydantic_web_server.py',
    cwd: '/home/adamsl/ottomator-agents/livekit-agent',
    color: '#E9D5FF',
    ports: [8000],
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
      let pidMatch = programInfo.match(/(\d+)\/);  // netstat format
      if (!pidMatch) {
        pidMatch = programInfo.match(/pid=(\d+)/);  // ss format
      }

      let programMatch = programInfo.match(/\/(.+)$/);  // netstat format
      if (!programMatch) {
        programMatch = programInfo.match(/\( \