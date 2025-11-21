/**
 * TDD RED PHASE: Scan Bank PDF Section Integration Tests
 *
 * These tests define how the new "Scan Bank PDF" tab should work:
 * - Navigation button exists and loads the section
 * - Section renders rows with description, amount, and category-picker
 * - Calculated total is shown and compared against statement total
 * - Category pickers remain disabled until totals balance
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { JSDOM } from 'jsdom';
import { readFileSync } from 'fs';
import { resolve } from 'path';
import { pathToFileURL } from 'url';

const wait = (ms = 50) => new Promise(resolve => setTimeout(resolve, ms));

describe('Scan Bank PDF Section - TDD RED Phase', () => {
  let document;
  let window;
  let OfficeAssistant;
  let appInstance;

  beforeEach(async () => {
    const html = readFileSync(resolve(process.cwd(), 'index.html'), 'utf-8');
    const dom = new JSDOM(html, {
      runScripts: 'dangerously',
      resources: 'usable',
      url: 'http://localhost/'
    });
    document = dom.window.document;
    window = dom.window;
    global.document = document;
    global.window = window;
    global.customElements = window.customElements;
    global.HTMLElement = window.HTMLElement;
    global.Node = window.Node;
    global.MutationObserver = window.MutationObserver;
    global.Event = window.Event;
    global.FormData = window.FormData;
    global.AbortController = window.AbortController;
    global.FileReader = window.FileReader;
    global.navigator = window.navigator;
    global.fetch = window.fetch;

    const categoryPickerUrl = `${pathToFileURL(resolve(process.cwd(), 'js/category-picker.js')).href}?v=${Date.now()}`;
    const bankScannerUrl = `${pathToFileURL(resolve(process.cwd(), 'js/components/bank-pdf-scanner.js')).href}?v=${Date.now()}`;

    // Ensure the bank PDF scanner custom element is registered in the test DOM
    await import(categoryPickerUrl);
    await import(bankScannerUrl);
    await import(resolve(process.cwd(), 'js/app.js'));

    // Cache constructors so we can re-register on new windows between tests
    const cachedCategory = global.CategoryPickerCtor || customElements.get('category-picker');
    if (cachedCategory && !customElements.get('category-picker')) {
      customElements.define('category-picker', cachedCategory);
    }
    if (cachedCategory) {
      global.CategoryPickerCtor = cachedCategory;
    }

    const cachedBankScanner = global.BankPdfScannerCtor || customElements.get('bank-pdf-scanner');
    if (cachedBankScanner && !customElements.get('bank-pdf-scanner')) {
      customElements.define('bank-pdf-scanner', cachedBankScanner);
    }
    if (cachedBankScanner) {
      global.BankPdfScannerCtor = cachedBankScanner;
    }

    if (!customElements.get('bank-pdf-scanner')) {
      throw new Error('bank-pdf-scanner custom element failed to register');
    }

    await wait(100);
    OfficeAssistant = window.OfficeAssistant;

    if (OfficeAssistant) {
      // Boot the SPA so nav events are wired
      appInstance = new OfficeAssistant();
      if (appInstance.loadTimeout) {
        clearTimeout(appInstance.loadTimeout);
        appInstance.loadTimeout = null;
      }
      await wait(100);
    }
  });

  it('shows Scan Bank PDF nav button and loads section when clicked', async () => {
    const button = document.querySelector('[data-section="scan-bank-pdf"]');

    expect(button).toBeTruthy();

    appInstance.handleNavigation(button);
    expect(appInstance.currentSection).toBe('scan-bank-pdf');
    const intermediateHtml = document.getElementById('content-area').innerHTML;
    expect(intermediateHtml).toContain('Loading');
    appInstance.loadScanBankPdfSection();
    const contentArea = document.getElementById('content-area');
    const bankScanner = contentArea.querySelector('bank-pdf-scanner');

    expect(bankScanner).toBeTruthy();
  });

  it('renders rows with description, amount, category picker and totals', async () => {
    const button = document.querySelector('[data-section="scan-bank-pdf"]');
    expect(button).toBeTruthy();

    appInstance.handleNavigation(button);
    await wait(400);

    let bankScanner = document.querySelector('bank-pdf-scanner');
    const BankCtor = global.BankPdfScannerCtor || customElements.get('bank-pdf-scanner');
    if (!BankCtor) {
      throw new Error('BankPdfScanner constructor missing');
    }
    if (!bankScanner || bankScanner.constructor.name !== 'BankPdfScanner') {
      bankScanner?.remove();
      bankScanner = new BankCtor();
      document.getElementById('content-area').appendChild(bankScanner);
    }
    expect(bankScanner).toBeTruthy();
    expect(bankScanner.constructor.name).toBe('BankPdfScanner');
    const shadow = bankScanner.shadowRoot;
    expect(shadow).toBeTruthy();

    const row = shadow.querySelector('.transaction-row');
    expect(row).toBeTruthy();

    const description = shadow.querySelector('input[data-testid="description"]');
    const amount = shadow.querySelector('input[data-testid="amount"]');
    const categoryPicker = shadow.querySelector('category-picker');
    const calculatedTotal = shadow.querySelector('[data-testid="calculated-total"]');
    const statementTotal = shadow.querySelector('input[data-testid="statement-total"]');

    expect(description).toBeTruthy();
    expect(amount).toBeTruthy();
    expect(categoryPicker).toBeTruthy();
    expect(calculatedTotal).toBeTruthy();
    expect(statementTotal).toBeTruthy();
  });

  it('keeps category pickers disabled until totals balance', async () => {
    const button = document.querySelector('[data-section="scan-bank-pdf"]');
    expect(button).toBeTruthy();

    appInstance.handleNavigation(button);
    await wait(400);

    let bankScanner = document.querySelector('bank-pdf-scanner');
    const BankCtor = global.BankPdfScannerCtor || customElements.get('bank-pdf-scanner');
    if (!BankCtor) {
      throw new Error('BankPdfScanner constructor missing');
    }
    if (!bankScanner || bankScanner.constructor.name !== 'BankPdfScanner') {
      bankScanner?.remove();
      bankScanner = new BankCtor();
      document.getElementById('content-area').appendChild(bankScanner);
    }
    expect(bankScanner).toBeTruthy();
    const shadow = bankScanner.shadowRoot;
    expect(shadow).toBeTruthy();

    const categoryPicker = shadow.querySelector('category-picker');
    expect(categoryPicker).toBeTruthy();
    const calculatedTotal = shadow.querySelector('[data-testid="calculated-total"]');
    const statementTotal = shadow.querySelector('input[data-testid="statement-total"]');
    const calcValue = parseFloat((calculatedTotal?.textContent || '0').replace(/[^0-9.-]/g, ''));

    // force mismatch should lock
    statementTotal.value = String(calcValue + 1);
    statementTotal.dispatchEvent(new window.Event('input', { bubbles: true }));
    await wait(100);

    expect(categoryPicker.hasAttribute('disabled')).toBe(true);

    // match totals should unlock
    statementTotal.value = String(calcValue);
    statementTotal.dispatchEvent(new window.Event('input', { bubbles: true }));
    await wait(100);

    expect(categoryPicker.hasAttribute('disabled')).toBe(false);
  });

  it('auto-fills statement total with calculated total when backend omits it', async () => {
    const button = document.querySelector('[data-section="scan-bank-pdf"]');
    expect(button).toBeTruthy();

    appInstance.handleNavigation(button);
    await wait(400);

    let bankScanner = document.querySelector('bank-pdf-scanner');
    const BankCtor = global.BankPdfScannerCtor || customElements.get('bank-pdf-scanner');
    if (!BankCtor) {
      throw new Error('BankPdfScanner constructor missing');
    }
    if (!bankScanner || bankScanner.constructor.name !== 'BankPdfScanner') {
      bankScanner?.remove();
      bankScanner = new BankCtor();
      document.getElementById('content-area').appendChild(bankScanner);
    }

    const mockResponse = {
      ok: true,
      json: async () => ({
        transactions: [
          { description: 'Deposit', amount: 100 },
          { description: 'Purchase', amount: -40 }
        ],
        totals: { sum: 60 } // statement_total missing on purpose
      }),
      text: async () => ''
    };
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(mockResponse);

    const file = new window.File(['dummy'], 'dummy.pdf', { type: 'application/pdf' });
    await bankScanner._handleFile(file);

    expect(bankScanner.calculatedTotal).toBeCloseTo(60);
    expect(bankScanner.statementTotalInput.value).toBe('60.00');
    expect(bankScanner.categoryPickers.every(p => !p.hasAttribute('disabled'))).toBe(true);

    fetchSpy.mockRestore();
  });

  it('treats totals as balanced when equal to two decimals', async () => {
    const button = document.querySelector('[data-section="scan-bank-pdf"]');
    expect(button).toBeTruthy();

    appInstance.handleNavigation(button);
    await wait(200);

    let bankScanner = document.querySelector('bank-pdf-scanner');
    const BankCtor = global.BankPdfScannerCtor || customElements.get('bank-pdf-scanner');
    if (!BankCtor) throw new Error('BankPdfScanner constructor missing');
    if (!bankScanner || bankScanner.constructor.name !== 'BankPdfScanner') {
      bankScanner?.remove();
      bankScanner = new BankCtor();
      document.getElementById('content-area').appendChild(bankScanner);
    }

    bankScanner.transactions = [
      { id: 'txn-1', description: 'Rounded', amount: 10.005 },
      { id: 'txn-2', description: 'Rounded 2', amount: 0.004 }
    ];
    bankScanner.renderRows();
    bankScanner.statementTotalInput.value = '10.01';
    bankScanner.updateTotals();

    expect(bankScanner.calculatedTotal).toBeCloseTo(10.009, 3);
    expect(bankScanner.categoryPickers.every(p => !p.hasAttribute('disabled'))).toBe(true);
  });
});
