/**
 * TDD RED PHASE: Receipt Table Category Picker Integration Tests
 *
 * These tests define the requirements for integrating the category-picker
 * component into each row of the receipt items table.
 *
 * EXPECTED: ALL TESTS WILL FAIL until implementation is complete (GREEN phase)
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { JSDOM } from 'jsdom';
import { readFileSync } from 'fs';
import { resolve } from 'path';

describe('Receipt Table Category Picker Integration - TDD RED Phase', () => {
  let dom;
  let document;
  let window;
  let receiptScanner;

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
    global.fetch = vi.fn();

    // Mock event-bus
    const eventBusMock = `
      export const emit = (event, data) => {
        window.dispatchEvent(new CustomEvent(event, { detail: data }));
      };
      export const on = (event, handler) => {
        window.addEventListener(event, (e) => handler(e.detail));
      };
    `;

    // Load category-picker component
    const categoryPickerJs = readFileSync(
      resolve(process.cwd(), 'js/category-picker.js'),
      'utf-8'
    );

    const modifiedCategoryPickerJs = categoryPickerJs.replace(
      /import\s+{[^}]+}\s+from\s+['"][^'"]+event-bus[^'"]+['"]/,
      eventBusMock
    );

    const categoryScript = document.createElement('script');
    categoryScript.type = 'module';
    categoryScript.textContent = modifiedCategoryPickerJs;
    document.body.appendChild(categoryScript);

    // Load receipt-scanner component
    const receiptScannerJs = readFileSync(
      resolve(process.cwd(), 'js/components/receipt-scanner.js'),
      'utf-8'
    );

    const modifiedReceiptScannerJs = receiptScannerJs.replace(
      /import\s+{[^}]+}\s+from\s+['"][^'"]+event-bus[^'"]+['"]/,
      eventBusMock
    );

    const receiptScript = document.createElement('script');
    receiptScript.type = 'module';
    receiptScript.textContent = modifiedReceiptScannerJs;
    document.body.appendChild(receiptScript);

    await new Promise(resolve => setTimeout(resolve, 300));

    // Mock fetch for categories API
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => [
        { id: '1', label: 'Food & Dining' },
        { id: '2', label: 'Transportation' },
        { id: '3', label: 'Shopping' },
      ],
    });

    receiptScanner = document.createElement('receipt-scanner');
    document.body.appendChild(receiptScanner);

    await new Promise(resolve => setTimeout(resolve, 100));
  });

  afterEach(() => {
    global.fetch.mockClear();
  });

  describe('Test 1: Category Column Added to Table Header', () => {
    it('should add a Category column to the receipt items table header', () => {
      const shadow = receiptScanner.shadowRoot;
      const table = shadow.querySelector('#receiptItemsTable');
      const headers = table.querySelectorAll('thead th');

      // EXPECTED TO FAIL: Category column not yet added
      expect(headers.length).toBe(5); // Item Name, Quantity, Price, Total, Category
      expect(headers[4].textContent).toBe('Category');
    });
  });

  describe('Test 2: Category Picker Rendered in Each Row', () => {
    it('should render a category-picker component in each table row', async () => {
      const shadow = receiptScanner.shadowRoot;

      // Populate with test data
      receiptScanner.parsedData = {
        party: { merchant_name: 'Test Store' },
        transaction_date: '2024-01-15',
        totals: { total_amount: 25.98, tax_amount: 2.00 },
        payment_method: 'CARD',
        meta: { raw_text: 'Test receipt' },
        items: [
          { description: 'Item 1', quantity: 1, unit_price: 10.99, line_total: 10.99 },
          { description: 'Item 2', quantity: 2, unit_price: 7.50, line_total: 15.00 },
        ],
      };

      receiptScanner._populateForm();
      await new Promise(resolve => setTimeout(resolve, 100));

      const rows = shadow.querySelectorAll('#receiptItemsBody tr');
      const firstRowCategoryPicker = rows[0].querySelector('category-picker');

      // EXPECTED TO FAIL: category-picker not yet rendered in rows
      expect(rows.length).toBe(2);
      expect(firstRowCategoryPicker).toBeTruthy();
      expect(firstRowCategoryPicker.tagName.toLowerCase()).toBe('category-picker');
    });
  });

  describe('Test 3: Category Picker Has Proper Attributes', () => {
    it('should configure category-picker with expense-id attribute', async () => {
      const shadow = receiptScanner.shadowRoot;

      receiptScanner.parsedData = {
        party: { merchant_name: 'Test Store' },
        transaction_date: '2024-01-15',
        totals: { total_amount: 10.99, tax_amount: 1.00 },
        payment_method: 'CARD',
        meta: { raw_text: 'Test' },
        items: [
          { description: 'Test Item', quantity: 1, unit_price: 10.99, line_total: 10.99 },
        ],
      };

      receiptScanner._populateForm();
      await new Promise(resolve => setTimeout(resolve, 100));

      const categoryPicker = shadow.querySelector('category-picker');

      // EXPECTED TO FAIL: attributes not yet configured
      expect(categoryPicker.hasAttribute('expense-id')).toBe(true);
      expect(categoryPicker.getAttribute('expense-id')).toMatch(/item-0/);
    });
  });

  describe('Test 4: Category Data Persisted to Receipt', () => {
    it('should store selected categories with receipt items', async () => {
      const shadow = receiptScanner.shadowRoot;

      receiptScanner.parsedData = {
        party: { merchant_name: 'Test Store' },
        transaction_date: '2024-01-15',
        totals: { total_amount: 10.99, tax_amount: 1.00 },
        payment_method: 'CARD',
        meta: { raw_text: 'Test' },
        items: [
          { description: 'Test Item', quantity: 1, unit_price: 10.99, line_total: 10.99 },
        ],
      };

      receiptScanner._populateForm();
      await new Promise(resolve => setTimeout(resolve, 100));

      const categoryPicker = shadow.querySelector('category-picker');

      // Simulate category selection
      categoryPicker.value = 'Food & Dining / Groceries';

      // Check if item has category stored
      // EXPECTED TO FAIL: category tracking not yet implemented
      expect(receiptScanner.parsedData.items[0].category).toBeDefined();
    });
  });

  describe('Test 5: Multiple Category Pickers Independent', () => {
    it('should maintain independent state for each category picker', async () => {
      const shadow = receiptScanner.shadowRoot;

      receiptScanner.parsedData = {
        party: { merchant_name: 'Test Store' },
        transaction_date: '2024-01-15',
        totals: { total_amount: 25.98, tax_amount: 2.00 },
        payment_method: 'CARD',
        meta: { raw_text: 'Test' },
        items: [
          { description: 'Item 1', quantity: 1, unit_price: 10.99, line_total: 10.99 },
          { description: 'Item 2', quantity: 2, unit_price: 7.50, line_total: 15.00 },
        ],
      };

      receiptScanner._populateForm();
      await new Promise(resolve => setTimeout(resolve, 100));

      const categoryPickers = shadow.querySelectorAll('category-picker');

      // EXPECTED TO FAIL: multiple pickers not yet implemented
      expect(categoryPickers.length).toBe(2);

      // Set different categories
      categoryPickers[0].value = 'Food & Dining';
      categoryPickers[1].value = 'Transportation';

      expect(categoryPickers[0].value).toBe('Food & Dining');
      expect(categoryPickers[1].value).toBe('Transportation');
    });
  });
});
