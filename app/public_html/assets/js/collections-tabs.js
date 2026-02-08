/**
 * Collections Tab Navigation
 * Hash-based tab switching with accessible keyboard navigation
 */

class CollectionsTabs {
    constructor() {
        this.tabButtons = document.querySelectorAll('.tab-button');
        this.tabPanels = document.querySelectorAll('.tab-panel');
        this.init();
    }

    init() {
        if (this.tabButtons.length === 0 || this.tabPanels.length === 0) {
            return;
        }

        this.bindTabButtons();
        this.bindKeyboardNavigation();
        this.handleHashChange();

        // Listen for hash changes (back/forward navigation)
        window.addEventListener('hashchange', () => this.handleHashChange());
    }

    /**
     * Handle URL hash change and switch to appropriate tab
     */
    handleHashChange() {
        // Get tab name from hash, default to 'collections'
        const hash = window.location.hash.slice(1);
        const tabName = hash || 'collections';

        this.switchTab(tabName);
    }

    /**
     * Switch to a specific tab
     * @param {string} tabName - The tab identifier to switch to
     */
    switchTab(tabName) {
        // Hide all panels
        this.tabPanels.forEach(panel => {
            panel.hidden = true;
        });

        // Deactivate all buttons
        this.tabButtons.forEach(button => {
            button.setAttribute('aria-selected', 'false');
            button.setAttribute('tabindex', '-1');
        });

        // Show target panel
        const targetPanel = document.getElementById(tabName);
        if (targetPanel) {
            targetPanel.hidden = false;
        }

        // Activate target button
        const targetButton = document.querySelector(`[data-tab="${tabName}"]`);
        if (targetButton) {
            targetButton.setAttribute('aria-selected', 'true');
            targetButton.setAttribute('tabindex', '0');
        }
    }

    /**
     * Bind click handlers to tab buttons
     */
    bindTabButtons() {
        this.tabButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const tabName = button.dataset.tab;

                // Update hash (triggers hashchange event)
                window.location.hash = tabName;
            });
        });
    }

    /**
     * Add keyboard navigation (arrow keys)
     */
    bindKeyboardNavigation() {
        this.tabButtons.forEach((button, index) => {
            button.addEventListener('keydown', (e) => {
                let targetIndex = index;

                // Left arrow or Up arrow
                if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
                    e.preventDefault();
                    targetIndex = index > 0 ? index - 1 : this.tabButtons.length - 1;
                }
                // Right arrow or Down arrow
                else if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
                    e.preventDefault();
                    targetIndex = index < this.tabButtons.length - 1 ? index + 1 : 0;
                }
                // Home key
                else if (e.key === 'Home') {
                    e.preventDefault();
                    targetIndex = 0;
                }
                // End key
                else if (e.key === 'End') {
                    e.preventDefault();
                    targetIndex = this.tabButtons.length - 1;
                }

                // Focus and activate target tab
                if (targetIndex !== index) {
                    const targetButton = this.tabButtons[targetIndex];
                    targetButton.focus();
                    targetButton.click();
                }
            });
        });
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new CollectionsTabs();
    });
} else {
    new CollectionsTabs();
}
