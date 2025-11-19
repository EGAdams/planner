/**
 * Process Manager - Core Process Lifecycle Management
 *
 * Handles:
 * - Spawning and tracking server processes
 * - Managing PIDs and process states
 * - Clean process termination
 * - Preventing duplicate process IDs
 */

import { spawn, ChildProcess } from 'child_process';
import { EventEmitter } from 'events';

export interface SpawnConfig {
  id: string;
  command: string;
  args?: string[];
  cwd: string;
  env?: Record<string, string>;
  ports?: number[];
}

export interface ProcessInfo {
  id: string;
  pid: number;
  command: string;
  args?: string[];
  cwd: string;
  status: 'running' | 'stopped' | 'error';
  startTime: Date;
  endTime?: Date;
  ports?: number[];
  process?: ChildProcess;
}

export interface KillResult {
  success: boolean;
  message: string;
}

export class ProcessManager extends EventEmitter {
  private processes: Map<string, ProcessInfo> = new Map();
  private logBuffers: Map<string, string[]> = new Map();
  private readonly MAX_LOG_LINES = 1000;

  /**
   * Spawn a new process and track it
   */
  async spawn(config: SpawnConfig): Promise<ProcessInfo> {
    // Check for duplicate ID
    if (this.processes.has(config.id)) {
      throw new Error(`Process ${config.id} is already running`);
    }

    return new Promise((resolve, reject) => {
      try {
        const child = spawn(config.command, config.args || [], {
          cwd: config.cwd,
          env: { ...process.env, ...config.env },
          detached: true,
          stdio: ['ignore', 'pipe', 'pipe'] // Capture stdout and stderr
        });

        child.unref();

        // Initialize log buffer
        this.logBuffers.set(config.id, []);

        // Capture stdout
        if (child.stdout) {
          child.stdout.on('data', (data) => {
            this.appendLog(config.id, data.toString());
          });
        }

        // Capture stderr
        if (child.stderr) {
          child.stderr.on('data', (data) => {
            this.appendLog(config.id, data.toString());
          });
        }

        // Handle spawn errors
        child.on('error', (error) => {
          this.processes.delete(config.id);
          this.logBuffers.delete(config.id);
          this.emit('processError', { id: config.id, error });
          reject(error);
        });

        // Handle process exit
        child.on('exit', (code, signal) => {
          const proc = this.processes.get(config.id);
          if (proc) {
            proc.status = 'stopped';
            proc.endTime = new Date();
            this.emit('processExit', { id: config.id, code, signal });
          }
          this.processes.delete(config.id);
          // Keep logs for a bit or clear them? For now, keep them until restart or explicit clear
          // this.logBuffers.delete(config.id); 
        });

        // Create process info
        const processInfo: ProcessInfo = {
          id: config.id,
          pid: child.pid!,
          command: config.command,
          args: config.args,
          cwd: config.cwd,
          status: 'running',
          startTime: new Date(),
          ports: config.ports,
          process: child
        };

        this.processes.set(config.id, processInfo);
        this.emit('processStarted', processInfo);

        // Return process info without the ChildProcess object for cleaner API
        const { process: _, ...infoWithoutProcess } = processInfo;
        resolve(infoWithoutProcess);
      } catch (error) {
        reject(error);
      }
    });
  }

  private appendLog(id: string, data: string) {
    const buffer = this.logBuffers.get(id) || [];
    const lines = data.split('\n');

    for (const line of lines) {
      if (line.trim()) { // Only store non-empty lines
        buffer.push(line);
      }
    }

    // Trim buffer if needed
    if (buffer.length > this.MAX_LOG_LINES) {
      buffer.splice(0, buffer.length - this.MAX_LOG_LINES);
    }

    this.logBuffers.set(id, buffer);
  }

  /**
   * Get logs for a process
   */
  getLogs(id: string): string[] {
    return this.logBuffers.get(id) || [];
  }

  /**
   * Get information about a specific process
   */
  getProcess(id: string): ProcessInfo | undefined {
    const proc = this.processes.get(id);
    if (!proc) return undefined;

    // Return without the ChildProcess object
    const { process: _, ...infoWithoutProcess } = proc;
    return infoWithoutProcess as ProcessInfo;
  }

  /**
   * Get all tracked processes
   */
  getAllProcesses(): ProcessInfo[] {
    return Array.from(this.processes.values()).map(proc => {
      const { process: _, ...infoWithoutProcess } = proc;
      return infoWithoutProcess as ProcessInfo;
    });
  }

  /**
   * Kill a process by ID
   */
  async kill(id: string): Promise<KillResult> {
    const processInfo = this.processes.get(id);

    if (!processInfo) {
      return {
        success: false,
        message: `Process ${id} not found`
      };
    }

    try {
      const { process: child } = processInfo;

      if (child && !child.killed) {
        // Try graceful kill first
        child.kill('SIGTERM');

        // Wait a bit, then force kill if needed
        await new Promise(resolve => setTimeout(resolve, 1000));

        if (!child.killed) {
          child.kill('SIGKILL');
        }
      }

      this.processes.delete(id);
      // Logs are preserved for inspection after kill

      return {
        success: true,
        message: `Process ${id} killed successfully`
      };
    } catch (error: any) {
      return {
        success: false,
        message: `Failed to kill process ${id}: ${error.message}`
      };
    }
  }

  /**
   * Kill all tracked processes
   */
  async killAll(): Promise<void> {
    const killPromises = Array.from(this.processes.keys()).map(id => this.kill(id));
    await Promise.all(killPromises);
  }

  /**
   * Check if a process is still running by PID
   */
  isRunning(id: string): boolean {
    const processInfo = this.processes.get(id);
    if (!processInfo) return false;

    try {
      // Sending signal 0 checks if process exists without killing it
      process.kill(processInfo.pid, 0);
      return true;
    } catch {
      return false;
    }
  }
}
