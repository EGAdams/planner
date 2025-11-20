// Test Setup - Global configuration for Vitest tests
import { expect, beforeEach, afterEach, vi } from 'vitest';

// Global test utilities
global.expect = expect;
global.vi = vi;

// Setup DOM environment before each test
beforeEach(() => {
  // Clear document body
  document.body.innerHTML = '';

  // Reset any mocked functions
  vi.clearAllMocks();

  // Setup console spies to reduce noise in tests
  vi.spyOn(console, 'log').mockImplementation(() => {});
  vi.spyOn(console, 'error').mockImplementation(() => {});
  vi.spyOn(console, 'warn').mockImplementation(() => {});
});

// Cleanup after each test
afterEach(() => {
  // Restore all mocks
  vi.restoreAllMocks();

  // Clear timers
  vi.clearAllTimers();
});

// Mock window.matchMedia (needed for responsive tests)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

// Mock localStorage
const localStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.localStorage = localStorageMock;

// Mock sessionStorage
const sessionStorageMock = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
global.sessionStorage = sessionStorageMock;
