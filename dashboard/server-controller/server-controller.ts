/**
 * ServerController Web Component
 * Responsibility: Control individual server start/stop operations
 */

import { eventBus } from '../event-bus/event-bus.js';

interface Server {
  id: string;
  name: string;
  running: boolean;
}

export class ServerController extends HTMLElement {
  private apiUrl: string = 'http://localhost:3030';
  private serverId: string = '';
  private server: Server | null = null;
  private isLoading: boolean = false;
  private unsubscribe: (() => void) | null = null;

  static get observedAttributes() {
    return ['server-id'];
  }

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  connectedCallback() {
    const apiUrl = this.getAttribute('api-url');
    if (apiUrl) {
      this.apiUrl = apiUrl;
    }

    this.serverId = this.getAttribute('server-id') || '';
    this.setupEventListeners();
    this.render();
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
    this.unsubscribe = eventBus.on('servers-updated', (data: Server[]) => {
      this.server = data.find(s => s.id === this.serverId) || null;
      this.render();
    });
  }

  private async toggleServer() {
    if (this.isLoading || !this.server) return;

    const action = this.server.running ? 'stop' : 'start';
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

  private render() {
    if (!this.shadowRoot) return;

    const isRunning = this.server?.running || false;
    const buttonText = this.isLoading ? 'Loading...' : (isRunning ? 'Stop' : 'Start');
    const buttonClass = isRunning ? 'btn-danger' : 'btn-success';

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

    const button = this.shadowRoot.querySelector('button');
    if (button) {
      button.addEventListener('click', () => this.toggleServer());
    }
  }
}

customElements.define('server-controller', ServerController);
