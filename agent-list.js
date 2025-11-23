/**
 * AgentList Web Component
 * Responsibility: Display list of managed agents
 */
import { eventBus } from '../event-bus/event-bus.js';
import './managed-agent.js';
export class AgentList extends HTMLElement {
    constructor() {
        super();
        this.agents = [];
        this.unsubscribe = null;
        this.attachShadow({ mode: 'open' });
    }
    connectedCallback() {
        this.setupEventListeners();
        this.render();
    }
    disconnectedCallback() {
        if (this.unsubscribe) {
            this.unsubscribe();
            this.unsubscribe = null;
        }
    }
    setupEventListeners() {
        this.unsubscribe = eventBus.on('servers-updated', (data) => {
            this.agents = this.normalizeServerData(data).filter(s => s.type === 'agent');
            this.render();
        });
    }
    normalizeServerData(data) {
        if (Array.isArray(data)) {
            return data;
        }
        if (data && typeof data === 'object') {
            return Object.values(data);
        }
        return [];
    }
    render() {
        if (!this.shadowRoot)
            return;
        this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          margin-bottom: 2rem;
        }

        h2 {
          font-size: 1.5rem;
          font-weight: 700;
          margin: 0 0 1.5rem 0;
          color: #1f2937;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .agent-icon {
          font-size: 1.5rem;
        }

        .empty-state {
          text-align: center;
          padding: 3rem;
          background: white;
          border-radius: 0.5rem;
          border: 1px dashed #e5e7eb;
          color: #6b7280;
        }
      </style>

      <h2>
        <span class="agent-icon">🤖</span>
        Managed Agents
      </h2>

      ${this.agents.length === 0 ? `
        <div class="empty-state">
          No agents configured. Add agents with type: 'agent' to the SERVER_REGISTRY.
        </div>
      ` : `
        <div class="agent-list">
          ${this.agents.map(agent => `
            <managed-agent
              agent-id="${agent.id}"
              name="${agent.name}"
              description="Managed AI Agent"
              running="${agent.running}"
            ></managed-agent>
          `).join('')}
        </div>
      `}
    `;
    }
}
customElements.define('agent-list', AgentList);
//# sourceMappingURL=agent-list.js.map