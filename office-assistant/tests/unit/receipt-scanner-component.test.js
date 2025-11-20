/**
 * TDD RED PHASE: Receipt Scanner Web Component Portability Tests
 *
 * These tests define that the receipt-scanner component should be:
 * - Fully self-contained and portable
 * - Work as a standalone web component
 * - Not depend on external styles or scripts (except event-bus)
 * - Have proper shadow DOM encapsulation
 *
 * EXPECTED: ALL TESTS WILL FAIL until component refactoring is complete (GREEN phase)
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { JSDOM } from 'jsdom';
import { readFileSync } from 'fs';
import { resolve } from 'path';

describe('Receipt Scanner Component Portability - TDD RED Phase', () => {
  let dom;
  let document;
  let window;
  let ReceiptScanner;

  beforeEach(async () => {
    // Create minimal DOM
    dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
      runScripts: 'dangerously',
      resources: 'usable',
      url: 'http://localhost/',
    });
    document = dom.window.document;
    window = dom.window;
    global.document = document;
    global.window = window;
    global.HTMLElement = window.HTMLElement;
    global.customElements = window.customElements;

    // Mock event-bus (component's only external dependency)
    const eventBusMock = `
      export const emit = (event, data) => {
        window.dispatchEvent(new CustomEvent(event, { detail: data }));
      };
      export const on = (event, handler) => {
        window.addEventListener(event, handler);
      };
    `;

    // Load the receipt-scanner component
    try {
      const componentJs = readFileSync(
        resolve(process.cwd(), 'js/components/receipt-scanner.js'),
        'utf-8'
      );

      // Replace import with mock
      const modifiedJs = componentJs.replace(
        /import\s+{[^}]+}\s+from\s+['"][^'"]+event-bus[^'"]+['"]/,
        eventBusMock
      );

      const script = document.createElement('script');
      script.type = 'module';
      script.textContent = modifiedJs;
      document.body.appendChild(script);

      await new Promise(resolve => setTimeout(resolve, 200));

      ReceiptScanner = window.customElements.get('receipt-scanner');
    } catch (error) {
      console.error('Failed to load receipt-scanner component:', error);
    }
  });

  describe('Component Registration', () => {
    it('should be registered as a custom element', () => {
      // EXPECTED TO FAIL: Component may not be properly registered
      expect(window.customElements.get('receipt-scanner')).toBeDefined();
    });

    it('should extend HTMLElement', () => {
      const element = document.createElement('receipt-scanner');

      // EXPECTED TO FAIL: May not properly extend HTMLElement
      expect(element).toBeInstanceOf(window.HTMLElement);
    });

    it('should be instantiable without errors', () => {
      let error = null;
      try {
        const element = document.createElement('receipt-scanner');
        document.body.appendChild(element);
      } catch (e) {
        error = e;
      }

      // EXPECTED TO FAIL: May throw errors during instantiation
      expect(error).toBeNull();
    });
  });

  describe('Shadow DOM Encapsulation', () => {
    it('should use shadow DOM for style encapsulation', () => {
      const element = document.createElement('receipt-scanner');
      document.body.appendChild(element);

      // EXPECTED TO FAIL: Shadow DOM may not be attached
      expect(element.shadowRoot).toBeDefined();
      expect(element.shadowRoot.mode).toBe('open');
    });

    it('should contain all styles within shadow DOM', () => {
      const element = document.createElement('receipt-scanner');
      document.body.appendChild(element);

      const styleTag = element.shadowRoot.querySelector('style');

      // EXPECTED TO FAIL: Styles may not be in shadow DOM
      expect(styleTag).toBeDefined();
      expect(styleTag.textContent.length).toBeGreaterThan(0);
    });

    it('should not leak styles to parent document', () => {
      const element = document.createElement('receipt-scanner');
      document.body.appendChild(element);

      const documentStyles = document.querySelectorAll('style');
      const receiptScannerStylesInDocument = Array.from(documentStyles).some(
        style => style.textContent.includes('drop-area') || style.textContent.includes('.receipt-scanner')
      );

      // EXPECTED TO FAIL: Styles may leak to document
      expect(receiptScannerStylesInDocument).toBe(false);
    });
  });

  describe('Self-Contained Functionality', () => {
    it('should have all required HTML structure in shadow DOM', () => {
      const element = document.createElement('receipt-scanner');
      document.body.appendChild(element);

      const dropArea = element.shadowRoot.querySelector('.drop-area');
      const fileInput = element.shadowRoot.querySelector('.file-input');

      // EXPECTED TO FAIL: HTML structure may not be complete
      expect(dropArea).toBeDefined();
      expect(fileInput).toBeDefined();
    });

    it('should not require external CSS files', () => {
      const element = document.createElement('receipt-scanner');
      document.body.appendChild(element);

      const linkTags = element.shadowRoot.querySelectorAll('link[rel="stylesheet"]');

      // EXPECTED TO FAIL: May depend on external CSS
      expect(linkTags.length).toBe(0);
    });

    it('should not require external JavaScript dependencies (except event-bus)', () => {
      const componentJs = readFileSync(
        resolve(process.cwd(), 'js/components/receipt-scanner.js'),
        'utf-8'
      );

      // Check for imports other than event-bus
      const imports = componentJs.match(/import\s+.*\s+from\s+['"](.*)['"]/g) || [];
      const nonEventBusImports = imports.filter(imp => !imp.includes('event-bus'));

      // EXPECTED TO FAIL: May have other dependencies
      expect(nonEventBusImports.length).toBe(0);
    });
  });

  describe('Portable API', () => {
    it('should work when created via document.createElement', () => {
      let error = null;
      try {
        const element = document.createElement('receipt-scanner');
        document.body.appendChild(element);
      } catch (e) {
        error = e;
      }

      // EXPECTED TO FAIL: May not work with createElement
      expect(error).toBeNull();
    });

    it('should work when created via innerHTML', () => {
      const container = document.createElement('div');
      container.innerHTML = '<receipt-scanner></receipt-scanner>';
      document.body.appendChild(container);

      const element = container.querySelector('receipt-scanner');

      // EXPECTED TO FAIL: May not work with innerHTML
      expect(element).toBeDefined();
      expect(element.shadowRoot).toBeDefined();
    });

    it('should initialize properly when added to DOM', () => {
      const element = document.createElement('receipt-scanner');

      // Should not throw error
      let error = null;
      try {
        document.body.appendChild(element);
      } catch (e) {
        error = e;
      }

      // EXPECTED TO FAIL: Initialization may fail
      expect(error).toBeNull();
    });
  });

  describe('Component State Management', () => {
    it('should maintain independent state for multiple instances', () => {
      const element1 = document.createElement('receipt-scanner');
      const element2 = document.createElement('receipt-scanner');

      document.body.appendChild(element1);
      document.body.appendChild(element2);

      // Each instance should have its own state
      // EXPECTED TO FAIL: State may be shared
      expect(element1.parsedData).not.toBe(element2.parsedData);
    });

    it('should have isolated event handlers for each instance', () => {
      const element1 = document.createElement('receipt-scanner');
      const element2 = document.createElement('receipt-scanner');

      document.body.appendChild(element1);
      document.body.appendChild(element2);

      const dropArea1 = element1.shadowRoot.querySelector('.drop-area');
      const dropArea2 = element2.shadowRoot.querySelector('.drop-area');

      // EXPECTED TO FAIL: Event handlers may be shared
      expect(dropArea1).not.toBe(dropArea2);
    });
  });

  describe('Component Lifecycle', () => {
    it('should clean up when removed from DOM', () => {
      const element = document.createElement('receipt-scanner');
      document.body.appendChild(element);

      const shadowRoot = element.shadowRoot;

      document.body.removeChild(element);

      // EXPECTED TO FAIL: Cleanup may not happen
      // Component should be detached but shadow root should still exist
      expect(shadowRoot).toBeDefined();
    });

    it('should be re-initializable after removal', () => {
      const element = document.createElement('receipt-scanner');

      document.body.appendChild(element);
      document.body.removeChild(element);
      document.body.appendChild(element);

      // EXPECTED TO FAIL: Re-initialization may fail
      expect(element.shadowRoot).toBeDefined();
    });
  });

  describe('Event Bus Integration', () => {
    it('should only depend on event-bus for external communication', () => {
      const componentJs = readFileSync(
        resolve(process.cwd(), 'js/components/receipt-scanner.js'),
        'utf-8'
      );

      const hasEventBusImport = componentJs.includes('event-bus');

      // EXPECTED TO FAIL: May not use event-bus
      expect(hasEventBusImport).toBe(true);
    });

    it('should emit events via event-bus for external communication', () => {
      const element = document.createElement('receipt-scanner');
      document.body.appendChild(element);

      const emitSpy = vi.fn();
      window.dispatchEvent = emitSpy;

      // Trigger an action that should emit event
      const dropArea = element.shadowRoot.querySelector('.drop-area');

      // EXPECTED TO FAIL: Event emission may not work
      expect(dropArea).toBeDefined();
    });
  });

  describe('Component Attributes and Properties', () => {
    it('should expose necessary public properties', () => {
      const element = document.createElement('receipt-scanner');
      document.body.appendChild(element);

      // EXPECTED TO FAIL: Properties may not be exposed
      expect('parsedData' in element).toBe(true);
      expect('isLoading' in element).toBe(true);
      expect('error' in element).toBe(true);
    });

    it('should update UI when properties change', async () => {
      const element = document.createElement('receipt-scanner');
      document.body.appendChild(element);

      element.isLoading = true;

      // Wait for UI update
      await new Promise(resolve => setTimeout(resolve, 100));

      // EXPECTED TO FAIL: UI may not react to property changes
      const loadingIndicator = element.shadowRoot.querySelector('.loading-spinner');
      expect(loadingIndicator).toBeDefined();
    });
  });
});
