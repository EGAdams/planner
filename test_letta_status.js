const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage();
  
  console.log('Opening dashboard...');
  
  // Navigate to the HTML file
  const filePath = 'file:///home/adamsl/planner/sys_admin_debug.html';
  await page.goto(filePath);
  
  console.log('Waiting for auto-diagnostic tests to complete...');
  // Wait 5 seconds for the auto-diagnostics to run
  await page.waitForTimeout(5000);
  
  console.log('Taking screenshot...');
  await page.screenshot({ path: '/tmp/letta_dashboard_status.png', fullPage: true });
  
  // Extract status information
  const lettaStatus = await page.textContent('#letta-status');
  const lettaTime = await page.textContent('#letta-time');
  const lettaLabel = await page.textContent('#letta-label');
  
  const dashboardStatus = await page.textContent('#dashboard-status');
  const dashboardTime = await page.textContent('#dashboard-time');
  const dashboardLabel = await page.textContent('#dashboard-label');
  
  const officeStatus = await page.textContent('#office-status');
  const officeTime = await page.textContent('#office-time');
  const officeLabel = await page.textContent('#office-label');
  
  const totalTests = await page.textContent('#total-tests');
  const successRate = await page.textContent('#success-rate');
  
  // Get logs
  const logs = await page.textContent('#logs');
  
  console.log('\n========================================');
  console.log('DASHBOARD STATUS VERIFICATION');
  console.log('========================================\n');
  
  console.log('LETTA SERVER (Port 8283/8284):');
  console.log('  Status: ' + lettaStatus);
  console.log('  Time: ' + lettaTime);
  console.log('  Label: ' + lettaLabel);
  console.log('');
  
  console.log('DASHBOARD API (Port 3000):');
  console.log('  Status: ' + dashboardStatus);
  console.log('  Time: ' + dashboardTime);
  console.log('  Label: ' + dashboardLabel);
  console.log('');
  
  console.log('OFFICE API (Port 8080):');
  console.log('  Status: ' + officeStatus);
  console.log('  Time: ' + officeTime);
  console.log('  Label: ' + officeLabel);
  console.log('');
  
  console.log('OVERALL METRICS:');
  console.log('  Total Tests: ' + totalTests);
  console.log('  Success Rate: ' + successRate);
  console.log('');
  
  console.log('RECENT LOGS:');
  console.log('----------------------------------------');
  const recentLogs = logs.split('\n').slice(-15).join('\n');
  console.log(recentLogs);
  console.log('----------------------------------------\n');
  
  // Verification
  console.log('VERIFICATION RESULTS:');
  console.log('----------------------------------------');
  
  const lettaOnline = lettaStatus.includes('✅');
  const lettaHasTime = lettaTime && lettaTime !== '-' && lettaTime !== 'Offline' && !lettaTime.includes('❌');
  const officeOffline = officeStatus.includes('❌');
  
  console.log('Letta Server Online: ' + (lettaOnline ? 'PASS ✅' : 'FAIL ❌'));
  console.log('Letta Response Time Showing: ' + (lettaHasTime ? 'PASS ✅' : 'FAIL ❌'));
  console.log('Office API Offline (Expected): ' + (officeOffline ? 'PASS ✅' : 'FAIL ❌'));
  
  const expectedSuccessRate = successRate.includes('67') || successRate.includes('66') || successRate.includes('50');
  console.log('Success Rate: ' + successRate + ' ' + (expectedSuccessRate ? '(acceptable)' : '(check logs)'));
  
  console.log('');
  console.log('Screenshot saved to: /tmp/letta_dashboard_status.png');
  console.log('========================================\n');
  
  // Keep browser open for 10 seconds to review
  console.log('Browser will remain open for 10 seconds for manual review...');
  await page.waitForTimeout(10000);
  
  await browser.close();
})();
