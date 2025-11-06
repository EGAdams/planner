/**
 * Playwright E2E Tests for Managed Servers Section
 * 
 * These tests validate the complete functionality of the "Managed Servers" section
 * of the admin dashboard, including:
 * - Server status display
 * - Start/Stop button functionality  
 * - Server process validation
 * - UI updates and real-time updates
 */

import { test, expect, Page } from '@playwright/test';

const DASHBOARD_URL = 'http://localhost:3030';
const API_URL = 'http://localhost:3030/api';

// Helper function to wait for server status to update
async function waitForServerStatus(page: Page, serverId: string, expectedRunning: boolean, timeout = 30000) {
  const startTime = Date.now();
  while (Date.now() - startTime < timeout) {
    const response = await page.request.get(API_URL + '/servers');
    const servers = await response.json();
    const server = servers.find((s: any) => s.id === serverId);
    
    if (server && server.running === expectedRunning) {
      return server;
    }
    
    await page.waitForTimeout(1000);
  }
  throw new Error('Timeout waiting for ' + serverId + ' to be ' + (expectedRunning ? 'running' : 'stopped'));
}

// Helper to check if a process is actually running
async function isProcessRunning(page: Page, serverId: string): Promise<boolean> {
  const response = await page.request.get(API_URL + '/servers');
  const servers = await response.json();
  const server = servers.find((s: any) => s.id === serverId);
  return server?.running || false;
}

// Helper to stop all servers before tests
async function stopAllServers(page: Page) {
  const response = await page.request.get(API_URL + '/servers');
  const servers = await response.json();
  
  for (const server of servers) {
    if (server.running && !server.orphaned) {
      await page.request.post(API_URL + '/servers/' + server.id + '?action=stop');
    }
  }
  
  // Wait a bit for all servers to stop
  await page.waitForTimeout(2000);
}

test.describe('Managed Servers Section - UI Display', () => {
  test('should display the "Managed Servers" section heading', async ({ page }) => {
    await page.goto(DASHBOARD_URL);
    
    // Find the server-list component in shadow DOM
    const serverList = page.locator('server-list');
    await expect(serverList).toBeVisible();
    
    // Check shadow DOM for the heading
    const heading = await serverList.evaluate((el) => {
      const shadow = el.shadowRoot;
      return shadow?.querySelector('h2')?.textContent;
    });
    
    expect(heading).toBe('Managed Servers');
  });

  test('should display all registered servers', async ({ page }) => {
    await page.goto(DASHBOARD_URL);
    
    // Get servers from API
    const response = await page.request.get(API_URL + '/servers');
    const servers = await response.json();
    
    expect(servers.length).toBeGreaterThan(0);
    
    // Check that each server is displayed
    for (const server of servers) {
      const serverCard = await page.locator('server-list').evaluate((el, serverId) => {
        const shadow = el.shadowRoot;
        const cards = shadow?.querySelectorAll('.server-card');
        if (!cards) return null;
        
        for (const card of cards) {
          const idElement = card.querySelector('.server-id');
          if (idElement?.textContent?.includes(serverId)) {
            return {
              name: card.querySelector('.server-name')?.textContent,
              id: idElement.textContent,
              hasController: !!card.querySelector('server-controller')
            };
          }
        }
        return null;
      }, server.id);
      
      expect(serverCard).toBeTruthy();
      expect(serverCard?.name).toContain(server.name);
      expect(serverCard?.hasController).toBe(true);
    }
  });

  test('should show correct status indicators (running vs stopped)', async ({ page }) => {
    await page.goto(DASHBOARD_URL);
    
    const response = await page.request.get(API_URL + '/servers');
    const servers = await response.json();
    
    for (const server of servers) {
      const statusClass = await page.locator('server-list').evaluate((el, serverId) => {
        const shadow = el.shadowRoot;
        const cards = shadow?.querySelectorAll('.server-card');
        if (!cards) return null;
        
        for (const card of cards) {
          const idElement = card.querySelector('.server-id');
          if (idElement?.textContent?.includes(serverId)) {
            const indicator = card.querySelector('.status-indicator');
            return indicator?.className || '';
          }
        }
        return null;
      }, server.id);
      
      if (server.running) {
        expect(statusClass).toContain('running');
      } else {
        expect(statusClass).toContain('stopped');
      }
    }
  });

  test('should display server colors correctly', async ({ page }) => {
    await page.goto(DASHBOARD_URL);
    
    const response = await page.request.get(API_URL + '/servers');
    const servers = await response.json();
    
    for (const server of servers) {
      if (server.orphaned) continue; // Skip orphaned servers (they have red background)
      
      const backgroundColor = await page.locator('server-list').evaluate((el, serverId) => {
        const shadow = el.shadowRoot;
        const cards = shadow?.querySelectorAll('.server-card');
        if (!cards) return null;
        
        for (const card of cards) {
          const idElement = card.querySelector('.server-id');
          if (idElement?.textContent?.includes(serverId)) {
            return (card as HTMLElement).style.backgroundColor;
          }
        }
        return null;
      }, server.id);
      
      expect(backgroundColor).toBeTruthy();
    }
  });
});

test.describe('Managed Servers Section - Button Functionality', () => {
  test.beforeEach(async ({ page }) => {
    // Ensure all servers are stopped before each test
    await page.goto(DASHBOARD_URL);
    await stopAllServers(page);
  });

  test('should start Pydantic Web Server when Start button is clicked', async ({ page }) => {
    await page.goto(DASHBOARD_URL);
    
    const serverId = 'pydantic-web-server';
    
    // Verify server is initially stopped
    const initialStatus = await isProcessRunning(page, serverId);
    expect(initialStatus).toBe(false);
    
    // Click the Start button
    await page.locator('server-list').evaluate((el, sid) => {
      const shadow = el.shadowRoot;
      const cards = shadow?.querySelectorAll('.server-card');
      if (!cards) return;
      
      for (const card of cards) {
        const idElement = card.querySelector('.server-id');
        if (idElement?.textContent?.includes(sid)) {
          const controller = card.querySelector('server-controller');
          const controllerShadow = controller?.shadowRoot;
          const button = controllerShadow?.querySelector('button');
          if (button instanceof HTMLElement) {
            button.click();
          }
        }
      }
    }, serverId);
    
    // Wait for server to start
    await waitForServerStatus(page, serverId, true);
    
    // Verify the server is actually running
    const finalStatus = await isProcessRunning(page, serverId);
    expect(finalStatus).toBe(true);
    
    // Verify the server is listening on port 8001
    await page.waitForTimeout(2000); // Give it time to bind to port
    const portsResponse = await page.request.get(API_URL + '/ports');
    const ports = await portsResponse.json();
    const port8001 = ports.find((p: any) => p.port === '8001');
    expect(port8001).toBeTruthy();
    
    // Clean up - stop the server
    await page.request.post(API_URL + '/servers/' + serverId + '?action=stop');
  });

  test('should stop a running server when Stop button is clicked', async ({ page }) => {
    await page.goto(DASHBOARD_URL);
    
    const serverId = 'pydantic-web-server';
    
    // First start the server via API
    await page.request.post(API_URL + '/servers/' + serverId + '?action=start');
    await waitForServerStatus(page, serverId, true);
    
    // Reload page to ensure UI is updated
    await page.reload();
    await page.waitForTimeout(1000);
    
    // Click the Stop button
    await page.locator('server-list').evaluate((el, sid) => {
      const shadow = el.shadowRoot;
      const cards = shadow?.querySelectorAll('.server-card');
      if (!cards) return;
      
      for (const card of cards) {
        const idElement = card.querySelector('.server-id');
        if (idElement?.textContent?.includes(sid)) {
          const controller = card.querySelector('server-controller');
          const controllerShadow = controller?.shadowRoot;
          const button = controllerShadow?.querySelector('button');
          if (button instanceof HTMLElement) {
            button.click();
          }
        }
      }
    }, serverId);
    
    // Wait for server to stop
    await waitForServerStatus(page, serverId, false);
    
    // Verify the server is actually stopped
    const finalStatus = await isProcessRunning(page, serverId);
    expect(finalStatus).toBe(false);
  });

  test('should update button text from Start to Stop after starting', async ({ page }) => {
    await page.goto(DASHBOARD_URL);
    
    const serverId = 'pydantic-web-server';
    
    // Click Start button
    await page.locator('server-list').evaluate((el, sid) => {
      const shadow = el.shadowRoot;
      const cards = shadow?.querySelectorAll('.server-card');
      if (!cards) return;
      
      for (const card of cards) {
        const idElement = card.querySelector('.server-id');
        if (idElement?.textContent?.includes(sid)) {
          const controller = card.querySelector('server-controller');
          const controllerShadow = controller?.shadowRoot;
          const button = controllerShadow?.querySelector('button');
          if (button instanceof HTMLElement) {
            button.click();
          }
        }
      }
    }, serverId);
    
    // Wait for server to start
    await waitForServerStatus(page, serverId, true);
    
    // Wait for UI to update (SSE updates every 5 seconds)
    await page.waitForTimeout(6000);
    
    // Check button text is now "Stop"
    const buttonText = await page.locator('server-list').evaluate((el, sid) => {
      const shadow = el.shadowRoot;
      const cards = shadow?.querySelectorAll('.server-card');
      if (!cards) return null;
      
      for (const card of cards) {
        const idElement = card.querySelector('.server-id');
        if (idElement?.textContent?.includes(sid)) {
          const controller = card.querySelector('server-controller');
          const controllerShadow = controller?.shadowRoot;
          const button = controllerShadow?.querySelector('button');
          return button?.textContent?.trim();
        }
      }
      return null;
    }, serverId);
    
    expect(buttonText).toBe('Stop');
    
    // Clean up
    await page.request.post(API_URL + '/servers/' + serverId + '?action=stop');
  });
});
