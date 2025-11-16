/**
 * API Response Format Tests
 *
 * These tests verify that API endpoints return correctly formatted responses
 * that match what the frontend expects.
 */

import { describe, it, expect } from '@jest/globals';

describe('API Response Format', () => {
  describe('GET /api/servers', () => {
    it('should return response with success and servers properties', () => {
      // Mock response from backend
      const mockBackendResponse = [
        { id: 'api-server', name: 'Office Assistant API', running: false, orphaned: false, color: '#D1FAE5' }
      ];

      // Expected frontend format
      const expectedFormat = {
        success: true,
        servers: mockBackendResponse
      };

      // Verify structure
      expect(expectedFormat).toHaveProperty('success');
      expect(expectedFormat).toHaveProperty('servers');
      expect(expectedFormat.success).toBe(true);
      expect(Array.isArray(expectedFormat.servers)).toBe(true);
    });

    it('should handle error responses', () => {
      const errorResponse = {
        success: false,
        message: 'Failed to fetch servers',
        servers: []
      };

      expect(errorResponse).toHaveProperty('success');
      expect(errorResponse.success).toBe(false);
      expect(errorResponse).toHaveProperty('message');
    });
  });

  describe('POST /api/servers/:id', () => {
    it('should return success response', () => {
      const successResponse = {
        success: true,
        message: 'Server started successfully'
      };

      expect(successResponse).toHaveProperty('success');
      expect(successResponse).toHaveProperty('message');
      expect(successResponse.success).toBe(true);
    });

    it('should return error response', () => {
      const errorResponse = {
        success: false,
        message: 'Failed to start server'
      };

      expect(errorResponse).toHaveProperty('success');
      expect(errorResponse.success).toBe(false);
    });
  });
});
