const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();
  page.on('console', msg => console.log('🪵', msg.text()));

  await page.goto('http://localhost:8080/office/daily_expense_categorizer.html', {
    waitUntil: 'networkidle0'
  });

  await page.waitForSelector('#mainTable', { visible: true });
  await new Promise(r => setTimeout(r, 2000));

  const initialDate = await page.$eval('#dateText', el => el.textContent);
  console.log(`📅 Starting date: ${initialDate}`);

  // Find and categorize first uncategorized
  const categorized = await page.evaluate(() => {
    const pickers = document.querySelectorAll('category-picker');
    for (let picker of pickers) {
      const select = picker.shadowRoot.querySelector('select');
      if (!select.value || select.value === '') {
        const options = select.querySelectorAll('option');
        if (options.length > 1) {
          select.value = options[1].value;
          select.dispatchEvent(new Event('change', { bubbles: true }));
          return true;
        }
      }
    }
    return false;
  });

  if (categorized) {
    console.log('✅ Categorized an expense');
    await new Promise(r => setTimeout(r, 3000)); // Wait for API + reload

    // Navigate to FIRST day
    console.log('⏮️ Navigating to first day...');
    await page.click('#firstBtn');
    await new Promise(r => setTimeout(r, 1500));

    const firstDate = await page.$eval('#dateText', el => el.textContent);
    console.log(`📅 First date: ${firstDate}`);

    // Navigate back to LAST day (where we categorized)
    console.log('⏭️ Navigating back to last day...');
    await page.click('#lastBtn');
    await new Promise(r => setTimeout(r, 1500));

    const backDate = await page.$eval('#dateText', el => el.textContent);
    console.log(`📅 Back to: ${backDate}`);

    if (backDate === initialDate) {
      // Check if the category persisted - check both value and visual state
      const stillCategorized = await page.evaluate(() => {
        const pickers = document.querySelectorAll('category-picker');
        let categorizedCount = 0;
        for (let picker of pickers) {
          // Check if picker has data-state="done" attribute (green background)
          if (picker.getAttribute('data-state') === 'done') {
            categorizedCount++;
          }
        }
        console.log(`Found ${pickers.length} pickers, ${categorizedCount} in 'done' state`);
        return categorizedCount;
      });

      console.log(`✅ Found ${stillCategorized} categorized expenses after navigation`);
      console.log(stillCategorized > 0 ? '🎉 CATEGORIES PERSIST!' : '❌ Categories lost');
    } else {
      console.log(`⚠️ Didn't return to same date (expected ${initialDate}, got ${backDate})`);
    }
  }

  await browser.close();
})();
