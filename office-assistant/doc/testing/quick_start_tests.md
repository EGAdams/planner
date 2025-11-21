# Quick Start - TDD Test Infrastructure

## IMMEDIATE COMMANDS

### View Current Test Status (RED Phase)
```bash
npm test
```

**Expected Output**:
```
Test Files  4 failed | 4 passed (8)
      Tests  45 failed | 56 passed (101)
```
This is CORRECT! Tests should fail before implementation.

### Watch Mode (Recommended for Development)
```bash
npm run test:watch
```
Auto-runs tests when files change.

### Interactive UI
```bash
npm run test:ui
```
Opens browser with test UI at http://localhost:51204

### Coverage Report
```bash
npm run test:coverage
```
Shows which code is covered by tests.

---

## WHAT TESTS DEFINE

### Required Changes to index.html
Change navigation buttons from:
```html
<button data-section="expenses">💰 Expense Categorizer</button>
<button data-section="upload">📤 Upload to Computer</button>
<button data-section="calendar">📅 Calendar</button>
```

To:
```html
<button data-section="expenses">💰 Expense Categorizer</button>
<button data-section="upload-bank-statement">📤 Upload Bank Statement</button>
<button data-section="scan-receipt">📸 Scan Receipt</button>
```

### Required Changes to js/app.js
1. Rename `loadUploadSection()` → `loadUploadBankStatementSection()`
2. Update switch case: `'upload'` → `'upload-bank-statement'`
3. Add new method: `loadScanReceiptSection()`
4. Add switch case: `'scan-receipt'`

### New Section Implementation
```javascript
loadScanReceiptSection() {
  const contentArea = document.getElementById('content-area');
  contentArea.className = 'bg-white rounded-lg shadow-md p-4 min-h-[70vh]';
  contentArea.innerHTML = `
    <div class="fade-in">
      <receipt-scanner></receipt-scanner>
    </div>
  `;
}
```

---

## WHEN TESTS PASS (GREEN Phase)

All 45 failing tests should turn green when:
1. Navigation has correct 3 buttons
2. "Upload Bank Statement" loads upload_pdf_statements.html
3. "Scan Receipt" loads receipt-scanner web component
4. Old "Upload to Computer" button is removed
5. Calendar button is removed from main nav

**Run `npm test` after each change to see progress!**

---

## DETAILED DOCUMENTATION

See `/home/adamsl/planner/office-assistant/tests/README.md` for:
- Complete TDD methodology explanation
- Detailed test descriptions
- Troubleshooting guide
- Implementation checklist

See `/home/adamsl/planner/office-assistant/TDD_INFRASTRUCTURE_DELIVERY.md` for:
- Full delivery report
- Test execution results
- File locations
- Verification details

---

## TEST FILE LOCATIONS

```
tests/
├── setup.js                                # Global test config
├── README.md                               # Full documentation
├── unit/
│   ├── navigation.test.js                  # Navigation structure tests
│   └── receipt-scanner-component.test.js   # Web component tests
└── integration/
    ├── upload-bank-statement.test.js       # Upload section tests
    └── scan-receipt.test.js                # Scan section tests
```

---

**Remember**: Failing tests in RED phase = GOOD! They define what needs to be built.
