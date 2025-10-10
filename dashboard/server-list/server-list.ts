/**
 * ServerList Web Component
 * Responsibility: Display list of registered servers with their status
 */

import { eventBus } from '../event-bus/event-bus.js';

interface Server {
  id: string;
  name: string;
  running: boolean;
}

export class ServerList extends HTMLElement {
  private servers: Server[] = [];
  private unsubscribe: (() => void) | null = null;

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  connectedCallback() {
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

  private setupEventListeners() {
    // Subscribe to servers updates from the EventBus
    this.unsubscribe = eventBus.on('servers-updated', (data) => {
      this.servers = data;
      this.render();
    });
  }

  private render() {
    if (!this.shadowRoot) return;

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
        }

        .container {
          background: white;
          border-radius: 0.5rem;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
          padding: 1.5rem;
        }

        h2 {
          font-size: 1.25rem;
          font-weight: 600;
          margin: 0 0 1rem 0;
          color: #1f2937;
        }

        .server-grid {
          display: grid;
          gap: 1rem;
        }

        .server-card {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 1rem;
          border: 1px solid #e5e7eb;
          border-radius: 0.5rem;
          transition: all 0.2s;
        }

        .server-card:hover {
          border-color: #d1d5db;
          box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }

        .server-info {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .status-indicator {
          width: 12px;
          height: 12px;
          border-radius: 50%;
          flex-shrink: 0;
        }

        .status-indicator.running {
          background: #10b981;
          box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
        }

        .status-indicator.stopped {
          background: #ef4444;
          box-shadow: 0 0 0 3px rgba(239, 68, 68, 0.2);
        }

        .server-name {
          font-weight: 500;
          color: #1f2937;
        }

        .server-id {
          font-size: 0.75rem;
          color: #6b7280;
          font-family: monospace;
        }

        .empty-state {
          text-align: center;
          padding: 2rem;
          color: #6b7280;
        }

        .empty-state-title {
          font-weight: 500;
          margin-bottom: 0.5rem;
        }

        .empty-state-text {
          font-size: 0.875rem;
        }
      </style>

      <div class="container">
        <h2>Managed Servers</h2>

        ${this.servers.length === 0 ? `
          <div class="empty-state">
            <div class="empty-state-title">No servers configured</div>
            <div class="empty-state-text">
              Add servers to the SERVER_REGISTRY in backend/server.ts
            </div>
          </div>
        ` : `
          <div class="server-grid">
            ${this.servers.map(server => `
              <div class="server-card">
                <div class="server-info">
                  <div class="status-indicator ${server.running ? 'running' : 'stopped'}"></div>
                  <div>
                    <div class="server-name">${server.name}</div>
                    <div class="server-id">${server.id}</div>
                  </div>
                </div>
                <server-controller server-id="${server.id}"></server-controller>
              </div>
            `).join('')}
          </div>
        `}
      </div>
    `;
  }
}

customElements.define('server-list', ServerList);
