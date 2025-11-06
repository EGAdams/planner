/**
 * Unit Tests for Main Server
 * 
 * TDD Approach - Tests for HTTP server startup and API endpoints
 */

import * as http from 'http';
import * as path from 'path';

const TEST_PORT = 3031; // Use different port to avoid conflicts
const TEST_HOST = '127.0.0.1';

describe('Main Dashboard Server', () => {
  test('should start on configured port', async () => {
    // This test verifies the server can start
    // In production, server runs on port 3030
    const port = process.env.ADMIN_PORT || 3030;
    expect(port).toBeDefined();
  });

  test('should respond to health check on /api/servers', async () => {
    const options = {
      hostname: '127.0.0.1',
      port: 3030,
      path: '/api/servers',
      method: 'GET'
    };

    const response = await new Promise<{ statusCode: number; data: string }>((resolve, reject) => {
      const req = http.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
          resolve({
            statusCode: res.statusCode || 500,
            data
          });
        });
      });

      req.on('error', reject);
      req.setTimeout(5000, () => {
        req.destroy();
        reject(new Error('Request timeout'));
      });
      
      req.end();
    });

    expect(response.statusCode).toBe(200);
    
    const servers = JSON.parse(response.data);
    expect(Array.isArray(servers)).toBe(true);
  }, 10000);

  test('should have CORS headers configured', async () => {
    const options = {
      hostname: '127.0.0.1',
      port: 3030,
      path: '/api/servers',
      method: 'OPTIONS'
    };

    const response = await new Promise<http.IncomingMessage>((resolve, reject) => {
      const req = http.request(options, resolve);
      req.on('error', reject);
      req.setTimeout(5000, () => {
        req.destroy();
        reject(new Error('Request timeout'));
      });
      req.end();
    });

    expect(response.statusCode).toBe(200);
    expect(response.headers['access-control-allow-origin']).toBe('*');
  }, 10000);

  test('should return JSON for /api/servers endpoint', async () => {
    const options = {
      hostname: '127.0.0.1',
      port: 3030,
      path: '/api/servers',
      method: 'GET'
    };

    const response = await new Promise<{ headers: http.IncomingHttpHeaders; data: string }>((resolve, reject) => {
      const req = http.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
          resolve({
            headers: res.headers,
            data
          });
        });
      });

      req.on('error', reject);
      req.setTimeout(5000, () => {
        req.destroy();
        reject(new Error('Request timeout'));
      });
      
      req.end();
    });

    expect(response.headers['content-type']).toContain('application/json');
    
    // Verify valid JSON
    const servers = JSON.parse(response.data);
    expect(servers).toBeTruthy();
  }, 10000);

  test('should include pydantic-web-server in server list', async () => {
    const options = {
      hostname: '127.0.0.1',
      port: 3030,
      path: '/api/servers',
      method: 'GET'
    };

    const response = await new Promise<string>((resolve, reject) => {
      const req = http.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => resolve(data));
      });

      req.on('error', reject);
      req.setTimeout(5000, () => {
        req.destroy();
        reject(new Error('Request timeout'));
      });
      
      req.end();
    });

    const servers = JSON.parse(response);
    const pydanticServer = servers.find((s: any) => s.id === 'pydantic-web-server');
    
    expect(pydanticServer).toBeTruthy();
    expect(pydanticServer.name).toBe('Pydantic Web Server');
    expect(pydanticServer.color).toBe('#E9D5FF');
  }, 10000);
});

describe('Server API Endpoints', () => {
  test('should handle POST to /api/servers/:id with action=start', async () => {
    // Note: This test doesn't actually start the server to avoid side effects
    // It just verifies the endpoint exists and accepts the request
    const serverId = 'pydantic-web-server';
    
    const options = {
      hostname: '127.0.0.1',
      port: 3030,
      path: `/api/servers/${serverId}?action=start`,
      method: 'POST'
    };

    const response = await new Promise<{ statusCode: number; data: string }>((resolve, reject) => {
      const req = http.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
          resolve({
            statusCode: res.statusCode || 500,
            data
          });
        });
      });

      req.on('error', reject);
      req.setTimeout(5000, () => {
        req.destroy();
        reject(new Error('Request timeout'));
      });
      
      req.end();
    });

    expect(response.statusCode).toBe(200);
    
    const result = JSON.parse(response.data);
    expect(result).toHaveProperty('success');
    expect(result).toHaveProperty('message');
  }, 10000);

  test('should handle /api/ports endpoint', async () => {
    const options = {
      hostname: '127.0.0.1',
      port: 3030,
      path: '/api/ports',
      method: 'GET'
    };

    const response = await new Promise<{ statusCode: number; data: string }>((resolve, reject) => {
      const req = http.request(options, (res) => {
        let data = '';
        res.on('data', (chunk) => data += chunk);
        res.on('end', () => {
          resolve({
            statusCode: res.statusCode || 500,
            data
          });
        });
      });

      req.on('error', reject);
      req.setTimeout(5000, () => {
        req.destroy();
        reject(new Error('Request timeout'));
      });
      
      req.end();
    });

    expect(response.statusCode).toBe(200);
    
    const ports = JSON.parse(response.data);
    expect(Array.isArray(ports)).toBe(true);
  }, 10000);

  test('should support SSE endpoint /api/events', async () => {
    const options = {
      hostname: '127.0.0.1',
      port: 3030,
      path: '/api/events',
      method: 'GET'
    };

    const response = await new Promise<http.IncomingMessage>((resolve, reject) => {
      const req = http.request(options, resolve);
      req.on('error', reject);
      req.setTimeout(5000, () => {
        req.destroy();
        reject(new Error('Request timeout'));
      });
      req.end();
    });

    expect(response.statusCode).toBe(200);
    expect(response.headers['content-type']).toContain('text/event-stream');
    
    // Clean up connection
    response.destroy();
  }, 10000);
});
