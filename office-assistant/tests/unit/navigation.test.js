/**
 * TDD RED PHASE: Navigation Structure Tests
 *
 * These tests define the REQUIRED navigation structure after refactoring:
 * - 5 navigation buttons: Expense Categorizer, Upload Bank Statement, Scan Receipt, Scan Bank PDF, Calendar
 * - "Upload to Computer" tab should NOT exist
 * - Each button should have correct icon and data attributes
 */

import { describe, it, expect, beforeEach } from 'vitest';
import { JSDOM } from 'jsdom';
import { readFileSync } from 'fs';
import { resolve } from 'path';

describe('Navigation Structure - TDD RED Phase', () => {
  let dom;
  let document;
  let window;

  beforeEach(() => {
    // Load the actual index.html file
    const html = readFileSync(resolve(process.cwd(), 'index.html'), 'utf-8');
    dom = new JSDOM(html, {
      runScripts: 'dangerously',
      resources: 'usable',
    });
    document = dom.window.document;
    window = dom.window;
    global.document = document;
    global.window = window;
  });

  describe('Navigation Button Count', () => {
    it('should have exactly 5 navigation buttons', () => {
      const navButtons = document.querySelectorAll('.nav-button');

      expect(navButtons.length).toBe(5);
    });
  });

  describe('Expense Categorizer Button', () => {
    it('should have Expense Categorizer as first button with correct icon', () => {
      const buttons = document.querySelectorAll('.nav-button');
      const expenseButton = buttons[0];

      expect(expenseButton.getAttribute('data-section')).toBe('expenses');
      expect(expenseButton.textContent).toContain('Expense Categorizer');
      expect(expenseButton.querySelector('.text-2xl').textContent).toBe('💰');
    });

    it('should be marked as active by default', () => {
      const expenseButton = document.querySelector('[data-section="expenses"]');

      expect(expenseButton.getAttribute('data-active')).toBe('true');
    });
  });

  describe('Upload Bank Statement Button', () => {
    it('should have Upload Bank Statement as second button with upload icon', () => {
      const buttons = document.querySelectorAll('.nav-button');
      const uploadButton = buttons[1];

      // EXPECTED TO FAIL: Currently shows "Upload to Computer"
      expect(uploadButton.getAttribute('data-section')).toBe('upload-bank-statement');
      expect(uploadButton.textContent).toContain('Upload Bank Statement');
      expect(uploadButton.querySelector('.text-2xl').textContent).toBe('📤');
    });

    it('should NOT have "Upload to Computer" text', () => {
      const uploadButton = document.querySelector('[data-section="upload-bank-statement"]');

      // EXPECTED TO FAIL: Currently has "Upload to Computer"
      expect(uploadButton.textContent).not.toContain('Upload to Computer');
    });
  });

  describe('Scan Receipt Button', () => {
    it('should have Scan Receipt as third button with camera icon', () => {
      const buttons = document.querySelectorAll('.nav-button');
      const scanButton = buttons[2];

      expect(scanButton.getAttribute('data-section')).toBe('scan-receipt');
      expect(scanButton.textContent).toContain('Scan Receipt');
      expect(scanButton.querySelector('.text-2xl').textContent).toBe('📸');
    });

    it('should be inactive by default', () => {
      const scanButton = document.querySelector('[data-section="scan-receipt"]');

      expect(scanButton).toBeDefined();
      expect(scanButton.getAttribute('data-active')).toBe('false');
    });
  });

  describe('Scan Bank PDF Button', () => {
    it('should have Scan Bank PDF as fourth button with bank icon', () => {
      const buttons = document.querySelectorAll('.nav-button');
      const scanBankButton = buttons[3];

      expect(scanBankButton.getAttribute('data-section')).toBe('scan-bank-pdf');
      expect(scanBankButton.textContent).toContain('Scan Bank PDF');
      expect(scanBankButton.querySelector('.text-2xl').textContent).toBe('🏦');
    });

    it('should be inactive by default', () => {
      const scanBankButton = document.querySelector('[data-section="scan-bank-pdf"]');

      expect(scanBankButton).toBeDefined();
      expect(scanBankButton.getAttribute('data-active')).toBe('false');
    });
  });

  describe('Calendar Button', () => {
    it('should exist as fifth button with calendar icon', () => {
      const buttons = document.querySelectorAll('.nav-button');
      const calendarButton = buttons[4];

      expect(calendarButton.getAttribute('data-section')).toBe('calendar');
      expect(calendarButton.textContent).toContain('Calendar');
      expect(calendarButton.querySelector('.text-2xl').textContent).toBe('📅');
    });

    it('should be inactive by default', () => {
      const calendarButton = document.querySelector('[data-section="calendar"]');

      expect(calendarButton).toBeDefined();
      expect(calendarButton.getAttribute('data-active')).toBe('false');
    });
  });

  describe('Deprecated Navigation Elements', () => {
    it('should NOT have "Upload to Computer" button anymore', () => {
      const buttons = Array.from(document.querySelectorAll('.nav-button'));
      const oldUploadButton = buttons.find(btn => btn.textContent.includes('Upload to Computer'));

      expect(oldUploadButton).toBeUndefined();
    });
  });

  describe('Navigation Button Attributes', () => {
    it('should have correct data-section attributes for all buttons', () => {
      const buttons = document.querySelectorAll('.nav-button');
      const sections = Array.from(buttons).map(btn => btn.getAttribute('data-section'));

      expect(sections).toEqual(['expenses', 'upload-bank-statement', 'scan-receipt', 'scan-bank-pdf', 'calendar']);
    });

    it('should have keyboard accessibility attributes', () => {
      const buttons = document.querySelectorAll('.nav-button');

      buttons.forEach((button, index) => {
        expect(button.getAttribute('tabindex')).toBe('0');
        expect(button.hasAttribute('aria-label')).toBe(true);
        expect(button.hasAttribute('title')).toBe(true);
      });
    });
  });

  describe('Navigation Visual Elements', () => {
    it('should have emoji icons for all buttons', () => {
      const buttons = document.querySelectorAll('.nav-button');

      buttons.forEach(button => {
        const icon = button.querySelector('.text-2xl');
        expect(icon).toBeDefined();
        expect(icon.textContent.length).toBeGreaterThan(0);
      });
    });

    it('should have proper Tailwind CSS classes', () => {
      const buttons = document.querySelectorAll('.nav-button');

      buttons.forEach(button => {
        expect(button.classList.contains('flex')).toBe(true);
        expect(button.classList.contains('flex-col')).toBe(true);
        expect(button.classList.contains('items-center')).toBe(true);
      });
    });
  });
});
