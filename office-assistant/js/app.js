// Main Application JavaScript

class OfficeAssistant {
    constructor() {
        this.currentSection = 'expenses';
        this.loadTimeout = null;
        this.init();
    }

    init() {
        console.log('Office Assistant initialized');
        this.setupEventListeners();
        this.loadInitialContent();
    }

    setupEventListeners() {
        // Navigation event delegation
        const navContainer = document.querySelector('.nav-container');
        if (navContainer) {
            navContainer.addEventListener('click', (e) => {
                const navButton = e.target.closest('.nav-button');
                if (navButton) {
                    this.handleNavigation(navButton);
                }
            });
        } else {
            console.error('Nav container not found!');
        }

        // Handle window resize for responsive behavior
        window.addEventListener('resize', () => {
            this.handleResize();
        });
    }

    handleNavigation(button) {
        const section = button.dataset.section;

        // Update active state using data attribute for Tailwind
        document.querySelectorAll('.nav-button').forEach(btn => {
            btn.setAttribute('data-active', 'false');
        });
        button.setAttribute('data-active', 'true');

        // Load content for the section
        this.loadSection(section);
        this.currentSection = section;
    }

    loadSection(section) {
        const contentArea = document.getElementById('content-area');

        // Add loading state
        contentArea.innerHTML = '<div class="flex items-center justify-center py-20"><div class="text-gray-500">Loading...</div></div>';

        // Cancel any previously scheduled load to avoid race conditions
        if (this.loadTimeout) {
            clearTimeout(this.loadTimeout);
            this.loadTimeout = null;
        }

        // Load actual content or show placeholder
        this.loadTimeout = setTimeout(() => {
            switch(section) {
                case 'expenses':
                    this.loadExpensesSection();
                    break;
                case 'upload-bank-statement':
                    this.loadUploadBankStatementSection();
                    break;
                case 'scan-receipt':
                    this.loadScanReceiptSection();
                    break;
                case 'scan-bank-pdf':
                    this.loadScanBankPdfSection();
                    break;
                case 'calendar':
                    this.loadCalendarSection();
                    break;
                default:
                    this.showNotImplementedAlert(section);
            }
            this.loadTimeout = null;
        }, 300);
    }

    loadExpensesSection() {
        console.log('Loading expenses section...');
        const contentArea = document.getElementById('content-area');
        contentArea.className = 'bg-white rounded-lg shadow-md overflow-hidden';
        contentArea.innerHTML = `
            <iframe src="daily_expense_categorizer.html"
                    class="w-full h-[calc(100vh-200px)] border-0"
                    title="Daily Expense Categorizer"
                    onload="console.log('Iframe loaded successfully')"
                    onerror="console.error('Iframe failed to load')">
            </iframe>
        `;
    }

    loadUploadBankStatementSection() {
        console.log('Loading upload bank statement section...');
        const contentArea = document.getElementById('content-area');
        contentArea.className = 'bg-white rounded-lg shadow-md overflow-hidden';
        contentArea.innerHTML = `
            <iframe src="upload_pdf_statements.html"
                    class="w-full h-[calc(100vh-200px)] border-0"
                    title="Upload PDF Statements"
                    onload="console.log('Upload iframe loaded successfully')"
                    onerror="console.error('Upload iframe failed to load')">
            </iframe>
        `;
    }

    loadScanReceiptSection() {
        console.log('Loading scan receipt section...');
        const contentArea = document.getElementById('content-area');
        contentArea.className = 'bg-white rounded-lg shadow-md p-4 min-h-[70vh]';
        contentArea.innerHTML = `
            <div class="fade-in">
                <receipt-scanner></receipt-scanner>
            </div>
        `;
    }

    loadScanBankPdfSection() {
        console.log('Loading scan bank PDF section...');
        const contentArea = document.getElementById('content-area');
        contentArea.className = 'bg-white rounded-lg shadow-md p-4 min-h-[70vh]';
        contentArea.innerHTML = `
            <div class="fade-in">
                <bank-pdf-scanner></bank-pdf-scanner>
            </div>
        `;
    }

    loadCalendarSection() {
        if (typeof window.calendar === 'undefined') {
            console.error('Calendar component not loaded');
            this.showNotImplementedAlert('calendar');
            return;
        }

        const contentArea = document.getElementById('content-area');
        contentArea.className = 'bg-white rounded-lg shadow-md p-4 min-h-[70vh]';
        contentArea.innerHTML = `
            <div class="fade-in">
                ${window.calendar.render()}
            </div>
        `;
    }

    showNotImplementedAlert(section) {
        const sectionNames = {
            expenses: 'Expense Categorizer',
            projects: 'Projects',
            clients: 'Clients',
            calendar: 'Calendar',
            documents: 'Documents',
            settings: 'Settings'
        };

        const contentArea = document.getElementById('content-area');
        contentArea.className = 'bg-white rounded-lg shadow-md p-4 min-h-[70vh]';
        const sectionName = sectionNames[section] || section;

        contentArea.innerHTML = `
            <div class="fade-in">
                <div class="bg-blue-50 border-l-4 border-blue-500 p-4 mb-6 rounded">
                    <div class="flex items-start">
                        <span class="text-2xl mr-3">ℹ️</span>
                        <div>
                            <strong class="text-blue-800">${sectionName} Section</strong><br>
                            <span class="text-blue-700">Not implemented yet. This feature is planned for future development.</span>
                        </div>
                    </div>
                </div>

                <div class="bg-white border border-gray-200 rounded-lg overflow-hidden">
                    <div class="bg-gray-50 px-6 py-4 border-b border-gray-200">
                        <h3 class="text-xl font-semibold text-gray-800">${sectionName} Overview</h3>
                        <p class="text-sm text-gray-600">Coming Soon</p>
                    </div>
                    <div class="px-6 py-4">
                        <p class="mb-3 text-gray-700">This section will contain:</p>
                        <ul class="ml-6 mb-6 list-disc text-gray-600">
                            ${this.getSectionFeatures(section)}
                        </ul>

                        <div class="flex gap-3">
                            <button class="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors" onclick="app.showFeatureModal('${section}')">
                                Learn More
                            </button>
                            <button class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors" onclick="app.goToExpenses()">
                                Back to Expense Categorizer
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    getSectionFeatures(section) {
        const features = {
            expenses: `
                <li>Daily transaction categorization</li>
                <li>Category assignment</li>
                <li>Transaction notes</li>
                <li>Month and day navigation</li>
                <li>Uncategorized expense tracking</li>
            `,
            projects: `
                <li>Project creation and management</li>
                <li>Task tracking and assignments</li>
                <li>Timeline and milestone tracking</li>
                <li>File and resource management</li>
                <li>Progress reporting</li>
            `,
            clients: `
                <li>Client contact information</li>
                <li>Communication history</li>
                <li>Project associations</li>
                <li>Billing and invoicing</li>
                <li>Client relationship management</li>
            `,
            calendar: `
                <li>Appointment scheduling</li>
                <li>Meeting management</li>
                <li>Deadline tracking</li>
                <li>Integration with external calendars</li>
                <li>Reminder notifications</li>
            `,
            documents: `
                <li>File upload and storage</li>
                <li>Document organization</li>
                <li>Template management</li>
                <li>Version control</li>
                <li>Sharing and collaboration</li>
            `,
            settings: `
                <li>User preferences</li>
                <li>System configuration</li>
                <li>Notification settings</li>
                <li>Data backup and export</li>
                <li>Security and privacy controls</li>
            `
        };

        return features[section] || '<li>Feature details coming soon</li>';
    }

    showFeatureModal(section) {
        const sectionNames = {
            expenses: 'Expense Categorizer',
            projects: 'Projects',
            clients: 'Clients',
            calendar: 'Calendar',
            documents: 'Documents',
            settings: 'Settings'
        };

        const modal = document.createElement('div');
        modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4';
        modal.innerHTML = `
            <div class="bg-white rounded-lg max-w-lg w-full shadow-xl">
                <div class="flex justify-between items-center px-6 py-4 border-b border-gray-200">
                    <h2 class="text-xl font-semibold text-gray-800">${sectionNames[section]} Features</h2>
                    <button class="text-gray-400 hover:text-gray-600 text-2xl" onclick="this.closest('.fixed').remove()">&times;</button>
                </div>
                <div class="px-6 py-4">
                    <div class="bg-yellow-50 border-l-4 border-yellow-500 p-4 mb-4 rounded">
                        <div class="flex items-start">
                            <span class="text-xl mr-2">🚧</span>
                            <div>
                                <strong class="text-yellow-800">Development Status</strong><br>
                                <span class="text-yellow-700">This section is currently in the planning phase and will be implemented in future updates.</span>
                            </div>
                        </div>
                    </div>
                    <p class="text-gray-700 mb-4">The ${sectionNames[section]} section will be a comprehensive tool for managing this aspect of your freelance business.</p>
                    <div>
                        <button class="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors" onclick="this.closest('.fixed').remove()">
                            Close
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Close modal when clicking overlay
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.remove();
            }
        });
    }

    goToExpenses() {
        const expensesButton = document.querySelector('[data-section="expenses"]');
        this.handleNavigation(expensesButton);
    }

    loadInitialContent() {
        // Load expense categorizer by default
        this.loadSection('expenses');
    }

    handleResize() {
        // Handle responsive behavior if needed
        console.log('Window resized');
    }

    // Utility method for showing alerts
    showAlert(message, type = 'info') {
        const colors = {
            info: 'bg-blue-50 border-blue-500 text-blue-700',
            warning: 'bg-yellow-50 border-yellow-500 text-yellow-700',
            success: 'bg-green-50 border-green-500 text-green-700',
            error: 'bg-red-50 border-red-500 text-red-700'
        };
        const icons = {
            info: 'ℹ️',
            warning: '⚠️',
            success: '✅',
            error: '❌'
        };

        const alertEl = document.createElement('div');
        alertEl.className = `${colors[type]} border-l-4 p-4 mb-4 rounded fade-in flex items-start`;
        alertEl.innerHTML = `
            <span class="text-xl mr-3">${icons[type]}</span>
            <div>${message}</div>
        `;

        const contentArea = document.getElementById('content-area');
        contentArea.insertBefore(alertEl, contentArea.firstChild);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alertEl.parentNode) {
                alertEl.remove();
            }
        }, 5000);
    }
}

// Make OfficeAssistant available globally for testing
try {
    if (typeof window !== 'undefined' && window) {
        window.OfficeAssistant = OfficeAssistant;
    }
} catch (e) {
    // Window not available in Node environment
}

// Initialize the application when DOM is loaded
try {
    if (typeof document !== 'undefined' && document) {
        document.addEventListener('DOMContentLoaded', () => {
            window.app = new OfficeAssistant();
        });
    }
} catch (e) {
    // Document not available in Node environment
}
