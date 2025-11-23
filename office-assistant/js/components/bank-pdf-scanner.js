import '../category-picker.js';

class BankPdfScanner extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.transactions = [
            { id: 'txn-1', description: 'Opening balance check', amount: -150.0, bank_item_type: 'WITHDRAWAL' },
            { id: 'txn-2', description: 'Groceries', amount: -45.75, bank_item_type: 'WITHDRAWAL' },
            { id: 'txn-3', description: 'Utilities', amount: -62.1, bank_item_type: 'WITHDRAWAL' }
        ];
        this.allTransactions = [...this.transactions];
        this.transactions = this._filterDisplayTransactions(this.allTransactions);
        this.categoryPickers = [];
        this.calculatedTotal = this._computeNetTotal(this.allTransactions);
        this.accountSummary = null;
        this.breakdown = this._computeBreakdown(this.allTransactions);
        this.verification = { passes: false, issues: [], ending: null };
        this.hasParsed = false;
        this.backendIssues = [];
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
                .summary-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
                    gap: 12px;
                    margin: 12px 0 10px;
                }
                .summary-card {
                    background: #fff;
                    border: 1px solid #e2e8f0;
                    border-radius: 10px;
                    padding: 12px;
                    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
                }
                .summary-card h3 {
                    margin: 0 0 8px 0;
                    font-size: 1rem;
                    color: #0f172a;
                }
                .summary-row {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 4px 0;
                    font-size: 0.95rem;
                }
                .summary-row span.value {
                    font-weight: 600;
                }
                .summary-row.mismatch span.value {
                    color: #b91c1c;
                }
                .pill {
                    display: inline-block;
                    padding: 4px 8px;
                    border-radius: 999px;
                    font-size: 0.82rem;
                    background: #e2e8f0;
                    color: #0f172a;
                }
                .pill.mismatch {
                    background: #fee2e2;
                    color: #991b1b;
                    border: 1px solid #fecdd3;
                }
                .issues {
                    margin: 4px 0 12px;
                    color: #991b1b;
                    background: #fef2f2;
                    border: 1px solid #fecdd3;
                    border-radius: 8px;
                    padding: 8px 10px;
                    font-size: 0.9rem;
                }
                .issues.hidden { display: none; }
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
                <div class="summary-grid">
                    <div class="summary-card" data-testid="account-summary-card">
                        <h3>Account Summary (Statement)</h3>
                        <div class="summary-row"><span>Beginning Balance</span><span class="value" data-testid="account-beginning">--</span></div>
                        <div class="summary-row"><span>Ending Balance</span><span class="value" data-testid="account-ending">--</span></div>
                        <div class="summary-row"><span>Checks</span><span class="value" data-testid="account-checks">--</span></div>
                        <div class="summary-row"><span>Withdrawals / Debits</span><span class="value" data-testid="account-withdrawals">--</span></div>
                        <div class="summary-row"><span>Deposits / Credits</span><span class="value" data-testid="account-deposits">--</span></div>
                    </div>
                    <div class="summary-card" data-testid="calculated-summary-card">
                        <h3>Calculated Summary (Parsed)</h3>
                        <div class="summary-row"><span>Ending Balance (calculated)</span><span class="value" data-testid="calc-ending">--</span></div>
                        <div class="summary-row"><span>Checks</span><span class="value" data-testid="calc-checks">--</span></div>
                        <div class="summary-row"><span>Withdrawals / Debits</span><span class="value" data-testid="calc-withdrawals">--</span></div>
                        <div class="summary-row"><span>Deposits / Credits</span><span class="value" data-testid="calc-deposits">--</span></div>
                    </div>
                </div>
                <div class="issues hidden" data-testid="verification-issues"></div>
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
                </div>
                <p class="note">Category pickers stay disabled until the statement summary matches the parsed summary.</p>
            </div>
        `;
    }

    connectedCallback() {
        this.rowsEl = this.shadowRoot.getElementById('rows');
        this.statusEl = this.shadowRoot.querySelector('[data-testid="status-text"]');
        this.issuesEl = this.shadowRoot.querySelector('[data-testid="verification-issues"]');
        this.addRowBtn = this.shadowRoot.getElementById('addRow');
        this.dropArea = this.shadowRoot.getElementById('dropArea');
        this.fileInput = this.shadowRoot.getElementById('fileInput');
        this.loadingEl = this.shadowRoot.getElementById('loading');
        this.errorEl = this.shadowRoot.getElementById('error');
        this.fileNameEl = this.shadowRoot.getElementById('fileName');

        this.addRowBtn.addEventListener('click', () => this.addTransaction());
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
            this.hasParsed = true;
            this.backendIssues = data?.verification?.errors || [];
            this.fileName = file.name;
            this.fileNameEl.textContent = this.fileName;
            const parsed = Array.isArray(data.transactions) ? data.transactions : [];
            const accountSummary = data?.account_info?.summary || data?.verification?.expected || null;
            const hasStatementTotal = data?.totals?.statement_total !== undefined && data.totals.statement_total !== null;
            const knownStatementTotal = hasStatementTotal
                ? data.totals.statement_total
                : accountSummary?.ending_balance;

            if (parsed.length) {
                this.allTransactions = parsed.map((txn, idx) => ({
                    id: txn.id || `txn-${idx}`,
                    description: txn.description || '',
                    amount: Number(txn.amount) || 0,
                    bank_item_type: txn.bank_item_type || txn.transaction_type || '',
                }));
            } else {
                this.allTransactions = [{ id: 'txn-1', description: 'No transactions found', amount: 0, bank_item_type: 'WITHDRAWAL' }];
            }
            this.transactions = this._filterDisplayTransactions(this.allTransactions);
            this.accountSummary = accountSummary;
            const apiBreakdown = data?.verification?.calculated;
            this.breakdown = apiBreakdown && Object.keys(apiBreakdown).length
                ? apiBreakdown
                : this._computeBreakdown(this.allTransactions);
            this.calculatedTotal = this._computeNetTotal(this.allTransactions);
            this.verification = this._evaluateVerification();
            this.renderRows();
            this.updateTotals();
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
        const newTxn = {
            id: `txn-${Date.now()}`,
            description: 'Manual entry',
            amount: 0,
            bank_item_type: 'WITHDRAWAL',
        };
        this.transactions.push(newTxn);
        this.allTransactions.push(newTxn);
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
        const filteredAll = this._filterDisplayTransactions(this.allTransactions || []);
        const hasDisplay = Array.isArray(this.transactions) && this.transactions.length;
        if (hasDisplay && (!this.allTransactions || filteredAll.length !== this.transactions.length)) {
            const deposits = (this.allTransactions || []).filter(txn => this._isDeposit(txn));
            this.allTransactions = [...this.transactions, ...deposits];
        }

        const sourceTxns = this.allTransactions?.length ? this.allTransactions : this.transactions;
        this.transactions = this._filterDisplayTransactions(sourceTxns);
        this.calculatedTotal = this._computeNetTotal(sourceTxns);
        this.breakdown = this._computeBreakdown(sourceTxns);
        this.verification = this._evaluateVerification();
        this.renderSummaries();
        this.updateBalanceState();
    }

    updateBalanceState() {
        if (!this.hasParsed) {
            if (this.statusEl) {
                this.statusEl.className = 'status warning';
                this.statusEl.textContent = 'Upload a bank statement to verify.';
            }
            this.categoryPickers.forEach(picker => {
                picker.toggleAttribute('disabled', true);
            });
            if (this.issuesEl) {
                this.issuesEl.classList.add('hidden');
                this.issuesEl.textContent = '';
            }
            return;
        }
        const summary = this.verification || { passes: false, issues: [] };
        const passes = !!summary.passes;
        const issues = summary.issues || [];
        const statusClass = passes ? 'status ok' : 'status warning';
        const statusText = passes
            ? 'Statement summary verified. Category pickers unlocked.'
            : `Verification locked: ${issues.join(', ') || 'summary mismatch'}.`;

        if (this.statusEl) {
            this.statusEl.className = statusClass;
            this.statusEl.textContent = statusText;
        }

        this.categoryPickers.forEach(picker => {
            picker.toggleAttribute('disabled', !passes);
        });
    }

    _computeNetTotal(transactions = []) {
        return transactions.reduce((sum, txn) => {
            const val = Number(txn?.amount);
            return sum + (Number.isFinite(val) ? val : 0);
        }, 0);
    }

    _computeBreakdown(transactions = []) {
        const breakdown = {
            checks: { count: 0, total: 0 },
            withdrawals: { count: 0, total: 0 },
            deposits: { count: 0, total: 0 }
        };

        transactions.forEach(txn => {
            const amount = Number(txn?.amount);
            if (!Number.isFinite(amount)) return;
            if (this._isCheck(txn)) {
                breakdown.checks.count += 1;
                breakdown.checks.total += Math.abs(amount);
            } else if (this._isDeposit(txn)) {
                breakdown.deposits.count += 1;
                breakdown.deposits.total += Math.abs(amount);
            } else {
                breakdown.withdrawals.count += 1;
                breakdown.withdrawals.total += Math.abs(amount);
            }
        });

        breakdown.checks.total = Number(breakdown.checks.total.toFixed(2));
        breakdown.withdrawals.total = Number(breakdown.withdrawals.total.toFixed(2));
        breakdown.deposits.total = Number(breakdown.deposits.total.toFixed(2));
        return breakdown;
    }

    _evaluateVerification() {
        if (!this.hasParsed) {
            return { passes: false, issues: [], ending_calculated: null, expected: this.accountSummary, calculated: this.breakdown };
        }
        const close = (a, b, tol = 0.01) => Number.isFinite(a) && Number.isFinite(b) && Math.abs(a - b) <= tol;
        const summary = this.accountSummary && Object.keys(this.accountSummary || {}).length ? this.accountSummary : null;
        const breakdown = this.breakdown || this._computeBreakdown(this.allTransactions || this.transactions || []);

        const beginningBalance = summary?.beginning_balance;
        const endingBalance = summary?.ending_balance;
        const endingCalculated = Number.isFinite(beginningBalance)
            ? Number((beginningBalance - breakdown.checks.total - breakdown.withdrawals.total + breakdown.deposits.total).toFixed(2))
            : null;

        const issues = [...(this.backendIssues || [])];
        if (!summary) {
            issues.push('No account summary detected in PDF');
        } else {
            ['checks', 'withdrawals', 'deposits'].forEach(key => {
                const expectedGroup = summary[key] || {};
                const expectedCount = expectedGroup.count;
                const expectedTotal = expectedGroup.total;
                if (expectedCount !== undefined && expectedCount !== null && expectedCount !== breakdown[key].count) {
                    issues.push(`${key} count mismatch (${breakdown[key].count} vs ${expectedCount})`);
                }
                if (expectedTotal !== undefined && expectedTotal !== null && !close(expectedTotal, breakdown[key].total)) {
                    issues.push(`${key} total mismatch (${breakdown[key].total.toFixed(2)} vs ${expectedTotal.toFixed(2)})`);
                }
            });

            if (endingBalance !== undefined && endingBalance !== null && endingCalculated !== null && !close(endingBalance, endingCalculated)) {
                issues.push(`ending balance mismatch (${endingCalculated.toFixed(2)} vs ${Number(endingBalance).toFixed(2)})`);
            }
        }

        return {
            passes: issues.length === 0,
            issues,
            ending_calculated: endingCalculated,
            expected: summary,
            calculated: breakdown
        };
    }

    renderSummaries() {
        if (!this.hasParsed) {
            const placeholders = [
                '[data-testid="account-beginning"]',
                '[data-testid="account-ending"]',
                '[data-testid="account-checks"]',
                '[data-testid="account-withdrawals"]',
                '[data-testid="account-deposits"]',
                '[data-testid="calc-ending"]',
                '[data-testid="calc-checks"]',
                '[data-testid="calc-withdrawals"]',
                '[data-testid="calc-deposits"]'
            ];
            placeholders.forEach(sel => {
                const el = this.shadowRoot.querySelector(sel);
                if (el) el.textContent = '--';
            });
            if (this.issuesEl) {
                this.issuesEl.classList.add('hidden');
                this.issuesEl.textContent = '';
            }
            return;
        }
        const expected = this.accountSummary || {};
        const calc = this.breakdown || { checks: { count: 0, total: 0 }, withdrawals: { count: 0, total: 0 }, deposits: { count: 0, total: 0 } };
        const verification = this.verification || {};
        const endingCalc = verification.ending_calculated;

        const setText = (selector, value, fallback = '--') => {
            const el = this.shadowRoot.querySelector(selector);
            if (el) el.textContent = value ?? fallback;
        };

        setText('[data-testid="account-beginning"]', this._formatMoney(expected.beginning_balance));
        setText('[data-testid="account-ending"]', this._formatMoney(expected.ending_balance));
        setText('[data-testid="account-checks"]', this._formatCountTotal(expected.checks));
        setText('[data-testid="account-withdrawals"]', this._formatCountTotal(expected.withdrawals));
        setText('[data-testid="account-deposits"]', this._formatCountTotal(expected.deposits));

        setText('[data-testid="calc-ending"]', this._formatMoney(endingCalc));
        setText('[data-testid="calc-checks"]', this._formatCountTotal(calc.checks));
        setText('[data-testid="calc-withdrawals"]', this._formatCountTotal(calc.withdrawals));
        setText('[data-testid="calc-deposits"]', this._formatCountTotal(calc.deposits));

        this._flagMismatch('[data-testid="account-ending"]', '[data-testid="calc-ending"]', expected.ending_balance, endingCalc);
        this._flagMismatch('[data-testid="account-checks"]', null, expected.checks?.total, calc.checks?.total, expected.checks?.count, calc.checks?.count);
        this._flagMismatch('[data-testid="account-withdrawals"]', null, expected.withdrawals?.total, calc.withdrawals?.total, expected.withdrawals?.count, calc.withdrawals?.count);
        this._flagMismatch('[data-testid="account-deposits"]', null, expected.deposits?.total, calc.deposits?.total, expected.deposits?.count, calc.deposits?.count);

        if (this.issuesEl) {
            const issues = verification.issues || [];
            if (issues.length === 0) {
                this.issuesEl.classList.add('hidden');
                this.issuesEl.textContent = '';
            } else {
                this.issuesEl.classList.remove('hidden');
                this.issuesEl.textContent = issues.join(' • ');
            }
        }
    }

    _flagMismatch(accountSelector, calcSelector, expectedTotal, calcTotal, expectedCount, calcCount) {
        const close = (a, b, tol = 0.01) => Number.isFinite(a) && Number.isFinite(b) && Math.abs(a - b) <= tol;
        const mismatch = (expectedTotal !== undefined && expectedTotal !== null && calcTotal !== undefined && calcTotal !== null && !close(expectedTotal, calcTotal))
            || (expectedCount !== undefined && expectedCount !== null && calcCount !== undefined && calcCount !== null && expectedCount !== calcCount);
        if (accountSelector) {
            const el = this.shadowRoot.querySelector(accountSelector);
            if (el) el.classList.toggle('mismatch', !!mismatch);
        }
        if (calcSelector) {
            const elCalc = this.shadowRoot.querySelector(calcSelector);
            if (elCalc) elCalc.classList.toggle('mismatch', !!mismatch);
        }
    }

    _formatMoney(value) {
        if (!Number.isFinite(value)) return '--';
        return this.formatCurrency(value);
    }

    _formatCountTotal(group) {
        if (!group) return '--';
        const count = group.count ?? '—';
        const total = Number.isFinite(group.total) ? this.formatCurrency(group.total) : '--';
        return `${count} / ${total}`;
    }

    _filterDisplayTransactions(transactions = []) {
        return transactions.filter(txn => !this._isDeposit(txn));
    }

    _isCheck(txn) {
        if (!txn) return false;
        const hint = String(txn.bank_item_type || '').toUpperCase();
        if (hint === 'CHECK') return true;
        const desc = String(txn.description || '').toLowerCase();
        return desc.includes('check');
    }

    _isDeposit(txn) {
        if (!txn) return false;
        const hint = String(txn.bank_item_type || '').toUpperCase();
        if (hint === 'DEPOSIT' || hint === 'CREDIT') return true;
        const amt = Number(txn.amount);
        if (!Number.isFinite(amt)) return false;
        return amt > 0 && !this._isCheck(txn);
    }

    _isWithdrawal(txn) {
        if (!txn) return false;
        const hint = String(txn.bank_item_type || '').toUpperCase();
        if (hint === 'WITHDRAWAL' || hint === 'DEBIT') return true;
        const amt = Number(txn.amount);
        if (!Number.isFinite(amt)) return false;
        return amt <= 0 && !this._isCheck(txn);
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
