const { chromium } = require('playwright');

(async () => {
    const browser = await chromium.launch({ headless: false });
    const page = await browser.newPage();

    // Collect console messages
    const consoleLogs = [];
    page.on('console', msg => {
        const msgType = msg.type();
        const text = msg.text();
        consoleLogs.push({ msgType, text, timestamp: new Date().toISOString() });
        console.log('[BROWSER ' + msgType.toUpperCase() + '] ' + text);
    });

    // Collect network errors
    const networkErrors = [];
    page.on('requestfailed', request => {
        const failure = request.failure();
        networkErrors.push({
            url: request.url(),
            error: failure ? failure.errorText : 'Unknown error',
            timestamp: new Date().toISOString()
        });
        console.log('[NETWORK ERROR] ' + request.url() + ' - ' + (failure ? failure.errorText : 'Unknown'));
    });

    // Navigate to the HTML file
    const htmlPath = 'file:///home/adamsl/planner/sys_admin_debug.html';
    console.log('\n=== NAVIGATING TO: ' + htmlPath + ' ===\n');
    
    await page.goto(htmlPath);

    // Wait for initial auto-diagnostics to complete (10 seconds)
    console.log('\n=== WAITING 10 SECONDS FOR AUTO-DIAGNOSTICS ===\n');
    await page.waitForTimeout(10000);

    // Take screenshot
    const screenshotPath = '/tmp/dashboard_debug_screenshot.png';
    await page.screenshot({ path: screenshotPath, fullPage: true });
    console.log('\n=== SCREENSHOT SAVED TO: ' + screenshotPath + ' ===\n');

    // Extract status information
    const lettaStatus = await page.locator('#letta-status').textContent();
    const lettaTime = await page.locator('#letta-time').textContent();
    const lettaLabel = await page.locator('#letta-label').textContent();
    
    const dashboardStatus = await page.locator('#dashboard-status').textContent();
    const dashboardTime = await page.locator('#dashboard-time').textContent();
    const dashboardLabel = await page.locator('#dashboard-label').textContent();

    const officeStatus = await page.locator('#office-status').textContent();
    const officeTime = await page.locator('#office-time').textContent();
    const officeLabel = await page.locator('#office-label').textContent();

    const totalTests = await page.locator('#total-tests').textContent();
    const successRate = await page.locator('#success-rate').textContent();

    // Get log contents
    const logs = await page.locator('#logs').textContent();

    // Print results
    console.log('\n========================================');
    console.log('DASHBOARD STATUS REPORT');
    console.log('========================================\n');
    
    console.log('LETTA SERVER:');
    console.log('  Status: ' + lettaStatus);
    console.log('  Time: ' + lettaTime);
    console.log('  Label: ' + lettaLabel);
    console.log('');
    
    console.log('DASHBOARD API:');
    console.log('  Status: ' + dashboardStatus);
    console.log('  Time: ' + dashboardTime);
    console.log('  Label: ' + dashboardLabel);
    console.log('');
    
    console.log('OFFICE API:');
    console.log('  Status: ' + officeStatus);
    console.log('  Time: ' + officeTime);
    console.log('  Label: ' + officeLabel);
    console.log('');
    
    console.log('TEST METRICS:');
    console.log('  Total Tests: ' + totalTests);
    console.log('  Success Rate: ' + successRate);
    console.log('');
    
    console.log('========================================');
    console.log('BROWSER CONSOLE LOGS:');
    console.log('========================================\n');
    consoleLogs.forEach(log => {
        console.log('[' + log.timestamp + '] [' + log.msgType.toUpperCase() + '] ' + log.text);
    });
    
    console.log('\n========================================');
    console.log('NETWORK ERRORS:');
    console.log('========================================\n');
    if (networkErrors.length === 0) {
        console.log('No network errors detected');
    } else {
        networkErrors.forEach(err => {
            console.log('[' + err.timestamp + '] ' + err.url);
            console.log('  Error: ' + err.error);
        });
    }
    
    console.log('\n========================================');
    console.log('APPLICATION LOGS (last 500 chars):');
    console.log('========================================\n');
    console.log(logs.slice(-500));
    
    console.log('\n========================================');
    console.log('ANALYSIS:');
    console.log('========================================\n');
    
    if (lettaStatus === '❌') {
        console.log('ISSUE FOUND: Letta server showing as FAILED in dashboard');
        console.log('URL being tested: http://localhost:8284/v1/health/');
        console.log('');
        console.log('Possible causes:');
        console.log('1. CORS proxy on port 8284 is not running');
        console.log('2. CORS proxy is not properly forwarding requests');
        console.log('3. Browser security blocking the request');
        console.log('4. Network timeout or connection issue');
    } else if (lettaStatus === '✅') {
        console.log('SUCCESS: Letta server showing as ONLINE in dashboard');
    } else {
        console.log('UNEXPECTED STATUS: Letta showing as "' + lettaStatus + '"');
    }

    // Keep browser open for manual inspection
    console.log('\n=== KEEPING BROWSER OPEN FOR 30 SECONDS ===');
    console.log('(You can manually inspect the page)\n');
    await page.waitForTimeout(30000);

    await browser.close();
})();
