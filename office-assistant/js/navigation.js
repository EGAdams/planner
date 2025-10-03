// Navigation-specific functionality

class NavigationManager {
    constructor() {
        this.navigationHistory = [];
        this.init();
    }

    init() {
        this.setupKeyboardNavigation();
        this.setupAccessibility();
    }

    setupKeyboardNavigation() {
        // Handle keyboard navigation
        document.addEventListener('keydown', (e) => {
            // Alt + number keys for quick navigation
            if (e.altKey && e.key >= '1' && e.key <= '6') {
                e.preventDefault();
                const index = parseInt(e.key) - 1;
                const buttons = document.querySelectorAll('.nav-button');
                if (buttons[index]) {
                    buttons[index].click();
                }
            }

            // ESC to go back to expense categorizer
            if (e.key === 'Escape') {
                const expensesButton = document.querySelector('[data-section="expenses"]');
                if (expensesButton && expensesButton.getAttribute('data-active') !== 'true') {
                    expensesButton.click();
                }
            }
        });
    }

    setupAccessibility() {
        // Add keyboard accessibility to navigation buttons
        const navButtons = document.querySelectorAll('.nav-button');
        navButtons.forEach((button, index) => {
            // Add tabindex and aria labels
            button.setAttribute('tabindex', '0');
            button.setAttribute('aria-label', `Navigate to ${button.dataset.section}`);
            button.setAttribute('title', `Alt+${index + 1} for quick access`);

            // Handle Enter and Space key presses
            button.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    button.click();
                }
            });
        });
    }

    // Track navigation history
    addToHistory(section) {
        this.navigationHistory.push({
            section: section,
            timestamp: new Date()
        });

        // Keep only last 10 entries
        if (this.navigationHistory.length > 10) {
            this.navigationHistory.shift();
        }
    }

    // Get navigation statistics
    getNavigationStats() {
        const stats = {};
        this.navigationHistory.forEach(entry => {
            stats[entry.section] = (stats[entry.section] || 0) + 1;
        });
        return stats;
    }

    // Breadcrumb functionality (for future use)
    updateBreadcrumb(section) {
        // This would update a breadcrumb navigation if implemented
        console.log(`Breadcrumb: Home > ${section}`);
    }

    // Section-specific navigation logic
    canNavigateToSection(section) {
        // Add any business logic for section access
        // For now, all sections are accessible
        return true;
    }

    // Mobile navigation handling
    setupMobileNavigation() {
        // Add swipe gesture support for mobile
        let startX = 0;
        let endX = 0;

        document.addEventListener('touchstart', (e) => {
            startX = e.changedTouches[0].screenX;
        });

        document.addEventListener('touchend', (e) => {
            endX = e.changedTouches[0].screenX;
            this.handleSwipeGesture();
        });
    }

    handleSwipeGesture() {
        const threshold = 50;
        const diff = startX - endX;

        if (Math.abs(diff) > threshold) {
            const currentButton = document.querySelector('.nav-button.active');
            const allButtons = Array.from(document.querySelectorAll('.nav-button'));
            const currentIndex = allButtons.indexOf(currentButton);

            if (diff > 0 && currentIndex < allButtons.length - 1) {
                // Swipe left - next section
                allButtons[currentIndex + 1].click();
            } else if (diff < 0 && currentIndex > 0) {
                // Swipe right - previous section
                allButtons[currentIndex - 1].click();
            }
        }
    }

    // Quick navigation shortcuts
    showNavigationHelp() {
        const helpModal = document.createElement('div');
        helpModal.className = 'modal-overlay';
        helpModal.innerHTML = `
            <div class="modal">
                <div class="modal-header">
                    <h2 class="modal-title">Navigation Shortcuts</h2>
                    <button class="modal-close" onclick="this.closest('.modal-overlay').remove()">&times;</button>
                </div>
                <div class="modal-body">
                    <h4>Keyboard Shortcuts:</h4>
                    <ul style="margin-left: 1rem;">
                        <li><kbd>Alt + 1</kbd> - Expense Categorizer</li>
                        <li><kbd>Alt + 2</kbd> - Projects</li>
                        <li><kbd>Alt + 3</kbd> - Clients</li>
                        <li><kbd>Alt + 4</kbd> - Calendar</li>
                        <li><kbd>Alt + 5</kbd> - Documents</li>
                        <li><kbd>Alt + 6</kbd> - Settings</li>
                        <li><kbd>Esc</kbd> - Return to Expense Categorizer</li>
                    </ul>

                    <h4 class="mt-2">Mobile:</h4>
                    <ul style="margin-left: 1rem;">
                        <li>Swipe left/right to navigate between sections</li>
                        <li>Tap navigation buttons for direct access</li>
                    </ul>

                    <div class="mt-3">
                        <button class="btn btn-secondary" onclick="this.closest('.modal-overlay').remove()">
                            Got it!
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(helpModal);
    }
}

// Initialize navigation manager
document.addEventListener('DOMContentLoaded', () => {
    window.navManager = new NavigationManager();

    // Add help shortcut
    document.addEventListener('keydown', (e) => {
        if (e.key === 'F1' || (e.ctrlKey && e.key === '/')) {
            e.preventDefault();
            window.navManager.showNavigationHelp();
        }
    });
});