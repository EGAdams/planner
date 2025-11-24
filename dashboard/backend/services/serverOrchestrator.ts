/**
 * Server Orchestrator - High-level coordination of all process management services
 *
 * Integrates:
 * - ProcessManager: Core process lifecycle
 * - ProcessMonitor: Background health checking
 * - ProcessStateStore: Persistent state across restarts
 *
 * Provides:
 * - Unified API for server management
 * - Automatic state persistence
 * - Recovery from crashes
 * - Orphan process detection and cleanup
 */

import { ProcessManager, SpawnConfig } from './processManager';
import { ProcessMonitor } from './processMonitor';
import { ProcessStateStore, StoredProcessInfo } from './processStateStore';
import { EventEmitter } from 'events';

export interface ServerConfig {
  name: string;
  command: string;
  cwd: string;
  env?: Record<string, string>;
  color: string;
  ports: number[];
  type?: 'server' | 'agent';
}

export interface ServerStatus {
  id: string;
  name: string;
  running: boolean;
  orphaned: boolean;
  orphanedPid?: string;
  color: string;
  healthy?: boolean;
  lastCheck?: Date;
  type?: 'server' | 'agent';
}

export class ServerOrchestrator extends EventEmitter {
  private processManager: ProcessManager;
  private processMonitor: ProcessMonitor;
  private processStateStore: ProcessStateStore;
  private serverRegistry: Map<string, ServerConfig> = new Map();

  constructor(
    stateDbPath?: string,
    monitorIntervalMs: number = 3000
  ) {
    super();

    // Initialize services
    this.processManager = new ProcessManager();
    this.processMonitor = new ProcessMonitor(this.processManager);
    this.processStateStore = new ProcessStateStore(stateDbPath);

    // Wire up event forwarding
    this.setupEventForwarding();

    // Start monitoring
    this.processMonitor.start(monitorIntervalMs);
  }

  /**
   * Initialize the orchestrator - load state and recover processes
   */
  async initialize(): Promise<void> {
    await this.processStateStore.load();

    // Check for orphaned processes that were running before restart
    const storedProcesses = await this.processStateStore.getAllProcesses();

    for (const stored of storedProcesses) {
      // Check if process is still running
      const isStillRunning = this.isProcessAlive(stored.pid);

      if (!isStillRunning) {
        // Clean up dead process from state
        await this.processStateStore.removeProcess(stored.id);
      }
    }

    this.emit('initialized', {
      recoveredProcesses: storedProcesses.length
    });
  }

  /**
   * Register a server configuration
   */
  registerServer(id: string, config: ServerConfig): void {
    this.serverRegistry.set(id, config);
  }

  /**
   * Register multiple servers
   */
  registerServers(registry: Record<string, ServerConfig>): void {
    for (const [id, config] of Object.entries(registry)) {
      this.registerServer(id, config);
    }
  }

  /**
   * Split a command string into the executable and argument list.
   * Supports basic quoting so Windows paths with spaces can be launched.
   */
  private parseCommand(commandLine: string): { command: string; args: string[] } {
    const tokens: string[] = [];
    let current = '';
    let quote: '"' | '\'' | null = null;

    for (let i = 0; i < commandLine.length; i++) {
      const char = commandLine[i];

      if (quote) {
        if (char === quote) {
          quote = null;
        } else {
          current += char;
        }
        continue;
      }

      if (char === '"' || char === '\'') {
        quote = char;
        continue;
      }

      if (/\s/.test(char)) {
        if (current) {
          tokens.push(current);
          current = '';
        }
        continue;
      }

      current += char;
    }

    if (current) {
      tokens.push(current);
    }

    if (quote) {
      throw new Error('Unterminated quoted section in command string.');
    }

    if (tokens.length === 0) {
      throw new Error('Command string is empty.');
    }

    const [command, ...args] = tokens;
    return { command, args };
  }

  /**
   * Start a server
   */
  async startServer(serverId: string): Promise<{ success: boolean; message: string }> {
    const config = this.serverRegistry.get(serverId);

    if (!config) {
      return { success: false, message: `Server ${serverId} not found in registry` };
    }

    // Check if already running
    const existing = this.processManager.getProcess(serverId);
    if (existing) {
      return { success: false, message: `Server ${serverId} is already running` };
    }

    try {
      const { command, args } = this.parseCommand(config.command);

      // Spawn process
      const processInfo = await this.processManager.spawn({
        id: serverId,
        command,
        args,
        cwd: config.cwd,
        env: config.env,
        ports: config.ports
      });

      // Save to persistent state
      await this.processStateStore.saveProcess({
        id: serverId,
        pid: processInfo.pid,
        command: config.command,
        cwd: config.cwd,
        startTime: processInfo.startTime,
        status: 'running',
        ports: config.ports
      });

      this.emit('serverStarted', { serverId, pid: processInfo.pid });

      return { success: true, message: `Server ${serverId} started successfully (PID: ${processInfo.pid})` };
    } catch (error: any) {
      return { success: false, message: `Failed to start server: ${error.message}` };
    }
  }

  /**
   * Stop a server
   */
  async stopServer(serverId: string): Promise<{ success: boolean; message: string }> {
    const result = await this.processManager.kill(serverId);

    if (result.success) {
      await this.processStateStore.removeProcess(serverId);
      this.emit('serverStopped', { serverId });
    }

    return result;
  }

  /**
   * Get status of all registered servers
   */
  async getServerStatus(currentPorts?: Array<{ pid: string; port: string }>): Promise<ServerStatus[]> {
    const statuses: ServerStatus[] = [];

    for (const [id, config] of this.serverRegistry.entries()) {
      const managedProcess = this.processManager.getProcess(id);
      const monitorStatus = this.processMonitor.getStatus(id);

      // Check if any of the server's ports are in use
      const portInUse = currentPorts && config.ports.some(port =>
        currentPorts.some(p => parseInt(p.port) === port)
      );

      // Find the PID if port is in use but not managed
      const orphanedProcess = portInUse && !managedProcess && currentPorts
        ? currentPorts.find(p => config.ports.includes(parseInt(p.port)))
        : null;

      const isOrphaned = !!(portInUse && !managedProcess);
      const isRunning = !!managedProcess || !!portInUse;

      statuses.push({
        id,
        name: config.name,
        running: isRunning,
        orphaned: isOrphaned,
        orphanedPid: orphanedProcess?.pid,
        color: config.color,
        healthy: monitorStatus?.isHealthy,
        lastCheck: monitorStatus?.lastCheck,
        type: config.type || 'server'
      });
    }

    return statuses;
  }

  /**
   * Kill an orphaned process by PID
   */
  async killOrphanedProcess(serverId: string, pid: string): Promise<{ success: boolean; message: string }> {
    try {
      // Try to kill the process
      process.kill(parseInt(pid), 'SIGTERM');

      // Wait a bit, then force kill if needed
      await new Promise(resolve => setTimeout(resolve, 1000));

      try {
        process.kill(parseInt(pid), 0); // Check if still alive
        // Still alive, force kill
        process.kill(parseInt(pid), 'SIGKILL');
      } catch {
        // Process is dead, good
      }

      this.emit('orphanKilled', { serverId, pid });

      return { success: true, message: `Orphaned process ${pid} killed successfully` };
    } catch (error: any) {
      return { success: false, message: `Failed to kill orphan: ${error.message}` };
    }
  }

  /**
   * Stop monitoring and cleanup
   */
  async shutdown(): Promise<void> {
    this.processMonitor.stop();
    await this.processManager.killAll();
  }

  /**
   * Setup event forwarding from services
   */
  private setupEventForwarding(): void {
    // Forward process manager events
    this.processManager.on('processStarted', (data) => this.emit('processStarted', data));
    this.processManager.on('processExit', (data) => {
      this.emit('processExit', data);
      // Clean up state
      this.processStateStore.removeProcess(data.id).catch(err =>
        console.error('Failed to clean up state:', err)
      );
    });
    this.processManager.on('processError', (data) => this.emit('processError', data));

    // Forward monitor events
    this.processMonitor.on('healthCheck', (data) => this.emit('healthCheck', data));
    this.processMonitor.on('statusChange', (data) => this.emit('statusChange', data));
    this.processMonitor.on('processDied', (data) => this.emit('processDied', data));
  }

  /**
   * Get logs for a server
   */
  getLogs(serverId: string): string[] {
    return this.processManager.getLogs(serverId);
  }

  /**
   * Check if a process is alive by PID
   */
  private isProcessAlive(pid: number): boolean {
    try {
      process.kill(pid, 0); // Signal 0 just checks existence
      return true;
    } catch {
      return false;
    }
  }
}
