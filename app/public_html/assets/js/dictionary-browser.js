/**
 * Dictionary Browser Controller
 *
 * Handles client-side interactions for the 3-column dictionary browser:
 * - State management and URL synchronization
 * - Grouping navigation and expand/collapse
 * - Word list filtering, search, and pagination
 * - Word detail loading
 */

class DictionaryBrowser {
    constructor(options = {}) {
        this.state = {
            groupType: 'all',
            groupValue: null,
            searchQuery: '',
            selectedWordId: null,
            offset: 0,
            total: 0,
            isLoadingList: false,
            isLoadingDetail: false,
            ...options.initialState
        };

        this.debounceTimer = null;
        this.debounceDelay = 300;

        this.elements = {
            browser: document.querySelector('.dict-browser'),
            groupings: document.querySelector('.dict-browser__groupings'),
            wordList: document.querySelector('.dict-word-list'),
            wordListItems: document.querySelector('[data-word-list]'),
            wordCount: document.querySelector('[data-word-count]'),
            detail: document.querySelector('.dict-browser__detail'),
            searchInput: document.querySelector('.dict-word-list__search-input'),
            activeFilter: document.querySelector('.dict-word-list__active-filter'),
            filterLabel: document.querySelector('[data-filter-label]'),
            loadMoreBtn: document.querySelector('[data-action="load-more"]')
        };

        this.init();
    }

    init() {
        this.bindEvents();
        this.syncFromURL();
    }

    // =========================================================================
    // Event Binding
    // =========================================================================

    bindEvents() {
        // Grouping items
        document.querySelectorAll('.dict-groupings__item').forEach(item => {
            item.addEventListener('click', (e) => this.handleGroupingClick(e));
        });

        // Section expand/collapse
        document.querySelectorAll('.dict-groupings__section-header').forEach(header => {
            header.addEventListener('click', (e) => this.handleSectionToggle(e));
        });

        // Mobile groupings toggle
        document.querySelector('[data-action="toggle-groupings"]')?.addEventListener('click', () => {
            this.toggleGroupingsPanel();
        });

        document.querySelector('.dict-groupings__close')?.addEventListener('click', () => {
            this.closeGroupingsPanel();
        });

        document.querySelector('.dict-browser__groupings-backdrop')?.addEventListener('click', () => {
            this.closeGroupingsPanel();
        });

        // Search input
        if (this.elements.searchInput) {
            this.elements.searchInput.addEventListener('input', (e) => {
                this.handleSearchInput(e.target.value);
            });

            this.elements.searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    this.clearSearch();
                }
            });
        }

        // Clear search button
        document.querySelector('[data-action="clear-search"]')?.addEventListener('click', () => {
            this.clearSearch();
        });

        // Clear filter button
        document.querySelector('[data-action="clear-filter"]')?.addEventListener('click', () => {
            this.clearFilter();
        });

        // Clear all button (in empty state)
        document.querySelector('[data-action="clear-all"]')?.addEventListener('click', () => {
            this.clearAll();
        });

        // Word item clicks (delegated)
        this.elements.wordListItems?.addEventListener('click', (e) => {
            const item = e.target.closest('.dict-word-item');
            if (item && !item.classList.contains('dict-word-item--skeleton')) {
                this.selectWord(item.dataset.entryId);
            }
        });

        // Keyboard navigation in word list
        this.elements.wordListItems?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                const item = e.target.closest('.dict-word-item');
                if (item) {
                    e.preventDefault();
                    this.selectWord(item.dataset.entryId);
                }
            }
        });

        // Load more button
        this.elements.loadMoreBtn?.addEventListener('click', () => {
            this.loadMore();
        });

        // Related word clicks in detail panel (delegated)
        this.elements.detail?.addEventListener('click', (e) => {
            const relatedWord = e.target.closest('[data-entry-id]');
            if (relatedWord && relatedWord.tagName === 'A') {
                e.preventDefault();
                this.selectWord(relatedWord.dataset.entryId);
            }
        });

        // Browser history navigation
        window.addEventListener('popstate', (e) => {
            if (e.state) {
                this.restoreState(e.state);
            } else {
                this.syncFromURL();
            }
        });

        // Mobile detail panel close
        document.querySelector('.dict-browser__detail-handle')?.addEventListener('click', () => {
            this.closeMobileDetail();
        });
    }

    // =========================================================================
    // Groupings
    // =========================================================================

    handleGroupingClick(e) {
        const item = e.currentTarget;
        const group = item.dataset.group;
        const value = item.dataset.value || null;

        this.setGroupFilter(group, value);
        this.closeGroupingsPanel();
    }

    handleSectionToggle(e) {
        const section = e.currentTarget.closest('.dict-groupings__section');
        const isExpanded = section.dataset.expanded === 'true';
        section.dataset.expanded = isExpanded ? 'false' : 'true';
    }

    setGroupFilter(groupType, groupValue) {
        // Update active state in UI
        document.querySelectorAll('.dict-groupings__item').forEach(item => {
            const isActive = (groupType === 'all' && item.dataset.group === 'all') ||
                           (item.dataset.group === groupType && item.dataset.value === groupValue);
            item.classList.toggle('dict-groupings__item--active', isActive);
        });

        // Update state and reload
        this.state.groupType = groupType;
        this.state.groupValue = groupValue;
        this.state.offset = 0;
        this.state.selectedWordId = null;

        this.updateActiveFilterDisplay();
        this.loadWordList(true);
        this.updateURL();
    }

    toggleGroupingsPanel() {
        const isOpen = this.elements.groupings.dataset.open === 'true';
        this.elements.groupings.dataset.open = isOpen ? 'false' : 'true';
    }

    closeGroupingsPanel() {
        this.elements.groupings.dataset.open = 'false';
    }

    // =========================================================================
    // Search
    // =========================================================================

    handleSearchInput(value) {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            this.state.searchQuery = value.trim();
            this.state.offset = 0;
            this.state.selectedWordId = null;
            this.loadWordList(true);
            this.updateURL();
        }, this.debounceDelay);
    }

    clearSearch() {
        if (this.elements.searchInput) {
            this.elements.searchInput.value = '';
        }
        this.state.searchQuery = '';
        this.state.offset = 0;
        this.loadWordList(true);
        this.updateURL();
    }

    clearFilter() {
        this.setGroupFilter('all', null);
    }

    clearAll() {
        this.clearSearch();
        this.clearFilter();
    }

    updateActiveFilterDisplay() {
        if (!this.elements.activeFilter) return;

        const isFiltered = this.state.groupType !== 'all';
        this.elements.activeFilter.dataset.visible = isFiltered ? 'true' : 'false';

        if (isFiltered && this.elements.filterLabel) {
            const labels = this.getFilterLabels();
            this.elements.filterLabel.textContent = labels[this.state.groupType]?.[this.state.groupValue] || this.state.groupValue;
        }
    }

    getFilterLabels() {
        return {
            pos: {
                'N': 'Noun', 'V': 'Verb', 'AJ': 'Adjective', 'AV': 'Adverb',
                'PN': 'Personal Name', 'DN': 'Divine Name', 'GN': 'Geographic Name', 'RN': 'Royal Name'
            },
            language: {
                'akk': 'Akkadian', 'sux': 'Sumerian', 'qpn': 'Proper Nouns'
            },
            frequency: {
                '1': 'Hapax', '2-10': 'Rare', '11-100': 'Uncommon', '101-500': 'Common', '500+': 'Very Common'
            }
        };
    }

    // =========================================================================
    // Word List
    // =========================================================================

    async loadWordList(replace = false) {
        if (this.state.isLoadingList) return;

        this.state.isLoadingList = true;
        this.elements.browser?.querySelector('.dict-browser__words')?.setAttribute('data-loading', 'true');

        try {
            const params = new URLSearchParams({
                limit: 50,
                offset: replace ? 0 : this.state.offset
            });

            if (this.state.searchQuery) {
                params.set('search', this.state.searchQuery);
            }

            if (this.state.groupType !== 'all' && this.state.groupValue) {
                params.set('group_type', this.state.groupType);
                params.set('group_value', this.state.groupValue);
            }

            const response = await fetch(`/api/dictionary/browse.php?${params}`);
            const data = await response.json();

            this.state.total = data.total;
            this.state.offset = replace ? data.entries.length : this.state.offset + data.entries.length;

            this.renderWordList(data.entries, replace);
            this.updateWordCount(replace ? data.entries.length : this.state.offset, data.total);
            this.updateLoadMoreButton(data.hasMore);

            // Auto-select first word if replacing and we have results
            if (replace && data.entries.length > 0 && !this.state.selectedWordId) {
                this.selectWord(data.entries[0].entry_id, false);
            }

        } catch (error) {
            console.error('Error loading word list:', error);
        } finally {
            this.state.isLoadingList = false;
            this.elements.browser?.querySelector('.dict-browser__words')?.setAttribute('data-loading', 'false');
        }
    }

    renderWordList(entries, replace) {
        if (!this.elements.wordListItems) return;

        const html = entries.map(entry => this.renderWordItem(entry)).join('');

        if (replace) {
            this.elements.wordListItems.innerHTML = html;
        } else {
            this.elements.wordListItems.insertAdjacentHTML('beforeend', html);
        }

        // Update empty state
        const wordsPanel = this.elements.browser?.querySelector('.dict-browser__words');
        wordsPanel?.setAttribute('data-empty', entries.length === 0 && replace ? 'true' : 'false');
    }

    renderWordItem(entry) {
        const isActive = entry.entry_id === this.state.selectedWordId;
        const langLabels = { 'akk': 'Akkadian', 'sux': 'Sumerian', 'qpn': 'Names' };
        const langLabel = langLabels[entry.language?.split('-')[0]] || entry.language || '';
        const posLabel = entry.pos || '';

        return `
            <div class="dict-word-item ${isActive ? 'dict-word-item--active' : ''}"
                 data-entry-id="${this.escapeHtml(entry.entry_id)}"
                 tabindex="0" role="button">
                <div class="dict-word-item__header">
                    <span class="dict-word-item__headword">${this.escapeHtml(entry.headword)}</span>
                    ${entry.guide_word ? `<span class="dict-word-item__guide-word">[${this.escapeHtml(entry.guide_word)}]</span>` : ''}
                </div>
                <div class="dict-word-item__meta">
                    ${posLabel ? `<span class="dict-word-item__badge dict-word-item__badge--pos">${this.escapeHtml(posLabel)}</span>` : ''}
                    ${langLabel ? `<span class="dict-word-item__badge dict-word-item__badge--lang">${this.escapeHtml(langLabel)}</span>` : ''}
                    <span class="dict-word-item__count">${entry.icount?.toLocaleString() || 0}</span>
                </div>
            </div>
        `;
    }

    updateWordCount(showing, total) {
        if (this.elements.wordCount) {
            this.elements.wordCount.textContent = `Showing ${showing.toLocaleString()} of ${total.toLocaleString()}`;
        }
    }

    updateLoadMoreButton(hasMore) {
        if (this.elements.loadMoreBtn) {
            this.elements.loadMoreBtn.dataset.hidden = hasMore ? 'false' : 'true';
        }
    }

    loadMore() {
        this.loadWordList(false);
    }

    // =========================================================================
    // Word Detail
    // =========================================================================

    async selectWord(entryId, updateUrl = true) {
        if (!entryId || entryId === this.state.selectedWordId) return;

        // Update active state in list
        document.querySelectorAll('.dict-word-item').forEach(item => {
            item.classList.toggle('dict-word-item--active', item.dataset.entryId === entryId);
        });

        this.state.selectedWordId = entryId;

        if (updateUrl) {
            this.updateURL();
        }

        // Show mobile detail panel
        if (window.innerWidth <= 768) {
            this.elements.detail.dataset.open = 'true';
        }

        await this.loadWordDetail(entryId);
    }

    async loadWordDetail(entryId) {
        if (this.state.isLoadingDetail) return;

        this.state.isLoadingDetail = true;
        this.elements.detail?.setAttribute('data-loading', 'true');

        try {
            const response = await fetch(`/api/dictionary/word-detail.php?entry_id=${encodeURIComponent(entryId)}`);
            const data = await response.json();

            this.renderWordDetail(data);

        } catch (error) {
            console.error('Error loading word detail:', error);
            this.renderDetailError();
        } finally {
            this.state.isLoadingDetail = false;
            this.elements.detail?.setAttribute('data-loading', 'false');
        }
    }

    renderWordDetail(data) {
        if (!this.elements.detail || !data || !data.entry) return;

        // Build HTML for word detail
        // Note: This is a simplified version - the full detail is rendered server-side
        // For dynamic updates, we fetch the rendered HTML or build it client-side

        const entry = data.entry;
        const langLabels = {
            'sux': 'Sumerian', 'akk': 'Akkadian', 'akk-x-stdbab': 'Standard Babylonian',
            'qpn': 'Personal Name'
        };
        const posLabels = {
            'N': 'Noun', 'V': 'Verb', 'AJ': 'Adjective', 'AV': 'Adverb',
            'PN': 'Personal Name', 'DN': 'Divine Name', 'GN': 'Geographic Name'
        };

        const langLabel = langLabels[entry.language] || entry.language;
        const posLabel = posLabels[entry.pos] || entry.pos;

        const html = `
            <div class="dict-browser__detail-handle"></div>
            <div class="word-detail-content">
                <div class="page-header word-header">
                    <div class="page-header-main">
                        <div class="page-header-title">
                            <h1>${this.escapeHtml(entry.headword)}${entry.guide_word ? `<span class="guide-word">[${this.escapeHtml(entry.guide_word)}]</span>` : ''}</h1>
                        </div>
                        <div class="page-header-actions">
                            <span class="badge badge--pos">${this.escapeHtml(posLabel)}</span>
                            <span class="badge badge--language">${this.escapeHtml(langLabel)}</span>
                            <span class="badge badge--frequency">${(entry.icount || 0).toLocaleString()} attestations</span>
                        </div>
                    </div>
                </div>

                <div class="word-meta tablet-meta">
                    <dl class="tablet-meta__row">
                        <div class="meta-item">
                            <dt>Citation Form</dt>
                            <dd>${this.escapeHtml(entry.citation_form || entry.headword)}</dd>
                        </div>
                        ${entry.guide_word ? `
                        <div class="meta-item">
                            <dt>Guide Word</dt>
                            <dd>${this.escapeHtml(entry.guide_word)}</dd>
                        </div>` : ''}
                        <div class="meta-item">
                            <dt>Part of Speech</dt>
                            <dd>${this.escapeHtml(posLabel)}</dd>
                        </div>
                        <div class="meta-item">
                            <dt>Language</dt>
                            <dd>${this.escapeHtml(langLabel)}</dd>
                        </div>
                        <div class="meta-item">
                            <dt>Corpus Frequency</dt>
                            <dd>${(entry.icount || 0).toLocaleString()} occurrences</dd>
                        </div>
                    </dl>
                </div>

                ${this.renderVariants(data.variants)}
                ${this.renderSigns(data.signs)}
                ${this.renderAttestations(data.attestations?.sample, entry.icount)}
            </div>
            <div class="dict-loading-overlay">
                <div class="dict-spinner"></div>
            </div>
        `;

        this.elements.detail.innerHTML = html;

        // Rebind mobile close handler
        document.querySelector('.dict-browser__detail-handle')?.addEventListener('click', () => {
            this.closeMobileDetail();
        });
    }

    renderVariants(variants) {
        if (!variants || variants.length === 0) return '';

        const maxCount = Math.max(...variants.map(v => v.count || 0));

        return `
            <section class="word-section">
                <h2>Attested Forms</h2>
                <div class="variants-chart">
                    ${variants.map(v => {
                        const pct = maxCount > 0 ? (v.count / maxCount) * 100 : 0;
                        return `
                            <div class="variant-bar">
                                <span class="variant-form">${this.escapeHtml(v.form)}</span>
                                <div class="variant-frequency-container">
                                    <div class="variant-frequency" style="width: ${pct}%"></div>
                                </div>
                                <span class="variant-count">${v.count} times</span>
                            </div>
                        `;
                    }).join('')}
                </div>
            </section>
        `;
    }

    renderSigns(signs) {
        if (!signs || signs.length === 0) return '';

        return `
            <section class="word-section">
                <h2>Cuneiform Signs</h2>
                <div class="sign-breakdown">
                    ${signs.map(s => `
                        <a href="/dictionary/sign/${encodeURIComponent(s.sign_id)}" class="sign-item">
                            <span class="sign-cuneiform">${s.utf8 || ''}</span>
                            <span class="sign-id">${this.escapeHtml(s.sign_id)}</span>
                            <span class="sign-value">${this.escapeHtml(s.sign_value)}</span>
                            ${s.value_type ? `<span class="sign-type">${this.escapeHtml(s.value_type)}</span>` : ''}
                        </a>
                    `).join('')}
                </div>
            </section>
        `;
    }

    renderAttestations(attestations, totalCount) {
        if (!attestations || attestations.length === 0) return '';

        return `
            <section class="word-section">
                <h2>Corpus Examples</h2>
                <div class="examples-list">
                    ${attestations.map(a => `
                        <div class="example-item">
                            <div class="example-header">
                                <a href="/tablets/detail.php?p=${encodeURIComponent(a.p_number)}" class="p-number">${this.escapeHtml(a.p_number)}</a>
                                ${a.period || a.provenience ? `<span class="example-meta">${this.escapeHtml([a.period, a.provenience].filter(Boolean).join(' · '))}</span>` : ''}
                            </div>
                            <div class="example-content">
                                <span class="transliteration">${this.escapeHtml(a.form)}</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
                <p class="examples-footer">
                    Showing ${attestations.length} of ${(totalCount || 0).toLocaleString()} attestations
                </p>
            </section>
        `;
    }

    renderDetailError() {
        if (!this.elements.detail) return;

        this.elements.detail.innerHTML = `
            <div class="dict-browser__detail-handle"></div>
            <div class="dict-error">
                <svg class="dict-error__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M12 8v4M12 16h.01"/>
                </svg>
                <h3 class="dict-error__title">Error loading word</h3>
                <p class="dict-error__description">Unable to load the word details. Please try again.</p>
                <button class="dict-error__retry" onclick="window.dictionaryBrowser.loadWordDetail('${this.state.selectedWordId}')">
                    Retry
                </button>
            </div>
            <div class="dict-loading-overlay">
                <div class="dict-spinner"></div>
            </div>
        `;
    }

    closeMobileDetail() {
        if (this.elements.detail) {
            this.elements.detail.dataset.open = 'false';
        }
    }

    // =========================================================================
    // URL Management
    // =========================================================================

    updateURL() {
        const params = new URLSearchParams();

        if (this.state.selectedWordId) {
            params.set('word', this.state.selectedWordId);
        }

        if (this.state.groupType !== 'all' && this.state.groupValue) {
            params.set('group', this.state.groupType);
            params.set('value', this.state.groupValue);
        }

        if (this.state.searchQuery) {
            params.set('search', this.state.searchQuery);
        }

        const url = params.toString() ? `/dictionary/?${params}` : '/dictionary/';
        history.pushState({ ...this.state }, '', url);
    }

    syncFromURL() {
        const params = new URLSearchParams(window.location.search);

        this.state.selectedWordId = params.get('word') || null;
        this.state.groupType = params.get('group') || 'all';
        this.state.groupValue = params.get('value') || null;
        this.state.searchQuery = params.get('search') || '';

        // Update UI to match URL state
        if (this.elements.searchInput) {
            this.elements.searchInput.value = this.state.searchQuery;
        }

        this.updateActiveFilterDisplay();

        // Update grouping active states
        document.querySelectorAll('.dict-groupings__item').forEach(item => {
            const isActive = (this.state.groupType === 'all' && item.dataset.group === 'all') ||
                           (item.dataset.group === this.state.groupType && item.dataset.value === this.state.groupValue);
            item.classList.toggle('dict-groupings__item--active', isActive);
        });
    }

    restoreState(state) {
        this.state = { ...this.state, ...state };

        if (this.elements.searchInput) {
            this.elements.searchInput.value = this.state.searchQuery || '';
        }

        this.updateActiveFilterDisplay();
        this.loadWordList(true);

        if (this.state.selectedWordId) {
            this.loadWordDetail(this.state.selectedWordId);
        }
    }

    // =========================================================================
    // Utilities
    // =========================================================================

    escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = DictionaryBrowser;
}
