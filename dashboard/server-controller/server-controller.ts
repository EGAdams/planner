/**
 * ServerController Web Component
 * Responsibility: Control individual server start/stop operations
 */

import { eventBus } from '../event-bus/event-bus.js';

interface Server {
  id: string;
  name: string;
  running: boolean;
  orphaned: boolean;
  orphanedPid?: string;
}

export class ServerController extends HTMLElement {
  private apiUrl: string = '';
  private serverId: string = '';
  private server: Server | null = null;
  private isLoading: boolean = false;
  private unsubscribe: (() => void) | null = null;
  private buttonClickHandler: (() => void) | null = null;

  static get observedAttributes() {
    return ['server-id'];
  }

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    // Bind the toggle method to preserve 'this' context
    this.buttonClickHandler = () => this.toggleServer();
  }

  connectedCallback() {
    const apiUrl = this.getAttribute('api-url');
    if (apiUrl) {
      this.apiUrl = apiUrl;
    } else {
      // Use current origin if no API URL is specified
      // The dashboard backend runs on the same host and port as the frontend
      this.apiUrl = `${window.location.protocol}//${window.location.host}`;
    }

    this.serverId = this.getAttribute('server-id') || '';

    // Initialize server data - check if we need to fetch current servers
    // If this component is created after servers have loaded, we won't have data yet
    // We'll get it when the next 'servers-updated' event fires
    console.log('ServerController connected', { serverId: this.serverId, apiUrl: this.apiUrl });

    this.setupEventListeners();
    this.fetchInitialServerState();
    this.render();
  }

  private async fetchInitialServerState() {
    // Fetch current server state on initialization
    try {
      const response = await fetch(`${this.apiUrl}/api/servers`);
      const result = await response.json();

      if (result.success && result.servers) {
        const servers = Array.isArray(result.servers) ? result.servers : Object.values(result.servers || {});
        this.server = servers.find((s: Server) => s.id === this.serverId) || null;
        console.log('Initial server state fetched', { serverId: this.serverId, server: this.server });
        this.render();
      }
    } catch (error) {
      console.error('Failed to fetch initial server state:', error);
      // Continue - EventBus updates will still work
    }
  }

  disconnectedCallback() {
    // Clean up event subscription
    if (this.unsubscribe) {
      this.unsubscribe();
      this.unsubscribe = null;
    }
  }

  attributeChangedCallback(name: string, oldValue: string, newValue: string) {
    if (name === 'server-id' && oldValue !== newValue) {
      this.serverId = newValue;
      this.render();
    }
  }

  private setupEventListeners() {
    // Subscribe to servers updates from the EventBus
    this.unsubscribe = eventBus.on('servers-updated', (data: Server[] | Record<string, Server>) => {
      const servers = Array.isArray(data) ? data : Object.values(data || {});
      this.server = servers.find(s => s.id === this.serverId) || null;
      this.render();
    });
  }

  private async toggleServer() {
    console.log('toggleServer called', { isLoading: this.isLoading, server: this.server });

    if (this.isLoading || !this.server) {
      console.warn('toggleServer aborted - loading or no server', { isLoading: this.isLoading, hasServer: !!this.server });
      return;
    }

    // If server is orphaned, force kill it
    if (this.server.orphaned && this.server.orphanedPid) {
      await this.forceKill(this.server.orphanedPid);
      return;
    }

    const action = this.server.running ? 'stop' : 'start';
    console.log('Setting isLoading to true, action:', action);
    this.isLoading = true;
    this.render();

    try {
      const response = await fetch(`${this.apiUrl}/api/servers/${this.serverId}?action=${action}`, {
        method: 'POST'
      });

      const result = await response.json();

      if (!result.success) {
        console.error('Server action failed:', result.message);
        alert(`Failed to ${action} server: ${result.message}`);
      }
    } catch (error: any) {
      console.error('Error toggling server:', error);
      alert(`Error: ${error.message}`);
    }

    this.isLoading = false;
    this.render();
  }

  private async forceKill(pid: string) {
    if (this.isLoading) return;

    if (!confirm(`Force kill orphaned process (PID: ${pid})? This cannot be undone.`)) {
      return;
    }

    this.isLoading = true;
    this.render();

    try {
      const response = await fetch(`${this.apiUrl}/api/kill`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ pid })
      });

      const result = await response.json();

      if (!result.success) {
        console.error('Force kill failed:', result.message);
        alert(`Failed to kill process: ${result.message}`);
      }
    } catch (error: any) {
      console.error('Error killing process:', error);
      alert(`Error: ${error.message}`);
    }

    this.isLoading = false;
    this.render();
  }

  private render() {
    if (!this.shadowRoot) return;

    const isOrphaned = this.server?.orphaned || false;
    const isRunning = this.server?.running || false;

    let buttonText: string;
    let buttonClass: string;

    if (this.isLoading) {
      buttonText = 'Loading...';
      buttonClass = isOrphaned ? 'btn-warning' : (isRunning ? 'btn-danger' : 'btn-success');
    } else if (isOrphaned) {
      buttonText = 'Force Kill';
      buttonClass = 'btn-warning';
    } else if (isRunning) {
      buttonText = 'Stop';
      buttonClass = 'btn-danger';
    } else {
      buttonText = 'Start';
      buttonClass = 'btn-success';
    }

    // Remove old event listener before re-rendering
    const oldButton = this.shadowRoot.querySelector('button');
    if (oldButton && this.buttonClickHandler) {
      oldButton.removeEventListener('click', this.buttonClickHandler);
    }

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: inline-block;
        }

        button {
          padding: 0.5rem 1rem;
          border: none;
          border-radius: 0.375rem;
          font-size: 0.875rem;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
          min-width: 80px;
        }

        button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .btn-success {
          background: #10b981;
          color: white;
        }

        .btn-success:hover:not(:disabled) {
          background: #059669;
        }

        .btn-danger {
          background: #ef4444;
          color: white;
        }

        .btn-danger:hover:not(:disabled) {
          background: #dc2626;
        }

        .btn-warning {
          background: #f59e0b;
          color: white;
        }

        .btn-warning:hover:not(:disabled) {
          background: #d97706;
        }

        .spinner {
          display: inline-block;
          width: 12px;
          height: 12px;
          border: 2px solid rgba(255, 255, 255, 0.3);
          border-top-color: white;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
          margin-right: 0.5rem;
          vertical-align: middle;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }
      </style>

      <button class="${buttonClass}" ${this.isLoading ? 'disabled' : ''}>
        ${this.isLoading ? '<span class="spinner"></span>' : ''}
        ${buttonText}
      </button>
    `;

    // Attach event listener to the new button element
    const button = this.shadowRoot.querySelector('button');
    if (button && this.buttonClickHandler) {
      console.log('Attaching click handler to button', { serverId: this.serverId, buttonText });
      button.addEventListener('click', this.buttonClickHandler);
    } else {
      console.error('Failed to attach click handler', { hasButton: !!button, hasHandler: !!this.buttonClickHandler });
    }
  }
}

customElements.define('server-controller', ServerController);
