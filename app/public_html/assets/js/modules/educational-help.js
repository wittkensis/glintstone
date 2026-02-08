/**
 * Educational Help System
 *
 * Unified help system serving all users through comprehensive content.
 *
 * Manages:
 * - Help tooltip visibility
 * - Welcome banner in sidebar (collapsible)
 * - Context-sensitive help
 */

class EducationalHelpSystem {
    constructor() {
        this.welcomeKey = 'cuneiform_welcome_shown';
        this.welcomeCollapsedKey = 'cuneiform_welcome_collapsed';
        this.helpVisibilityKey = 'cuneiform_help_visible';
        this.helpVisible = this.loadHelpVisibility();
        this.educationalContent = null;
    }

    /**
     * Load help visibility preference
     */
    loadHelpVisibility() {
        const stored = localStorage.getItem(this.helpVisibilityKey);
        if (stored === null) return true; // Default to visible
        return stored === 'true';
    }

    /**
     * Toggle help visibility
     */
    toggleHelpVisibility() {
        this.helpVisible = !this.helpVisible;
        localStorage.setItem(this.helpVisibilityKey, this.helpVisible);
        this.emit('helpVisibilityChanged', this.helpVisible);
        this.updateHelpElements();
    }

    /**
     * Set help visibility explicitly
     */
    setHelpVisibility(visible) {
        this.helpVisible = visible;
        localStorage.setItem(this.helpVisibilityKey, visible);
        this.emit('helpVisibilityChanged', visible);
        this.updateHelpElements();
    }

    /**
     * Update all help elements on the page based on visibility preference
     */
    updateHelpElements() {
        document.querySelectorAll('.help-toggle').forEach(button => {
            button.style.display = this.helpVisible ? '' : 'none';
        });

        // Hide all open tooltips if help is turned off
        if (!this.helpVisible) {
            document.querySelectorAll('.field-help').forEach(help => {
                help.hidden = true;
            });
        }
    }

    /**
     * Initialize welcome banner in filter sidebar
     */
    async initWelcomeBanner() {
        const sidebar = document.querySelector('.filter-sidebar');
        if (!sidebar) return;

        await this.loadEducationalContent();

        const shown = localStorage.getItem(this.welcomeKey);
        const collapsed = localStorage.getItem(this.welcomeCollapsedKey);

        // Create and add banner to sidebar
        const banner = this.createWelcomeBanner();
        sidebar.insertBefore(banner, sidebar.firstChild);

        // Set initial collapsed state
        if (collapsed === 'true') {
            banner.classList.add('collapsed');
        }

        // Add collapse/expand handler
        const header = banner.querySelector('.banner-header');
        const toggle = banner.querySelector('.collapse-toggle');

        header.addEventListener('click', () => {
            banner.classList.toggle('collapsed');
            const isCollapsed = banner.classList.contains('collapsed');
            localStorage.setItem(this.welcomeCollapsedKey, isCollapsed);
            toggle.textContent = isCollapsed ? '+' : '−';
        });

        // Mark as shown
        if (!shown) {
            localStorage.setItem(this.welcomeKey, 'true');
        }
    }

    /**
     * Create welcome banner HTML for sidebar
     */
    createWelcomeBanner() {
        const content = this.educationalContent?.welcome || {
            title: 'How to Use the Dictionary',
            description: 'Explore 21,000+ words from ancient Sumerian and Akkadian:',
            features: [
                'Search by ancient word form OR English meaning',
                'Filter by language, grammar, or frequency',
                'Click any word for variants and examples',
                'Hover ⓘ icons for explanations'
            ]
        };

        const banner = document.createElement('section');
        banner.className = 'getting-started-banner';

        const isCollapsed = localStorage.getItem(this.welcomeCollapsedKey) === 'true';

        banner.innerHTML = `
            <header class="banner-header">
                <h3>
                    <span class="icon">ℹ️</span>
                    ${content.title}
                </h3>
                <button class="collapse-toggle" aria-label="Toggle guide">${isCollapsed ? '+' : '−'}</button>
            </header>
            <div class="banner-content">
                <p>${content.description}</p>
                <ul>
                    ${content.features.map(f => `<li>${f}</li>`).join('')}
                </ul>
            </div>
        `;

        return banner;
    }

    /**
     * Start guided tour
     */
    async startGuidedTour() {
        // TODO: Implement interactive tour using tooltips
        console.log('Guided tour started');
        // This could use a library like Shepherd.js or Driver.js
        // For now, just a placeholder
    }

    /**
     * Load educational content from server
     */
    async loadEducationalContent() {
        if (this.educationalContent) return;

        try {
            const response = await fetch('/includes/educational-content.php');
            if (!response.ok) throw new Error('Failed to load educational content');

            const text = await response.text();
            this.educationalContent = JSON.parse(text);
        } catch (error) {
            console.error('Error loading educational content:', error);
            this.educationalContent = {};
        }
    }

    /**
     * Get help text for a specific field
     */
    getHelpText(fieldKey) {
        if (!this.educationalContent || !this.educationalContent.field_help) return '';

        const helpData = this.educationalContent.field_help[fieldKey];
        return helpData || ''; // Simple string lookup (no more user levels)
    }

    /**
     * Initialize help system on page load
     */
    init() {
        // Update help elements based on visibility preference
        this.updateHelpElements();

        // Initialize welcome banner in sidebar (if on dictionary pages)
        if (document.querySelector('.filtered-list-page') || document.querySelector('.dictionary-word-detail')) {
            this.initWelcomeBanner();
        }
    }

    /**
     * Simple event emitter
     */
    emit(event, data) {
        document.dispatchEvent(new CustomEvent(`educationalHelp:${event}`, { detail: data }));
    }

    /**
     * Listen to events
     */
    on(event, callback) {
        document.addEventListener(`educationalHelp:${event}`, (e) => callback(e.detail));
    }
}

// Create singleton instance
const educationalHelp = new EducationalHelpSystem();

// Auto-initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => educationalHelp.init());
} else {
    educationalHelp.init();
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EducationalHelpSystem;
}
