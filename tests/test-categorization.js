const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1400, height: 900 });

  // Capture console logs and network errors
  page.on('console', msg => console.log('🪵 BROWSER:', msg.text()));
  page.on('pageerror', error => console.log('❌ PAGE ERROR:', error.message));
  page.on('requestfailed', request => {
    console.log('❌ REQUEST FAILED:', request.url(), request.failure().errorText);
  });
  page.on('response', response => {
    if (response.status() >= 400) {
      console.log(`❌ HTTP ${response.status()}:`, response.url());
    }
  });

  console.log('📍 Navigating to http://localhost:8080/office/daily_expense_categorizer.html');
  await page.goto('http://localhost:8080/office/daily_expense_categorizer.html', {
    waitUntil: 'networkidle0',
    timeout: 10000
  });

  // Wait for page to load
  await page.waitForSelector('#mainTable', { visible: true, timeout: 10000 });
  await new Promise(resolve => setTimeout(resolve, 2000));

  console.log('📸 Taking screenshot 1: Initial page load');
  await page.screenshot({ path: '/tmp/test-1-initial.png', fullPage: true });

  // Check if there are any uncategorized expenses
  const uncatCount = await page.$eval('#uncatCount', el => el.textContent);
  console.log(`📊 Uncategorized count: ${uncatCount}`);

  // Look for the first category-picker that is NOT already categorized
  const hasUncategorized = await page.evaluate(() => {
    const pickers = Array.from(document.querySelectorAll('category-picker'));
    return pickers.some(picker => !picker.hasAttribute('value') || picker.value === '');
  });

  console.log(`🔍 Has uncategorized expenses: ${hasUncategorized}`);

  if (hasUncategorized) {
    console.log('🎯 Attempting to categorize first uncategorized expense...');

    // Click on first uncategorized category picker
    const clicked = await page.evaluate(() => {
      const pickers = Array.from(document.querySelectorAll('category-picker'));
      const uncategorized = pickers.find(picker => !picker.hasAttribute('value') || picker.value === '');
      if (uncategorized) {
        uncategorized.click();
        return true;
      }
      return false;
    });

    if (clicked) {
      await new Promise(resolve => setTimeout(resolve, 1000));
      console.log('📸 Taking screenshot 2: After clicking picker');
      await page.screenshot({ path: '/tmp/test-2-picker-opened.png', fullPage: true });

      // Try to click a category option
      const categorySelected = await page.evaluate(() => {
        // Look for category buttons in the picker dialog
        const buttons = Array.from(document.querySelectorAll('button'));
        const categoryBtn = buttons.find(btn => btn.textContent.trim() && !btn.textContent.includes('Cancel'));
        if (categoryBtn) {
          console.log('Found category button:', categoryBtn.textContent);
          categoryBtn.click();
          return true;
        }
        return false;
      });

      if (categorySelected) {
        await new Promise(resolve => setTimeout(resolve, 2000));
        console.log('📸 Taking screenshot 3: After selecting category');
        await page.screenshot({ path: '/tmp/test-3-after-categorize.png', fullPage: true });

        // Get current date display
        const currentDate = await page.$eval('#dateText', el => el.textContent);
        console.log(`📅 Current date: ${currentDate}`);

        // Click Next button
        console.log('⏭️ Clicking Next button...');
        await page.click('#nextBtn');
        await new Promise(resolve => setTimeout(resolve, 1500));

        console.log('📸 Taking screenshot 4: After clicking Next');
        await page.screenshot({ path: '/tmp/test-4-after-next.png', fullPage: true });

        const newDate = await page.$eval('#dateText', el => el.textContent);
        console.log(`📅 New date: ${newDate}`);

        // Click Previous button to go back
        console.log('⏮️ Clicking Previous button to go back...');
        await page.click('#prevBtn');
        await new Promise(resolve => setTimeout(resolve, 1500));

        console.log('📸 Taking screenshot 5: After clicking Previous (back to original)');
        await page.screenshot({ path: '/tmp/test-5-after-previous.png', fullPage: true });

        const backDate = await page.$eval('#dateText', el => el.textContent);
        console.log(`📅 Back to date: ${backDate}`);

        // Check if category is still there
        const categoryPersisted = await page.evaluate(() => {
          const firstRow = document.querySelector('tbody tr');
          if (!firstRow) return false;
          const categoryCell = firstRow.querySelector('.category category-picker');
          if (!categoryCell) return false;
          const picker = categoryCell;
          return picker.value && picker.value !== '';
        });

        console.log(`✅ Category persisted: ${categoryPersisted}`);

        // Get console logs
        const logs = await page.evaluate(() => {
          return window.lastLogs || [];
        });
        console.log('🪵 Console logs:', logs);
      }
    }
  }

  console.log('\n📸 Screenshots saved to /tmp/');
  console.log('View with: ls -lh /tmp/test-*.png');

  await browser.close();
})();
