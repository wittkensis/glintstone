/**
 * Educational Help System
 *
 * Manages:
 * - User level preferences (student, scholar, expert)
 * - Help tooltip visibility
 * - First-time welcome overlay
 * - Context-sensitive help
 */

class EducationalHelpSystem {
    constructor() {
        this.storageKey = 'cuneiform_user_level';
        this.welcomeKey = 'cuneiform_welcome_shown';
        this.helpVisibilityKey = 'cuneiform_help_visible';
        this.userLevel = this.loadUserLevel();
        this.helpVisible = this.loadHelpVisibility();
        this.educationalContent = null;
    }

    /**
     * Load user level from localStorage
     */
    loadUserLevel() {
        const stored = localStorage.getItem(this.storageKey);
        return stored || 'student'; // Default to student
    }

    /**
     * Save user level to localStorage
     */
    saveUserLevel(level) {
        if (['student', 'scholar', 'expert'].includes(level)) {
            this.userLevel = level;
            localStorage.setItem(this.storageKey, level);
            this.emit('levelChanged', level);
        }
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
     * Check if welcome overlay should be shown
     */
    shouldShowWelcome() {
        return !localStorage.getItem(this.welcomeKey);
    }

    /**
     * Mark welcome overlay as shown
     */
    markWelcomeShown() {
        localStorage.setItem(this.welcomeKey, 'true');
    }

    /**
     * Show welcome overlay
     */
    async showWelcomeOverlay() {
        if (!this.shouldShowWelcome()) return;

        await this.loadEducationalContent();

        const overlay = this.createWelcomeOverlay();
        document.body.appendChild(overlay);

        // Attach event listeners
        overlay.querySelector('.welcome-close')?.addEventListener('click', () => {
            this.dismissWelcome(overlay);
        });

        overlay.querySelector('.welcome-start')?.addEventListener('click', () => {
            this.dismissWelcome(overlay);
        });

        overlay.querySelector('.welcome-tour')?.addEventListener('click', () => {
            this.dismissWelcome(overlay);
            this.startGuidedTour();
        });

        // User level selection
        overlay.querySelectorAll('.user-level-option').forEach(button => {
            button.addEventListener('click', (e) => {
                const level = button.dataset.level;
                this.saveUserLevel(level);
                overlay.querySelectorAll('.user-level-option').forEach(btn => {
                    btn.classList.remove('selected');
                });
                button.classList.add('selected');
            });
        });
    }

    /**
     * Create welcome overlay HTML
     */
    createWelcomeOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'educational-welcome-overlay';
        overlay.innerHTML = `
            <div class="welcome-modal">
                <button class="welcome-close" aria-label="Close">&times;</button>

                <h1>Welcome to the Cuneiform Library!</h1>

                <p class="welcome-intro">
                    This browser lets you explore 21,000+ words from ancient
                    Sumerian and Akkadian languages, along with 3,300+ cuneiform signs.
                </p>

                <div class="welcome-features">
                    <ul>
                        <li>Search by ancient word form (e.g., "lugal") OR English meaning (e.g., "king")</li>
                        <li>Filter by language, grammar, or frequency</li>
                        <li>Explore cuneiform signs and their values</li>
                        <li>Navigate between bilingual equivalents (Sumerian ↔ Akkadian)</li>
                        <li>See corpus examples from real ancient tablets</li>
                    </ul>
                </div>

                <div class="user-level-selection">
                    <h3>Choose your experience level:</h3>
                    <div class="user-level-options">
                        <button class="user-level-option selected" data-level="student">
                            <strong>Student</strong>
                            <span>Full explanations and examples</span>
                        </button>
                        <button class="user-level-option" data-level="scholar">
                            <strong>Scholar</strong>
                            <span>Concise technical definitions</span>
                        </button>
                        <button class="user-level-option" data-level="expert">
                            <strong>Expert</strong>
                            <span>Minimal help (toggle on demand)</span>
                        </button>
                    </div>
                    <p class="level-note">You can change this anytime in settings</p>
                </div>

                <div class="welcome-actions">
                    <button class="welcome-tour btn btn--secondary">Take guided tour</button>
                    <button class="welcome-start btn btn--primary">Start browsing</button>
                </div>
            </div>
        `;

        return overlay;
    }

    /**
     * Dismiss welcome overlay
     */
    dismissWelcome(overlay) {
        this.markWelcomeShown();
        overlay.remove();
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
        if (!helpData) return '';

        return helpData[this.userLevel] || helpData.student || '';
    }

    /**
     * Initialize help system on page load
     */
    init() {
        // Update help elements based on visibility preference
        this.updateHelpElements();

        // Show welcome overlay if first time
        if (document.querySelector('.library-browser') || document.querySelector('.library-word-detail')) {
            this.showWelcomeOverlay();
        }

        // Add settings toggle to header if not present
        this.addSettingsToggle();
    }

    /**
     * Add help settings toggle to header
     */
    addSettingsToggle() {
        const header = document.querySelector('.site-header');
        if (!header || document.querySelector('.help-settings-toggle')) return;

        const toggle = document.createElement('button');
        toggle.className = 'help-settings-toggle';
        toggle.innerHTML = `
            <span class="help-icon">${this.helpVisible ? '?' : '?'}</span>
            <span class="help-label">${this.helpVisible ? 'Hide Help' : 'Show Help'}</span>
        `;
        toggle.setAttribute('aria-label', 'Toggle help tooltips');
        toggle.addEventListener('click', () => {
            this.toggleHelpVisibility();
            toggle.querySelector('.help-label').textContent = this.helpVisible ? 'Hide Help' : 'Show Help';
        });

        // Insert before search or at end of header
        const searchForm = header.querySelector('.search-form');
        if (searchForm) {
            searchForm.parentNode.insertBefore(toggle, searchForm);
        } else {
            header.appendChild(toggle);
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
