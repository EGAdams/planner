import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    include: [
      'tests/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}',
      '.claude-collective/tests/**/*.{test,spec}.{js,mjs,cjs,ts,mts,cts,jsx,tsx}'
    ],
    exclude: [
      'tests/browser/**',
      'tests/integration/scan-receipt.test.js',
      'tests/integration/upload-bank-statement.test.js',
      'tests/unit/receipt-scanner-component.test.js',
      'tests/unit/receipt-table-category-picker.test.js',
      'tests/unit/receipt-items-api.test.js'
    ],
    setupFiles: ['./tests/setup.js'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: [
        'node_modules/',
        'tests/',
        '**/*.test.js',
        '**/*.spec.js'
      ]
    },
    deps: {
      external: ['fs-extra']
    }
  }
});
