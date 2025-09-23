// Main Application JavaScript

class OfficeAssistant {
    constructor() {
        this.currentSection = 'dashboard';
        this.init();
    }

    init() {
        console.log('Office Assistant initialized');
        this.setupEventListeners();
        this.loadInitialContent();
    }

    setupEventListeners() {
        // Navigation event delegation
        document.querySelector('.nav-container').addEventListener('click', (e) => {
            const navButton = e.target.closest('.nav-button');
            if (navButton) {
                this.handleNavigation(navButton);
            }
        });

        // Handle window resize for responsive behavior
        window.addEventListener('resize', () => {
            this.handleResize();
        });
    }

    handleNavigation(button) {
        const section = button.dataset.section;

        // Update active state
        document.querySelectorAll('.nav-button').forEach(btn => {
            btn.classList.remove('active');
        });
        button.classList.add('active');

        // Load content for the section
        this.loadSection(section);
        this.currentSection = section;
    }

    loadSection(section) {
        const contentArea = document.getElementById('content-area');

        // Add loading state
        contentArea.innerHTML = '<div class="loading"><div class="spinner"></div>Loading...</div>';

        // Load actual content or show placeholder
        setTimeout(() => {
            switch(section) {
                case 'calendar':
                    this.loadCalendarSection();
                    break;
                default:
                    this.showNotImplementedAlert(section);
            }
        }, 300);
    }

    loadCalendarSection() {
        if (typeof window.calendar === 'undefined') {
            console.error('Calendar component not loaded');
            this.showNotImplementedAlert('calendar');
            return;
        }

        const contentArea = document.getElementById('content-area');
        contentArea.innerHTML = `
            <div class="fade-in">
                ${window.calendar.render()}
            </div>
        `;
    }

    showNotImplementedAlert(section) {
        const sectionNames = {
            dashboard: 'Dashboard',
            projects: 'Projects',
            clients: 'Clients',
            calendar: 'Calendar',
            documents: 'Documents',
            settings: 'Settings'
        };

        const contentArea = document.getElementById('content-area');
        const sectionName = sectionNames[section] || section;

        contentArea.innerHTML = `
            <div class="fade-in">
                <div class="alert alert-info">
                    <span style="font-size: 1.2rem;">ℹ️</span>
                    <div>
                        <strong>${sectionName} Section</strong><br>
                        Not implemented yet. This feature is planned for future development.
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <h3 class="card-title">${sectionName} Overview</h3>
                        <p class="card-subtitle">Coming Soon</p>
                    </div>
                    <div class="card-body">
                        <p>This section will contain:</p>
                        <ul style="margin-left: 1.5rem; margin-top: 0.5rem;">
                            ${this.getSectionFeatures(section)}
                        </ul>

                        <div class="mt-3">
                            <button class="btn btn-primary" onclick="app.showFeatureModal('${section}')">
                                Learn More
                            </button>
                            <button class="btn btn-outline" onclick="app.goToDashboard()">
                                Back to Dashboard
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    getSectionFeatures(section) {
        const features = {
            dashboard: `
                <li>Project status overview</li>
                <li>Recent client communications</li>
                <li>Upcoming deadlines</li>
                <li>Quick action buttons</li>
                <li>Performance metrics</li>
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
            dashboard: 'Dashboard',
            projects: 'Projects',
            clients: 'Clients',
            calendar: 'Calendar',
            documents: 'Documents',
            settings: 'Settings'
        };

        const modal = document.createElement('div');
        modal.className = 'modal-overlay';
        modal.innerHTML = `
            <div class="modal">
                <div class="modal-header">
                    <h2 class="modal-title">${sectionNames[section]} Features</h2>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <div class="alert alert-warning">
                        <span style="font-size: 1.1rem;">🚧</span>
                        <div>
                            <strong>Development Status</strong><br>
                            This section is currently in the planning phase and will be implemented in future updates.
                        </div>
                    </div>
                    <p>The ${sectionNames[section]} section will be a comprehensive tool for managing this aspect of your freelance business.</p>
                    <div class="mt-2">
                        <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">
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

    goToDashboard() {
        const dashboardButton = document.querySelector('[data-section="dashboard"]');
        this.handleNavigation(dashboardButton);
    }

    loadInitialContent() {
        // Load dashboard by default
        this.loadSection('dashboard');
    }

    handleResize() {
        // Handle responsive behavior if needed
        console.log('Window resized');
    }

    // Utility method for showing alerts
    showAlert(message, type = 'info') {
        const alertEl = document.createElement('div');
        alertEl.className = `alert alert-${type} fade-in`;
        alertEl.innerHTML = `
            <span style="font-size: 1.1rem;">${type === 'info' ? 'ℹ️' : type === 'warning' ? '⚠️' : type === 'success' ? '✅' : '❌'}</span>
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

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.app = new OfficeAssistant();
});