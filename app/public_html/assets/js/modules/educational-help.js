/**
 * Educational Help System
 *
 * Manages educational content for dictionary and tablet pages:
 * - Welcome banner in filter sidebar (collapsible)
 * - Context-sensitive help text
 * - Centralized educational content loading
 *
 * Help is always visible -- no toggle.
 */

class EducationalHelpSystem {
    constructor() {
        this.welcomeKey = 'cuneiform_welcome_shown';
        this.welcomeCollapsedKey = 'cuneiform_welcome_collapsed';
        this.educationalContent = null;
        this._loadPromise = null;
    }

    /**
     * Initialize welcome banner in filter sidebar
     */
    async initWelcomeBanner() {
        const sidebar = document.querySelector('.filter-sidebar');
        if (!sidebar) return;

        await this.loadEducationalContent();

        const collapsed = localStorage.getItem(this.welcomeCollapsedKey);

        const banner = this.createWelcomeBanner();
        sidebar.insertBefore(banner, sidebar.firstChild);

        if (collapsed === 'true') {
            banner.classList.add('collapsed');
        }

        const header = banner.querySelector('.banner-header');
        const toggle = banner.querySelector('.collapse-toggle');

        header.addEventListener('click', () => {
            banner.classList.toggle('collapsed');
            const isCollapsed = banner.classList.contains('collapsed');
            localStorage.setItem(this.welcomeCollapsedKey, isCollapsed);
            toggle.textContent = isCollapsed ? '+' : '\u2212';
        });

        if (!localStorage.getItem(this.welcomeKey)) {
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
                'Click any word for variants and examples'
            ]
        };

        const banner = document.createElement('section');
        banner.className = 'getting-started-banner';

        const isCollapsed = localStorage.getItem(this.welcomeCollapsedKey) === 'true';

        banner.innerHTML = `
            <header class="banner-header">
                <h3>${content.title}</h3>
                <button class="collapse-toggle" aria-label="Toggle guide">${isCollapsed ? '+' : '\u2212'}</button>
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
     * Load educational content from server.
     * Returns cached result on subsequent calls.
     */
    async loadEducationalContent() {
        if (this.educationalContent) return this.educationalContent;
        if (this._loadPromise) return this._loadPromise;

        this._loadPromise = fetch('/api/educational-content.php')
            .then(r => {
                if (!r.ok) throw new Error('Failed to load educational content');
                return r.json();
            })
            .then(data => {
                this.educationalContent = data;
                return data;
            })
            .catch(error => {
                console.error('Error loading educational content:', error);
                this.educationalContent = {};
                return {};
            });

        return this._loadPromise;
    }

    /**
     * Get help text for a specific field
     */
    getHelpText(fieldKey) {
        if (!this.educationalContent?.field_help) return '';
        return this.educationalContent.field_help[fieldKey] || '';
    }

    /**
     * Get a section description by key
     */
    getSectionDescription(key) {
        if (!this.educationalContent?.section_descriptions) return '';
        return this.educationalContent.section_descriptions[key] || '';
    }

    /**
     * Initialize help system on page load
     */
    init() {
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
