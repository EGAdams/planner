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

  it('renders rows and both Account/Calculated summaries', async () => {
    const button = document.querySelector('[data-section="scan-bank-pdf"]');
    expect(button).toBeTruthy();

    appInstance.handleNavigation(button);
    await wait(400);

    let bankScanner = document.querySelector('bank-pdf-scanner');
    const BankCtor = global.BankPdfScannerCtor || customElements.get('bank-pdf-scanner');
    if (!BankCtor) throw new Error('BankPdfScanner constructor missing');
    if (!bankScanner || bankScanner.constructor.name !== 'BankPdfScanner') {
      bankScanner?.remove();
      bankScanner = new BankCtor();
      document.getElementById('content-area').appendChild(bankScanner);
    }
    const shadow = bankScanner.shadowRoot;
    expect(shadow).toBeTruthy();

    expect(shadow.querySelector('[data-testid="account-summary-card"]')).toBeTruthy();
    expect(shadow.querySelector('[data-testid="calculated-summary-card"]')).toBeTruthy();
    expect(shadow.querySelector('.transaction-row')).toBeTruthy();
    expect(shadow.querySelector('category-picker')).toBeTruthy();
  });

  it('unlocks when the parsed summary matches the account summary', async () => {
    const button = document.querySelector('[data-section="scan-bank-pdf"]');
    expect(button).toBeTruthy();

    appInstance.handleNavigation(button);
    await wait(300);

    let bankScanner = document.querySelector('bank-pdf-scanner');
    const BankCtor = global.BankPdfScannerCtor || customElements.get('bank-pdf-scanner');
    if (!BankCtor) throw new Error('BankPdfScanner constructor missing');
    if (!bankScanner || bankScanner.constructor.name !== 'BankPdfScanner') {
      bankScanner?.remove();
      bankScanner = new BankCtor();
      document.getElementById('content-area').appendChild(bankScanner);
    }

    const transactions = [
      { id: 'c1', description: 'Check #1', amount: -200, bank_item_type: 'CHECK' },
      { id: 'd1', description: 'Debit 1', amount: -100, bank_item_type: 'WITHDRAWAL' },
      { id: 'dep1', description: 'Deposit', amount: 300, bank_item_type: 'DEPOSIT' }
    ];
    const accountSummary = {
      beginning_balance: 1000,
      ending_balance: 1000,
      checks: { count: 1, total: 200 },
      withdrawals: { count: 1, total: 100 },
      deposits: { count: 1, total: 300 }
    };

    const mockResponse = {
      ok: true,
      json: async () => ({
        transactions,
        totals: { sum: 0, debits: 300, credits: 300, statement_total: 1000 },
        account_info: { summary: accountSummary },
        verification: { expected: accountSummary, calculated: {}, passes: true, errors: [] }
      }),
      text: async () => ''
    };
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(mockResponse);

    const file = new window.File(['dummy'], 'statement.pdf', { type: 'application/pdf' });
    await bankScanner._handleFile(file);

    expect(bankScanner.categoryPickers.every(p => !p.hasAttribute('disabled'))).toBe(true);
    expect(bankScanner.shadowRoot.querySelector('[data-testid="verification-issues"]').classList.contains('hidden')).toBe(true);

    fetchSpy.mockRestore();
  });

  it('stays locked and surfaces mismatches when counts differ', async () => {
    const button = document.querySelector('[data-section="scan-bank-pdf"]');
    expect(button).toBeTruthy();

    appInstance.handleNavigation(button);
    await wait(300);

    let bankScanner = document.querySelector('bank-pdf-scanner');
    const BankCtor = global.BankPdfScannerCtor || customElements.get('bank-pdf-scanner');
    if (!BankCtor) throw new Error('BankPdfScanner constructor missing');
    if (!bankScanner || bankScanner.constructor.name !== 'BankPdfScanner') {
      bankScanner?.remove();
      bankScanner = new BankCtor();
      document.getElementById('content-area').appendChild(bankScanner);
    }

    const transactions = [
      { id: 'c1', description: 'Check #1', amount: -200, bank_item_type: 'CHECK' },
      { id: 'd1', description: 'Debit 1', amount: -100, bank_item_type: 'WITHDRAWAL' },
      { id: 'dep1', description: 'Deposit', amount: 300, bank_item_type: 'DEPOSIT' }
    ];
    const accountSummary = {
      beginning_balance: 1000,
      ending_balance: 1000,
      checks: { count: 2, total: 200 }, // mismatch count
      withdrawals: { count: 1, total: 100 },
      deposits: { count: 1, total: 300 }
    };

    const mockResponse = {
      ok: true,
      json: async () => ({
        transactions,
        totals: { sum: 0, debits: 300, credits: 300, statement_total: 1000 },
        account_info: { summary: accountSummary },
        verification: { expected: accountSummary, calculated: {}, passes: false, errors: ['checks count mismatch'] }
      }),
      text: async () => ''
    };
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(mockResponse);

    const file = new window.File(['dummy'], 'statement.pdf', { type: 'application/pdf' });
    await bankScanner._handleFile(file);

    expect(bankScanner.categoryPickers.every(p => p.hasAttribute('disabled'))).toBe(true);
    const issuesText = bankScanner.shadowRoot.querySelector('[data-testid="verification-issues"]').textContent.toLowerCase();
    expect(issuesText).toContain('mismatch');

    fetchSpy.mockRestore();
  });

  it('hides deposits from categorization while still using them for verification', async () => {
    const button = document.querySelector('[data-section="scan-bank-pdf"]');
    expect(button).toBeTruthy();

    appInstance.handleNavigation(button);
    await wait(300);

    let bankScanner = document.querySelector('bank-pdf-scanner');
    const BankCtor = global.BankPdfScannerCtor || customElements.get('bank-pdf-scanner');
    if (!BankCtor) throw new Error('BankPdfScanner constructor missing');
    if (!bankScanner || bankScanner.constructor.name !== 'BankPdfScanner') {
      bankScanner?.remove();
      bankScanner = new BankCtor();
      document.getElementById('content-area').appendChild(bankScanner);
    }

    const transactions = [
      { id: 'c1', description: 'Check #1', amount: -200, bank_item_type: 'CHECK' },
      { id: 'd1', description: 'Debit 1', amount: -100, bank_item_type: 'WITHDRAWAL' },
      { id: 'dep1', description: 'Deposit', amount: 300, bank_item_type: 'DEPOSIT' }
    ];
    const accountSummary = {
      beginning_balance: 1000,
      ending_balance: 1000,
      checks: { count: 1, total: 200 },
      withdrawals: { count: 1, total: 100 },
      deposits: { count: 1, total: 300 }
    };

    const mockResponse = {
      ok: true,
      json: async () => ({
        transactions,
        totals: { sum: 0, debits: 300, credits: 300, statement_total: 1000 },
        account_info: { summary: accountSummary },
        verification: { expected: accountSummary, calculated: {}, passes: true, errors: [] }
      }),
      text: async () => ''
    };
    const fetchSpy = vi.spyOn(global, 'fetch').mockResolvedValue(mockResponse);

    const file = new window.File(['dummy'], 'statement.pdf', { type: 'application/pdf' });
    await bankScanner._handleFile(file);

    const rows = bankScanner.shadowRoot.querySelectorAll('.transaction-row');
    expect(rows.length).toBe(2); // deposit hidden
    rows.forEach(row => {
      const amount = row.querySelector('input[data-testid="amount"]');
      expect(parseFloat(amount.value)).toBeLessThanOrEqual(0);
    });
    expect(bankScanner.categoryPickers.every(p => !p.hasAttribute('disabled'))).toBe(true);

    fetchSpy.mockRestore();
  });
});
