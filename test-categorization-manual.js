const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: false,  // Show browser so we can see what's happening
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
    slowMo: 100  // Slow down so we can see
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1600, height: 1000 });

  // Capture console
  page.on('console', msg => console.log('🪵', msg.text()));
  page.on('pageerror', error => console.log('❌', error.message));

  console.log('📍 Opening page...');
  await page.goto('http://localhost:8080/office/daily_expense_categorizer.html', {
    waitUntil: 'networkidle0'
  });

  await page.waitForSelector('#mainTable', { visible: true });
  await new Promise(r => setTimeout(r, 2000));

  console.log('📸 Taking initial screenshot');
  await page.screenshot({ path: '/tmp/manual-1-initial.png', fullPage: true });

  console.log('🔍 Looking for first uncategorized category-picker...');
  const hasUncat = await page.evaluate(() => {
    const pickers = document.querySelectorAll('category-picker');
    console.log(`Found ${pickers.length} category-picker elements`);
    for (let i = 0; i < pickers.length; i++) {
      const picker = pickers[i];
      const select = picker.shadowRoot?.querySelector('select');
      console.log(`Picker ${i}: select value = "${select?.value || 'NONE'}"`);
      if (!select || select.value === '' || select.value === 'Select category...') {
        return i;
      }
    }
    return -1;
  });

  if (hasUncat >= 0) {
    console.log(`✅ Found uncategorized picker at index ${hasUncat}`);

    console.log('🎯 Clicking on the select dropdown...');
    await page.evaluate((idx) => {
      const picker = document.querySelectorAll('category-picker')[idx];
      const select = picker.shadowRoot.querySelector('select');
      select.click();
      select.focus();
    }, hasUncat);

    await new Promise(r => setTimeout(r, 500));
    await page.screenshot({ path: '/tmp/manual-2-dropdown-open.png', fullPage: true });

    console.log('📝 Selecting first category option...');
    await page.evaluate((idx) => {
      const picker = document.querySelectorAll('category-picker')[idx];
      const select = picker.shadowRoot.querySelector('select');
      const options = select.querySelectorAll('option');
      console.log(`Found ${options.length} options`);
      if (options.length > 1) {
        select.value = options[1].value;
        select.dispatchEvent(new Event('change', { bubbles: true }));
        console.log(`Selected option: ${options[1].value}`);
      }
    }, hasUncat);

    await new Promise(r => setTimeout(r, 3000));  // Wait for API call
    await page.screenshot({ path: '/tmp/manual-3-after-select.png', fullPage: true });

    const currentDate = await page.$eval('#dateText', el => el.textContent);
    console.log(`📅 Current date: ${currentDate}`);

    console.log('⏭️ Clicking Next...');
    await page.click('#nextBtn');
    await new Promise(r => setTimeout(r, 2000));
    await page.screenshot({ path: '/tmp/manual-4-next.png', fullPage: true });

    const newDate = await page.$eval('#dateText', el => el.textContent);
    console.log(`📅 New date: ${newDate}`);

    console.log('⏮️ Clicking Previous...');
    await page.click('#prevBtn');
    await new Promise(r => setTimeout(r, 2000));
    await page.screenshot({ path: '/tmp/manual-5-back.png', fullPage: true });

    const backDate = await page.$eval('#dateText', el => el.textContent);
    console.log(`📅 Back to: ${backDate}`);

    console.log('🔍 Checking if category persisted...');
    const persisted = await page.evaluate((idx) => {
      const picker = document.querySelectorAll('category-picker')[idx];
      const select = picker.shadowRoot.querySelector('select');
      const value = select?.value || '';
      console.log(`Category value after navigation: "${value}"`);
      return value !== '' && value !== 'Select category...';
    }, hasUncat);

    console.log(`✅ Category persisted: ${persisted}`);
  }

  console.log('\n✅ Test complete!');
  console.log('Press Ctrl+C to close browser');
  // Keep browser open for inspection
  // await browser.close();
})();
