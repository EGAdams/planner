import { describe, it, expect, beforeEach, vi } from 'vitest';
import { JSDOM } from 'jsdom';

const loadComponent = async (port = '8000') => {
  const dom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {
    url: `http://localhost:${port}/`,
  });

  global.window = dom.window;
  global.document = dom.window.document;
  global.HTMLElement = dom.window.HTMLElement;
  global.customElements = dom.window.customElements;

  // Defer import until globals are ready
  await import('../../js/components/receipt-scanner.js');

  const element = document.createElement('receipt-scanner');
  document.body.appendChild(element);
  return element;
};

describe('receipt-scanner API routing', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
  });

  it('uses :8080/api base when UI served from :8000', async () => {
    const component = await loadComponent('8000');

    // Provide minimal category option and parsed item
    component.categoryOptions = [
      { label: 'Food', _original: { id: 10 } },
    ];
    component.parsedData = {
      transaction_date: '2024-01-01',
      payment_method: 'CARD',
      party: { merchant_name: 'Test Store' },
      items: [
        { description: 'Lunch', quantity: 1, unit_price: 10, line_total: 10 },
      ],
    };

    // Mock fetch and inspect the first call
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ expense_id: 123 }),
    });
    vi.stubGlobal('fetch', fetchMock);

    await component._handleCategorySelection(0, { label: 'Food', path: ['Food'] });

    expect(fetchMock).toHaveBeenCalled();
    const url = fetchMock.mock.calls[0][0];
    expect(url).toBe('http://localhost:8080/api/receipt-items');
  });

  it('updates existing expense ID with category', async () => {
    const component = await loadComponent('8080');

    component.categoryOptions = [
      { label: 'Supplies', _original: { id: 22 } },
    ];
    component.parsedData = {
      transaction_date: '2024-02-02',
      payment_method: 'CARD',
      party: { merchant_name: 'Tools' },
      items: [
        { description: 'Hammer', quantity: 1, unit_price: 5, line_total: 5, expense_id: 999 },
      ],
    };

    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({}),
    });
    vi.stubGlobal('fetch', fetchMock);

    await component._handleCategorySelection(0, { label: 'Supplies', path: ['Supplies'] });

    expect(fetchMock).toHaveBeenCalled();
    const [url] = fetchMock.mock.calls[0];
    expect(url).toBe('http://localhost:8080/api/expenses/999/category');
  });
});
