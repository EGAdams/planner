/**
 * ServerController Web Component
 * Responsibility: Control individual server start/stop operations
 */
import { eventBus } from '../event-bus/event-bus.js';
export class ServerController extends HTMLElement {
    static get observedAttributes() {
        return ['server-id'];
    }
    constructor() {
        super();
        this.apiUrl = 'http://localhost:3030';
        this.serverId = '';
        this.server = null;
        this.isLoading = false;
        this.unsubscribe = null;
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
    attributeChangedCallback(name, oldValue, newValue) {
        if (name === 'server-id' && oldValue !== newValue) {
            this.serverId = newValue;
            this.render();
        }
    }
    setupEventListeners() {
        // Subscribe to servers updates from the EventBus
        this.unsubscribe = eventBus.on('servers-updated', (data) => {
            const servers = Array.isArray(data) ? data : Object.values(data || {});
            this.server = servers.find(s => s.id === this.serverId) || null;
            this.render();
        });
    }
    async toggleServer() {
        if (this.isLoading || !this.server)
            return;
        // If server is orphaned, force kill it
        if (this.server.orphaned && this.server.orphanedPid) {
            await this.forceKill(this.server.orphanedPid);
            return;
        }
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
        }
        catch (error) {
            console.error('Error toggling server:', error);
            alert(`Error: ${error.message}`);
        }
        this.isLoading = false;
        this.render();
    }
    async forceKill(pid) {
        if (this.isLoading)
            return;
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
        }
        catch (error) {
            console.error('Error killing process:', error);
            alert(`Error: ${error.message}`);
        }
        this.isLoading = false;
        this.render();
    }
    render() {
        if (!this.shadowRoot)
            return;
        const isOrphaned = this.server?.orphaned || false;
        const isRunning = this.server?.running || false;
        let buttonText;
        let buttonClass;
        if (this.isLoading) {
            buttonText = 'Loading...';
            buttonClass = isOrphaned ? 'btn-warning' : (isRunning ? 'btn-danger' : 'btn-success');
        }
        else if (isOrphaned) {
            buttonText = 'Force Kill';
            buttonClass = 'btn-warning';
        }
        else if (isRunning) {
            buttonText = 'Stop';
            buttonClass = 'btn-danger';
        }
        else {
            buttonText = 'Start';
            buttonClass = 'btn-success';
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
        const button = this.shadowRoot.querySelector('button');
        if (button) {
            button.addEventListener('click', () => this.toggleServer());
        }
    }
}
customElements.define('server-controller', ServerController);
//# sourceMappingURL=server-controller.js.map