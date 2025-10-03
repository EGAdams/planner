const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1600, height: 1000 });

  page.on('console', msg => {
    const text = msg.text();
    if (text.includes('Setting picker') || text.includes('Picker state') || text.includes('category')) {
      console.log('🪵', text);
    }
  });

  console.log('📍 Loading page...');
  await page.goto('http://localhost:8080/office/daily_expense_categorizer.html', {
    waitUntil: 'networkidle0'
  });

  await page.waitForSelector('#mainTable', { visible: true });
  await new Promise(r => setTimeout(r, 2000));

  await page.screenshot({ path: '/tmp/full-path-display.png', fullPage: true });

  // Check what the category-pickers display
  const categories = await page.evaluate(() => {
    const pickers = document.querySelectorAll('category-picker');
    const results = [];
    pickers.forEach((picker, i) => {
      const statusInput = picker.shadowRoot?.querySelector('#status');
      const state = picker.getAttribute('data-state');
      results.push({
        index: i,
        status: statusInput?.value || 'N/A',
        state: state
      });
    });
    return results;
  });

  console.log('📋 Category displays:');
  categories.forEach(cat => {
    console.log(`  [${cat.index}] ${cat.state || 'pending'}: "${cat.status}"`);
  });

  await browser.close();
})();
