/**
 * ManagedAgent Web Component
 * Responsibility: Display individual agent status, controls, and terminal logs
 */
export class ManagedAgent extends HTMLElement {
    static get observedAttributes() {
        return ['agent-id', 'name', 'description', 'running'];
    }
    constructor() {
        super();
        this.agentId = '';
        this.agentName = '';
        this.agentDescription = '';
        this.isRunning = false;
        this.isLoading = false;
        this.logs = [];
        this.logPollInterval = null;
        this.apiUrl = '';
        this.attachShadow({ mode: 'open' });
    }
    connectedCallback() {
        this.agentId = this.getAttribute('agent-id') || '';
        this.agentName = this.getAttribute('name') || 'Unknown Agent';
        this.agentDescription = this.getAttribute('description') || '';
        this.isRunning = this.getAttribute('running') === 'true';
        // Use current origin if no API URL is specified
        this.apiUrl = `${window.location.protocol}//${window.location.host}`;
        this.render();
        this.startLogPolling();
    }
    disconnectedCallback() {
        this.stopLogPolling();
    }
    attributeChangedCallback(name, oldValue, newValue) {
        if (oldValue === newValue)
            return;
        if (name === 'agent-id')
            this.agentId = newValue;
        if (name === 'name')
            this.agentName = newValue;
        if (name === 'description')
            this.agentDescription = newValue;
        if (name === 'running') {
            this.isRunning = newValue === 'true';
            // If status changed, we might want to adjust polling frequency or UI immediately
            this.render();
        }
    }
    startLogPolling() {
        // Poll for logs every 2 seconds
        this.fetchLogs();
        this.logPollInterval = window.setInterval(() => this.fetchLogs(), 2000);
    }
    stopLogPolling() {
        if (this.logPollInterval) {
            clearInterval(this.logPollInterval);
            this.logPollInterval = null;
        }
    }
    async fetchLogs() {
        if (!this.agentId)
            return;
        try {
            const response = await fetch(`${this.apiUrl}/api/logs/${this.agentId}`);
            const result = await response.json();
            if (result.success && Array.isArray(result.logs)) {
                // Only update if logs have changed to avoid unnecessary re-renders
                // Simple check: length difference or last item difference
                if (result.logs.length !== this.logs.length ||
                    (result.logs.length > 0 && result.logs[result.logs.length - 1] !== this.logs[this.logs.length - 1])) {
                    this.logs = result.logs;
                    this.updateTerminal();
                }
            }
        }
        catch (error) {
            console.error(`Failed to fetch logs for ${this.agentId}:`, error);
        }
    }
    async sendMessage(message) {
        if (!message.trim() || !this.agentId)
            return;
        try {
            const response = await fetch(`${this.apiUrl}/api/agents/${this.agentId}/message`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ message: message.trim() })
            });
            const result = await response.json();
            if (!result.success) {
                console.error(`Failed to send message: ${result.message}`);
            }
        }
        catch (error) {
            console.error('Error sending message to agent:', error);
        }
    }
    async toggleAgent() {
        if (this.isLoading)
            return;
        const action = this.isRunning ? 'stop' : 'start';
        this.isLoading = true;
        this.render(); // Re-render to show loading state
        try {
            const response = await fetch(`${this.apiUrl}/api/servers/${this.agentId}?action=${action}`, {
                method: 'POST'
            });
            const result = await response.json();
            if (!result.success) {
                alert(`Failed to ${action} agent: ${result.message}`);
            }
            // Success will be handled by the global server update event which updates attributes
        }
        catch (error) {
            alert(`Error: ${error.message}`);
        }
        finally {
            this.isLoading = false;
            this.render();
        }
    }
    updateTerminal() {
        if (!this.shadowRoot)
            return;
        const terminalContent = this.shadowRoot.querySelector('.terminal-content');
        if (terminalContent) {
            terminalContent.innerHTML = this.logs.length > 0
                ? this.logs.map(line => `<div>${this.escapeHtml(line)}</div>`).join('')
                : '<div class="empty-logs">No logs available...</div>';
            // Auto-scroll to bottom
            terminalContent.scrollTop = terminalContent.scrollHeight;
        }
    }
    escapeHtml(text) {
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    render() {
        if (!this.shadowRoot)
            return;
        const statusColor = this.isRunning ? '#10b981' : '#ef4444';
        const statusText = this.isRunning ? 'Running' : 'Stopped';
        const buttonText = this.isLoading ? 'Loading...' : (this.isRunning ? 'Stop' : 'Start');
        const buttonClass = this.isRunning ? 'btn-danger' : 'btn-success';
        this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          margin-bottom: 1.5rem;
        }

        .agent-card {
          background: white;
          border-radius: 0.75rem;
          box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
          overflow: hidden;
          border: 1px solid #e5e7eb;
        }

        .agent-header {
          padding: 1.25rem;
          border-bottom: 1px solid #f3f4f6;
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          background: #f9fafb;
        }

        .agent-info h3 {
          margin: 0 0 0.25rem 0;
          font-size: 1.125rem;
          font-weight: 600;
          color: #111827;
        }

        .agent-description {
          color: #6b7280;
          font-size: 0.875rem;
          margin: 0;
        }

        .agent-controls {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .status-badge {
          display: inline-flex;
          align-items: center;
          padding: 0.25rem 0.75rem;
          border-radius: 9999px;
          font-size: 0.75rem;
          font-weight: 500;
          background-color: ${this.isRunning ? '#d1fae5' : '#fee2e2'};
          color: ${this.isRunning ? '#065f46' : '#991b1b'};
        }

        .status-dot {
          width: 0.5rem;
          height: 0.5rem;
          border-radius: 50%;
          background-color: ${statusColor};
          margin-right: 0.375rem;
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

        .terminal-container {
          background: #111827;
          padding: 1rem;
          border-top: 1px solid #374151;
        }

        .terminal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.5rem;
          color: #9ca3af;
          font-size: 0.75rem;
          font-family: monospace;
          text-transform: uppercase;
          letter-spacing: 0.05em;
        }

        .terminal-content {
          height: 200px;
          overflow-y: auto;
          font-family: 'Courier New', Courier, monospace;
          font-size: 0.875rem;
          line-height: 1.5;
          color: #e5e7eb;
          white-space: pre-wrap;
          word-break: break-all;
        }

        .terminal-content::-webkit-scrollbar {
          width: 8px;
        }

        .terminal-content::-webkit-scrollbar-track {
          background: #1f2937;
        }

        .terminal-content::-webkit-scrollbar-thumb {
          background: #4b5563;
          border-radius: 4px;
        }

        .empty-logs {
          color: #6b7280;
          font-style: italic;
        }

        .chat-input-container {
          background: #1f2937;
          padding: 0.75rem 1rem;
          border-top: 1px solid #374151;
          display: flex;
          gap: 0.5rem;
          align-items: center;
        }

        .chat-input {
          flex: 1;
          background: #111827;
          border: 1px solid #374151;
          border-radius: 0.375rem;
          padding: 0.5rem 0.75rem;
          color: #e5e7eb;
          font-family: 'Courier New', Courier, monospace;
          font-size: 0.875rem;
          outline: none;
          transition: border-color 0.2s;
        }

        .chat-input:focus {
          border-color: #3b82f6;
        }

        .chat-input::placeholder {
          color: #6b7280;
        }

        .send-btn {
          padding: 0.5rem 1rem;
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 0.375rem;
          font-size: 0.875rem;
          font-weight: 500;
          cursor: pointer;
          transition: background 0.2s;
          white-space: nowrap;
        }

        .send-btn:hover:not(:disabled) {
          background: #2563eb;
        }

        .send-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
      </style>

      <div class="agent-card">
        <div class="agent-header">
          <div class="agent-info">
            <h3>${this.agentName}</h3>
            <p class="agent-description">${this.agentDescription}</p>
          </div>
          <div class="agent-controls">
            <div class="status-badge">
              <span class="status-dot"></span>
              ${statusText}
            </div>
            <button class="${buttonClass}" ${this.isLoading ? 'disabled' : ''}>
              ${buttonText}
            </button>
          </div>
        </div>
        <div class="terminal-container">
          <div class="terminal-header">
            <span>Terminal Output</span>
            <span>${this.agentId}</span>
          </div>
          <div class="terminal-content">
            <!-- Logs will be injected here -->
          </div>
        </div>
        <div class="chat-input-container">
          <input 
            type="text" 
            class="chat-input" 
            placeholder="Send a message to the agent..."
            ${!this.isRunning ? 'disabled' : ''}
          />
          <button class="send-btn" ${!this.isRunning ? 'disabled' : ''}>
            Send
          </button>
        </div>
      </div>
    `;
        // Attach event listeners
        const button = this.shadowRoot.querySelector('button.btn-success, button.btn-danger');
        if (button) {
            button.addEventListener('click', () => this.toggleAgent());
        }
        const sendBtn = this.shadowRoot.querySelector('.send-btn');
        const chatInput = this.shadowRoot.querySelector('.chat-input');
        if (sendBtn && chatInput) {
            sendBtn.addEventListener('click', () => {
                const message = chatInput.value;
                if (message.trim()) {
                    this.sendMessage(message);
                    chatInput.value = '';
                }
            });
            chatInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    const message = chatInput.value;
                    if (message.trim()) {
                        this.sendMessage(message);
                        chatInput.value = '';
                    }
                }
            });
        }
        // Initial terminal update
        this.updateTerminal();
    }
}
customElements.define('managed-agent', ManagedAgent);
//# sourceMappingURL=managed-agent.js.map