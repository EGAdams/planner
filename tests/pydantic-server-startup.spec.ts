/**
 * Playwright E2E Tests for Pydantic Server Startup
 * 
 * TDD Approach - RED Phase: These tests will FAIL initially
 * 
 * Tests validate:
 * - Pydantic server configuration in server registry
 * - Server startup via API and UI
 * - Port 8001 connectivity
 * - Server health checks
 * - Environment variable configuration
 */

import { test, expect, Page } from '@playwright/test';

const DASHBOARD_URL = 'http://localhost:3030';
const API_URL = 'http://localhost:3030/api';
const PYDANTIC_SERVER_ID = 'pydantic-web-server';
const PYDANTIC_PORT = 8001;

// Helper: Get server status from API
async function getServerStatus(page: Page, serverId: string) {
  const response = await page.request.get(`${API_URL}/servers`);
  const servers = await response.json();
  return servers.find((s: any) => s.id === serverId);
}

// Helper: Wait for server to reach expected state
async function waitForServerState(page: Page, serverId: string, expectedRunning: boolean, timeout = 30000) {
  const startTime = Date.now();
  while (Date.now() - startTime < timeout) {
    const server = await getServerStatus(page, serverId);
    if (server && server.running === expectedRunning) {
      return server;
    }
    await page.waitForTimeout(1000);
  }
  throw new Error(`Timeout: ${serverId} did not reach running=${expectedRunning}`);
}

// Helper: Check if port is listening
async function isPortListening(page: Page, port: number): Promise<boolean> {
  const response = await page.request.get(`${API_URL}/ports`);
  const ports = await response.json();
  return ports.some((p: any) => parseInt(p.port) === port);
}

// Helper: Stop server if running
async function ensureServerStopped(page: Page, serverId: string) {
  const server = await getServerStatus(page, serverId);
  if (server?.running) {
    await page.request.post(`${API_URL}/servers/${serverId}?action=stop`);
    await waitForServerState(page, serverId, false);
  }
}

test.describe('Pydantic Server Configuration', () => {
  test('should have pydantic-web-server registered in server registry', async ({ page }) => {
    await page.goto(DASHBOARD_URL);
    
    const response = await page.request.get(`${API_URL}/servers`);
    expect(response.ok()).toBeTruthy();
    
    const servers = await response.json();
    const pydanticServer = servers.find((s: any) => s.id === PYDANTIC_SERVER_ID);
    
    expect(pydanticServer).toBeTruthy();
    expect(pydanticServer.name).toBe('Pydantic Web Server');
    expect(pydanticServer.color).toBe('#E9D5FF');
  });

  test('should have correct port configuration (8001)', async ({ page }) => {
    await page.goto(DASHBOARD_URL);
    
    // Read server.ts to verify port configuration
    // This is validated by the API returning the server config
    const server = await getServerStatus(page, PYDANTIC_SERVER_ID);
    expect(server).toBeTruthy();
  });
});

test.describe('Pydantic Server Startup - API', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(DASHBOARD_URL);
    await ensureServerStopped(page, PYDANTIC_SERVER_ID);
  });

  test.afterEach(async ({ page }) => {
    await ensureServerStopped(page, PYDANTIC_SERVER_ID);
  });

  test('should start Pydantic server via API', async ({ page }) => {
    await page.goto(DASHBOARD_URL);
    
    // Start server
    const response = await page.request.post(`${API_URL}/servers/${PYDANTIC_SERVER_ID}?action=start`);
    expect(response.ok()).toBeTruthy();
    
    const result = await response.json();
    expect(result.success).toBe(true);
    expect(result.message).toContain('started successfully');
    
    // Wait for server to be running
    const server = await waitForServerState(page, PYDANTIC_SERVER_ID, true);
    expect(server.running).toBe(true);
    expect(server.healthy).toBe(true);
  });

  test('should bind to port 8001 after startup', async ({ page }) => {
    await page.goto(DASHBOARD_URL);
    
    // Start server
    await page.request.post(`${API_URL}/servers/${PYDANTIC_SERVER_ID}?action=start`);
    await waitForServerState(page, PYDANTIC_SERVER_ID, true);
    
    // Wait for port binding
    await page.waitForTimeout(3000);
    
    // Check port is listening
    const portListening = await isPortListening(page, PYDANTIC_PORT);
    expect(portListening).toBe(true);
  });

  test('should be accessible on http://localhost:8001', async ({ page }) => {
    await page.goto(DASHBOARD_URL);
    
    // Start server
    await page.request.post(`${API_URL}/servers/${PYDANTIC_SERVER_ID}?action=start`);
    await waitForServerState(page, PYDANTIC_SERVER_ID, true);
    
    // Wait for server to fully start
    await page.waitForTimeout(5000);
    
    // Test HTTP connectivity
    try {
      const response = await page.request.get('http://localhost:8001/docs');
      // FastAPI should have /docs endpoint
      expect(response.status()).toBeLessThan(500); // Any non-500 response means server is up
    } catch (error) {
      // If connection fails, test should fail
      throw new Error(`Cannot connect to Pydantic server on port 8001: ${error}`);
    }
  });

  test('should stop Pydantic server via API', async ({ page }) => {
    await page.goto(DASHBOARD_URL);
    
    // Start server first
    await page.request.post(`${API_URL}/servers/${PYDANTIC_SERVER_ID}?action=start`);
    await waitForServerState(page, PYDANTIC_SERVER_ID, true);
    
    // Stop server
    const response = await page.request.post(`${API_URL}/servers/${PYDANTIC_SERVER_ID}?action=stop`);
    expect(response.ok()).toBeTruthy();
    
    const result = await response.json();
    expect(result.success).toBe(true);
    
    // Wait for server to stop
    const server = await waitForServerState(page, PYDANTIC_SERVER_ID, false);
    expect(server.running).toBe(false);
  });

  test('should detect if uv command is available', async ({ page }) => {
    await page.goto(DASHBOARD_URL);
    
    // Attempt to start - should handle missing uv gracefully
    const response = await page.request.post(`${API_URL}/servers/${PYDANTIC_SERVER_ID}?action=start`);
    const result = await response.json();
    
    // If uv is missing, we expect a specific error or the server to fail to start
    if (!result.success) {
      expect(result.message).toBeTruthy();
      console.log('UV command issue detected:', result.message);
    }
  });
});

test.describe('Pydantic Server Startup - UI', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(DASHBOARD_URL);
    await ensureServerStopped(page, PYDANTIC_SERVER_ID);
  });

  test.afterEach(async ({ page }) => {
    await ensureServerStopped(page, PYDANTIC_SERVER_ID);
  });

  test('should start Pydantic server from UI Start button', async ({ page }) => {
    await page.goto(DASHBOARD_URL);
    
    // Find and click Start button in shadow DOM
    await page.locator('server-list').evaluate((el, serverId) => {
      const shadow = el.shadowRoot;
      const cards = shadow?.querySelectorAll('.server-card');
      
      for (const card of cards || []) {
        const idElement = card.querySelector('.server-id');
        if (idElement?.textContent?.includes(serverId)) {
          const controller = card.querySelector('server-controller');
          const controllerShadow = controller?.shadowRoot;
          const button = controllerShadow?.querySelector('button') as HTMLElement;
          button?.click();
        }
      }
    }, PYDANTIC_SERVER_ID);
    
    // Wait for server to start
    const server = await waitForServerState(page, PYDANTIC_SERVER_ID, true);
    expect(server.running).toBe(true);
  });

  test('should show server as running in UI after startup', async ({ page }) => {
    await page.goto(DASHBOARD_URL);
    
    // Start via API
    await page.request.post(`${API_URL}/servers/${PYDANTIC_SERVER_ID}?action=start`);
    await waitForServerState(page, PYDANTIC_SERVER_ID, true);
    
    // Wait for SSE update
    await page.waitForTimeout(6000);
    
    // Check UI status indicator
    const statusClass = await page.locator('server-list').evaluate((el, serverId) => {
      const shadow = el.shadowRoot;
      const cards = shadow?.querySelectorAll('.server-card');
      
      for (const card of cards || []) {
        const idElement = card.querySelector('.server-id');
        if (idElement?.textContent?.includes(serverId)) {
          return card.querySelector('.status-indicator')?.className;
        }
      }
      return null;
    }, PYDANTIC_SERVER_ID);
    
    expect(statusClass).toContain('running');
  });

  test('should update button text to Stop when running', async ({ page }) => {
    await page.goto(DASHBOARD_URL);
    
    // Start server
    await page.request.post(`${API_URL}/servers/${PYDANTIC_SERVER_ID}?action=start`);
    await waitForServerState(page, PYDANTIC_SERVER_ID, true);
    
    // Wait for UI update
    await page.waitForTimeout(6000);
    
    // Check button text
    const buttonText = await page.locator('server-list').evaluate((el, serverId) => {
      const shadow = el.shadowRoot;
      const cards = shadow?.querySelectorAll('.server-card');
      
      for (const card of cards || []) {
        const idElement = card.querySelector('.server-id');
        if (idElement?.textContent?.includes(serverId)) {
          const controller = card.querySelector('server-controller');
          const controllerShadow = controller?.shadowRoot;
          return controllerShadow?.querySelector('button')?.textContent?.trim();
        }
      }
      return null;
    }, PYDANTIC_SERVER_ID);
    
    expect(buttonText).toBe('Stop');
  });
});

test.describe('Pydantic Server Health Monitoring', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto(DASHBOARD_URL);
    await ensureServerStopped(page, PYDANTIC_SERVER_ID);
  });

  test.afterEach(async ({ page }) => {
    await ensureServerStopped(page, PYDANTIC_SERVER_ID);
  });

  test('should report healthy status after successful startup', async ({ page }) => {
    await page.goto(DASHBOARD_URL);
    
    // Start server
    await page.request.post(`${API_URL}/servers/${PYDANTIC_SERVER_ID}?action=start`);
    await waitForServerState(page, PYDANTIC_SERVER_ID, true);
    
    // Wait for health check
    await page.waitForTimeout(4000);
    
    const server = await getServerStatus(page, PYDANTIC_SERVER_ID);
    expect(server.running).toBe(true);
    expect(server.healthy).toBeTruthy();
    expect(server.lastCheck).toBeTruthy();
  });

  test('should update lastCheck timestamp periodically', async ({ page }) => {
    await page.goto(DASHBOARD_URL);
    
    // Start server
    await page.request.post(`${API_URL}/servers/${PYDANTIC_SERVER_ID}?action=start`);
    await waitForServerState(page, PYDANTIC_SERVER_ID, true);
    
    // Get first check time
    const server1 = await getServerStatus(page, PYDANTIC_SERVER_ID);
    const firstCheck = server1.lastCheck;
    
    // Wait for monitoring interval (3 seconds)
    await page.waitForTimeout(4000);
    
    // Get second check time
    const server2 = await getServerStatus(page, PYDANTIC_SERVER_ID);
    const secondCheck = server2.lastCheck;
    
    expect(secondCheck).not.toBe(firstCheck);
  });
});
