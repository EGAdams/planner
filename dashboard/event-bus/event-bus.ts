/**
 * EventBus Web Component
 * Responsibility: Manage application-wide event communication using SSE and custom events
 */

interface EventBusEvent extends CustomEvent {
  detail: {
    type: string;
    data: any;
  };
}

export class EventBus extends HTMLElement {
  private eventSource: EventSource | null = null;
  private apiUrl: string = 'http://localhost:3030';

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
  }

  connectedCallback() {
    const apiUrl = this.getAttribute('api-url');
    if (apiUrl) {
      this.apiUrl = apiUrl;
    }

    this.connectSSE();
    this.render();
  }

  disconnectedCallback() {
    if (this.eventSource) {
      this.eventSource.close();
    }
  }

  private connectSSE() {
    this.eventSource = new EventSource(`${this.apiUrl}/api/events`);

    this.eventSource.addEventListener('ports', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      this.dispatchBusEvent('ports-updated', data);
    });

    this.eventSource.addEventListener('servers', (e: MessageEvent) => {
      const data = JSON.parse(e.data);
      this.dispatchBusEvent('servers-updated', data);
    });

    this.eventSource.onerror = (error) => {
      console.error('SSE Error:', error);
      this.dispatchBusEvent('connection-error', { message: 'Lost connection to server' });

      // Attempt to reconnect after 5 seconds
      setTimeout(() => {
        if (this.eventSource) {
          this.eventSource.close();
        }
        this.connectSSE();
      }, 5000);
    };

    this.eventSource.onopen = () => {
      this.dispatchBusEvent('connection-open', { message: 'Connected to server' });
    };
  }

  private dispatchBusEvent(type: string, data: any) {
    const event = new CustomEvent('bus-event', {
      bubbles: true,
      composed: true,
      detail: { type, data }
    });
    this.dispatchEvent(event);
    window.dispatchEvent(event);
  }

  private render() {
    if (!this.shadowRoot) return;

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: none;
        }
      </style>
    `;
  }
}

customElements.define('event-bus', EventBus);
