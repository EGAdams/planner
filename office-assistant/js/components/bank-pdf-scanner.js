import '../category-picker.js';

class BankPdfScanner extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.transactions = [
            { id: 'txn-1', description: 'Opening balance check', amount: 150.0 },
            { id: 'txn-2', description: 'Groceries', amount: -45.75 },
            { id: 'txn-3', description: 'Utilities', amount: -62.1 }
        ];
        this.categoryPickers = [];
        this.calculatedTotal = 0;
        this.fileName = '';
        this.apiBase = this._computeApiBase();
        this.apiEndpoint = `${this.apiBase}/parse-bank-pdf`;
        this.shadowRoot.innerHTML = `
            <style>
                :host {
                    display: block;
                    font-family: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
                    color: #0f172a;
                }
                .panel {
                    background: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                    padding: 16px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.06);
                }
                h2 {
                    margin: 0 0 8px 0;
                    font-size: 1.25rem;
                }
                .status {
                    margin: 0 0 12px 0;
                    padding: 8px 12px;
                    border-radius: 8px;
                    font-size: 0.95rem;
                }
                .status.warning {
                    background: #fff7ed;
                    border: 1px solid #fdba74;
                    color: #9a3412;
                }
                .status.ok {
                    background: #ecfdf3;
                    border: 1px solid #4ade80;
                    color: #166534;
                }
                .drop-area {
                    border: 2px dashed #cbd5e1;
                    border-radius: 10px;
                    padding: 14px;
                    background: #fff;
                    cursor: pointer;
                    transition: border-color 0.2s ease, background 0.2s ease;
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 12px;
                    margin-bottom: 10px;
                }
                .drop-area:hover {
                    border-color: #94a3b8;
                    background: #f8fafc;
                }
                .drop-area.highlight {
                    border-color: #2563eb;
                    background: #eff6ff;
                }
                .drop-text {
                    display: flex;
                    flex-direction: column;
                    gap: 4px;
                }
                .drop-text strong {
                    font-size: 0.98rem;
                    color: #0f172a;
                }
                .file-pill {
                    padding: 6px 10px;
                    background: #e2e8f0;
                    border-radius: 999px;
                    font-size: 0.85rem;
                    color: #0f172a;
                }
                .loading {
                    font-size: 0.9rem;
                    color: #0f172a;
                }
                .error {
                    color: #b91c1c;
                    background: #fef2f2;
                    border: 1px solid #fecdd3;
                    padding: 8px 10px;
                    border-radius: 8px;
                    margin-bottom: 8px;
                    font-size: 0.9rem;
                }
                .totals {
                    display: flex;
                    gap: 16px;
                    align-items: center;
                    flex-wrap: wrap;
                    margin-bottom: 12px;
                }
                .totals label {
                    display: flex;
                    flex-direction: column;
                    font-size: 0.9rem;
                    color: #0f172a;
                }
                .totals input {
                    padding: 8px;
                    border-radius: 8px;
                    border: 1px solid #cbd5e1;
                    margin-top: 4px;
                    min-width: 160px;
                }
                .calculated-total {
                    background: #e2e8f0;
                    padding: 10px 12px;
                    border-radius: 8px;
                    font-weight: 600;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    background: white;
                    border: 1px solid #e2e8f0;
                }
                th, td {
                    padding: 10px;
                    border-bottom: 1px solid #e2e8f0;
                    text-align: left;
                }
                th {
                    background: #f1f5f9;
                    font-weight: 600;
                    color: #0f172a;
                }
                tr:last-child td {
                    border-bottom: none;
                }
                .transaction-row input[type="text"],
                .transaction-row input[type="number"] {
                    width: 100%;
                    padding: 8px;
                    border: 1px solid #cbd5e1;
                    border-radius: 8px;
                }
                .category-cell category-picker[disabled] {
                    opacity: 0.6;
                    pointer-events: none;
                }
                .note {
                    margin-top: 12px;
                    font-size: 0.9rem;
                    color: #475569;
                }
                .actions {
                    margin-top: 10px;
                    display: flex;
                    gap: 8px;
                }
                button.secondary {
                    border: 1px solid #cbd5e1;
                    background: white;
                    padding: 8px 12px;
                    border-radius: 8px;
                    cursor: pointer;
                }
                button.secondary:hover {
                    background: #f8fafc;
                }
            </style>
            <div class="panel">
                <h2>Scan Bank PDF</h2>
                <div class="error" id="error" style="display:none;"></div>
                <div class="drop-area" id="dropArea">
                    <div class="drop-text">
                        <strong>Upload or drop a PDF bank statement</strong>
                        <span>We’ll parse it with Docling, then fall back to Gemini if needed.</span>
                    </div>
                    <div class="file-pill" id="fileName">No file selected</div>
                    <input type="file" id="fileInput" accept="application/pdf" style="display:none;" />
                </div>
                <div class="loading" id="loading" style="display:none;">Parsing PDF, please wait…</div>
                <p class="status warning" data-testid="status-text">
                    Totals must balance before you can start categorizing.
                </p>
                <div class="totals">
                    <label>
                        Statement Total
                        <input type="number" step="0.01" data-testid="statement-total" aria-label="Statement total">
                    </label>
                    <div class="calculated-total">
                        Calculated Total:
                        <span data-testid="calculated-total">${this.formatCurrency(this.calculatedTotal)}</span>
                    </div>
                    <button class="secondary" id="rebalance">Recalculate</button>
                </div>
                <div class="table-wrapper">
                    <table>
                        <thead>
                            <tr>
                                <th>Description</th>
                                <th>Amount</th>
                                <th>Category</th>
                            </tr>
                        </thead>
                        <tbody id="rows"></tbody>
                    </table>
                </div>
                <div class="actions">
                    <button class="secondary" id="addRow">Add Row</button>
                    <button class="secondary" id="autoBalance">Set statement to calculated total</button>
                </div>
                <p class="note">Category pickers stay disabled until the calculated total matches your statement total.</p>
            </div>
        `;
    }

    connectedCallback() {
        this.rowsEl = this.shadowRoot.getElementById('rows');
        this.statusEl = this.shadowRoot.querySelector('[data-testid="status-text"]');
        this.statementTotalInput = this.shadowRoot.querySelector('input[data-testid="statement-total"]');
        this.calculatedTotalEl = this.shadowRoot.querySelector('[data-testid="calculated-total"]');
        this.rebalanceBtn = this.shadowRoot.getElementById('rebalance');
        this.addRowBtn = this.shadowRoot.getElementById('addRow');
        this.autoBalanceBtn = this.shadowRoot.getElementById('autoBalance');
        this.dropArea = this.shadowRoot.getElementById('dropArea');
        this.fileInput = this.shadowRoot.getElementById('fileInput');
        this.loadingEl = this.shadowRoot.getElementById('loading');
        this.errorEl = this.shadowRoot.getElementById('error');
        this.fileNameEl = this.shadowRoot.getElementById('fileName');

        this.statementTotalInput.addEventListener('input', () => this.updateBalanceState());
        this.rebalanceBtn.addEventListener('click', () => this.updateTotals());
        this.addRowBtn.addEventListener('click', () => this.addTransaction());
        this.autoBalanceBtn.addEventListener('click', () => {
            this.statementTotalInput.value = this.calculatedTotal.toFixed(2);
            this.updateBalanceState();
        });
        this.dropArea.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', (e) => {
            const file = e.target.files?.[0];
            if (file) this._handleFile(file);
        });
        this.dropArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.dropArea.classList.add('highlight');
        });
        this.dropArea.addEventListener('dragleave', () => {
            this.dropArea.classList.remove('highlight');
        });
        this.dropArea.addEventListener('drop', (e) => {
            e.preventDefault();
            this.dropArea.classList.remove('highlight');
            const file = e.dataTransfer?.files?.[0];
            if (file) this._handleFile(file);
        });

        this.renderRows();
        this.updateTotals();
    }

    async _handleFile(file) {
        if (file.type !== 'application/pdf') {
            this._setError('Please upload a PDF file.');
            return;
        }
        this._setError('');
        this._setLoading(true);
        try {
            const formData = new FormData();
            formData.append('file', file);
            const res = await fetch(this.apiEndpoint, { method: 'POST', body: formData });
            if (!res.ok) {
                const message = await res.text();
                throw new Error(message || `Parse failed (${res.status})`);
            }
            const data = await res.json();
            this.fileName = file.name;
            this.fileNameEl.textContent = this.fileName;
            const parsed = Array.isArray(data.transactions) ? data.transactions : [];
            const hasStatementTotal = data?.totals?.statement_total !== undefined && data.totals.statement_total !== null;
            if (parsed.length) {
                this.transactions = parsed.map((txn, idx) => ({
                    id: txn.id || `txn-${idx}`,
                    description: txn.description || '',
                    amount: Number(txn.amount) || 0
                }));
            } else {
                this.transactions = [{ id: 'txn-1', description: 'No transactions found', amount: 0 }];
            }
            if (hasStatementTotal) {
                this.statementTotalInput.value = Number(data.totals.statement_total);
            }
            this.renderRows();
            this.updateTotals();
            if (!hasStatementTotal) {
                this.statementTotalInput.value = this.calculatedTotal.toFixed(2);
                this.updateBalanceState();
            }
        } catch (err) {
            // Surface endpoint for easier debugging when backend is unreachable
            const prefix = this.apiEndpoint ? `(${this.apiEndpoint}) ` : '';
            this._setError(`${prefix}${err?.message || 'Failed to parse PDF.'}`);
        } finally {
            this._setLoading(false);
        }
    }

    _setLoading(on) {
        this.loadingEl.style.display = on ? 'block' : 'none';
        this.dropArea.classList.toggle('highlight', on);
        this.dropArea.style.pointerEvents = on ? 'none' : 'auto';
    }

    _setError(msg) {
        if (!msg) {
            this.errorEl.style.display = 'none';
            this.errorEl.textContent = '';
            return;
        }
        this.errorEl.style.display = 'block';
        this.errorEl.textContent = msg;
    }

    addTransaction() {
        this.transactions.push({
            id: `txn-${Date.now()}`,
            description: 'Manual entry',
            amount: 0
        });
        this.renderRows();
        this.updateTotals();
    }

    renderRows() {
        this.categoryPickers = [];
        this.rowsEl.innerHTML = '';
        this.transactions.forEach((txn, index) => {
            const row = document.createElement('tr');
            row.className = 'transaction-row';

            const descTd = document.createElement('td');
            const descInput = document.createElement('input');
            descInput.type = 'text';
            descInput.value = txn.description;
            descInput.dataset.testid = 'description';
            descInput.addEventListener('input', (e) => {
                txn.description = e.target.value;
            });
            descTd.appendChild(descInput);

            const amtTd = document.createElement('td');
            const amtInput = document.createElement('input');
            amtInput.type = 'number';
            amtInput.step = '0.01';
            amtInput.value = txn.amount;
            amtInput.dataset.testid = 'amount';
            amtInput.addEventListener('input', (e) => {
                const val = parseFloat(e.target.value);
                txn.amount = Number.isFinite(val) ? val : 0;
                this.updateTotals();
            });
            amtTd.appendChild(amtInput);

            const catTd = document.createElement('td');
            catTd.className = 'category-cell';
            const picker = document.createElement('category-picker');
            picker.setAttribute('data-src', './data/categories.json');
            picker.setAttribute('expense-id', txn.id);
            picker.setAttribute('placeholder', 'Choose category');
            this.categoryPickers.push(picker);
            catTd.appendChild(picker);

            row.appendChild(descTd);
            row.appendChild(amtTd);
            row.appendChild(catTd);
            this.rowsEl.appendChild(row);

            // Positionally mark first row to align with tests
            if (index === 0) {
                row.dataset.testid = 'first-row';
            }
        });
        this.updateBalanceState();
    }

    updateTotals() {
        this.calculatedTotal = this.transactions.reduce((sum, txn) => {
            const val = Number(txn.amount) || 0;
            return sum + val;
        }, 0);
        const currentStatementVal = parseFloat(this.statementTotalInput?.value ?? '');
        if (!Number.isFinite(currentStatementVal)) {
            if (this.statementTotalInput) {
                this.statementTotalInput.value = this.calculatedTotal.toFixed(2);
            }
        }
        if (this.calculatedTotalEl) {
            this.calculatedTotalEl.textContent = this.formatCurrency(this.calculatedTotal);
        }
        this.updateBalanceState();
    }

    updateBalanceState() {
        const expectedTotal = parseFloat(this.statementTotalInput?.value ?? '');
        const expectedRounded = Number.isFinite(expectedTotal) ? Number(expectedTotal.toFixed(2)) : NaN;
        const calculatedRounded = Number(this.calculatedTotal.toFixed(2));
        const isBalanced = Number.isFinite(expectedRounded) && Math.abs(expectedRounded - calculatedRounded) < 0.001;
        const statusClass = isBalanced ? 'status ok' : 'status warning';
        const statusText = isBalanced
            ? 'Totals balanced — categorization unlocked.'
            : 'Totals do not match yet. Category pickers are locked.';

        if (this.statusEl) {
            this.statusEl.className = statusClass;
            this.statusEl.textContent = statusText;
        }

        this.categoryPickers.forEach(picker => {
            picker.toggleAttribute('disabled', !isBalanced);
        });
    }

    formatCurrency(value) {
        if (!Number.isFinite(value)) return '$0.00';
        return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(value);
    }

    _computeApiBase() {
        // Allow global override for unusual deployments
        if (window.APP_API_BASE) return window.APP_API_BASE.replace(/\/$/, '');

        const { protocol, hostname, port } = window.location;

        // If running from file:// or no host, default to local backend
        if (!hostname || protocol === 'file:') {
            return 'http://localhost:8080/api';
        }

        // mirror receipt-scanner logic: if frontend on 8081/8000, target 8080 API
        if (port === '8081' || port === '8000') {
            return `${protocol}//${hostname}:8080/api`;
        }
        if (port && port !== '') {
            return `${protocol}//${hostname}:${port}/api`;
        }
        return `${protocol}//${hostname}/api`;
    }
}

try {
    if (typeof globalThis !== 'undefined') {
        globalThis.BankPdfScanner = BankPdfScanner;
    }
} catch (_e) {
    // noop
}

customElements.define('bank-pdf-scanner', BankPdfScanner);
