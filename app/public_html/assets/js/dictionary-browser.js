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
            sortBy: 'frequency',
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

        // Sort select
        document.querySelector('[data-action="sort"]')?.addEventListener('change', (e) => {
            this.handleSortChange(e.target.value);
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

        // Detail panel actions (share, toggle, show more)
        this.elements.detail?.addEventListener('click', (e) => {
            // Share button
            const shareBtn = e.target.closest('[data-action="share"]');
            if (shareBtn) {
                this.handleShare(shareBtn.dataset.url);
                return;
            }

            // Meta toggle button
            const metaToggle = e.target.closest('.word-meta__toggle');
            if (metaToggle) {
                this.handleMetaToggle(metaToggle);
                return;
            }

            // Show more/less variants toggle
            const variantsToggle = e.target.closest('[data-action="toggle-variants"]');
            if (variantsToggle) {
                this.handleVariantsToggle(variantsToggle);
                return;
            }

            // Show more/less tablets toggle
            const tabletsToggle = e.target.closest('[data-action="toggle-tablets"]');
            if (tabletsToggle) {
                this.handleTabletsToggle(tabletsToggle);
                return;
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

        // Close all other sections first
        document.querySelectorAll('.dict-groupings__section').forEach(s => {
            if (s !== section) {
                s.dataset.expanded = 'false';
            }
        });

        // Toggle the clicked section
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

    handleSortChange(sortBy) {
        this.state.sortBy = sortBy;
        this.state.offset = 0;
        this.state.selectedWordId = null;
        this.loadWordList(true);
        this.updateURL();
    }

    getFilterLabels() {
        return {
            pos: {
                'N': 'Noun', 'V': 'Verb', 'AJ': 'Adjective', 'AV': 'Adverb', 'NU': 'Number',
                'PRP': 'Preposition', 'PP': 'Possessive Pronoun', 'CNJ': 'Conjunction',
                'DP': 'Demonstrative', 'IP': 'Pronoun', 'RP': 'Reflexive', 'XP': 'Indefinite Pronoun',
                'REL': 'Relative', 'QP': 'Interrogative', 'DET': 'Determiner', 'MOD': 'Modal',
                'J': 'Interjection', 'SBJ': 'Subjunction', 'MA': 'Auxiliary', 'M': 'Morpheme', 'O': 'Other',
                'V/i': 'Intransitive Verb', 'V/t': 'Transitive Verb',
                'PN': 'Personal Name', 'DN': 'Divine Name', 'GN': 'Geographic Name', 'SN': 'Settlement Name',
                'TN': 'Temple Name', 'WN': 'Watercourse Name', 'RN': 'Royal Name', 'EN': 'Ethnic Name',
                'CN': 'Celestial Name', 'ON': 'Object Name', 'MN': 'Month Name', 'AN': 'Artifact Name',
                'LN': 'Line Name'
            },
            language: {
                'akk': 'Akkadian', 'akk-x-stdbab': 'Standard Babylonian', 'akk-x-oldbab': 'Old Babylonian',
                'akk-x-neoass': 'Neo-Assyrian', 'sux': 'Sumerian', 'sux-x-emesal': 'Emesal',
                'xhu': 'Hurrian', 'uga': 'Ugaritic', 'elx': 'Elamite'
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
                offset: replace ? 0 : this.state.offset,
                sort: this.state.sortBy
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
        const langLabels = {
            'akk': 'Akkadian', 'akk-x-stdbab': 'Standard Babylonian', 'akk-x-oldbab': 'Old Babylonian',
            'akk-x-neoass': 'Neo-Assyrian', 'sux': 'Sumerian', 'sux-x-emesal': 'Emesal',
            'xhu': 'Hurrian', 'uga': 'Ugaritic', 'elx': 'Elamite', 'qpn': 'Names'
        };
        const posLabels = {
            'N': 'Noun', 'V': 'Verb', 'AJ': 'Adjective', 'AV': 'Adverb', 'NU': 'Number',
            'PRP': 'Preposition', 'PP': 'Possessive Pronoun', 'CNJ': 'Conjunction',
            'DP': 'Demonstrative', 'IP': 'Pronoun', 'RP': 'Reflexive', 'XP': 'Indefinite Pronoun',
            'REL': 'Relative', 'QP': 'Interrogative', 'DET': 'Determiner', 'MOD': 'Modal',
            'J': 'Interjection', 'SBJ': 'Subjunction', 'MA': 'Auxiliary', 'M': 'Morpheme', 'O': 'Other',
            'V/i': 'Intransitive Verb', 'V/t': 'Transitive Verb',
            'PN': 'Personal Name', 'DN': 'Divine Name', 'GN': 'Geographic Name', 'SN': 'Settlement Name',
            'TN': 'Temple Name', 'WN': 'Watercourse Name', 'RN': 'Royal Name', 'EN': 'Ethnic Name',
            'CN': 'Celestial Name', 'ON': 'Object Name', 'MN': 'Month Name', 'AN': 'Artifact Name',
            'LN': 'Line Name'
        };
        const langLabel = langLabels[entry.language] || langLabels[entry.language?.split('-')[0]] || '';
        const posLabel = posLabels[entry.pos] || entry.pos || '';
        const displayName = entry.citation_form || entry.headword;

        // Conditional badge display based on active filter
        const showPosBadge = this.state.groupType !== 'pos';
        const showLangBadge = this.state.groupType !== 'language';

        return `
            <div class="dict-word-item ${isActive ? 'dict-word-item--active' : ''}"
                 data-entry-id="${this.escapeHtml(entry.entry_id)}"
                 tabindex="0" role="button">
                <div class="dict-word-item__header">
                    <span class="dict-word-item__headword">${this.escapeHtml(displayName)}</span>
                    ${entry.guide_word ? `<span class="dict-word-item__guide-word">${this.escapeHtml(entry.guide_word)}</span>` : ''}
                </div>
                <div class="dict-word-item__meta">
                    ${showPosBadge && posLabel ? `<span class="dict-word-item__badge dict-word-item__badge--pos">${this.escapeHtml(posLabel)}</span>` : ''}
                    ${showLangBadge && langLabel ? `<span class="dict-word-item__badge dict-word-item__badge--lang">${this.escapeHtml(langLabel)}</span>` : ''}
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

    async selectWord(entryId, updateUrl = true, shouldHighlight = false) {
        if (!entryId || entryId === this.state.selectedWordId) return;

        // Update active state in list
        document.querySelectorAll('.dict-word-item').forEach(item => {
            const isActive = item.dataset.entryId === entryId;
            item.classList.toggle('dict-word-item--active', isActive);

            // Add highlight animation if requested
            if (isActive && shouldHighlight) {
                item.classList.add('dict-word-item--highlight');
                // Remove highlight class after animation completes
                setTimeout(() => {
                    item.classList.remove('dict-word-item--highlight');
                }, 2000);
            }
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
            'sux': 'Sumerian', 'sux-x-emesal': 'Emesal', 'akk': 'Akkadian',
            'akk-x-stdbab': 'Standard Babylonian', 'akk-x-oldbab': 'Old Babylonian',
            'akk-x-neoass': 'Neo-Assyrian', 'xhu': 'Hurrian', 'uga': 'Ugaritic', 'elx': 'Elamite'
        };
        const posLabels = {
            'N': 'Noun', 'V': 'Verb', 'AJ': 'Adjective', 'AV': 'Adverb', 'NU': 'Number',
            'PRP': 'Preposition', 'PP': 'Possessive Pronoun', 'CNJ': 'Conjunction',
            'DP': 'Demonstrative', 'IP': 'Pronoun', 'RP': 'Reflexive', 'XP': 'Indefinite Pronoun',
            'REL': 'Relative', 'QP': 'Interrogative', 'DET': 'Determiner', 'MOD': 'Modal',
            'J': 'Interjection', 'SBJ': 'Subjunction', 'MA': 'Auxiliary', 'M': 'Morpheme', 'O': 'Other',
            'V/i': 'Intransitive Verb', 'V/t': 'Transitive Verb',
            'PN': 'Personal Name', 'DN': 'Divine Name', 'GN': 'Geographic Name', 'SN': 'Settlement Name',
            'TN': 'Temple Name', 'WN': 'Watercourse Name', 'RN': 'Royal Name', 'EN': 'Ethnic Name',
            'CN': 'Celestial Name', 'ON': 'Object Name', 'MN': 'Month Name', 'AN': 'Artifact Name',
            'LN': 'Line Name'
        };

        const langLabel = langLabels[entry.language] || entry.language;
        const posLabel = posLabels[entry.pos] || entry.pos;

        const html = `
            <div class="dict-browser__detail-handle"></div>
            <div class="word-detail-content">
                <div class="page-header word-header">
                    <div class="page-header-main">
                        <div class="page-header-title">
                            <h1>${this.escapeHtml(entry.citation_form || entry.headword)}</h1>
                        </div>
                    </div>
                </div>

                <!-- Word Metadata -->
                <div class="word-meta">
                    <dl class="word-meta__row">
                        <div class="meta-item meta-item--primary">
                            <dt>Guide Word</dt>
                            <dd class="meta-guide-word">${entry.guide_word ? this.escapeHtml(entry.guide_word) : '<span class="meta-placeholder">—</span>'}</dd>
                        </div>
                        <div class="meta-item">
                            <dt>Language</dt>
                            <dd>${this.escapeHtml(langLabel)}</dd>
                        </div>
                        <div class="meta-item">
                            <dt>Part of Speech</dt>
                            <dd>${this.escapeHtml(posLabel)}</dd>
                        </div>
                        <div class="meta-item">
                            <dt>Attestations</dt>
                            <dd>${(entry.icount || 0).toLocaleString()}</dd>
                        </div>
                        <div class="meta-item">
                            <button class="word-meta__toggle" data-action="toggle-meta" aria-expanded="false" aria-controls="word-meta-secondary">
                                <svg class="word-meta__toggle-icon" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="9 18 15 12 9 6"/>
                                </svg>
                                More
                            </button>
                        </div>
                    </dl>
                    <dl class="word-meta__secondary" id="word-meta-secondary">
                        <div class="meta-item">
                            <dt>Entry ID</dt>
                            <dd>${entry.entry_id ? `<code>${this.escapeHtml(entry.entry_id)}</code>` : '<span class="meta-placeholder">—</span>'}</dd>
                        </div>
                        <div class="meta-item">
                            <dt>Semantic Category</dt>
                            <dd>${entry.semantic_category ? this.escapeHtml(entry.semantic_category) : '<span class="meta-placeholder">—</span>'}</dd>
                        </div>
                    </dl>
                </div>

                ${this.renderMeanings(data.senses)}
                ${this.renderVariants(data.variants)}
                ${this.renderSigns(data.signs)}
                ${this.renderRelatedWords(data.related_words)}
                ${this.renderAttestations(data.attestations?.sample, entry.icount)}
                ${this.renderCAD(data.cad)}
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
        if (!variants || variants.length === 0) {
            return `
                <section class="word-section">
                    <h2>Attested Forms</h2>
                    <p class="section-description">Different spellings and grammatical forms found in the corpus, ordered by frequency.</p>
                    <p class="section-placeholder">No attested forms documented yet.</p>
                </section>
            `;
        }

        const maxCount = Math.max(...variants.map(v => v.count || 0));
        const visibleCount = 12;
        const hasMore = variants.length > visibleCount;

        return `
            <section class="word-section">
                <h2>Attested Forms <span class="section-count-badge">${variants.length}</span></h2>
                <p class="section-description">Different spellings and grammatical forms found in the corpus, ordered by frequency.</p>
                <div class="variants-chart">
                    ${variants.map((v, index) => {
                        const pct = maxCount > 0 ? (v.count / maxCount) * 100 : 0;
                        const isHidden = index >= visibleCount;
                        return `
                            <div class="variant-bar${isHidden ? ' variant-bar--hidden' : ''}" ${isHidden ? 'style="display: none;"' : ''}>
                                <span class="variant-form">${this.escapeHtml(v.form)}</span>
                                <div class="variant-frequency-container">
                                    <div class="variant-frequency" style="width: ${pct}%"></div>
                                </div>
                                <span class="variant-count">${v.count} attestation${v.count !== 1 ? 's' : ''}</span>
                            </div>
                        `;
                    }).join('')}
                </div>
                ${hasMore ? `
                    <button class="btn btn--secondary" data-action="toggle-variants" style="margin-top: var(--space-4);">
                        <span data-show-text>Show all ${variants.length} forms</span>
                        <span data-hide-text style="display: none;">Show fewer forms</span>
                    </button>
                ` : ''}
            </section>
        `;
    }

    renderSigns(signs) {
        if (!signs || signs.length === 0) {
            return `
                <section class="word-section">
                    <h2>Cuneiform Signs</h2>
                    <p class="section-description">The signs used to write this word. Click a sign to explore all its readings.</p>
                    <p class="section-placeholder">No cuneiform signs documented yet.</p>
                </section>
            `;
        }

        return `
            <section class="word-section">
                <h2>Cuneiform Signs <span class="section-count-badge">${signs.length}</span></h2>
                <p class="section-description">The signs used to write this word. Click a sign to explore all its readings.</p>
                <div class="sign-breakdown">
                    ${signs.map(s => `
                        <div class="sign-item">
                            <span class="sign-cuneiform">${s.utf8 || ''}</span>
                            <span class="sign-value">${this.escapeHtml(s.sign_value)}</span>
                            ${s.value_type ? `<span class="sign-type">${this.escapeHtml(s.value_type)}</span>` : ''}
                        </div>
                    `).join('')}
                </div>
            </section>
        `;
    }

    renderAttestations(attestations, totalCount) {
        if (!attestations || attestations.length === 0) {
            return `
                <section class="word-section">
                    <h2>Tablets</h2>
                    <p class="section-description">Ancient tablets where this word has been identified in the corpus.</p>
                    <p class="section-placeholder">No tablet attestations available yet.</p>
                </section>
            `;
        }

        const visibleCount = 12;
        const hasMore = attestations.length > visibleCount;

        return `
            <section class="word-section">
                <h2>Tablets <span class="section-count-badge">${attestations.length}</span></h2>
                <p class="section-description">Ancient tablets where this word has been identified in the corpus.</p>
                <div class="tablet-grid" data-tablet-grid>
                    ${attestations.map((a, index) => this.renderTabletCard(a, index >= visibleCount)).join('')}
                </div>
                ${hasMore ? `
                    <button class="btn btn--secondary" data-action="toggle-tablets" style="margin-top: var(--space-4);">
                        <span data-show-text>Show all ${attestations.length} tablets</span>
                        <span data-hide-text style="display: none;">Show fewer tablets</span>
                    </button>
                ` : `
                    <p class="examples-footer">
                        ${attestations.length} tablet${attestations.length !== 1 ? 's' : ''} in corpus
                    </p>
                `}
            </section>
        `;
    }

    renderTabletCard(attestation, isHidden = false) {
        const pNumber = this.escapeHtml(attestation.p_number);
        const period = attestation.period ? this.escapeHtml(this.truncateText(attestation.period, 25)) : '';
        const provenience = attestation.provenience ? this.escapeHtml(this.truncateText(attestation.provenience, 20)) : '';
        const genre = attestation.genre ? this.escapeHtml(this.truncateText(attestation.genre, 20)) : '';

        return `
            <a href="/tablets/detail.php?p=${encodeURIComponent(attestation.p_number)}"
               class="card tablet-card${isHidden ? ' tablet-card--hidden' : ''}"
               data-p-number="${pNumber}"
               ${isHidden ? 'style="display: none;"' : ''}>
                <div class="card-image">
                    <img src="/api/thumbnail.php?p=${encodeURIComponent(attestation.p_number)}&size=200"
                         alt="${pNumber}"
                         loading="lazy"
                         onerror="this.parentElement.classList.add('no-image')">
                    <div class="card-placeholder">
                        <span class="cuneiform-icon">𒀭</span>
                    </div>
                </div>
                <div class="card-details card-overlay">
                    <span class="card-eyebrow p-number">${pNumber}</span>
                    ${period ? `<span class="card-primary meta-period">${period}</span>` : ''}
                    ${provenience ? `<span class="card-meta">${provenience}</span>` : ''}
                    ${genre ? `<span class="card-meta">${genre}</span>` : ''}
                </div>
            </a>
        `;
    }

    renderMeanings(senses) {
        if (!senses || senses.length === 0) {
            return `
                <section class="word-section">
                    <h2>Meanings</h2>
                    <p class="section-description">Detailed senses with definitions, usage contexts, and frequency data. Different from the guide word above, which is a simple gloss for quick reference.</p>
                    <p class="section-placeholder">No meanings documented yet.</p>
                </section>
            `;
        }

        return `
            <section class="word-section">
                <h2>Meanings <span class="section-count-badge">${senses.length}</span></h2>
                <p class="section-description">Detailed senses with definitions, usage contexts, and frequency data. Different from the guide word above, which is a simple gloss for quick reference.</p>
                <ol class="meanings-list">
                    ${senses.map(sense => `
                        <li class="meaning">
                            <div class="meaning__header">
                                <strong>${this.escapeHtml(sense.guide_word)}</strong>
                                ${sense.frequency_percentage ? `<span class="meaning__usage">${Math.round(sense.frequency_percentage)}% of uses</span>` : ''}
                            </div>
                            ${sense.definition ? `<p class="meaning__definition">${this.escapeHtml(sense.definition)}</p>` : ''}
                            ${sense.usage_context ? `<p class="meaning__context">${this.escapeHtml(sense.usage_context)}</p>` : ''}
                        </li>
                    `).join('')}
                </ol>
            </section>
        `;
    }

    renderRelatedWords(related) {
        const hasRelated = related && (
            (related.translations && related.translations.length > 0) ||
            (related.synonyms && related.synonyms.length > 0) ||
            (related.cognates && related.cognates.length > 0) ||
            (related.see_also && related.see_also.length > 0)
        );

        if (!hasRelated) {
            return `
                <section class="word-section">
                    <h2>Related Words</h2>
                    <p class="section-description">Bilingual equivalents, synonyms, and cognates across Sumerian and Akkadian.</p>
                    <p class="section-placeholder">No related words documented yet.</p>
                </section>
            `;
        }

        const langLabels = {
            'sux': 'Sumerian', 'sux-x-emesal': 'Emesal', 'akk': 'Akkadian',
            'akk-x-stdbab': 'Standard Babylonian', 'akk-x-oldbab': 'Old Babylonian',
            'akk-x-neoass': 'Neo-Assyrian', 'xhu': 'Hurrian', 'uga': 'Ugaritic', 'elx': 'Elamite'
        };

        return `
            <section class="word-section">
                <h2>Related Words</h2>
                <p class="section-description">Bilingual equivalents, synonyms, and cognates across Sumerian and Akkadian.</p>

                ${related.translations && related.translations.length > 0 ? `
                    <div class="related-group">
                        <h3>Bilingual Equivalents</h3>
                        <div class="related-words-grid">
                            ${related.translations.map(rel => `
                                <a href="/dictionary/?word=${encodeURIComponent(rel.entry_id)}" class="card card-word" data-entry-id="${this.escapeHtml(rel.entry_id)}">
                                    <div class="card-word__header">
                                        <span class="card-word__headword">${this.escapeHtml(rel.headword)}</span>
                                        ${rel.guide_word ? `<span class="card-word__guide-word">${this.escapeHtml(rel.guide_word)}</span>` : ''}
                                    </div>
                                    <div class="card-word__meta">
                                        <span class="card-word__badge card-word__badge--lang">${langLabels[rel.language] || rel.language}</span>
                                        ${rel.icount ? `<span class="card-word__count">${rel.icount.toLocaleString()}</span>` : ''}
                                    </div>
                                    ${rel.notes ? `<div class="card-word__notes">${this.escapeHtml(rel.notes)}</div>` : ''}
                                </a>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                ${related.synonyms && related.synonyms.length > 0 ? `
                    <div class="related-group">
                        <h3>Synonyms</h3>
                        <div class="related-words-grid">
                            ${related.synonyms.map(rel => `
                                <a href="/dictionary/?word=${encodeURIComponent(rel.entry_id)}" class="card card-word" data-entry-id="${this.escapeHtml(rel.entry_id)}">
                                    <div class="card-word__header">
                                        <span class="card-word__headword">${this.escapeHtml(rel.headword)}</span>
                                        ${rel.guide_word ? `<span class="card-word__guide-word">${this.escapeHtml(rel.guide_word)}</span>` : ''}
                                    </div>
                                    <div class="card-word__meta">
                                        ${rel.icount ? `<span class="card-word__count">${rel.icount.toLocaleString()}</span>` : ''}
                                    </div>
                                </a>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                ${related.cognates && related.cognates.length > 0 ? `
                    <div class="related-group">
                        <h3>Cognates</h3>
                        <div class="related-words-grid">
                            ${related.cognates.map(rel => `
                                <a href="/dictionary/?word=${encodeURIComponent(rel.entry_id)}" class="card card-word" data-entry-id="${this.escapeHtml(rel.entry_id)}">
                                    <div class="card-word__header">
                                        <span class="card-word__headword">${this.escapeHtml(rel.headword)}</span>
                                    </div>
                                    <div class="card-word__meta">
                                        <span class="card-word__badge card-word__badge--lang">${langLabels[rel.language] || rel.language}</span>
                                        ${rel.icount ? `<span class="card-word__count">${rel.icount.toLocaleString()}</span>` : ''}
                                    </div>
                                </a>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}

                ${related.see_also && related.see_also.length > 0 ? `
                    <div class="related-group">
                        <h3>See Also</h3>
                        <div class="related-words-grid">
                            ${related.see_also.map(rel => `
                                <a href="/dictionary/?word=${encodeURIComponent(rel.entry_id)}" class="card card-word" data-entry-id="${this.escapeHtml(rel.entry_id)}">
                                    <div class="card-word__header">
                                        <span class="card-word__headword">${this.escapeHtml(rel.headword)}</span>
                                        ${rel.guide_word ? `<span class="card-word__guide-word">${this.escapeHtml(rel.guide_word)}</span>` : ''}
                                    </div>
                                    <div class="card-word__meta">
                                        ${rel.icount ? `<span class="card-word__count">${rel.icount.toLocaleString()}</span>` : ''}
                                    </div>
                                </a>
                            `).join('')}
                        </div>
                    </div>
                ` : ''}
            </section>
        `;
    }

    renderCAD(cad) {
        if (!cad) {
            return `
                <section class="word-section">
                    <h2>Chicago Assyrian Dictionary</h2>
                    <p class="section-description">Reference from the authoritative dictionary for Akkadian, published by the Oriental Institute.</p>
                    <p class="section-placeholder">No CAD reference available.</p>
                </section>
            `;
        }

        return `
            <section class="word-section">
                <h2>Chicago Assyrian Dictionary</h2>
                <p class="section-description">Reference from the authoritative dictionary for Akkadian, published by the Oriental Institute.</p>
                <div class="cad-content">
                    <div class="cad-header">
                        <span class="volume-badge">CAD ${this.escapeHtml(cad.volume)}, pp. ${cad.page_start}${cad.page_end ? `-${cad.page_end}` : ''}</span>
                        ${cad.pdf_url ? `<a href="${this.escapeHtml(cad.pdf_url)}/page/${cad.page_start}" target="_blank" class="pdf-link">View PDF →</a>` : ''}
                        ${cad.human_verified ? '<span class="verified-badge">✓ Verified</span>' : ''}
                    </div>
                    ${cad.etymology ? `
                        <div class="cad-etymology">
                            <strong>Etymology:</strong> ${this.escapeHtml(cad.etymology)}
                        </div>
                    ` : ''}
                    ${cad.semantic_notes ? `<div class="cad-notes">${this.escapeHtml(cad.semantic_notes)}</div>` : ''}
                </div>
            </section>
        `;
    }

    truncateText(text, maxLength) {
        if (!text || text.length <= maxLength) return text;
        return text.substring(0, maxLength - 1) + '…';
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
    // Detail Panel Actions
    // =========================================================================

    handleShare(url) {
        const fullUrl = window.location.origin + url;

        if (navigator.clipboard) {
            navigator.clipboard.writeText(fullUrl).then(() => {
                this.showToast('Link copied to clipboard');
            }).catch(() => {
                this.fallbackCopy(fullUrl);
            });
        } else {
            this.fallbackCopy(fullUrl);
        }
    }

    fallbackCopy(text) {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.opacity = '0';
        document.body.appendChild(textarea);
        textarea.select();
        try {
            document.execCommand('copy');
            this.showToast('Link copied to clipboard');
        } catch (e) {
            this.showToast('Unable to copy link');
        }
        document.body.removeChild(textarea);
    }

    showToast(message) {
        // Remove existing toast
        document.querySelector('.toast')?.remove();

        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2000);
    }

    handleMetaToggle(toggleBtn) {
        const isExpanded = toggleBtn.getAttribute('aria-expanded') === 'true';
        const targetId = toggleBtn.getAttribute('aria-controls');
        const target = document.getElementById(targetId);

        toggleBtn.setAttribute('aria-expanded', isExpanded ? 'false' : 'true');
        target?.classList.toggle('is-open', !isExpanded);
    }

    handleVariantsToggle(toggleBtn) {
        const section = toggleBtn.closest('.word-section');
        const hiddenVariants = section?.querySelectorAll('.variant-bar--hidden');
        if (!hiddenVariants || hiddenVariants.length === 0) return;

        const firstHidden = hiddenVariants[0];
        const isShowingAll = firstHidden.style.display !== 'none';

        // Toggle visibility of all hidden variants
        hiddenVariants.forEach(variant => {
            variant.style.display = isShowingAll ? 'none' : '';
        });

        // Toggle button text
        const showText = toggleBtn.querySelector('[data-show-text]');
        const hideText = toggleBtn.querySelector('[data-hide-text]');
        if (isShowingAll) {
            showText.style.display = '';
            hideText.style.display = 'none';
        } else {
            showText.style.display = 'none';
            hideText.style.display = '';
        }
    }

    handleTabletsToggle(toggleBtn) {
        const section = toggleBtn.closest('.word-section');
        const hiddenTablets = section?.querySelectorAll('.tablet-card--hidden');
        if (!hiddenTablets || hiddenTablets.length === 0) return;

        const firstHidden = hiddenTablets[0];
        const isShowingAll = firstHidden.style.display !== 'none';

        // Toggle visibility of all hidden tablets
        hiddenTablets.forEach(tablet => {
            tablet.style.display = isShowingAll ? 'none' : '';
        });

        // Toggle button text
        const showText = toggleBtn.querySelector('[data-show-text]');
        const hideText = toggleBtn.querySelector('[data-hide-text]');
        if (isShowingAll) {
            showText.style.display = '';
            hideText.style.display = 'none';
        } else {
            showText.style.display = 'none';
            hideText.style.display = '';
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

        if (this.state.sortBy !== 'frequency') {
            params.set('sort', this.state.sortBy);
        }

        const url = params.toString() ? `/dictionary/?${params}` : '/dictionary/';
        history.pushState({ ...this.state }, '', url);
    }

    async syncFromURL() {
        const params = new URLSearchParams(window.location.search);

        this.state.selectedWordId = params.get('word') || null;
        this.state.groupType = params.get('group') || 'all';
        this.state.groupValue = params.get('value') || null;
        this.state.searchQuery = params.get('search') || '';
        this.state.sortBy = params.get('sort') || 'frequency';

        // Update UI to match URL state
        if (this.elements.searchInput) {
            this.elements.searchInput.value = this.state.searchQuery;
        }

        // Update sort select to match URL state
        const sortSelect = document.querySelector('[data-action="sort"]');
        if (sortSelect) {
            sortSelect.value = this.state.sortBy;
        }

        // Update grouping active states
        document.querySelectorAll('.dict-groupings__item').forEach(item => {
            const isActive = (this.state.groupType === 'all' && item.dataset.group === 'all') ||
                           (item.dataset.group === this.state.groupType && item.dataset.value === this.state.groupValue);
            item.classList.toggle('dict-groupings__item--active', isActive);
        });

        // Position-based pagination: if we have a word but no grouping, load the correct page
        if (this.state.selectedWordId && this.state.groupType === 'all' && !this.state.searchQuery) {
            await this.loadWordWithPosition(this.state.selectedWordId);
        } else {
            // Standard list load
            this.loadWordList(true);

            // Load word detail if word ID is in URL
            if (this.state.selectedWordId) {
                this.loadWordDetail(this.state.selectedWordId);
            }
        }
    }

    restoreState(state) {
        this.state = { ...this.state, ...state };

        if (this.elements.searchInput) {
            this.elements.searchInput.value = this.state.searchQuery || '';
        }

        this.loadWordList(true);

        if (this.state.selectedWordId) {
            this.loadWordDetail(this.state.selectedWordId);
        }
    }

    // =========================================================================
    // Position-Based Pagination
    // =========================================================================

    async loadWordWithPosition(entryId) {
        try {
            console.log('[Position Load] Starting for:', entryId);

            // Fetch word detail to get position information
            const response = await fetch(`/api/dictionary/word-detail.php?entry_id=${encodeURIComponent(entryId)}`);
            const data = await response.json();

            console.log('[Position Load] API response:', data);

            if (!data || !data.position) {
                console.warn('[Position Load] No position data, falling back');
                // Fallback to standard loading
                this.loadWordList(true);
                this.loadWordDetail(entryId);
                return;
            }

            // Determine position based on current sort order
            const position = this.state.sortBy === 'alpha' ? data.position.alpha : data.position.frequency;
            console.log('[Position Load] Sort:', this.state.sortBy, 'Position:', position);

            // Calculate which page this word is on (50 items per page)
            const pageSize = 50;
            const pageOffset = Math.floor(position / pageSize) * pageSize;
            console.log('[Position Load] Calculated offset:', pageOffset);

            // Update state offset
            this.state.offset = pageOffset;

            // Load the word list at the calculated offset
            await this.loadWordList(true);
            console.log('[Position Load] Word list loaded');

            // Wait for DOM to update before selecting and scrolling
            requestAnimationFrame(() => {
                requestAnimationFrame(async () => {
                    console.log('[Position Load] Attempting to select and scroll');

                    // Select the word and scroll to it with highlight
                    await this.selectWord(entryId, false, true);

                    // Scroll the word into view
                    const wordItem = document.querySelector(`[data-entry-id="${entryId}"]`);
                    console.log('[Position Load] Word item found:', wordItem);

                    if (wordItem) {
                        wordItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        console.log('[Position Load] Scrolled to word');
                    } else {
                        console.error('[Position Load] Word item not found in DOM!');
                    }
                });
            });

        } catch (error) {
            console.error('Error loading word with position:', error);
            // Fallback to standard loading
            this.loadWordList(true);
            if (entryId) {
                this.loadWordDetail(entryId);
            }
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
