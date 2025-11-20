/**
 * FUNCTIONAL BROWSER TESTING - OFFICE ASSISTANT NAVIGATION REFACTOR
 */

const { test, expect } = require('@playwright/test');

const BASE_URL = 'http://localhost:8000';

test.describe('Office Assistant Navigation - Functional Browser Tests', () => {
  
  test('1. Initial Page Load - Verify 3 Navigation Buttons Visible', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    await page.screenshot({ path: 'tests/browser/screenshots/01-initial-load.png', fullPage: true });
    
    await expect(page).toHaveTitle('Office Assistant');
    
    const header = page.locator('header h1');
    await expect(header).toHaveText("Mom's Dashboard");
    
    const expenseButton = page.locator('[data-section="expenses"]');
    const uploadButton = page.locator('[data-section="upload-bank-statement"]');
    const scanButton = page.locator('[data-section="scan-receipt"]');
    
    await expect(expenseButton).toBeVisible();
    await expect(uploadButton).toBeVisible();
    await expect(scanButton).toBeVisible();
    
    await expect(expenseButton).toContainText('💰');
    await expect(expenseButton).toContainText('Expense Categorizer');
    await expect(uploadButton).toContainText('📤');
    await expect(uploadButton).toContainText('Upload Bank Statement');
    await expect(scanButton).toContainText('📸');
    await expect(scanButton).toContainText('Scan Receipt');
    
    await expect(expenseButton).toHaveAttribute('data-active', 'true');
    await expect(uploadButton).toHaveAttribute('data-active', 'false');
    await expect(scanButton).toHaveAttribute('data-active', 'false');
    
    console.log('✓ TEST 1 PASSED: Initial load successful');
  });
  
  test('2A. Expense Categorizer Button - Click and Load Section', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    
    const expenseButton = page.locator('[data-section="expenses"]');
    await expenseButton.click();
    await page.waitForTimeout(500);
    await expect(expenseButton).toHaveAttribute('data-active', 'true');
    
    const iframe = page.frameLocator('iframe[src="daily_expense_categorizer.html"]');
    await expect(iframe.locator('body')).toBeAttached({ timeout: 10000 });
    await page.screenshot({ path: 'tests/browser/screenshots/02a-expense-categorizer.png', fullPage: true });
    
    console.log('✓ TEST 2A PASSED: Expense Categorizer loads correctly');
  });
  
  test('2B. Upload Bank Statement Button - Click and Load Section', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    
    const uploadButton = page.locator('[data-section="upload-bank-statement"]');
    await uploadButton.click();
    await page.waitForTimeout(500);
    await expect(uploadButton).toHaveAttribute('data-active', 'true');
    
    const iframe = page.frameLocator('iframe[src="upload_pdf_statements.html"]');
    await expect(iframe.locator('body')).toBeAttached({ timeout: 10000 });
    await page.screenshot({ path: 'tests/browser/screenshots/02b-upload-bank-statement.png', fullPage: true });
    
    console.log('✓ TEST 2B PASSED: Upload Bank Statement loads');
  });
  
  test('2C. Scan Receipt Button - Click and Load Web Component', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    
    const scanButton = page.locator('[data-section="scan-receipt"]');
    await scanButton.click();
    await page.waitForTimeout(1000);
    await expect(scanButton).toHaveAttribute('data-active', 'true');
    
    const receiptScanner = page.locator('receipt-scanner');
    await expect(receiptScanner).toBeAttached({ timeout: 5000 });
    await page.screenshot({ path: 'tests/browser/screenshots/02c-scan-receipt.png', fullPage: true });
    
    console.log('✓ TEST 2C PASSED: Scan Receipt loads');
  });
  
  test('3. Accessibility - Keyboard Navigation with Tab Key', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    
    const expenseButton = page.locator('[data-section="expenses"]');
    const uploadButton = page.locator('[data-section="upload-bank-statement"]');
    const scanButton = page.locator('[data-section="scan-receipt"]');
    
    await expenseButton.focus();
    await expect(expenseButton).toBeFocused();
    await page.screenshot({ path: 'tests/browser/screenshots/03a-keyboard-focus-1.png' });
    
    await page.keyboard.press('Tab');
    await expect(uploadButton).toBeFocused();
    await page.screenshot({ path: 'tests/browser/screenshots/03b-keyboard-focus-2.png' });
    
    await page.keyboard.press('Tab');
    await expect(scanButton).toBeFocused();
    await page.screenshot({ path: 'tests/browser/screenshots/03c-keyboard-focus-3.png' });
    
    await page.keyboard.press('Enter');
    await page.waitForTimeout(500);
    await expect(scanButton).toHaveAttribute('data-active', 'true');
    
    await expect(expenseButton).toHaveAttribute('aria-label');
    await expect(uploadButton).toHaveAttribute('aria-label');
    await expect(scanButton).toHaveAttribute('aria-label');
    
    console.log('✓ TEST 3 PASSED: Keyboard navigation works');
  });
  
  test('4. Section State Management - Only One Section Visible', async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    
    const expenseButton = page.locator('[data-section="expenses"]');
    const uploadButton = page.locator('[data-section="upload-bank-statement"]');
    const scanButton = page.locator('[data-section="scan-receipt"]');
    
    await uploadButton.click();
    await page.waitForTimeout(500);
    await expect(expenseButton).toHaveAttribute('data-active', 'false');
    await expect(uploadButton).toHaveAttribute('data-active', 'true');
    await expect(scanButton).toHaveAttribute('data-active', 'false');
    
    await scanButton.click();
    await page.waitForTimeout(500);
    await expect(expenseButton).toHaveAttribute('data-active', 'false');
    await expect(uploadButton).toHaveAttribute('data-active', 'false');
    await expect(scanButton).toHaveAttribute('data-active', 'true');
    
    await expenseButton.click();
    await page.waitForTimeout(500);
    await expect(expenseButton).toHaveAttribute('data-active', 'true');
    await expect(uploadButton).toHaveAttribute('data-active', 'false');
    await expect(scanButton).toHaveAttribute('data-active', 'false');
    
    console.log('✓ TEST 4 PASSED: Section state management works');
  });
  
  test('7. Browser Console - Check for Errors and Warnings', async ({ page }) => {
    const consoleMessages = { errors: [], warnings: [], logs: [] };
    const networkErrors = [];
    
    page.on('console', msg => {
      if (msg.type() === 'error') consoleMessages.errors.push(msg.text());
      else if (msg.type() === 'warning') consoleMessages.warnings.push(msg.text());
      else if (msg.type() === 'log') consoleMessages.logs.push(msg.text());
    });
    
    page.on('requestfailed', request => {
      networkErrors.push(request.url() + ' failed');
    });
    
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    
    const uploadButton = page.locator('[data-section="upload-bank-statement"]');
    await uploadButton.click();
    await page.waitForTimeout(1000);
    
    const scanButton = page.locator('[data-section="scan-receipt"]');
    await scanButton.click();
    await page.waitForTimeout(1000);
    
    console.log('Errors:', consoleMessages.errors.length);
    console.log('Warnings:', consoleMessages.warnings.length);
    console.log('Network Errors:', networkErrors.length);
    
    const fs = require('fs');
    fs.writeFileSync(
      'tests/browser/console-output.json',
      JSON.stringify({ consoleMessages, networkErrors }, null, 2)
    );
    
    console.log('✓ TEST 7 PASSED: Console inspection complete');
  });
  
  test('8. Responsive Design - Mobile Viewport Test', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto(BASE_URL);
    await page.waitForLoadState('networkidle');
    
    const expenseButton = page.locator('[data-section="expenses"]');
    const uploadButton = page.locator('[data-section="upload-bank-statement"]');
    const scanButton = page.locator('[data-section="scan-receipt"]');
    
    await expect(expenseButton).toBeVisible();
    await expect(uploadButton).toBeVisible();
    await expect(scanButton).toBeVisible();
    
    await page.screenshot({ path: 'tests/browser/screenshots/08-mobile-view.png', fullPage: true });
    
    await uploadButton.click();
    await page.waitForTimeout(500);
    await expect(uploadButton).toHaveAttribute('data-active', 'true');
    
    console.log('✓ TEST 8 PASSED: Responsive design works');
  });
  
});
