/**
 * PortMonitor Web Component
 * Responsibility: Display all listening ports and associated processes
 */

interface ProcessInfo {
  pid: string;
  port: string;
  protocol: string;
  program: string;
  command: string;
}

export class PortMonitor extends HTMLElement {
  private processes: ProcessInfo[] = [];

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  connectedCallback() {
    this.setupEventListeners();
    this.render();
  }

  private setupEventListeners() {
    window.addEventListener('bus-event', ((e: CustomEvent) => {
      if (e.detail.type === 'ports-updated') {
        this.processes = e.detail.data;
        this.render();
      }
    }) as EventListener);
  }

  private emitKillRequest(pid: string, port: string) {
    const event = new CustomEvent('kill-process', {
      bubbles: true,
      composed: true,
      detail: { pid, port }
    });
    this.dispatchEvent(event);
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

        table {
          width: 100%;
          border-collapse: collapse;
        }

        thead {
          background: #f9fafb;
        }

        th {
          padding: 0.75rem;
          text-align: left;
          font-size: 0.875rem;
          font-weight: 600;
          color: #6b7280;
          border-bottom: 1px solid #e5e7eb;
        }

        td {
          padding: 0.75rem;
          font-size: 0.875rem;
          color: #374151;
          border-bottom: 1px solid #f3f4f6;
        }

        tr:hover {
          background: #f9fafb;
        }

        .port-badge {
          display: inline-block;
          padding: 0.25rem 0.5rem;
          background: #dbeafe;
          color: #1e40af;
          border-radius: 0.25rem;
          font-weight: 500;
          font-size: 0.875rem;
        }

        .protocol-badge {
          display: inline-block;
          padding: 0.25rem 0.5rem;
          background: #e0e7ff;
          color: #4338ca;
          border-radius: 0.25rem;
          font-weight: 500;
          font-size: 0.75rem;
          text-transform: uppercase;
        }

        .command {
          font-family: monospace;
          font-size: 0.75rem;
          color: #6b7280;
          max-width: 300px;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }

        .actions {
          display: flex;
          gap: 0.5rem;
        }

        button {
          padding: 0.375rem 0.75rem;
          border: none;
          border-radius: 0.375rem;
          font-size: 0.75rem;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-danger {
          background: #ef4444;
          color: white;
        }

        .btn-danger:hover {
          background: #dc2626;
        }

        .empty-state {
          text-align: center;
          padding: 2rem;
          color: #6b7280;
        }

        .refresh-indicator {
          display: inline-block;
          width: 8px;
          height: 8px;
          background: #10b981;
          border-radius: 50%;
          margin-right: 0.5rem;
          animation: pulse 2s infinite;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      </style>

      <div class="container">
        <h2>
          <span class="refresh-indicator"></span>
          Listening Ports
        </h2>

        ${this.processes.length === 0 ? `
          <div class="empty-state">
            No listening ports detected
          </div>
        ` : `
          <table>
            <thead>
              <tr>
                <th>Port</th>
                <th>Protocol</th>
                <th>PID</th>
                <th>Program</th>
                <th>Command</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              ${this.processes.map(proc => `
                <tr>
                  <td><span class="port-badge">${proc.port}</span></td>
                  <td><span class="protocol-badge">${proc.protocol}</span></td>
                  <td>${proc.pid}</td>
                  <td>${proc.program}</td>
                  <td><div class="command" title="${proc.command}">${proc.command}</div></td>
                  <td>
                    <div class="actions">
                      <button class="btn-danger" data-pid="${proc.pid}" data-port="${proc.port}">
                        Kill
                      </button>
                    </div>
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        `}
      </div>
    `;

    // Attach event listeners to kill buttons
    this.shadowRoot.querySelectorAll('.btn-danger').forEach(button => {
      button.addEventListener('click', (e) => {
        const target = e.target as HTMLElement;
        const pid = target.getAttribute('data-pid') || '';
        const port = target.getAttribute('data-port') || '';
        this.emitKillRequest(pid, port);
      });
    });
  }
}

customElements.define('port-monitor', PortMonitor);
