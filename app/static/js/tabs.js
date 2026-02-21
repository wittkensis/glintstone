/**
 * Tab navigation system
 * Handles tab switching, keyboard navigation, and hash-based routing
 */

class TabManager {
    constructor() {
        this.tabs = document.querySelectorAll('.tab-button');
        this.panels = document.querySelectorAll('.tab-panel');

        if (this.tabs.length === 0 || this.panels.length === 0) return;

        this.init();
    }

    init() {
        // Click handlers
        this.tabs.forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab(tab.dataset.tab);
            });
        });

        // Keyboard navigation
        this.tabs.forEach((tab, index) => {
            tab.addEventListener('keydown', (e) => {
                let newIndex = index;

                if (e.key === 'ArrowRight') {
                    e.preventDefault();
                    newIndex = (index + 1) % this.tabs.length;
                } else if (e.key === 'ArrowLeft') {
                    e.preventDefault();
                    newIndex = (index - 1 + this.tabs.length) % this.tabs.length;
                } else if (e.key === 'Home') {
                    e.preventDefault();
                    newIndex = 0;
                } else if (e.key === 'End') {
                    e.preventDefault();
                    newIndex = this.tabs.length - 1;
                }

                if (newIndex !== index) {
                    this.tabs[newIndex].focus();
                    this.switchTab(this.tabs[newIndex].dataset.tab);
                }
            });
        });

        // Hash-based routing
        window.addEventListener('hashchange', () => {
            const hash = window.location.hash.slice(1);
            if (hash) {
                this.switchTab(hash);
            }
        });

        // Load from hash on init
        const initialHash = window.location.hash.slice(1);
        if (initialHash) {
            this.switchTab(initialHash);
        }
    }

    switchTab(tabName) {
        // Update tab buttons
        this.tabs.forEach(tab => {
            const isActive = tab.dataset.tab === tabName;
            tab.classList.toggle('active', isActive);
            tab.setAttribute('aria-selected', isActive);
            tab.setAttribute('tabindex', isActive ? '0' : '-1');
        });

        // Update panels
        this.panels.forEach(panel => {
            const isActive = panel.id === `${tabName}-panel`;
            panel.classList.toggle('active', isActive);
            panel.hidden = !isActive;
        });

        // Update hash without scrolling
        const newHash = `#${tabName}`;
        if (window.location.hash !== newHash) {
            history.replaceState(null, '', newHash);
        }
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => new TabManager());
} else {
    new TabManager();
}
