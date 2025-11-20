import { emit, on } from '../event-bus.js';
import '../category-picker.js';

class ReceiptScanner extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.parsedData = null;
        this.tempFileName = null;
        this.originalFileName = null;
        this.isLoading = false;
        this.error = null;
        this.calculatedTotal = 0;

        this.shadowRoot.innerHTML = `
            <style>
                /* Basic styling for the component */
                :host {
                    display: block;
                    font-family: sans-serif;
                    border: 1px solid #ccc;
                    padding: 1rem;
                    border-radius: 8px;
                    max-width: 800px; /* Increased width for table */
                    margin: 1rem auto;
                    background-color: #f9f9f9;
                }
                .drop-area {
                    border: 2px dashed #ccc;
                    padding: 20px;
                    text-align: center;
                    cursor: pointer;
                    margin-bottom: 1rem;
                    background-color: #fff;
                    border-radius: 4px;
                }
                .drop-area.highlight {
                    border-color: purple;
                }
                .file-input {
                    display: none;
                }
                .loading-spinner {
                    border: 4px solid rgba(0, 0, 0, 0.1);
                    border-left-color: #222;
                    border-radius: 50%;
                    width: 20px;
                    height: 20px;
                    animation: spin 1s linear infinite;
                    display: inline-block;
                    vertical-align: middle;
                    margin-left: 10px;
                }
                @keyframes spin {
                    to { transform: rotate(360deg); }
                }
                .error-message {
                    color: red;
                    margin-top: 1rem;
                }
                .parsed-data-form {
                    margin-top: 1rem;
                    border-top: 1px solid #eee;
                    padding-top: 1rem;
                }
                .form-group {
                    margin-bottom: 0.8rem;
                }
                .form-group label {
                    display: block;
                    margin-bottom: 0.2rem;
                    font-weight: bold;
                }
                .form-group input[type="text"],
                .form-group input[type="number"],
                .form-group input[type="date"],
                .form-group select {
                    width: 100%;
                    padding: 8px;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    box-sizing: border-box;
                }
                .form-group input.success-match {
                    background-color: #d4edda; /* Light green */
                    border-color: #c3e6cb;
                }
                .form-actions {
                    margin-top: 1.5rem;
                    text-align: right;
                }
                .form-actions button {
                    padding: 10px 15px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 1rem;
                    margin-left: 10px;
                }
                .form-actions button.save {
                    background-color: #28a745;
                    color: white;
                }
                .form-actions button.cancel {
                    background-color: #6c757d;
                    color: white;
                }
                .item-list {
                    margin-top: 1rem;
                    margin-bottom: 1rem;
                    border: 1px solid #eee;
                    padding: 0.5rem;
                    border-radius: 4px;
                    background-color: #fff;
                    overflow-x: auto;
                }
                .item-list h4 {
                    margin-top: 0;
                    margin-bottom: 0.5rem;
                }
                table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 0.5rem;
                }
                th, td {
                    padding: 8px;
                    text-align: left;
                    border-bottom: 1px solid #ddd;
                    color: black;
                }
                th {
                    background-color: #d3d3d3; /* Light gray */
                    font-weight: bold;
                }
                tr:nth-child(even) {
                    background-color: #f2f2f2; /* Light gray */
                }
                tr:nth-child(odd) {
                    background-color: #e6e6e6; /* Lighter gray */
                }
            </style>
            <div class="receipt-scanner-container">
                <h2>Scan New Receipt</h2>
                <div class="drop-area" id="dropArea">
                    <p>Drag & Drop Receipt Image Here or Click to Upload</p>
                    <input type="file" id="fileInput" class="file-input" accept="image/jpeg,image/png,image/webp,application/pdf">
                </div>
                <div id="loading" style="display:none;">
                    <div class="loading-spinner"></div> Parsing receipt...
                </div>
                <div id="error" class="error-message" style="display:none;"></div>

                <div id="parsedDataForm" class="parsed-data-form" style="display:none;">
                    <h3>Review & Edit</h3>
                    <form id="receiptForm">
                        <div class="form-group">
                            <label for="merchantName">Merchant Name:</label>
                            <input type="text" id="merchantName" name="merchantName" required>
                        </div>
                        <div class="form-group">
                            <label for="transactionDate">Transaction Date:</label>
                            <input type="date" id="transactionDate" name="transactionDate" required>
                        </div>
                        
                        <div class="item-list">
                            <h4>Items:</h4>
                            <table id="receiptItemsTable">
                                <thead>
                                    <tr>
                                        <th>Item Name</th>
                                        <th>Quantity</th>
                                        <th>Price</th>
                                        <th>Total</th>
                                        <th>Category</th>
                                    </tr>
                                </thead>
                                <tbody id="receiptItemsBody">
                                    <!-- Items will be rendered here -->
                                </tbody>
                            </table>
                        </div>

                        <div class="form-group">
                            <label for="totalAmount">Total Amount:</label>
                            <input type="number" id="totalAmount" name="totalAmount" step="0.01" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="calculatedAmount">Calculated Amount:</label>
                            <input type="number" id="calculatedAmount" name="calculatedAmount" step="0.01" readonly>
                        </div>

                        <div class="form-group">
                            <label for="taxAmount">Tax Amount:</label>
                            <input type="number" id="taxAmount" name="taxAmount" step="0.01">
                        </div>
                        <div class="form-group">
                            <label for="paymentMethod">Payment Method:</label>
                            <select id="paymentMethod" name="paymentMethod">
                                <option value="CARD">CARD</option>
                                <option value="CASH">CASH</option>
                                <option value="BANK">BANK</option>
                                <option value="OTHER">OTHER</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="description">Description:</label>
                            <input type="text" id="description" name="description">
                        </div>
                        
                        <div class="form-group">
                            <label for="categoryId">Category:</label>
                            <!-- Category picker will be integrated here -->
                            <select id="categoryId" name="categoryId" required>
                                <option value="">Select Category</option>
                            </select>
                        </div>

                        <div class="form-actions">
                            <button type="button" class="cancel" id="cancelButton">Cancel</button>
                            <button type="submit" class="save" id="saveButton">Save Expense</button>
                        </div>
                    </form>
                </div>
            </div>
        `;

        this.dropArea = this.shadowRoot.getElementById('dropArea');
        this.fileInput = this.shadowRoot.getElementById('fileInput');
        this.loadingIndicator = this.shadowRoot.getElementById('loading');
        this.errorMessage = this.shadowRoot.getElementById('error');
        this.parsedDataForm = this.shadowRoot.getElementById('parsedDataForm');
        this.receiptForm = this.shadowRoot.getElementById('receiptForm');
        this.receiptItemsBody = this.shadowRoot.getElementById('receiptItemsBody');
        this.cancelButton = this.shadowRoot.getElementById('cancelButton');
        this.saveButton = this.shadowRoot.getElementById('saveButton');
        this.categoryIdSelect = this.shadowRoot.getElementById('categoryId');
        this.calculatedAmountInput = this.shadowRoot.getElementById('calculatedAmount');
        this.categoryOptions = [];
        this.categoriesPromise = null;
        this.orgId = 1; // Default org; can be overridden via host context
        this.apiBase = this._computeApiBase();

        this._setupEventListeners();
        this.categoriesPromise = this._fetchCategories();
    }

    _computeApiBase() {
        const { protocol, hostname, port } = window.location;
        if (port === '8081' || port === '8000') {
            return `${protocol}//${hostname}:8080/api`;
        }
        if (port && port !== '') {
            return `${protocol}//${hostname}:${port}/api`;
        }
        return `${protocol}//${hostname}/api`;
    }

    _setupEventListeners() {
        this.dropArea.addEventListener('click', () => this.fileInput.click());
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
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this._handleFile(files[0]);
            }
        });
        this.fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this._handleFile(e.target.files[0]);
            }
        });

        this.receiptForm.addEventListener('submit', this._handleSave.bind(this));
        this.cancelButton.addEventListener('click', this._handleCancel.bind(this));
    }

    _showLoading(show) {
        this.isLoading = show;
        this.loadingIndicator.style.display = show ? 'block' : 'none';
        this.dropArea.style.display = show ? 'none' : 'block';
        this.parsedDataForm.style.display = 'none';
        this.errorMessage.style.display = 'none';
    }

    _showError(message) {
        this.error = message;
        this.errorMessage.textContent = message;
        this.errorMessage.style.display = 'block';
        this.dropArea.style.display = 'block';
        this.loadingIndicator.style.display = 'none';
        this.parsedDataForm.style.display = 'none';
    }

    _clearError() {
        this.error = null;
        this.errorMessage.style.display = 'none';
        this.errorMessage.textContent = '';
    }

    async _handleFile(file) {
        this._clearError();
        this._showLoading(true);
        this.originalFileName = file.name;

        console.log('Processing file:', file.name, 'type:', file.type, 'size:', file.size);

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${this.apiBase}/parse-receipt`, {
                method: 'POST',
                body: formData,
            });

            console.log('Parse receipt response status:', response.status, response.statusText);

            if (!response.ok) {
                let errorMessage = 'Failed to parse receipt.';
                const contentType = response.headers.get('content-type');

                try {
                    if (contentType && contentType.includes('application/json')) {
                        const errorData = await response.json();
                        errorMessage = errorData.detail || errorMessage;
                    } else {
                        const text = await response.text();
                        errorMessage = text || `Server error (${response.status})`;
                    }
                } catch (parseError) {
                    console.error('Error parsing error response:', parseError);
                    errorMessage = `Server error (${response.status})`;
                }
                throw new Error(errorMessage);
            }

            const result = await response.json();
            this.parsedData = result.parsed_data;
            this.tempFileName = result.temp_file_name;
            await this._populateForm();
            this._showLoading(false);
            this.parsedDataForm.style.display = 'block';
            emit('receipt:parsed', this.parsedData);

        } catch (error) {
            console.error('Error parsing receipt:', error);
            const errorMessage = error?.message || error?.toString() || 'Unknown error occurred';
            this._showError(errorMessage);
            this._showLoading(false);
            emit('receipt:error', { message: errorMessage });
        }
    }

    async _populateForm() {
        if (!this.parsedData) return;

        if (this.categoriesPromise) {
            try {
                await this.categoriesPromise;
            } catch (err) {
                console.error('Failed to load categories for category-picker:', err);
            }
        }

        const form = this.receiptForm;
        form.elements.merchantName.value = this.parsedData.party.merchant_name || '';
        form.elements.transactionDate.value = this.parsedData.transaction_date || '';
        
        const totalAmount = this.parsedData.totals.total_amount || 0;
        form.elements.totalAmount.value = totalAmount;
        
        form.elements.taxAmount.value = this.parsedData.totals.tax_amount || 0;
        form.elements.paymentMethod.value = this.parsedData.payment_method || 'OTHER';
        form.elements.description.value = this.parsedData.meta.raw_text || ''; // Using raw_text for description for now

        // Populate items and calculate total
        this.receiptItemsBody.innerHTML = '';
        this.calculatedTotal = 0;

        if (this.parsedData.items && this.parsedData.items.length > 0) {
            this.parsedData.items.forEach((item, index) => {
                const tr = document.createElement('tr');

                const nameTd = document.createElement('td');
                nameTd.textContent = item.description;
                tr.appendChild(nameTd);

                const qtyTd = document.createElement('td');
                qtyTd.textContent = item.quantity;
                tr.appendChild(qtyTd);

                const priceTd = document.createElement('td');
                priceTd.textContent = item.unit_price;
                tr.appendChild(priceTd);

                const totalTd = document.createElement('td');
                totalTd.textContent = item.line_total;
                tr.appendChild(totalTd);

                // Add category picker column
                const categoryTd = document.createElement('td');
                const categoryPicker = document.createElement('category-picker');
                categoryPicker.setAttribute('expense-id', item.expense_id ? `expense-${item.expense_id}` : `item-${index}`);
                categoryPicker.setAttribute('placeholder', 'Select category...');

                // Attach inline taxonomy matching the Daily Expense Categorizer page
                const taxonomy = document.createElement('script');
                taxonomy.type = 'application/json';
                taxonomy.textContent = JSON.stringify(this.categoryOptions || []);
                categoryPicker.appendChild(taxonomy);

                // Rehydrate existing category selection if present
                if (Array.isArray(item.category_path) && item.category_path.length > 0) {
                    const setValue = () => {
                        const selectEl = categoryPicker.shadowRoot?.querySelector('select');
                        if (selectEl && selectEl.options.length > 1) {
                            categoryPicker.value = item.category_path.join(' / ');
                        } else {
                            setTimeout(setValue, 50);
                        }
                    };
                    setTimeout(setValue, 0);
                }

                // Listen for category selection
                categoryPicker.addEventListener('completed', async (e) => {
                    await this._handleCategorySelection(index, e.detail);
                });

                // Listen for category reset
                categoryPicker.addEventListener('reset', async () => {
                    await this._clearCategorizedItem(index);
                });

                categoryTd.appendChild(categoryPicker);
                tr.appendChild(categoryTd);

                this.receiptItemsBody.appendChild(tr);

                // Add to calculated total
                const normalizedLineTotal = parseFloat(item.line_total || 0);
                this.calculatedTotal += Number.isFinite(normalizedLineTotal)
                    ? normalizedLineTotal
                    : 0;
            });
        } else {
            const tr = document.createElement('tr');
            const td = document.createElement('td');
            td.colSpan = 5; // Updated colspan for new category column
            td.textContent = 'No items extracted.';
            td.style.textAlign = 'center';
            tr.appendChild(td);
            this.receiptItemsBody.appendChild(tr);
        }

        // Update calculated amount field
        // Fix floating point precision issues
        this.calculatedTotal = Math.round(this.calculatedTotal * 100) / 100;
        this.calculatedAmountInput.value = this.calculatedTotal;

        // Check if calculated amount matches total amount
        // Allow for small floating point differences
        if (Math.abs(this.calculatedTotal - parseFloat(totalAmount)) < 0.01) {
            this.calculatedAmountInput.classList.add('success-match');
        } else {
            this.calculatedAmountInput.classList.remove('success-match');
        }
    }

    async _fetchCategories() {
        try {
            const response = await fetch(`${this.apiBase}/categories`);
            if (!response.ok) {
                throw new Error('Failed to fetch categories.');
            }
            const categories = await response.json();
            this.categoryOptions = this._buildCategoryTree(categories);
            this.categoryIdSelect.innerHTML = '<option value="">Select Category</option>';
            categories.forEach(cat => {
                const option = document.createElement('option');
                option.value = cat.id;
                option.textContent = cat.name;
                this.categoryIdSelect.appendChild(option);
            });
        } catch (error) {
            console.error('Error fetching categories:', error);
            // Optionally show error to user
        }
    }

    _buildCategoryTree(categories) {
        const map = {};
        const roots = [];

        categories.forEach(cat => {
            map[cat.id] = {
                id: String(cat.id),
                label: cat.name,
                children: [],
                _original: cat,
            };
        });

        categories.forEach(cat => {
            const node = map[cat.id];
            if (cat.parent_id && map[cat.parent_id]) {
                map[cat.parent_id].children.push(node);
            } else {
                roots.push(node);
            }
        });

        Object.values(map).forEach(node => {
            if (node.children.length === 0) {
                delete node.children;
            }
        });

        return roots;
    }

    _findCategoryNodeByPath(path) {
        let current = this.categoryOptions || [];
        let found = null;

        for (const label of path) {
            const next = (current || []).find(node => node.label === label);
            if (!next) return null;
            found = next;
            current = next.children || [];
        }

        return found;
    }

    async _handleCategorySelection(index, detail) {
        if (!this.parsedData?.items?.[index]) {
            return;
        }

        const path = detail?.path || [];
        const categoryNode = this._findCategoryNodeByPath(path);

        if (!categoryNode || !categoryNode._original) {
            console.error('Could not resolve category for path:', path);
            return;
        }

        const item = this.parsedData.items[index];
        item.category = detail.label;
        item.category_path = path;
        item.category_id = categoryNode._original.id;

        await this._persistCategorizedItem(index, categoryNode._original.id);
    }

    async _persistCategorizedItem(index, categoryId) {
        const item = this.parsedData?.items?.[index];
        if (!item) return;

        const amount = parseFloat(item.line_total ?? (item.unit_price || 0) * (item.quantity || 0)) || 0;
        const expenseDate = this.receiptForm?.elements.transactionDate.value || this.parsedData.transaction_date;
        const merchantName = this.receiptForm?.elements.merchantName.value || this.parsedData.party.merchant_name || 'Unknown merchant';
        const paymentMethod = this.receiptForm?.elements.paymentMethod.value || this.parsedData.payment_method || 'OTHER';

        const payload = {
            org_id: this.orgId,
            merchant_name: merchantName,
            expense_date: expenseDate,
            amount,
            category_id: categoryId,
            description: item.description || merchantName,
            method: paymentMethod,
            receipt_url: null,
        };

        try {
            if (item.expense_id) {
                await fetch(`${this.apiBase}/expenses/${item.expense_id}/category`, {
                    method: 'PUT',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ category_id: categoryId }),
                });
            } else {
                const response = await fetch(`${this.apiBase}/receipt-items`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(payload),
                });

                if (!response.ok) {
                    const text = await response.text();
                    throw new Error(text || 'Failed to store categorized item.');
                }

                const data = await response.json();
                item.expense_id = data.expense_id;
            }
        } catch (error) {
            console.error('Error persisting categorized item:', error);
            this.errorMessage.textContent = error?.message || 'Failed to save category selection.';
            this.errorMessage.style.display = 'block';
        }
    }

    async _clearCategorizedItem(index) {
        const item = this.parsedData?.items?.[index];
        if (!item) return;

        if (item.expense_id) {
            try {
                const response = await fetch(`${this.apiBase}/receipt-items/${item.expense_id}`, {
                    method: 'DELETE',
                });
                if (!response.ok) {
                    const text = await response.text();
                    console.error('Failed to delete categorized item:', text);
                }
            } catch (error) {
                console.error('Error clearing categorized item:', error);
            }
        }

        delete item.category;
        delete item.category_path;
        delete item.category_id;
        delete item.expense_id;
    }

    async _handleSave(event) {
        event.preventDefault();
        this._showLoading(true);
        this._clearError();

        const form = this.receiptForm;
        const selectedCategoryId = form.elements.categoryId.value;

        const categorizedItems = (this.parsedData.items || []).filter(
            (item) => item.category_id
        );

        if (categorizedItems.length === 0) {
            this._showError('Categorize at least one line item to save.');
            this._showLoading(false);
            return;
        }

        const formattedItems = categorizedItems.map((item) => {
            const qty = parseFloat(item.quantity || 0) || 0;
            const unit = parseFloat(item.unit_price || 0) || 0;
            const line = parseFloat(item.line_total || qty * unit) || 0;

            return {
                description: item.description || form.elements.description.value || form.elements.merchantName.value,
                quantity: qty,
                unit_price: unit,
                line_total: line,
                category_id: item.category_id,
                category_path: item.category_path || [],
                expense_id: item.expense_id,
            };
        });

        const saveRequest = {
            org_id: this.orgId, // Hardcoded for now, should come from user context
            merchant_name: form.elements.merchantName.value,
            expense_date: form.elements.transactionDate.value,
            total_amount: parseFloat(form.elements.totalAmount.value),
            tax_amount: parseFloat(form.elements.taxAmount.value) || 0.0,
            category_id: selectedCategoryId ? parseInt(selectedCategoryId) : null,
            payment_method: form.elements.paymentMethod.value,
            description: form.elements.description.value,
            original_file_name: this.originalFileName,
            temp_file_name: this.tempFileName,
            parsed_items: formattedItems,
        };

        try {
            const response = await fetch(`${this.apiBase}/save-receipt`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(saveRequest),
            });

            if (!response.ok) {
                let errorMessage = 'Failed to save expense.';
                const contentType = response.headers.get('content-type');

                try {
                    if (contentType && contentType.includes('application/json')) {
                        const errorData = await response.json();
                        errorMessage = errorData.detail || errorMessage;
                    } else {
                        const text = await response.text();
                        errorMessage = text || `Server error (${response.status})`;
                    }
                } catch (parseError) {
                    console.error('Error parsing error response:', parseError);
                    errorMessage = `Server error (${response.status})`;
                }
                throw new Error(errorMessage);
            }

            const result = await response.json();
            console.log('Expense saved:', result);
            await this._resetForm(true);
            this._showLoading(false);
            emit('receipt:saved', result);

        } catch (error) {
            console.error('Error saving expense:', error);
            const errorMessage = error?.message || error?.toString() || 'Unknown error occurred';
            this._showError(errorMessage);
            this._showLoading(false);
            emit('receipt:error', { message: errorMessage });
        }
    }

    async _handleCancel() {
        await this._resetForm();
        emit('receipt:cancelled');
    }

    async _resetForm(skipDbCleanup = false) {
        const expenseIds = (this.parsedData?.items || [])
            .map(item => item.expense_id)
            .filter(Boolean);

        if (!skipDbCleanup && expenseIds.length > 0) {
            await Promise.all(expenseIds.map(async (id) => {
                try {
                    const response = await fetch(`/api/receipt-items/${id}`, { method: 'DELETE' });
                    if (!response.ok) {
                        console.error('Failed to clean up expense', id);
                    }
                } catch (error) {
                    console.error('Error cleaning up expense', id, error);
                }
            }));
        }

        this.parsedData = null;
        this.tempFileName = null;
        this.originalFileName = null;
        this.calculatedTotal = 0;
        this.receiptItemsBody.innerHTML = '';
        this.receiptForm.reset();
        this.calculatedAmountInput.value = '';
        this.calculatedAmountInput.classList.remove('success-match');
        this.parsedDataForm.style.display = 'none';
        this.dropArea.style.display = 'block';
        this._clearError();
    }
}

customElements.define('receipt-scanner', ReceiptScanner);
