/**
 * Process Monitor - Background Health Monitoring
 *
 * Handles:
 * - Periodic health checks (every ~3 seconds)
 * - Port connectivity verification
 * - Process death detection
 * - Independent of UI/browser sessions
 * - Event emission for state changes
 */

import { EventEmitter } from 'events';
import { ProcessManager, ProcessInfo } from './processManager';
import * as net from 'net';

export interface ProcessStatus {
  id: string;
  isRunning: boolean;
  isHealthy: boolean;
  lastCheck: Date;
  portConnectivity?: Record<number, boolean>;
}

export class ProcessMonitor extends EventEmitter {
  private processManager: ProcessManager;
  private monitorInterval?: NodeJS.Timeout;
  private statusMap: Map<string, ProcessStatus> = new Map();
  private intervalMs: number = 3000;

  constructor(processManager: ProcessManager) {
    super();
    this.processManager = processManager;

    // Listen to process manager events
    this.processManager.on('processExit', (data) => {
      this.emit('processDied', data);
    });
  }

  /**
   * Start background monitoring
   */
  start(intervalMs: number = 3000): void {
    this.intervalMs = intervalMs;

    if (this.monitorInterval) {
      clearInterval(this.monitorInterval);
    }

    // Perform initial check immediately
    this.performHealthCheck();

    // Set up periodic checks
    this.monitorInterval = setInterval(() => {
      this.performHealthCheck();
    }, intervalMs);
  }

  /**
   * Stop monitoring
   */
  stop(): void {
    if (this.monitorInterval) {
      clearInterval(this.monitorInterval);
      this.monitorInterval = undefined;
    }
  }

  /**
   * Perform a health check on all processes
   */
  private async performHealthCheck(): Promise<void> {
    const processes = this.processManager.getAllProcesses();

    this.emit('healthCheck', {
      timestamp: new Date(),
      processCount: processes.length
    });

    for (const proc of processes) {
      await this.checkProcess(proc);
    }
  }

  /**
   * Check health of a specific process
   */
  private async checkProcess(proc: ProcessInfo): Promise<void> {
    const isRunning = this.processManager.isRunning(proc.id);
    const portConnectivity = proc.ports
      ? await this.checkPorts(proc.ports)
      : undefined;

    const status: ProcessStatus = {
      id: proc.id,
      isRunning,
      isHealthy: isRunning && (portConnectivity ? Object.values(portConnectivity).every(v => v) : true),
      lastCheck: new Date(),
      portConnectivity
    };

    const previousStatus = this.statusMap.get(proc.id);
    this.statusMap.set(proc.id, status);

    // Emit status change event if status changed
    if (previousStatus && (
      previousStatus.isRunning !== status.isRunning ||
      previousStatus.isHealthy !== status.isHealthy
    )) {
      this.emit('statusChange', {
        id: proc.id,
        previous: previousStatus,
        current: status
      });
    }

    // Emit specific events for important changes
    if (previousStatus?.isRunning && !status.isRunning) {
      this.emit('processDied', { id: proc.id, lastCheck: status.lastCheck });
    }
  }

  /**
   * Check connectivity to specified ports
   */
  private async checkPorts(ports: number[]): Promise<Record<number, boolean>> {
    const results: Record<number, boolean> = {};

    await Promise.all(
      ports.map(async (port) => {
        results[port] = await this.checkPort(port);
      })
    );

    return results;
  }

  /**
   * Check if a specific port is reachable
   */
  private async checkPort(port: number, host: string = 'localhost', timeout: number = 1000): Promise<boolean> {
    return new Promise((resolve) => {
      const socket = new net.Socket();
      let resolved = false;

      const cleanup = () => {
        if (!resolved) {
          resolved = true;
          socket.destroy();
        }
      };

      socket.setTimeout(timeout);

      socket.on('connect', () => {
        cleanup();
        resolve(true);
      });

      socket.on('timeout', () => {
        cleanup();
        resolve(false);
      });

      socket.on('error', () => {
        cleanup();
        resolve(false);
      });

      socket.connect(port, host);
    });
  }

  /**
   * Get current status of a process
   */
  getStatus(id: string): ProcessStatus | undefined {
    return this.statusMap.get(id);
  }

  /**
   * Get all process statuses
   */
  getAllStatuses(): ProcessStatus[] {
    return Array.from(this.statusMap.values());
  }
}
