/**
 * Dictionary Search Component
 *
 * Shared search functionality for:
 * - Library browser search bar
 * - Knowledge sidebar search
 * - Header global search
 *
 * Features:
 * - Autocomplete suggestions
 * - Search by headword, citation form, or guide word
 * - Debounced input
 * - Keyboard navigation
 */

class DictionarySearch {
    constructor(inputElement, options = {}) {
        this.input = inputElement;
        this.options = {
            minChars: 2,
            debounceMs: 300,
            maxSuggestions: 10,
            onSelect: options.onSelect || this.defaultOnSelect.bind(this),
            apiEndpoint: options.apiEndpoint || '/api/glossary-browse.php',
            placeholder: options.placeholder || 'Search by word or meaning...',
            showLanguageBadges: options.showLanguageBadges ?? true,
            compact: options.compact ?? false
        };

        this.suggestions = [];
        this.selectedIndex = -1;
        this.debounceTimer = null;
        this.suggestionsContainer = null;

        this.init();
    }

    /**
     * Initialize search component
     */
    init() {
        // Set placeholder
        this.input.setAttribute('placeholder', this.options.placeholder);

        // Create suggestions container
        this.createSuggestionsContainer();

        // Attach event listeners
        this.attachEventListeners();
    }

    /**
     * Create suggestions dropdown container
     */
    createSuggestionsContainer() {
        this.suggestionsContainer = document.createElement('div');
        this.suggestionsContainer.className = 'search-suggestions';
        this.suggestionsContainer.setAttribute('role', 'listbox');
        this.suggestionsContainer.hidden = true;

        // Insert after input
        this.input.parentNode.insertBefore(this.suggestionsContainer, this.input.nextSibling);
    }

    /**
     * Attach event listeners
     */
    attachEventListeners() {
        // Input event (debounced)
        this.input.addEventListener('input', (e) => {
            this.handleInput(e.target.value);
        });

        // Keyboard navigation
        this.input.addEventListener('keydown', (e) => {
            this.handleKeyDown(e);
        });

        // Focus/blur
        this.input.addEventListener('focus', () => {
            if (this.suggestions.length > 0) {
                this.showSuggestions();
            }
        });

        this.input.addEventListener('blur', () => {
            // Delay to allow click on suggestion
            setTimeout(() => this.hideSuggestions(), 200);
        });

        // Click outside to close
        document.addEventListener('click', (e) => {
            if (!this.input.contains(e.target) && !this.suggestionsContainer.contains(e.target)) {
                this.hideSuggestions();
            }
        });
    }

    /**
     * Handle input with debouncing
     */
    handleInput(value) {
        clearTimeout(this.debounceTimer);

        if (value.length < this.options.minChars) {
            this.hideSuggestions();
            return;
        }

        this.debounceTimer = setTimeout(() => {
            this.fetchSuggestions(value);
        }, this.options.debounceMs);
    }

    /**
     * Fetch suggestions from API
     */
    async fetchSuggestions(query) {
        try {
            const params = new URLSearchParams({
                search: query,
                limit: this.options.maxSuggestions,
                offset: 0
            });

            const response = await fetch(`${this.options.apiEndpoint}?${params}`);
            if (!response.ok) throw new Error('Search API error');

            const data = await response.json();
            this.suggestions = data.entries || [];
            this.renderSuggestions();
        } catch (error) {
            console.error('Error fetching suggestions:', error);
            this.suggestions = [];
            this.hideSuggestions();
        }
    }

    /**
     * Render suggestions dropdown
     */
    renderSuggestions() {
        if (this.suggestions.length === 0) {
            this.hideSuggestions();
            return;
        }

        const html = this.suggestions.map((entry, index) => `
            <div
                class="search-suggestion ${index === this.selectedIndex ? 'selected' : ''}"
                data-index="${index}"
                data-entry-id="${this.escapeHtml(entry.entry_id)}"
                role="option"
                aria-selected="${index === this.selectedIndex}"
            >
                <div class="suggestion-main">
                    <span class="suggestion-headword">${this.highlightMatch(entry.headword)}</span>
                    ${entry.guide_word ? `<span class="suggestion-guide-word">[${this.escapeHtml(entry.guide_word)}]</span>` : ''}
                </div>
                <div class="suggestion-meta">
                    ${this.options.showLanguageBadges ? `<span class="badge badge--language">${this.getLanguageLabel(entry.language)}</span>` : ''}
                    <span class="badge badge--pos">${this.escapeHtml(entry.pos)}</span>
                    ${!this.options.compact ? `<span class="suggestion-count">${entry.icount} uses</span>` : ''}
                </div>
            </div>
        `).join('');

        this.suggestionsContainer.innerHTML = html;

        // Attach click listeners
        this.suggestionsContainer.querySelectorAll('.search-suggestion').forEach(item => {
            item.addEventListener('click', () => {
                const index = parseInt(item.dataset.index);
                this.selectSuggestion(index);
            });
        });

        this.showSuggestions();
    }

    /**
     * Show suggestions dropdown
     */
    showSuggestions() {
        this.suggestionsContainer.hidden = false;
    }

    /**
     * Hide suggestions dropdown
     */
    hideSuggestions() {
        this.suggestionsContainer.hidden = true;
        this.selectedIndex = -1;
    }

    /**
     * Handle keyboard navigation
     */
    handleKeyDown(e) {
        if (this.suggestions.length === 0) return;

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectedIndex = Math.min(this.selectedIndex + 1, this.suggestions.length - 1);
                this.renderSuggestions();
                break;

            case 'ArrowUp':
                e.preventDefault();
                this.selectedIndex = Math.max(this.selectedIndex - 1, -1);
                this.renderSuggestions();
                break;

            case 'Enter':
                e.preventDefault();
                if (this.selectedIndex >= 0) {
                    this.selectSuggestion(this.selectedIndex);
                } else if (this.suggestions.length > 0) {
                    this.selectSuggestion(0);
                }
                break;

            case 'Escape':
                this.hideSuggestions();
                this.input.blur();
                break;
        }
    }

    /**
     * Select a suggestion
     */
    selectSuggestion(index) {
        if (index < 0 || index >= this.suggestions.length) return;

        const entry = this.suggestions[index];
        this.options.onSelect(entry);
        this.hideSuggestions();
        this.input.value = ''; // Clear input after selection
    }

    /**
     * Default selection handler (navigate to word detail page)
     */
    defaultOnSelect(entry) {
        window.location.href = `/library/word/${encodeURIComponent(entry.entry_id)}`;
    }

    /**
     * Highlight matching text in suggestions
     */
    highlightMatch(text) {
        if (!text) return '';

        const query = this.input.value.trim();
        if (!query) return this.escapeHtml(text);

        const regex = new RegExp(`(${this.escapeRegex(query)})`, 'gi');
        const escaped = this.escapeHtml(text);
        return escaped.replace(regex, '<mark>$1</mark>');
    }

    /**
     * Get language label
     */
    getLanguageLabel(langCode) {
        const labels = {
            'sux': 'Sumerian',
            'akk': 'Akkadian',
            'akk-x-stdbab': 'Std. Babylonian',
            'akk-x-oldbab': 'Old Babylonian',
            'akk-x-neoass': 'Neo-Assyrian'
        };

        return labels[langCode] || langCode;
    }

    /**
     * Escape HTML
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Escape regex special characters
     */
    escapeRegex(text) {
        return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    /**
     * Destroy search component
     */
    destroy() {
        clearTimeout(this.debounceTimer);
        if (this.suggestionsContainer) {
            this.suggestionsContainer.remove();
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DictionarySearch;
}
