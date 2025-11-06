/**yyy
 * SSEManager Module
 * Responsibility: Manage Server-Sent Events connection and emit events to EventBus
 */

import { eventBus } from './event-bus.js';

export class SSEManager {
  private eventSource: EventSource | null = null;
  private apiUrl: string;
  private reconnectTimeout: number = 5000;
  private reconnectTimer: number | null = null;

  constructor(apiUrl: string = 'http://localhost:3030') {
    this.apiUrl = apiUrl;
  }

  /**
   * Connect to the SSE endpoint
   */
  public connect(): void {
    if (this.eventSource) {
      console.warn('SSE connection already established');
      return;
    }

    try {
      this.eventSource = new EventSource(`${this.apiUrl}/api/events`);

      // Handle ports updates
      this.eventSource.addEventListener('ports', (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          eventBus.emit('ports-updated', data);
        } catch (error) {
          console.error('Error parsing ports data:', error);
        }
      });

      // Handle servers updates
      this.eventSource.addEventListener('servers', (e: MessageEvent) => {
        try {
          const data = JSON.parse(e.data);
          eventBus.emit('servers-updated', data);
        } catch (error) {
          console.error('Error parsing servers data:', error);
        }
      });

      // Handle connection open
      this.eventSource.onopen = () => {
        console.log('SSE connection established');
        eventBus.emit('connection-status', { status: 'connected', message: 'Connected to server' });

        // Clear any reconnect timer
        if (this.reconnectTimer) {
          clearTimeout(this.reconnectTimer);
          this.reconnectTimer = null;
        }
      };

      // Handle connection errors
      this.eventSource.onerror = (error) => {
        console.error('SSE connection error:', error);
        eventBus.emit('connection-status', { status: 'error', message: 'Connection error - Reconnecting...' });

        // Close the connection and attempt to reconnect
        this.disconnect();
        this.scheduleReconnect();
      };

    } catch (error) {
      console.error('Failed to establish SSE connection:', error);
      eventBus.emit('connection-status', { status: 'error', message: 'Failed to connect' });
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from the SSE endpoint
   */
  public disconnect(): void {
    if (this.eventSource) {
      this.eventSource.close();
      this.eventSource = null;
      console.log('SSE connection closed');
    }

    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  /**
   * Schedule a reconnection attempt
   */
  private scheduleReconnect(): void {
    if (this.reconnectTimer) {
      return; // Already scheduled
    }

    console.log(`Reconnecting in ${this.reconnectTimeout}ms...`);
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, this.reconnectTimeout);
  }

  /**
   * Check if connected
   */
  public isConnected(): boolean {
    return this.eventSource !== null && this.eventSource.readyState === EventSource.OPEN;
  }

  /**
   * Set reconnect timeout
   */
  public setReconnectTimeout(timeout: number): void {
    this.reconnectTimeout = timeout;
  }
}

// Export single instance
export const sseManager = new SSEManager();
