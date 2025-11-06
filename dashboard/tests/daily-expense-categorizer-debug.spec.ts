import { test, expect } from '@playwright/test';

test.describe('Daily Expense Categorizer - Debug', () => {
  test('investigate missing server monitors', async ({ page }) => {
    // Set up console message capture
    const consoleMessages: Array<{ type: string; text: string }> = [];
    page.on('console', msg => {
      consoleMessages.push({
        type: msg.type(),
        text: msg.text()
      });
    });

    // Set up network response capture
    const networkResponses: Array<{ url: string; status: number }> = [];
    page.on('response', response => {
      networkResponses.push({
        url: response.url(),
        status: response.status()
      });
    });

    // Set up error capture
    const pageErrors: string[] = [];
    page.on('pageerror', error => {
      pageErrors.push(error.message);
    });

    console.log('\n=== NAVIGATING TO DAILY EXPENSE CATEGORIZER ===');
    
    // Navigate to the page
    const response = await page.goto('http://localhost:8080/office/daily_expense_categorizer.html', {
      waitUntil: 'networkidle',
      timeout: 30000
    });

    const responseStatus = response ? response.status() : 'no response';
    const responseStatusText = response ? response.statusText() : 'no response';

    console.log(`\n=== HTTP RESPONSE ===`);
    console.log(`Status: ${responseStatus}`);
    console.log(`Status Text: ${responseStatusText}`);
    
    // Wait a bit for any dynamic content
    await page.waitForTimeout(2000);

    // Take screenshot
    await page.screenshot({ 
      path: 'test-results/daily-expense-categorizer-debug.png',
      fullPage: true 
    });
    console.log('\n=== SCREENSHOT SAVED ===');
    console.log('Path: test-results/daily-expense-categorizer-debug.png');

    // Get page title
    const title = await page.title();
    console.log(`\n=== PAGE TITLE ===`);
    console.log(title);

    // Get visible content
    const bodyText = await page.locator('body').textContent();
    console.log(`\n=== VISIBLE BODY TEXT (first 500 chars) ===`);
    console.log(bodyText?.substring(0, 500));

    // Get HTML content
    const htmlContent = await page.content();
    console.log(`\n=== HTML SOURCE (first 1000 chars) ===`);
    console.log(htmlContent.substring(0, 1000));

    // Check for specific elements
    console.log(`\n=== ELEMENT CHECKS ===`);
    const hasH1 = await page.locator('h1').count();
    console.log(`H1 elements found: ${hasH1}`);
    
    const hasServerMonitors = await page.locator('#server-monitors-container').count();
    console.log(`#server-monitors-container found: ${hasServerMonitors}`);
    
    const hasExpenseForm = await page.locator('form').count();
    console.log(`Form elements found: ${hasExpenseForm}`);

    // Print all console messages
    console.log(`\n=== CONSOLE MESSAGES (${consoleMessages.length} total) ===`);
    consoleMessages.forEach((msg, idx) => {
      console.log(`[${idx + 1}] [${msg.type.toUpperCase()}] ${msg.text}`);
    });

    // Print page errors
    if (pageErrors.length > 0) {
      console.log(`\n=== PAGE ERRORS (${pageErrors.length} total) ===`);
      pageErrors.forEach((error, idx) => {
        console.log(`[${idx + 1}] ${error}`);
      });
    } else {
      console.log(`\n=== NO PAGE ERRORS ===`);
    }

    // Print network responses
    console.log(`\n=== NETWORK RESPONSES (showing failed or suspicious) ===`);
    const failedResponses = networkResponses.filter(r => r.status >= 400);
    if (failedResponses.length > 0) {
      failedResponses.forEach((resp, idx) => {
        console.log(`[${idx + 1}] ${resp.status} - ${resp.url}`);
      });
    } else {
      console.log('No failed network requests');
    }

    // Check if SSE endpoint is accessible
    console.log(`\n=== CHECKING SSE ENDPOINT ===`);
    const sseResponse = await page.request.get('http://localhost:3000/sse');
    console.log(`SSE endpoint status: ${sseResponse.status()}`);

    // Check if backend API is responding
    console.log(`\n=== CHECKING BACKEND API ===`);
    const statusResponse = await page.request.get('http://localhost:3000/api/status');
    console.log(`Backend status: ${statusResponse.status()}`);
    if (statusResponse.ok()) {
      const statusData = await statusResponse.json();
      console.log(`Backend response:`, JSON.stringify(statusData, null, 2));
    }

    // Create detailed error context
    const errorContext = {
      pageTitle: title,
      httpStatus: responseStatus,
      elementsFound: {
        h1: hasH1,
        serverMonitors: hasServerMonitors,
        forms: hasExpenseForm
      },
      consoleMessageCount: consoleMessages.length,
      errorCount: pageErrors.length,
      failedNetworkRequests: failedResponses.length,
      visibleTextLength: bodyText ? bodyText.length : 0
    };

    // Write error context to file
    await page.evaluate((context) => {
      console.log('=== ERROR CONTEXT SUMMARY ===');
      console.log(JSON.stringify(context, null, 2));
    }, errorContext);

    // Save error context to file
    const fs = require('fs');
    fs.writeFileSync(
      'test-results/daily-expense-categorizer-error-context.json',
      JSON.stringify({
        timestamp: new Date().toISOString(),
        errorContext,
        consoleMessages,
        pageErrors,
        failedResponses
      }, null, 2)
    );
    console.log('\n=== ERROR CONTEXT SAVED ===');
    console.log('Path: test-results/daily-expense-categorizer-error-context.json');

    // This test is for debugging, so we don't fail it
    // Just collect information
    console.log('\n=== DEBUG TEST COMPLETE ===');
  });
});
