# Office Assistant Test Suite - TDD Documentation

## Overview

This test suite implements **Test-Driven Development (TDD)** methodology for the Office Assistant navigation reorganization. All tests are written in the **RED phase** (failing tests) to define requirements BEFORE implementation.

## Project Context

### Objective
Split the "Upload to Computer" tab into two separate, specialized tabs:
1. **Upload Bank Statement** (📤 icon) - Uses `upload-component` for PDF bank statement processing
2. **Scan Receipt** (📸 icon) - Uses `receipt-scanner` web component for receipt image processing

### Current State
- Application has NO test infrastructure configured
- These tests define the REQUIRED behavior before implementation
- All tests are EXPECTED TO FAIL until implementation is complete

### TDD Methodology

#### Phase 1: RED (Current Phase)
- Write failing tests that define expected behavior
- Tests describe the "what" without implementing the "how"
- All tests should fail when run
- **Status**: COMPLETE ✓

#### Phase 2: GREEN (Next Phase - After Implementation)
- Implement minimal code to make tests pass
- Refactor `index.html` to add new navigation buttons
- Update `app.js` to handle new sections
- Add `receipt-scanner.js` script loading
- **Status**: PENDING

#### Phase 3: REFACTOR (Final Phase)
- Optimize implementation while keeping tests green
- Improve code quality, performance, and maintainability
- Ensure WSL2 compatibility
- **Status**: PENDING

## Test Structure

```
tests/
├── README.md                               # This file
├── setup.js                                # Global test configuration
├── unit/                                   # Unit tests for isolated components
│   ├── navigation.test.js                  # Navigation structure tests
│   └── receipt-scanner-component.test.js   # Web component portability tests
└── integration/                            # Integration tests for sections
    ├── upload-bank-statement.test.js       # Upload Bank Statement section tests
    └── scan-receipt.test.js                # Scan Receipt section tests
```

## Test Files

### 1. Unit Tests

#### `tests/unit/navigation.test.js`
Tests the new navigation structure requirements:
- ✗ Should have exactly 3 navigation buttons (currently has wrong buttons)
- ✗ "Expense Categorizer" button with 💰 icon (exists but will verify)
- ✗ "Upload Bank Statement" button with 📤 icon (needs creation)
- ✗ "Scan Receipt" button with 📸 icon (needs creation)
- ✗ Should NOT have "Upload to Computer" button (currently exists)
- ✗ Should NOT have "Calendar" button in main nav (currently exists)
- ✗ Proper keyboard accessibility attributes
- ✗ Correct data-section attributes

**Expected Failures**: 10-12 tests

#### `tests/unit/receipt-scanner-component.test.js`
Tests web component portability and self-containment:
- ✗ Component registration as custom element
- ✗ Shadow DOM encapsulation (styles don't leak)
- ✗ Self-contained functionality (no external CSS/JS dependencies)
- ✗ Portable API (works with createElement and innerHTML)
- ✗ Independent state management for multiple instances
- ✗ Event bus integration for external communication
- ✗ Proper lifecycle management

**Expected Failures**: 15-18 tests

### 2. Integration Tests

#### `tests/integration/upload-bank-statement.test.js`
Tests "Upload Bank Statement" section integration:
- ✗ Section loads when button is clicked
- ✗ Displays iframe with `upload_pdf_statements.html`
- ✗ Shows loading state during transition
- ✗ Clears previous content before loading
- ✗ Applies correct CSS classes to content area
- ✗ Sets active state on navigation button
- ✗ Deactivates other navigation buttons
- ✗ Uses `upload-component` for functionality
- ✗ Handles iframe loading errors gracefully

**Expected Failures**: 8-10 tests

#### `tests/integration/scan-receipt.test.js`
Tests "Scan Receipt" section integration:
- ✗ Section loads when button is clicked
- ✗ Loads `receipt-scanner` web component (NOT iframe)
- ✗ Shows loading state during transition
- ✗ Includes `receipt-scanner.js` script in page
- ✗ Creates `<receipt-scanner>` custom element in DOM
- ✗ Renders web component directly (not in iframe)
- ✗ Applies correct CSS classes and styling
- ✗ Sets active state on navigation button
- ✗ Works independently from Upload Bank Statement section
- ✗ Properly initializes receipt-scanner component

**Expected Failures**: 10-13 tests

## Running Tests

### Prerequisites
```bash
# Install dependencies
npm install
```

### Test Commands

#### Run all tests (RED phase - expect failures)
```bash
npm test
```

#### Run tests in watch mode (for development)
```bash
npm run test:watch
```

#### Run tests with UI (interactive mode)
```bash
npm run test:ui
```

#### Run tests with coverage report
```bash
npm run test:coverage
```

### Expected Output (RED Phase)

When you run `npm test`, you should see:

```
 FAIL  tests/unit/navigation.test.js
  Navigation Structure - TDD RED Phase
    Navigation Button Count
      ✗ should have exactly 3 navigation buttons
    Upload Bank Statement Button
      ✗ should have Upload Bank Statement as second button with upload icon
      ✗ should NOT have "Upload to Computer" text
    Scan Receipt Button
      ✗ should have Scan Receipt as third button with camera icon
      ✗ should be inactive by default
    ...

 FAIL  tests/integration/upload-bank-statement.test.js
  Upload Bank Statement Section - TDD RED Phase
    Section Loading
      ✗ should load Upload Bank Statement section when button is clicked
      ✗ should display iframe with correct attributes
    ...

 FAIL  tests/integration/scan-receipt.test.js
  Scan Receipt Section - TDD RED Phase
    Section Loading
      ✗ should load Scan Receipt section when button is clicked
      ✗ should load receipt-scanner web component
    ...

 FAIL  tests/unit/receipt-scanner-component.test.js
  Receipt Scanner Component Portability - TDD RED Phase
    Component Registration
      ✗ should be registered as a custom element
      ✗ should extend HTMLElement
    ...

Test Files  4 failed (4)
     Tests  43 failed (43)
   Duration  2.34s
```

**This is EXPECTED and CORRECT for the RED phase!**

## What Tests Define

### Navigation Requirements
1. **3 Navigation Buttons**:
   - Expense Categorizer (💰)
   - Upload Bank Statement (📤)
   - Scan Receipt (📸)

2. **Removed Buttons**:
   - "Upload to Computer" (being split)
   - "Calendar" (removed for now)

3. **Button Attributes**:
   - `data-section="expenses"`, `"upload-bank-statement"`, `"scan-receipt"`
   - `data-active="true"` for active button
   - Proper `tabindex`, `aria-label`, and `title` attributes

### Upload Bank Statement Section
1. Loads `upload_pdf_statements.html` in an iframe
2. Uses existing `upload-component` functionality
3. Shows loading state during transitions
4. Handles iframe loading/errors properly
5. Updates navigation active states

### Scan Receipt Section
1. Loads `receipt-scanner` web component directly (NOT iframe)
2. Creates `<receipt-scanner>` custom element in content area
3. Includes `js/components/receipt-scanner.js` script
4. Works independently from other sections
5. Properly styled container for web component

### Receipt Scanner Component
1. Fully self-contained portable web component
2. Uses Shadow DOM for style encapsulation
3. No external CSS dependencies
4. Only external dependency: `event-bus.js` for communication
5. Multiple instances maintain independent state
6. Works with `createElement` and `innerHTML`

## Implementation Checklist

After tests are written (RED phase), implement in this order:

### Step 1: Update Navigation (index.html)
- [ ] Change second button from "Upload to Computer" to "Upload Bank Statement"
  - Change text to "Upload Bank Statement"
  - Update `data-section="upload-bank-statement"`
  - Keep 📤 icon
- [ ] Change third button from "Calendar" to "Scan Receipt"
  - Change text to "Scan Receipt"
  - Update `data-section="scan-receipt"`
  - Change icon to 📸
- [ ] Add `receipt-scanner.js` script to page

### Step 2: Update App Logic (js/app.js)
- [ ] Rename `loadUploadSection()` to `loadUploadBankStatementSection()`
- [ ] Update switch case from `'upload'` to `'upload-bank-statement'`
- [ ] Create new `loadScanReceiptSection()` method
- [ ] Add `'scan-receipt'` case to switch statement
- [ ] Ensure proper content clearing and CSS class management

### Step 3: Implement Scan Receipt Section
- [ ] Create `<receipt-scanner>` custom element in content area
- [ ] Style container with proper Tailwind classes
- [ ] Ensure web component loads and initializes
- [ ] Verify independence from other sections

### Step 4: Run Tests (GREEN Phase)
```bash
npm test
```
All 43 tests should now PASS!

### Step 5: Refactor & Optimize
- [ ] Optimize loading performance
- [ ] Ensure WSL2 compatibility
- [ ] Add error handling improvements
- [ ] Code cleanup and documentation
- [ ] Keep all tests passing!

## Test-Driven Benefits

### Why TDD for This Project?

1. **Clear Requirements**: Tests document exactly what needs to change
2. **Confidence**: Know when implementation is complete (all tests pass)
3. **Regression Prevention**: Ensure existing features still work
4. **Refactoring Safety**: Optimize code while keeping tests green
5. **Living Documentation**: Tests show how components should work

### TDD Workflow

```
┌─────────────────────────────────────────────────┐
│  RED: Write Failing Tests (Current Phase)      │
│  - Define requirements as tests                 │
│  - All tests fail (expected)                    │
│  - Commit tests to repository                   │
└─────────────┬───────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│  GREEN: Implement Minimal Code                  │
│  - Write just enough code to pass tests         │
│  - Focus on making tests pass, not perfection   │
│  - All tests should now pass                    │
└─────────────┬───────────────────────────────────┘
              │
              ▼
┌─────────────────────────────────────────────────┐
│  REFACTOR: Optimize & Clean Up                  │
│  - Improve code quality                          │
│  - Add performance optimizations                 │
│  - Keep tests passing throughout                │
└─────────────────────────────────────────────────┘
```

## Configuration Files

### `vitest.config.js`
- Uses `jsdom` environment for DOM testing
- Includes both `tests/` and `.claude-collective/tests/` directories
- Loads `tests/setup.js` for global configuration
- Coverage reporting with v8 provider

### `package.json`
- Test scripts: `test`, `test:watch`, `test:ui`, `test:coverage`
- Dev dependencies: `vitest`, `jsdom`, `@vitest/ui`

### `tests/setup.js`
- Global test utilities and mocks
- DOM cleanup between tests
- Console spies to reduce noise
- localStorage and sessionStorage mocks
- window.matchMedia mock for responsive testing

## Troubleshooting

### Tests Won't Run
```bash
# Ensure dependencies are installed
npm install

# Check Node.js version (requires Node 18+)
node --version
```

### All Tests Pass (Unexpected in RED Phase)
This means implementation already exists or tests need adjustment. Review test assertions.

### Import Errors
The tests use ES modules. Ensure `"type": "module"` is in `package.json`.

### JSDOM Errors
Some browser APIs may not be available in JSDOM. Check `tests/setup.js` for mocks.

## Next Steps

1. **Review Tests**: Read through all test files to understand requirements
2. **Run Tests**: Execute `npm test` to see RED phase (all failures)
3. **Implement**: Follow implementation checklist above
4. **Validate**: Run tests again - should see GREEN phase (all passing)
5. **Refactor**: Optimize while keeping tests green

## Contact & Support

For questions about the test suite or TDD methodology, refer to:
- Vitest Documentation: https://vitest.dev/
- TDD Best Practices: https://martinfowler.com/bliki/TestDrivenDevelopment.html
- Web Components Testing: https://open-wc.org/docs/testing/testing-package/

---

**Remember**: Tests failing is GOOD in the RED phase. It means we've clearly defined what needs to be built!
