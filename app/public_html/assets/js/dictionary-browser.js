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

        // Section descriptions from centralized educational content
        this._sectionDesc = null;
        this._sectionDescPromise = null;

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

    /**
     * Load section descriptions from centralized educational content.
     * Returns cached result on subsequent calls.
     */
    async loadSectionDescriptions() {
        if (this._sectionDesc) return this._sectionDesc;
        if (this._sectionDescPromise) return this._sectionDescPromise;

        this._sectionDescPromise = fetch('/api/educational-content.php')
            .then(r => r.ok ? r.json() : {})
            .then(data => {
                this._sectionDesc = data?.section_descriptions || {};
                return this._sectionDesc;
            })
            .catch(() => {
                this._sectionDesc = {};
                return this._sectionDesc;
            });

        return this._sectionDescPromise;
    }

    /**
     * Get a section description by key, with fallback.
     */
    sd(key) {
        return this._sectionDesc?.[key] || '';
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
            const item = e.target.closest('.list-item');
            if (item && !item.classList.contains('list-item--skeleton')) {
                this.selectWord(item.dataset.entryId);
            }
        });

        // Keyboard navigation in word list
        this.elements.wordListItems?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                const item = e.target.closest('.list-item');
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
        const hideBadge = this.state.groupType !== 'all' ? this.state.groupType : null;
        return WordListItem.render(entry, {
            active: entry.entry_id === this.state.selectedWordId,
            hideBadge
        });
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
        document.querySelectorAll('.dict-word-list__items .list-item').forEach(item => {
            const isActive = item.dataset.entryId === entryId;
            item.classList.toggle('list-item--active', isActive);

            // Add highlight animation if requested
            if (isActive && shouldHighlight) {
                item.classList.add('list-item--highlight');
                // Remove highlight class after animation completes
                setTimeout(() => {
                    item.classList.remove('list-item--highlight');
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
            const [response] = await Promise.all([
                fetch(`/api/dictionary/word-detail.php?entry_id=${encodeURIComponent(entryId)}`),
                this.loadSectionDescriptions()
            ]);
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
                            <h1>
                                <span class="word-header__citation">${this.escapeHtml(entry.citation_form || entry.headword)}</span>
                                <button class="btn btn--icon word-share-btn" data-action="share" data-url="/dictionary/?word=${encodeURIComponent(entry.entry_id)}" title="Copy link to clipboard">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/>
                                        <polyline points="16 6 12 2 8 6"/>
                                        <line x1="12" y1="2" x2="12" y2="15"/>
                                    </svg>
                                </button>
                            </h1>
                            ${entry.guide_word ? `<p class="word-header__guide-word">${this.escapeHtml(entry.guide_word)}</p>` : ''}
                        </div>
                    </div>
                </div>

                <!-- Word Metadata -->
                <div class="word-meta">
                    <dl class="word-meta__row">
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
                    <p class="section-description">${this.sd('attested_forms')}</p>
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
                <p class="section-description">${this.sd('attested_forms')}</p>
                <div class="variants-chart">
                    ${variants.map((v, index) => {
                        const pct = maxCount > 0 ? (v.count / maxCount) * 100 : 0;
                        const isHidden = index >= visibleCount;
                        return `
                            <div class="variant-bar${isHidden ? ' variant-bar--hidden is-hidden' : ''}">
                                <span class="variant-form">${this.escapeHtml(v.form)}</span>
                                <div class="variant-frequency-container">
                                    <div class="variant-frequency" style="--bar-width: ${pct}%"></div>
                                </div>
                                <span class="variant-count">${v.count} attestation${v.count !== 1 ? 's' : ''}</span>
                            </div>
                        `;
                    }).join('')}
                </div>
                ${hasMore ? `
                    <button class="btn btn--secondary btn--section-toggle" data-action="toggle-variants">
                        <span data-show-text>Show all ${variants.length} forms</span>
                        <span data-hide-text class="is-hidden">Show fewer forms</span>
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
                    <p class="section-description">${this.sd('cuneiform_signs')}</p>
                    <p class="section-placeholder">No cuneiform signs documented yet.</p>
                </section>
            `;
        }

        return `
            <section class="word-section">
                <h2>Cuneiform Signs <span class="section-count-badge">${signs.length}</span></h2>
                <p class="section-description">${this.sd('cuneiform_signs')}</p>
                <div class="sign-breakdown">
                    ${signs.map(s => `
                        <a href="/dictionary/signs/?sign=${encodeURIComponent(s.sign_id)}" class="sign-item">
                            <span class="sign-cuneiform">${s.utf8 || ''}</span>
                            <span class="sign-value">${this.escapeHtml(s.sign_value)}</span>
                            ${s.value_type ? `<span class="sign-type">${this.escapeHtml(s.value_type)}</span>` : ''}
                        </a>
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
                    <p class="section-description">${this.sd('tablets')}</p>
                    <p class="section-placeholder">No tablet attestations available yet.</p>
                </section>
            `;
        }

        const visibleCount = 12;
        const hasMore = attestations.length > visibleCount;

        return `
            <section class="word-section">
                <h2>Tablets <span class="section-count-badge">${attestations.length}</span></h2>
                <p class="section-description">${this.sd('tablets')}</p>
                <div class="tablet-grid" data-tablet-grid>
                    ${attestations.map((a, index) => this.renderTabletCard(a, index >= visibleCount)).join('')}
                </div>
                ${hasMore ? `
                    <button class="btn btn--secondary btn--section-toggle" data-action="toggle-tablets">
                        <span data-show-text>Show all ${attestations.length} tablets</span>
                        <span data-hide-text class="is-hidden">Show fewer tablets</span>
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
               class="card tablet-card${isHidden ? ' tablet-card--hidden is-hidden' : ''}"
               data-p-number="${pNumber}">
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
                    <p class="section-description">${this.sd('meanings')}</p>
                    <p class="section-placeholder">No meanings documented yet.</p>
                </section>
            `;
        }

        return `
            <section class="word-section">
                <h2>Meanings <span class="section-count-badge">${senses.length}</span></h2>
                <p class="section-description">${this.sd('meanings')}</p>
                <p class="section-description">${this.sd('senses_explanation')}</p>
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
                    <p class="section-description">${this.sd('related_words')}</p>
                    <p class="section-placeholder">No related words documented yet.</p>
                </section>
            `;
        }

        const renderGroup = (title, words) => {
            if (!words || words.length === 0) return '';
            return `
                <div class="related-group">
                    <h3>${title}</h3>
                    <div class="related-words-grid">
                        ${words.map(rel => WordListItem.render(rel, { card: true, notes: rel.notes })).join('')}
                    </div>
                </div>
            `;
        };

        return `
            <section class="word-section">
                <h2>Related Words</h2>
                <p class="section-description">${this.sd('related_words')}</p>
                ${renderGroup('Bilingual Equivalents', related.translations)}
                ${renderGroup('Synonyms', related.synonyms)}
                ${renderGroup('Cognates', related.cognates)}
                ${renderGroup('See Also', related.see_also)}
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

        const isShowingAll = !hiddenVariants[0].classList.contains('is-hidden');

        // Toggle visibility of all hidden variants
        hiddenVariants.forEach(variant => {
            variant.classList.toggle('is-hidden', isShowingAll);
        });

        // Toggle button text
        const showText = toggleBtn.querySelector('[data-show-text]');
        const hideText = toggleBtn.querySelector('[data-hide-text]');
        showText.classList.toggle('is-hidden', !isShowingAll);
        hideText.classList.toggle('is-hidden', isShowingAll);
    }

    handleTabletsToggle(toggleBtn) {
        const section = toggleBtn.closest('.word-section');
        const hiddenTablets = section?.querySelectorAll('.tablet-card--hidden');
        if (!hiddenTablets || hiddenTablets.length === 0) return;

        const isShowingAll = !hiddenTablets[0].classList.contains('is-hidden');

        // Toggle visibility of all hidden tablets
        hiddenTablets.forEach(tablet => {
            tablet.classList.toggle('is-hidden', isShowingAll);
        });

        // Toggle button text
        const showText = toggleBtn.querySelector('[data-show-text]');
        const hideText = toggleBtn.querySelector('[data-hide-text]');
        showText.classList.toggle('is-hidden', !isShowingAll);
        hideText.classList.toggle('is-hidden', isShowingAll);
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
