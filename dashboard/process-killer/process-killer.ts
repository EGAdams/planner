/**
 * ProcessKiller Web Component
 * Responsibility: Handle process termination requests and display status
 */

import { eventBus } from '../event-bus/event-bus.js';

export class ProcessKiller extends HTMLElement {
  private apiUrl: string = '';
  private isKilling: boolean = false;
  private lastMessage: string = '';
  private lastMessageType: 'success' | 'error' | '' = '';
  private unsubscribe: (() => void) | null = null;

  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
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
    // Subscribe to kill-process events from the EventBus
    this.unsubscribe = eventBus.on('kill-process', (data: { pid: string; port: string }) => {
      const { pid, port } = data;
      this.killProcess(pid, port);
    });
  }

  private async killProcess(pid: string, port: string) {
    if (this.isKilling) return;

    this.isKilling = true;
    this.lastMessage = `Killing process ${pid} on port ${port}...`;
    this.lastMessageType = '';
    this.render();

    try {
      const response = await fetch(`${this.apiUrl}/api/kill`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ pid, port })
      });

      // Check if response is ok (status 200-299)
      if (!response.ok) {
        const result = await response.json().catch(() => ({
          success: false,
          message: `HTTP ${response.status}: ${response.statusText}`
        }));
        this.lastMessage = `Failed: ${result.message || 'Unknown error'}`;
        this.lastMessageType = 'error';
      } else {
        const result = await response.json();

        if (result.success) {
          this.lastMessage = result.message || `Process ${pid} killed successfully`;
          this.lastMessageType = 'success';
        } else {
          this.lastMessage = `Failed: ${result.message || 'Unknown error'}`;
          this.lastMessageType = 'error';
        }
      }
    } catch (error: any) {
      // Network error or fetch failed
      console.error('Kill process error:', error);
      this.lastMessage = `Network Error: ${error.message}. Check that server is running on ${this.apiUrl}`;
      this.lastMessageType = 'error';
    }

    this.isKilling = false;
    this.render();

    // Clear message after 5 seconds
    setTimeout(() => {
      this.lastMessage = '';
      this.lastMessageType = '';
      this.render();
    }, 5000);
  }

  private render() {
    if (!this.shadowRoot) return;

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          position: fixed;
          bottom: 1rem;
          right: 1rem;
          z-index: 1000;
        }

        .notification {
          background: white;
          border-radius: 0.5rem;
          box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
          padding: 1rem 1.5rem;
          min-width: 300px;
          max-width: 400px;
          border-left: 4px solid #6b7280;
          animation: slideIn 0.3s ease-out;
        }

        .notification.success {
          border-left-color: #10b981;
        }

        .notification.error {
          border-left-color: #ef4444;
        }

        .notification.hidden {
          display: none;
        }

        .message {
          font-size: 0.875rem;
          color: #374151;
          margin: 0;
        }

        .message.success {
          color: #059669;
        }

        .message.error {
          color: #dc2626;
        }

        .spinner {
          display: inline-block;
          width: 14px;
          height: 14px;
          border: 2px solid #e5e7eb;
          border-top-color: #3b82f6;
          border-radius: 50%;
          animation: spin 0.8s linear infinite;
          margin-right: 0.5rem;
          vertical-align: middle;
        }

        @keyframes spin {
          to { transform: rotate(360deg); }
        }

        @keyframes slideIn {
          from {
            transform: translateX(100%);
            opacity: 0;
          }
          to {
            transform: translateX(0);
            opacity: 1;
          }
        }
      </style>

      <div class="notification ${this.lastMessage ? '' : 'hidden'} ${this.lastMessageType}">
        <p class="message ${this.lastMessageType}">
          ${this.isKilling ? '<span class="spinner"></span>' : ''}
          ${this.lastMessage}
        </p>
      </div>
    `;
  }
}

customElements.define('process-killer', ProcessKiller);
