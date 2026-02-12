/**
 * Unified Search Component
 * Handles typeahead search across all entity types with smart prioritization
 */

class UnifiedSearch {
    constructor() {
        this.input = document.querySelector('.header-search input');
        this.dropdown = null;
        this.debounceTimeout = null;
        this.currentQuery = '';
        this.selectedIndex = -1;
        this.results = [];
        this.abortController = null;

        this.init();
    }

    init() {
        if (!this.input) return;

        // Create dropdown element
        this.createDropdown();

        // Bind event handlers
        this.input.addEventListener('input', this.handleInput.bind(this));
        this.input.addEventListener('keydown', this.handleKeydown.bind(this));
        this.input.addEventListener('focus', this.handleFocus.bind(this));

        // Close dropdown on outside click
        document.addEventListener('click', this.handleOutsideClick.bind(this));

        // Close dropdown on escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this.closeDropdown();
        });

        // Prevent form submission when dropdown is open
        const form = this.input.closest('form');
        if (form) {
            form.addEventListener('submit', (e) => {
                if (this.dropdown.classList.contains('is-open') && this.results.length > 0) {
                    e.preventDefault();
                    if (this.selectedIndex >= 0) {
                        this.selectResult(this.selectedIndex);
                    } else {
                        // Navigate to first result
                        this.selectResult(0);
                    }
                }
            });
        }
    }

    createDropdown() {
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'search-dropdown';
        this.dropdown.id = 'search-dropdown';
        this.dropdown.setAttribute('role', 'listbox');

        this.dropdown.innerHTML = `
            <div class="search-dropdown__content"></div>
            <div class="search-dropdown__loading" style="display: none;">
                <span>Searching...</span>
            </div>
            <div class="search-dropdown__empty" style="display: none;">
                <p>No results found for "<span class="search-query"></span>"</p>
            </div>
        `;

        this.input.parentElement.appendChild(this.dropdown);
        this.input.parentElement.style.position = 'relative';
    }

    handleInput(e) {
        const query = e.target.value.trim();

        // Clear existing debounce
        if (this.debounceTimeout) {
            clearTimeout(this.debounceTimeout);
        }

        // Cancel pending request
        if (this.abortController) {
            this.abortController.abort();
        }

        // If query is empty, close dropdown
        if (!query) {
            this.closeDropdown();
            return;
        }

        // Debounce search
        this.debounceTimeout = setTimeout(() => {
            this.performSearch(query);
        }, 200);
    }

    async performSearch(query) {
        this.currentQuery = query;
        this.showLoading();

        try {
            // Create abort controller for this request
            this.abortController = new AbortController();

            const response = await fetch(
                `/api/search.php?q=${encodeURIComponent(query)}&limit=20`,
                { signal: this.abortController.signal }
            );

            if (!response.ok) {
                throw new Error('Search failed');
            }

            const data = await response.json();
            this.displayResults(data);

        } catch (err) {
            if (err.name === 'AbortError') {
                // Request was cancelled, ignore
                return;
            }
            console.error('Search error:', err);
            this.showError();
        }
    }

    displayResults(data) {
        const content = this.dropdown.querySelector('.search-dropdown__content');
        const loading = this.dropdown.querySelector('.search-dropdown__loading');
        const empty = this.dropdown.querySelector('.search-dropdown__empty');

        loading.style.display = 'none';

        if (!data.categories || data.categories.length === 0) {
            empty.style.display = 'block';
            empty.querySelector('.search-query').textContent = this.currentQuery;
            content.innerHTML = '';
            this.openDropdown();
            return;
        }

        empty.style.display = 'none';

        // Build HTML
        let html = '';
        this.results = [];

        data.categories.forEach(category => {
            if (category.results.length === 0) return;

            html += `
                <div class="search-category" data-category="${category.type}">
                    <div class="search-category__header">
                        <span class="search-category__label">${this.escapeHtml(category.label)}</span>
                        <span class="search-category__count">${category.count}</span>
                    </div>
                    <div class="search-category__results">
            `;

            category.results.forEach(result => {
                const resultHtml = this.renderResult(category.type, result);
                html += resultHtml;
                this.results.push({
                    type: category.type,
                    data: result
                });
            });

            html += `
                    </div>
                </div>
            `;
        });

        content.innerHTML = html;
        this.selectedIndex = -1;
        this.openDropdown();

        // Add click handlers
        content.querySelectorAll('[role="option"]').forEach((el, idx) => {
            el.addEventListener('click', (e) => {
                e.preventDefault();
                this.selectResult(idx);
            });
        });
    }

    renderResult(type, data) {
        switch (type) {
            case 'tablets':
                return TabletListItem.render(data, { search: true });

            case 'signs':
                return `
                    <a href="/dictionary/signs/?sign=${encodeURIComponent(data.sign_id)}"
                       class="search-result search-result--sign"
                       role="option">
                        <div class="search-result__content">
                            <div class="search-result__title">
                                ${data.utf8 || this.escapeHtml(data.sign_id)}
                                ${data.values ? `<span class="search-result__meta">(${this.escapeHtml(data.values)})</span>` : ''}
                            </div>
                            <div class="search-result__meta">Sign ID: ${this.escapeHtml(data.sign_id)}</div>
                        </div>
                    </a>
                `;

            case 'dictionary':
                return WordListItem.render(data, { search: true });

            case 'collections':
                return CollectionListItem.render(data, { search: true });

            case 'composites':
                return `
                    <a href="/composites/${encodeURIComponent(data.q_number)}"
                       class="search-result search-result--composite"
                       role="option">
                        <div class="search-result__content">
                            <div class="search-result__title">${this.escapeHtml(data.q_number)}</div>
                            <div class="search-result__meta">
                                ${data.designation ? this.escapeHtml(data.designation) : ''}
                                ${data.tablet_count ? ` · ${data.tablet_count} exemplars` : ''}
                            </div>
                        </div>
                    </a>
                `;

            default:
                return '';
        }
    }

    handleKeydown(e) {
        if (!this.dropdown.classList.contains('is-open')) return;

        const resultElements = this.dropdown.querySelectorAll('[role="option"]');

        switch (e.key) {
            case 'ArrowDown':
                e.preventDefault();
                this.selectedIndex = Math.min(this.selectedIndex + 1, resultElements.length - 1);
                this.updateSelection(resultElements);
                break;

            case 'ArrowUp':
                e.preventDefault();
                this.selectedIndex = Math.max(this.selectedIndex - 1, -1);
                this.updateSelection(resultElements);
                break;

            case 'Enter':
                e.preventDefault();
                if (this.selectedIndex >= 0 && resultElements[this.selectedIndex]) {
                    resultElements[this.selectedIndex].click();
                }
                break;

            case 'Escape':
                e.preventDefault();
                this.closeDropdown();
                break;
        }
    }

    updateSelection(elements) {
        elements.forEach((el, idx) => {
            el.classList.toggle('is-selected', idx === this.selectedIndex);
        });

        // Scroll selected item into view
        if (this.selectedIndex >= 0 && elements[this.selectedIndex]) {
            elements[this.selectedIndex].scrollIntoView({
                block: 'nearest',
                behavior: 'smooth'
            });
        }
    }

    selectResult(index) {
        const resultElements = this.dropdown.querySelectorAll('[role="option"]');
        if (resultElements[index]) {
            window.location.href = resultElements[index].href;
        }
    }

    handleFocus() {
        // If there's a query and results, reopen dropdown
        if (this.currentQuery && this.results.length > 0) {
            this.openDropdown();
        }
    }

    handleOutsideClick(e) {
        if (!this.input.parentElement.contains(e.target)) {
            this.closeDropdown();
        }
    }

    openDropdown() {
        this.dropdown.classList.add('is-open');
        this.input.setAttribute('aria-expanded', 'true');

        // Position dropdown to avoid viewport overflow
        this.positionDropdown();
    }

    closeDropdown() {
        this.dropdown.classList.remove('is-open');
        this.input.setAttribute('aria-expanded', 'false');
        this.selectedIndex = -1;
    }

    positionDropdown() {
        const rect = this.input.getBoundingClientRect();
        const spaceBelow = window.innerHeight - rect.bottom;
        const dropdownHeight = this.dropdown.offsetHeight;

        if (spaceBelow < Math.min(dropdownHeight, window.innerHeight * 0.7) && rect.top > spaceBelow) {
            // Position above input
            this.dropdown.style.bottom = 'calc(100% + 4px)';
            this.dropdown.style.top = 'auto';
        } else {
            // Position below (default)
            this.dropdown.style.top = 'calc(100% + 4px)';
            this.dropdown.style.bottom = 'auto';
        }
    }

    showLoading() {
        this.dropdown.querySelector('.search-dropdown__loading').style.display = 'flex';
        this.dropdown.querySelector('.search-dropdown__empty').style.display = 'none';
        this.dropdown.querySelector('.search-dropdown__content').innerHTML = '';
        this.openDropdown();
    }

    showError() {
        const empty = this.dropdown.querySelector('.search-dropdown__empty');
        empty.style.display = 'block';
        empty.querySelector('p').textContent = 'An error occurred. Please try again.';
        this.dropdown.querySelector('.search-dropdown__loading').style.display = 'none';
        this.openDropdown();
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    new UnifiedSearch();
});
