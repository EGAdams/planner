const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: false,
    args: ['--no-sandbox', '--disable-setuid-sandbox'],
    slowMo: 200
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1600, height: 1000 });

  page.on('console', msg => console.log('🪵', msg.text()));

  console.log('📍 Opening page...');
  await page.goto('http://localhost:8080/office/daily_expense_categorizer.html', {
    waitUntil: 'networkidle0'
  });

  await page.waitForSelector('#mainTable', { visible: true });
  await new Promise(r => setTimeout(r, 2000));

  console.log('📸 Taking screenshot before categorization');
  await page.screenshot({ path: '/tmp/hierarchical-1-before.png', fullPage: true });

  console.log('🎯 Selecting first uncategorized picker...');
  const pickerIndex = await page.evaluate(() => {
    const pickers = document.querySelectorAll('category-picker');
    for (let i = 0; i < pickers.length; i++) {
      if (pickers[i].getAttribute('data-state') !== 'done') {
        return i;
      }
    }
    return -1;
  });

  if (pickerIndex >= 0) {
    console.log(`✅ Found uncategorized picker at index ${pickerIndex}`);

    // Select "Utilities" (parent category)
    console.log('📝 Step 1: Selecting "Utilities"...');
    await page.evaluate((idx) => {
      const picker = document.querySelectorAll('category-picker')[idx];
      const select = picker.shadowRoot.querySelector('select');
      const options = Array.from(select.querySelectorAll('option'));
      const utilitiesOption = options.find(opt => opt.textContent.includes('Utilities'));
      if (utilitiesOption) {
        select.value = utilitiesOption.value;
        select.dispatchEvent(new Event('change', { bubbles: true }));
        console.log('Selected Utilities, value:', utilitiesOption.value);
      }
    }, pickerIndex);

    await new Promise(r => setTimeout(r, 1000));
    await page.screenshot({ path: '/tmp/hierarchical-2-utilities.png', fullPage: true });

    // Select "Housing" (child category)
    console.log('📝 Step 2: Selecting "Housing"...');
    await page.evaluate((idx) => {
      const picker = document.querySelectorAll('category-picker')[idx];
      const select = picker.shadowRoot.querySelector('select');
      const statusInput = picker.shadowRoot.querySelector('#status');
      console.log('Status after Utilities:', statusInput.value);

      const options = Array.from(select.querySelectorAll('option'));
      const housingOption = options.find(opt => opt.textContent.includes('Housing'));
      if (housingOption) {
        select.value = housingOption.value;
        select.dispatchEvent(new Event('change', { bubbles: true }));
        console.log('Selected Housing, value:', housingOption.value);
      }
    }, pickerIndex);

    await new Promise(r => setTimeout(r, 1000));
    await page.screenshot({ path: '/tmp/hierarchical-3-housing.png', fullPage: true });

    // Select "Gas" (final category)
    console.log('📝 Step 3: Selecting "Gas"...');
    await page.evaluate((idx) => {
      const picker = document.querySelectorAll('category-picker')[idx];
      const select = picker.shadowRoot.querySelector('select');
      const statusInput = picker.shadowRoot.querySelector('#status');
      console.log('Status after Housing:', statusInput.value);

      const options = Array.from(select.querySelectorAll('option'));
      const gasOption = options.find(opt => opt.textContent.includes('Gas'));
      if (gasOption) {
        select.value = gasOption.value;
        select.dispatchEvent(new Event('change', { bubbles: true }));
        console.log('Selected Gas, value:', gasOption.value);
      }
    }, pickerIndex);

    await new Promise(r => setTimeout(r, 3000)); // Wait for save
    await page.screenshot({ path: '/tmp/hierarchical-4-gas-final.png', fullPage: true });

    // Check final status display
    const finalStatus = await page.evaluate((idx) => {
      const picker = document.querySelectorAll('category-picker')[idx];
      const statusInput = picker.shadowRoot.querySelector('#status');
      return statusInput.value;
    }, pickerIndex);

    console.log(`📋 Final breadcrumb display: "${finalStatus}"`);
    console.log(`⚠️  Expected: "Utilities / Housing / Gas"`);

    console.log('\n📸 Screenshots saved to /tmp/hierarchical-*.png');
  }

  console.log('\n✅ Test complete - check screenshots');
  // Keep browser open
  await new Promise(() => {});
})();
