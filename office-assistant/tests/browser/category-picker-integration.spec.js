/**
 * Playwright Browser Test: Category Picker Integration
 *
 * This test verifies the category picker component is properly integrated
 * into the receipt scanner table rows.
 */

import { test, expect } from '@playwright/test';

test.describe('Category Picker Integration in Receipt Table', () => {
  test.beforeEach(async ({ page }) => {
    // Navigate to the test page
    await page.goto('http://localhost:8000/test-category-picker-integration.html');
    await page.waitForLoadState('networkidle');
  });

  test('Test 1: Category column should be added to table header', async ({ page }) => {
    // Click the run test button
    await page.click('#run-test-btn');
    await page.waitForTimeout(500);

    // Get the receipt scanner component
    const receiptScanner = page.locator('receipt-scanner');

    // Query shadow DOM for table headers
    const headers = await receiptScanner.evaluate((scanner) => {
      const shadow = scanner.shadowRoot;
      const table = shadow.querySelector('#receiptItemsTable');
      const headerCells = table.querySelectorAll('thead th');
      return Array.from(headerCells).map(th => th.textContent);
    });

    // Verify we have 5 columns
    expect(headers.length).toBe(5);

    // Verify the last column is "Category"
    expect(headers[4]).toBe('Category');
  });

  test('Test 2: Category pickers should be rendered in each row', async ({ page }) => {
    // Click the run test button
    await page.click('#run-test-btn');
    await page.waitForTimeout(500);

    const receiptScanner = page.locator('receipt-scanner');

    const categoryPickerCount = await receiptScanner.evaluate((scanner) => {
      const shadow = scanner.shadowRoot;
      const pickers = shadow.querySelectorAll('category-picker');
      return pickers.length;
    });

    // Should have 4 category pickers (one per item)
    expect(categoryPickerCount).toBe(4);
  });

  test('Test 3: Category pickers should have proper attributes', async ({ page }) => {
    // Click the run test button
    await page.click('#run-test-btn');
    await page.waitForTimeout(500);

    const receiptScanner = page.locator('receipt-scanner');

    const pickerAttributes = await receiptScanner.evaluate((scanner) => {
      const shadow = scanner.shadowRoot;
      const firstPicker = shadow.querySelector('category-picker');
      return {
        hasExpenseId: firstPicker.hasAttribute('expense-id'),
        expenseIdValue: firstPicker.getAttribute('expense-id'),
        hasDataSrc: firstPicker.hasAttribute('data-src'),
        dataSrcValue: firstPicker.getAttribute('data-src'),
        hasPlaceholder: firstPicker.hasAttribute('placeholder'),
      };
    });

    expect(pickerAttributes.hasExpenseId).toBe(true);
    expect(pickerAttributes.expenseIdValue).toBe('item-0');
    expect(pickerAttributes.hasDataSrc).toBe(true);
    expect(pickerAttributes.dataSrcValue).toBe('/data/categories-taxonomy.json');
    expect(pickerAttributes.hasPlaceholder).toBe(true);
  });

  test('Test 4: Category selection should be stored in item data', async ({ page }) => {
    // Click the run test button
    await page.click('#run-test-btn');
    await page.waitForTimeout(500);

    const receiptScanner = page.locator('receipt-scanner');

    // Simulate category selection by setting value programmatically
    await receiptScanner.evaluate((scanner) => {
      const shadow = scanner.shadowRoot;
      const firstPicker = shadow.querySelector('category-picker');

      // Trigger the completed event manually
      firstPicker.dispatchEvent(new CustomEvent('completed', {
        detail: {
          label: 'Food & Dining / Groceries',
          path: ['Food & Dining', 'Groceries']
        },
        bubbles: true,
        composed: true
      }));
    });

    await page.waitForTimeout(200);

    // Check if category was stored in parsedData
    const hasCategory = await receiptScanner.evaluate((scanner) => {
      return scanner.parsedData.items[0].category !== undefined;
    });

    expect(hasCategory).toBe(true);
  });

  test('Test 5: Multiple category pickers should maintain independent state', async ({ page }) => {
    // Click the run test button
    await page.click('#run-test-btn');
    await page.waitForTimeout(500);

    const receiptScanner = page.locator('receipt-scanner');

    // Set different categories for first two items
    await receiptScanner.evaluate((scanner) => {
      const shadow = scanner.shadowRoot;
      const pickers = shadow.querySelectorAll('category-picker');

      // Set first picker
      pickers[0].dispatchEvent(new CustomEvent('completed', {
        detail: {
          label: 'Food & Dining / Groceries',
          path: ['Food & Dining', 'Groceries']
        },
        bubbles: true,
        composed: true
      }));

      // Set second picker
      pickers[1].dispatchEvent(new CustomEvent('completed', {
        detail: {
          label: 'Shopping / General Merchandise',
          path: ['Shopping', 'General Merchandise']
        },
        bubbles: true,
        composed: true
      }));
    });

    await page.waitForTimeout(200);

    // Verify both categories are stored independently
    const categories = await receiptScanner.evaluate((scanner) => {
      return {
        item0: scanner.parsedData.items[0].category,
        item1: scanner.parsedData.items[1].category,
      };
    });

    expect(categories.item0).toBe('Food & Dining / Groceries');
    expect(categories.item1).toBe('Shopping / General Merchandise');
  });

  test('Visual verification: All tests should pass automatically', async ({ page }) => {
    // Click the run test button
    await page.click('#run-test-btn');
    await page.waitForTimeout(500);

    // Check if all tests passed
    const testResults = await page.textContent('#test-results');
    expect(testResults).toContain('All basic tests passed!');
  });
});
