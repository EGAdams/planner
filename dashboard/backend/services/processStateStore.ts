/**
 * Process State Store - Persistent State Management
 *
 * Handles:
 * - Storing process information to disk
 * - Loading state across application restarts
 * - Tracking processes across sessions
 * - Clean state cleanup
 * - Data integrity and error handling
 */

import * as fs from 'fs/promises';
import * as path from 'path';

export interface StoredProcessInfo {
  id: string;
  pid: number;
  command: string;
  args?: string[];
  cwd: string;
  startTime: Date | string;
  status: 'running' | 'stopped' | 'error';
  ports?: number[];
}

export class ProcessStateStore {
  private dbPath: string;
  private state: Map<string, StoredProcessInfo> = new Map();

  constructor(dbPath: string = path.join(process.cwd(), 'process-state.json')) {
    this.dbPath = dbPath;
  }

  /**
   * Load state from disk
   */
  async load(): Promise<void> {
    try {
      const data = await fs.readFile(this.dbPath, 'utf-8');
      const parsed = JSON.parse(data);

      this.state.clear();

      for (const [id, info] of Object.entries(parsed)) {
        const processInfo = info as StoredProcessInfo;
        // Convert string dates back to Date objects
        if (typeof processInfo.startTime === 'string') {
          processInfo.startTime = new Date(processInfo.startTime);
        }
        this.state.set(id, processInfo);
      }
    } catch (error: any) {
      // If file doesn't exist or is corrupted, start with empty state
      if (error.code === 'ENOENT') {
        this.state.clear();
      } else {
        console.warn('Error loading process state:', error.message);
        this.state.clear();
      }
    }
  }

  /**
   * Save process to state
   */
  async saveProcess(processInfo: StoredProcessInfo): Promise<void> {
    this.state.set(processInfo.id, processInfo);
    await this.persist();
  }

  /**
   * Get process from state
   */
  async getProcess(id: string): Promise<StoredProcessInfo | undefined> {
    return this.state.get(id);
  }

  /**
   * Remove process from state
   */
  async removeProcess(id: string): Promise<void> {
    this.state.delete(id);
    await this.persist();
  }

  /**
   * Get all processes from state
   */
  async getAllProcesses(): Promise<StoredProcessInfo[]> {
    return Array.from(this.state.values());
  }

  /**
   * Clear all state
   */
  async clear(): Promise<void> {
    this.state.clear();
    await this.persist();
  }

  /**
   * Persist current state to disk
   */
  private async persist(): Promise<void> {
    try {
      // Convert Map to plain object for JSON serialization
      const obj: Record<string, StoredProcessInfo> = {};
      for (const [id, info] of this.state.entries()) {
        obj[id] = info;
      }

      const data = JSON.stringify(obj, null, 2);

      // Ensure directory exists
      const dir = path.dirname(this.dbPath);
      await fs.mkdir(dir, { recursive: true });

      // Write to file
      await fs.writeFile(this.dbPath, data, 'utf-8');
    } catch (error: any) {
      console.error('Error persisting process state:', error.message);
      throw error;
    }
  }

  /**
   * Check if a process exists in state
   */
  async hasProcess(id: string): Promise<boolean> {
    return this.state.has(id);
  }
}
