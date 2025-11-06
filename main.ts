/**
 * Main application entry point
 * Responsibility: Initialize the dashboard and handle global events
 */

import { eventBus } from './event-bus/event-bus.js';
import { sseManager } from './event-bus/sse-manager.js';

// Connection status indicator
const statusElement = document.getElementById('connection-status');
const statusText = document.getElementById('status-text');

// Subscribe to connection status updates
eventBus.on('connection-status', (data: { status: string; message: string }) => {
  if (data.status === 'connected') {
    showStatus('Connected', 'success');
  } else if (data.status === 'error') {
    showStatus(data.message, 'error');
  }
});

function showStatus(message: string, type: 'success' | 'error') {
  if (!statusElement || !statusText) return;

  statusText.textContent = message;
  statusElement.className = 'fixed top-4 right-4 px-4 py-2 rounded-md shadow-lg text-sm font-medium';

  if (type === 'success') {
    statusElement.classList.add('bg-green-500', 'text-white');
    statusElement.classList.remove('bg-red-500');
  } else {
    statusElement.classList.add('bg-red-500', 'text-white');
    statusElement.classList.remove('bg-green-500');
  }

  statusElement.classList.remove('hidden');

  // Auto-hide success messages after 3 seconds
  if (type === 'success') {
    setTimeout(() => {
      statusElement.classList.add('hidden');
    }, 3000);
  }
}

// Initialize SSE connection
sseManager.connect();

// Log app initialization
console.log('Admin Dashboard initialized');
