import { emit, on } from '../event-bus.js';

class ReceiptScanner extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });
        this.parsedData = null;
        this.tempFileName = null;
        this.originalFileName = null;
        this.isLoading = false;
        this.error = null;

        this.shadowRoot.innerHTML = `
            <style>
                /* Basic styling for the component */
                :host {
                    display: block;
                    font-family: sans-serif;
                    border: 1px solid #ccc;
                    padding: 1rem;
                    border-radius: 8px;
                    max-width: 600px;
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
                    border: 1px solid #eee;
                    padding: 0.5rem;
                    border-radius: 4px;
                    background-color: #fff;
                }
                .item-list h4 {
                    margin-top: 0;
                    margin-bottom: 0.5rem;
                }
                .item-list ul {
                    list-style: none;
                    padding: 0;
                }
                .item-list li {
                    padding: 5px 0;
                    border-bottom: 1px dashed #eee;
                }
                .item-list li:last-child {
                    border-bottom: none;
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
                        <div class="form-group">
                            <label for="totalAmount">Total Amount:</label>
                            <input type="number" id="totalAmount" name="totalAmount" step="0.01" required>
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
                        
                        <div class="item-list">
                            <h4>Items:</h4>
                            <ul id="receiptItems">
                                <!-- Items will be rendered here -->
                            </ul>
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
        this.receiptItemsList = this.shadowRoot.getElementById('receiptItems');
        this.cancelButton = this.shadowRoot.getElementById('cancelButton');
        this.saveButton = this.shadowRoot.getElementById('saveButton');
        this.categoryIdSelect = this.shadowRoot.getElementById('categoryId');

        this._setupEventListeners();
        this._fetchCategories();
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

        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/parse-receipt', {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to parse receipt.');
            }

            const result = await response.json();
            this.parsedData = result.parsed_data;
            this.tempFileName = result.temp_file_name;
            this._populateForm();
            this._showLoading(false);
            this.parsedDataForm.style.display = 'block';
            emit('receipt:parsed', this.parsedData);

        } catch (error) {
            console.error('Error parsing receipt:', error);
            this._showError(error.message);
            this._showLoading(false);
            emit('receipt:error', { message: error.message });
        }
    }

    _populateForm() {
        if (!this.parsedData) return;

        const form = this.receiptForm;
        form.elements.merchantName.value = this.parsedData.party.merchant_name || '';
        form.elements.transactionDate.value = this.parsedData.transaction_date || '';
        form.elements.totalAmount.value = this.parsedData.totals.total_amount || 0;
        form.elements.taxAmount.value = this.parsedData.totals.tax_amount || 0;
        form.elements.paymentMethod.value = this.parsedData.payment_method || 'OTHER';
        form.elements.description.value = this.parsedData.meta.raw_text || ''; // Using raw_text for description for now

        // Populate items
        this.receiptItemsList.innerHTML = '';
        if (this.parsedData.items && this.parsedData.items.length > 0) {
            this.parsedData.items.forEach(item => {
                const li = document.createElement('li');
                li.textContent = `${item.description} (x${item.quantity}) @ $${item.unit_price} = $${item.line_total}`;
                this.receiptItemsList.appendChild(li);
            });
        } else {
            this.receiptItemsList.innerHTML = '<li>No items extracted.</li>';
        }
    }

    async _fetchCategories() {
        try {
            const response = await fetch('/api/categories');
            if (!response.ok) {
                throw new Error('Failed to fetch categories.');
            }
            const categories = await response.json();
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

    async _handleSave(event) {
        event.preventDefault();
        this._showLoading(true);
        this._clearError();

        const form = this.receiptForm;
        const selectedCategoryId = form.elements.categoryId.value;

        if (!selectedCategoryId) {
            this._showError('Please select a category.');
            this._showLoading(false);
            return;
        }

        const saveRequest = {
            org_id: 1, // Hardcoded for now, should come from user context
            merchant_name: form.elements.merchantName.value,
            expense_date: form.elements.transactionDate.value,
            total_amount: parseFloat(form.elements.totalAmount.value),
            tax_amount: parseFloat(form.elements.taxAmount.value) || 0.0,
            category_id: parseInt(selectedCategoryId),
            payment_method: form.elements.paymentMethod.value,
            description: form.elements.description.value,
            original_file_name: this.originalFileName,
            temp_file_name: this.tempFileName,
            parsed_items: this.parsedData.items || [],
        };

        try {
            const response = await fetch('/api/save-receipt', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(saveRequest),
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to save expense.');
            }

            const result = await response.json();
            console.log('Expense saved:', result);
            this._resetForm();
            this._showLoading(false);
            emit('receipt:saved', result);

        } catch (error) {
            console.error('Error saving expense:', error);
            this._showError(error.message);
            this._showLoading(false);
            emit('receipt:error', { message: error.message });
        }
    }

    _handleCancel() {
        this._resetForm();
        emit('receipt:cancelled');
    }

    _resetForm() {
        this.parsedData = null;
        this.tempFileName = null;
        this.originalFileName = null;
        this.receiptForm.reset();
        this.parsedDataForm.style.display = 'none';
        this.dropArea.style.display = 'block';
        this._clearError();
    }
}

customElements.define('receipt-scanner', ReceiptScanner);