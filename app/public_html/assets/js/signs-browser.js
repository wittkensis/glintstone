/**
 * Signs Browser Controller
 *
 * Handles client-side interactions for the 3-column signs browser:
 * - State management and URL synchronization
 * - Grouping navigation and expand/collapse
 * - Sign list filtering, search, sort, and pagination
 * - Sign detail loading
 */

class SignsBrowser {
    constructor(options = {}) {
        this.state = {
            groupType: 'all',
            groupValue: null,
            searchQuery: '',
            sort: 'sign_id',
            selectedSignId: null,
            offset: 0,
            total: 0,
            isLoadingList: false,
            isLoadingDetail: false,
            ...options.initialState
        };

        this.debounceTimer = null;
        this.debounceDelay = 300;

        this.elements = {
            browser: document.querySelector('.signs-browser'),
            groupings: document.querySelector('.signs-browser__groupings'),
            signList: document.querySelector('.signs-list'),
            signListItems: document.querySelector('[data-sign-list]'),
            signCount: document.querySelector('[data-sign-count]'),
            detail: document.querySelector('.signs-browser__detail'),
            searchInput: document.querySelector('.signs-list__search-input'),
            sortSelect: document.querySelector('.signs-list__sort'),
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

        document.querySelector('.signs-browser__groupings-backdrop')?.addEventListener('click', () => {
            this.closeGroupingsPanel();
        });

        // Search input
        if (this.elements.searchInput) {
            this.elements.searchInput.addEventListener('input', (e) => {
                this.handleSearchInput(e.target.value);
            });
            this.elements.searchInput.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') this.clearSearch();
            });
        }

        // Clear search
        document.querySelector('[data-action="clear-search"]')?.addEventListener('click', () => {
            this.clearSearch();
        });

        // Sort select
        this.elements.sortSelect?.addEventListener('change', (e) => {
            this.handleSortChange(e.target.value);
        });

        // Clear all (in empty state)
        document.querySelector('[data-action="clear-all"]')?.addEventListener('click', () => {
            this.clearAll();
        });

        // Sign item clicks (delegated)
        this.elements.signListItems?.addEventListener('click', (e) => {
            const item = e.target.closest('.list-item');
            if (item) {
                this.selectSign(item.dataset.signId);
            }
        });

        // Keyboard navigation in sign list
        this.elements.signListItems?.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                const item = e.target.closest('.list-item');
                if (item) {
                    e.preventDefault();
                    this.selectSign(item.dataset.signId);
                }
            }
        });

        // Load more button
        this.elements.loadMoreBtn?.addEventListener('click', () => {
            this.loadMore();
        });

        // Detail panel clicks (delegated) -- homophone and word links
        this.elements.detail?.addEventListener('click', (e) => {
            // Homophone sign link (navigate within signs browser)
            const signLink = e.target.closest('[data-sign-id]');
            if (signLink && signLink.tagName === 'A') {
                e.preventDefault();
                this.selectSign(signLink.dataset.signId);
                return;
            }

            // Share button
            const shareBtn = e.target.closest('[data-action="share"]');
            if (shareBtn) {
                this.handleShare(shareBtn.dataset.url);
                return;
            }

            // Show more/less toggles (readings + words)
            const toggleBtn = e.target.closest('[data-action="toggle-readings"], [data-action="toggle-words"]');
            if (toggleBtn) {
                this.handleShowMoreToggle(toggleBtn);
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
        document.querySelector('.signs-browser__detail-handle')?.addEventListener('click', () => {
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

        // Close all other sections
        document.querySelectorAll('.dict-groupings__section').forEach(s => {
            if (s !== section) s.dataset.expanded = 'false';
        });

        section.dataset.expanded = isExpanded ? 'false' : 'true';
    }

    setGroupFilter(groupType, groupValue) {
        // Update active state in UI
        document.querySelectorAll('.dict-groupings__item').forEach(item => {
            const isActive = (groupType === 'all' && item.dataset.group === 'all') ||
                           (item.dataset.group === groupType && item.dataset.value === groupValue);
            item.classList.toggle('dict-groupings__item--active', isActive);
        });

        this.state.groupType = groupType;
        this.state.groupValue = groupValue;
        this.state.offset = 0;
        this.state.selectedSignId = null;

        this.loadSignList(true);
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
    // Search & Sort
    // =========================================================================

    handleSearchInput(value) {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            this.state.searchQuery = value.trim();
            this.state.offset = 0;
            this.state.selectedSignId = null;
            this.loadSignList(true);
            this.updateURL();
        }, this.debounceDelay);
    }

    clearSearch() {
        if (this.elements.searchInput) {
            this.elements.searchInput.value = '';
        }
        this.state.searchQuery = '';
        this.state.offset = 0;
        this.loadSignList(true);
        this.updateURL();
    }

    clearAll() {
        this.clearSearch();
        this.setGroupFilter('all', null);
    }

    handleSortChange(sort) {
        this.state.sort = sort;
        this.state.offset = 0;
        this.state.selectedSignId = null;
        this.loadSignList(true);
        this.updateURL();
    }

    // =========================================================================
    // Sign List
    // =========================================================================

    async loadSignList(replace = false) {
        if (this.state.isLoadingList) return;

        this.state.isLoadingList = true;
        this.elements.browser?.querySelector('.signs-browser__list')?.setAttribute('data-loading', 'true');

        try {
            const params = new URLSearchParams({
                limit: '50',
                offset: replace ? '0' : String(this.state.offset),
                sort: this.state.sort
            });

            if (this.state.searchQuery) {
                params.set('search', this.state.searchQuery);
            }

            if (this.state.groupType !== 'all' && this.state.groupValue) {
                // sign_type and has_glyph are direct filters
                if (this.state.groupType === 'sign_type') {
                    params.set('sign_type', this.state.groupValue);
                } else if (this.state.groupType === 'has_glyph') {
                    params.set('has_glyph', this.state.groupValue);
                } else {
                    params.set('group_type', this.state.groupType);
                    params.set('group_value', this.state.groupValue);
                }
            }

            const response = await fetch(`/api/dictionary/signs-browse.php?${params}`);
            const data = await response.json();

            if (!data.signs) throw new Error('Invalid response');

            this.state.total = data.pagination.total;
            this.state.offset = replace ? data.signs.length : this.state.offset + data.signs.length;

            this.renderSignList(data.signs, replace);
            this.updateSignCount(replace ? data.signs.length : this.state.offset, data.pagination.total);
            this.updateLoadMoreButton(data.pagination.has_more);

            // Auto-select first sign if replacing and we have results
            if (replace && data.signs.length > 0 && !this.state.selectedSignId) {
                this.selectSign(data.signs[0].sign_id, false);
            }

        } catch (error) {
            console.error('Error loading sign list:', error);
        } finally {
            this.state.isLoadingList = false;
            this.elements.browser?.querySelector('.signs-browser__list')?.setAttribute('data-loading', 'false');
        }
    }

    renderSignList(signs, replace) {
        if (!this.elements.signListItems) return;

        const html = signs.map(sign => this.renderSignItem(sign)).join('');

        if (replace) {
            this.elements.signListItems.innerHTML = html;
        } else {
            this.elements.signListItems.insertAdjacentHTML('beforeend', html);
        }

        // Update empty state
        const listPanel = this.elements.browser?.querySelector('.signs-browser__list');
        listPanel?.setAttribute('data-empty', signs.length === 0 && replace ? 'true' : 'false');
    }

    renderSignItem(sign) {
        const isActive = sign.sign_id === this.state.selectedSignId;
        const hideBadge = this.state.groupType;

        const showValueCount = hideBadge !== 'polyphony' && sign.value_count > 0;
        const showWordCount = hideBadge !== 'word_count' && sign.word_count > 0;

        const metaParts = [];
        if (showValueCount) {
            metaParts.push(`${sign.value_count} reading${sign.value_count !== 1 ? 's' : ''}`);
        }
        if (showWordCount) {
            metaParts.push(`${sign.word_count} word${sign.word_count !== 1 ? 's' : ''}`);
        }

        return `
            <div class="list-item sign-list-item${isActive ? ' list-item--active' : ''}"
                 data-sign-id="${this.escapeHtml(sign.sign_id)}"
                 tabindex="0" role="button">
                <div class="sign-list-item__info">
                    <div class="list-item__header">
                        <span class="list-item__title">${this.escapeHtml(sign.sign_id)}</span>
                        ${sign.most_common_value ? `<span class="list-item__subtitle">${this.escapeHtml(sign.most_common_value)}</span>` : ''}
                    </div>
                    ${metaParts.length > 0 ? `<div class="list-item__meta">${metaParts.join(' · ')}</div>` : ''}
                </div>
                <div class="sign-list-item__aside">
                    <span class="sign-list-item__glyph">${sign.utf8 || ''}</span>
                    ${sign.total_occurrences > 0 ? `<span class="sign-list-item__count">${sign.total_occurrences.toLocaleString()}</span>` : ''}
                </div>
            </div>
        `;
    }

    updateSignCount(showing, total) {
        if (this.elements.signCount) {
            this.elements.signCount.textContent = `Showing ${showing.toLocaleString()} of ${total.toLocaleString()}`;
        }
    }

    updateLoadMoreButton(hasMore) {
        if (this.elements.loadMoreBtn) {
            this.elements.loadMoreBtn.dataset.hidden = hasMore ? 'false' : 'true';
        }
    }

    loadMore() {
        this.loadSignList(false);
    }

    // =========================================================================
    // Sign Detail
    // =========================================================================

    async selectSign(signId, updateUrl = true) {
        if (!signId || signId === this.state.selectedSignId) return;

        // Update active state in list
        this.elements.signListItems?.querySelectorAll('.list-item').forEach(item => {
            item.classList.toggle('list-item--active', item.dataset.signId === signId);
        });

        this.state.selectedSignId = signId;

        if (updateUrl) this.updateURL();

        // Show mobile detail panel
        if (window.innerWidth <= 768) {
            this.elements.detail.dataset.open = 'true';
        }

        await this.loadSignDetail(signId);
    }

    async loadSignDetail(signId) {
        if (this.state.isLoadingDetail) return;

        this.state.isLoadingDetail = true;
        this.elements.detail?.classList.add('is-loading');

        try {
            const response = await fetch(`/api/dictionary/sign-detail.php?sign_id=${encodeURIComponent(signId)}`);
            const data = await response.json();

            this.renderSignDetail(data);

        } catch (error) {
            console.error('Error loading sign detail:', error);
            this.renderDetailError();
        } finally {
            this.state.isLoadingDetail = false;
            this.elements.detail?.classList.remove('is-loading');
        }
    }

    renderSignDetail(data) {
        if (!this.elements.detail || !data || !data.sign) return;

        const sign = data.sign;
        const stats = data.statistics;
        const values = data.values;
        const words = data.words;
        const homophones = data.homophones;

        const signTypeLabels = { simple: 'Simple', compound: 'Compound', variant: 'Variant' };
        const signTypeLabel = signTypeLabels[sign.sign_type] || sign.sign_type || 'Unknown';

        // Unicode code point
        let codePoint = '';
        if (sign.utf8) {
            codePoint = 'U+' + sign.utf8.codePointAt(0).toString(16).toUpperCase().padStart(4, '0');
        }

        const html = `
            <div class="signs-browser__detail-handle"></div>
            <div class="sign-detail-content">
                <!-- Header -->
                <div class="page-header sign-header">
                    <div class="page-header-main">
                        <div class="page-header-title">
                            <h1>
                                ${sign.utf8 ? `<span class="sign-header__glyph-box"><span class="sign-header__glyph">${sign.utf8}</span></span>` : ''}
                                <span class="sign-header__id">${this.escapeHtml(sign.sign_id)}</span>
                                <button class="btn btn--icon sign-share-btn" data-action="share" data-url="/dictionary/signs/?sign=${encodeURIComponent(sign.sign_id)}" title="Copy link to clipboard">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/>
                                        <polyline points="16 6 12 2 8 6"/>
                                        <line x1="12" y1="2" x2="12" y2="15"/>
                                    </svg>
                                </button>
                            </h1>
                            ${sign.most_common_value ? `<p class="sign-header__value">${this.escapeHtml(sign.most_common_value)}</p>` : ''}
                        </div>
                    </div>
                </div>

                <!-- Metadata -->
                <div class="word-meta">
                    <dl class="word-meta__row">
                        <div class="meta-item">
                            <dt>Sign Type</dt>
                            <dd>${this.escapeHtml(signTypeLabel)}</dd>
                        </div>
                        ${codePoint ? `
                        <div class="meta-item">
                            <dt>Unicode</dt>
                            <dd><code>${codePoint}</code></dd>
                        </div>
                        ` : ''}
                        <div class="meta-item">
                            <dt>Readings</dt>
                            <dd>${stats.total_values}</dd>
                        </div>
                        <div class="meta-item">
                            <dt>Words</dt>
                            <dd>${stats.total_words_using_sign.toLocaleString()}</dd>
                        </div>
                        <div class="meta-item">
                            <dt>Occurrences</dt>
                            <dd>${stats.total_corpus_occurrences.toLocaleString()}</dd>
                        </div>
                    </dl>
                </div>

                ${this.renderReadings(values)}
                ${this.renderHomophones(homophones)}
                ${this.renderWords(words)}
            </div>
            <div class="signs-loading-overlay">
                <div class="dict-spinner"></div>
            </div>
        `;

        this.elements.detail.innerHTML = html;

        // Rebind mobile close handler
        document.querySelector('.signs-browser__detail-handle')?.addEventListener('click', () => {
            this.closeMobileDetail();
        });
    }

    renderReadings(values) {
        const allValues = [
            ...values.logographic,
            ...values.syllabic,
            ...values.determinative,
            ...values.other
        ];

        if (allValues.length === 0) {
            return `
                <section class="word-section">
                    <h2>Readings</h2>
                    <p class="section-description">How this sign is read in different contexts.</p>
                    <p class="section-placeholder">No readings documented for this sign.</p>
                </section>
            `;
        }

        const maxFreq = Math.max(...allValues.map(v => v.frequency || 0), 1);
        const visibleLimit = 12;
        const hasMore = allValues.length > visibleLimit;

        const bars = allValues.map((v, i) => {
            const pct = maxFreq > 0 ? (v.frequency / maxFreq) * 100 : 0;
            const hiddenClass = (hasMore && i >= visibleLimit) ? ' variants-hidden-item' : '';
            return `
                <div class="variant-bar${hiddenClass}">
                    <span class="variant-form">${this.escapeHtml(v.value)}</span>
                    <div class="variant-frequency-container">
                        <div class="variant-frequency" style="--bar-width: ${pct}%"></div>
                    </div>
                    ${v.frequency > 0 ? `<span class="variant-count">${v.frequency.toLocaleString()}</span>` : ''}
                </div>
            `;
        }).join('');

        const toggleBtn = hasMore ? `
            <button class="btn" data-action="toggle-readings"
                    data-show-text="Show all ${allValues.length} readings"
                    data-hide-text="Show fewer"
                    style="margin-top: var(--space-4);">
                Show all ${allValues.length} readings
            </button>
        ` : '';

        return `
            <section class="word-section">
                <h2>Readings <span class="section-count-badge">${allValues.length}</span></h2>
                <p class="section-description">How this sign is read in different contexts.</p>
                <div class="variants-chart">
                    ${bars}
                </div>
                ${toggleBtn}
            </section>
        `;
    }

    renderHomophones(homophones) {
        if (!homophones || homophones.length === 0) return '';

        return `
            <section class="word-section">
                <h2>Homophones <span class="section-count-badge">${homophones.length}</span></h2>
                <p class="section-description">Other signs that share one or more reading values with this sign.</p>
                <div class="related-words-grid">
                    ${homophones.map(h => {
                        const metaParts = [];
                        if (h.value_count > 0) {
                            metaParts.push(`${h.value_count} reading${h.value_count !== 1 ? 's' : ''}`);
                        }
                        if (h.word_count > 0) {
                            metaParts.push(`${h.word_count} word${h.word_count !== 1 ? 's' : ''}`);
                        }
                        return `
                        <a href="/dictionary/signs/?sign=${encodeURIComponent(h.sign_id)}" class="list-item list-item--card sign-card" data-sign-id="${this.escapeHtml(h.sign_id)}">
                            <div class="sign-card__info">
                                <div class="list-item__header">
                                    <span class="list-item__title">${this.escapeHtml(h.sign_id)}</span>
                                    ${h.most_common_value ? `<span class="list-item__subtitle">${this.escapeHtml(h.most_common_value)}</span>` : ''}
                                </div>
                                ${metaParts.length > 0 ? `<div class="list-item__meta">${metaParts.join(' · ')}</div>` : ''}
                            </div>
                            ${h.utf8 ? `<span class="sign-card__glyph">${h.utf8}</span>` : ''}
                        </a>
                    `}).join('')}
                </div>
            </section>
        `;
    }

    renderWords(words) {
        if (!words || !words.sample || words.sample.length === 0) {
            return `
                <section class="word-section">
                    <h2>Words</h2>
                    <p class="section-description">Dictionary entries that use this sign.</p>
                    <p class="section-placeholder">No dictionary words linked to this sign yet.</p>
                </section>
            `;
        }

        const langLabels = window.LABELS?.language || {};
        const visibleLimit = 12;
        const hasMore = words.sample.length > visibleLimit;

        const cards = words.sample.map((w, i) => {
            const hiddenClass = (hasMore && i >= visibleLimit) ? ' variants-hidden-item' : '';
            return `
                <a href="/dictionary/?word=${encodeURIComponent(w.entry.entry_id)}" class="list-item list-item--card${hiddenClass}" data-entry-id="${this.escapeHtml(w.entry.entry_id)}">
                    <div class="list-item__header">
                        <span class="list-item__title">${this.escapeHtml(w.entry.headword)}</span>
                        ${w.entry.guide_word ? `<span class="list-item__subtitle">${this.escapeHtml(w.entry.guide_word)}</span>` : ''}
                    </div>
                    <div class="list-item__meta">
                        ${w.sign_value ? `<span class="badge badge--sm">${this.escapeHtml(w.sign_value)}</span>` : ''}
                        ${w.entry.language ? `<span class="badge badge--sm">${this.escapeHtml(langLabels[w.entry.language] || w.entry.language)}</span>` : ''}
                        ${w.entry.icount > 0 ? `<span class="list-item__count">${w.entry.icount.toLocaleString()}</span>` : ''}
                    </div>
                </a>
            `;
        }).join('');

        const toggleBtn = hasMore ? `
            <button class="btn" data-action="toggle-words"
                    data-show-text="Show all ${words.total_unique_words} words"
                    data-hide-text="Show fewer"
                    style="margin-top: var(--space-4);">
                Show all ${words.total_unique_words} words
            </button>
        ` : '';

        return `
            <section class="word-section">
                <h2>Words <span class="section-count-badge">${words.total_unique_words}</span></h2>
                <p class="section-description">Dictionary entries that use this sign in their written form.</p>
                <div class="related-words-grid related-words-grid--3col">
                    ${cards}
                </div>
                ${toggleBtn}
            </section>
        `;
    }

    renderDetailError() {
        if (!this.elements.detail) return;

        this.elements.detail.innerHTML = `
            <div class="signs-browser__detail-handle"></div>
            <div class="dict-error">
                <svg class="dict-error__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M12 8v4M12 16h.01"/>
                </svg>
                <h3 class="dict-error__title">Error loading sign</h3>
                <p class="dict-error__description">Unable to load sign details. Please try again.</p>
                <button class="dict-error__retry" onclick="window.signsBrowser.loadSignDetail('${this.state.selectedSignId}')">
                    Retry
                </button>
            </div>
            <div class="signs-loading-overlay">
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

    handleShowMoreToggle(btn) {
        const container = btn.previousElementSibling;
        if (!container) return;

        const isExpanded = container.dataset.showAll === 'true';
        container.dataset.showAll = isExpanded ? 'false' : 'true';
        btn.textContent = isExpanded ? btn.dataset.showText : btn.dataset.hideText;
    }

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
        document.querySelector('.toast')?.remove();
        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2000);
    }

    // =========================================================================
    // URL Management
    // =========================================================================

    updateURL() {
        const params = new URLSearchParams();

        if (this.state.selectedSignId) {
            params.set('sign', this.state.selectedSignId);
        }

        if (this.state.groupType !== 'all' && this.state.groupValue) {
            params.set('group', this.state.groupType);
            params.set('value', this.state.groupValue);
        }

        if (this.state.searchQuery) {
            params.set('search', this.state.searchQuery);
        }

        if (this.state.sort !== 'sign_id') {
            params.set('sort', this.state.sort);
        }

        const url = params.toString() ? `/dictionary/signs/?${params}` : '/dictionary/signs/';
        history.pushState({ ...this.state }, '', url);
    }

    syncFromURL() {
        const params = new URLSearchParams(window.location.search);

        const urlSignId = params.get('sign') || null;
        const urlGroup = params.get('group') || 'all';
        const urlValue = params.get('value') || null;
        const urlSearch = params.get('search') || '';
        const urlSort = params.get('sort') || 'sign_id';

        // Only reload if state actually changed
        const stateChanged = (
            urlSignId !== this.state.selectedSignId ||
            urlGroup !== this.state.groupType ||
            urlValue !== this.state.groupValue ||
            urlSearch !== this.state.searchQuery ||
            urlSort !== this.state.sort
        );

        this.state.selectedSignId = urlSignId;
        this.state.groupType = urlGroup;
        this.state.groupValue = urlValue;
        this.state.searchQuery = urlSearch;
        this.state.sort = urlSort;

        // Update UI to match URL state
        if (this.elements.searchInput) {
            this.elements.searchInput.value = this.state.searchQuery;
        }
        if (this.elements.sortSelect) {
            this.elements.sortSelect.value = this.state.sort;
        }

        // Update grouping active states
        document.querySelectorAll('.dict-groupings__item').forEach(item => {
            const isActive = (this.state.groupType === 'all' && item.dataset.group === 'all') ||
                           (item.dataset.group === this.state.groupType && item.dataset.value === this.state.groupValue);
            item.classList.toggle('dict-groupings__item--active', isActive);
        });

        // Load sign detail if sign ID is in URL
        if (this.state.selectedSignId) {
            this.loadSignDetail(this.state.selectedSignId);
        }
    }

    restoreState(state) {
        this.state = { ...this.state, ...state };

        if (this.elements.searchInput) {
            this.elements.searchInput.value = this.state.searchQuery || '';
        }
        if (this.elements.sortSelect) {
            this.elements.sortSelect.value = this.state.sort || 'sign_id';
        }

        this.loadSignList(true);

        if (this.state.selectedSignId) {
            this.loadSignDetail(this.state.selectedSignId);
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

if (typeof module !== 'undefined' && module.exports) {
    module.exports = SignsBrowser;
}
