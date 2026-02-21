/**
 * Dictionary Browser Controller
 * Manages 3-column dictionary interface with state/URL synchronization
 */

class DictionaryBrowser {
    constructor() {
        this.state = {
            groupType: 'all',
            groupValue: null,
            searchQuery: '',
            sortBy: 'frequency',
            selectedEntryId: null,
            page: 1,
            total: 0,
            isLoadingList: false,
            isLoadingDetail: false,
        };

        this.elements = {
            browser: document.querySelector('[data-dict-browser]'),
            groupings: document.querySelector('.dict-groupings'),
            wordList: document.querySelector('[data-word-list]'),
            wordCount: document.querySelector('[data-word-count]'),
            detail: document.querySelector('[data-detail-panel]'),
            searchInput: document.querySelector('[data-search-input]'),
            sortSelect: document.querySelector('[data-sort-select]'),
            loadMoreBtn: document.querySelector('[data-load-more]'),
        };

        this.debounceTimer = null;
        this.debounceDelay = 300; // ms
        this.perPage = 50;
        this.apiUrl = this.elements.browser?.dataset.apiUrl || '';

        if (this.elements.browser) {
            this.init();
        }
    }

    init() {
        this.bindEvents();
        this.syncFromURL();
        this.loadWordList(false);
    }

    bindEvents() {
        // Section expand/collapse
        const sectionHeaders = document.querySelectorAll('.dict-groupings__section-header');
        sectionHeaders.forEach((header) => {
            header.addEventListener('click', (e) => this.handleSectionToggle(e));
        });

        // Grouping item clicks
        const groupItems = document.querySelectorAll('.dict-groupings__item');
        groupItems.forEach((item) => {
            item.addEventListener('click', (e) => this.handleGroupingClick(e));
        });

        // Search input (debounced)
        if (this.elements.searchInput) {
            this.elements.searchInput.addEventListener('input', (e) => {
                this.handleSearchInput(e.target.value);
                // Toggle clear button visibility
                const clearBtn = document.querySelector('[data-search-clear]');
                if (clearBtn) {
                    clearBtn.hidden = !e.target.value;
                }
            });
        }

        // Search clear button
        const searchClearBtn = document.querySelector('[data-search-clear]');
        if (searchClearBtn) {
            searchClearBtn.addEventListener('click', () => {
                if (this.elements.searchInput) {
                    this.elements.searchInput.value = '';
                    searchClearBtn.hidden = true;
                    this.handleSearchInput('');
                }
            });
        }

        // Sort select
        if (this.elements.sortSelect) {
            this.elements.sortSelect.addEventListener('change', (e) => {
                this.handleSortChange(e.target.value);
            });
        }

        // Word item clicks (delegated)
        if (this.elements.wordList) {
            this.elements.wordList.addEventListener('click', (e) => {
                const item = e.target.closest('.list-item');
                if (item && !item.classList.contains('list-item--skeleton')) {
                    this.selectWord(item.dataset.entryId);
                }
            });
        }

        // Load more pagination
        if (this.elements.loadMoreBtn) {
            this.elements.loadMoreBtn.addEventListener('click', () => {
                this.loadMore();
            });
        }

        // Browser back/forward
        window.addEventListener('popstate', () => {
            this.syncFromURL();
            this.loadWordList(false);
            if (this.state.selectedEntryId) {
                this.loadWordDetail(this.state.selectedEntryId);
            }
        });
    }

    syncFromURL() {
        const params = new URLSearchParams(window.location.search);
        this.state.groupType = params.get('group_type') || 'all';
        this.state.groupValue = params.get('group_value') || null;
        this.state.searchQuery = params.get('search') || '';
        this.state.sortBy = params.get('sort') || 'frequency';
        this.state.selectedEntryId = params.get('entry_id') || null;

        // Update UI to match state
        if (this.elements.searchInput) {
            this.elements.searchInput.value = this.state.searchQuery;
        }
        if (this.elements.sortSelect) {
            this.elements.sortSelect.value = this.state.sortBy;
        }

        // Update active grouping
        document.querySelectorAll('.dict-groupings__item').forEach((el) => {
            const matchesGroup =
                el.dataset.groupType === this.state.groupType &&
                (this.state.groupType === 'all' || el.dataset.groupValue === this.state.groupValue);
            el.classList.toggle('dict-groupings__item--active', matchesGroup);
        });
    }

    updateURL() {
        const params = new URLSearchParams();
        if (this.state.groupType !== 'all') {
            params.set('group_type', this.state.groupType);
        }
        if (this.state.groupValue) {
            params.set('group_value', this.state.groupValue);
        }
        if (this.state.searchQuery) {
            params.set('search', this.state.searchQuery);
        }
        if (this.state.sortBy !== 'frequency') {
            params.set('sort', this.state.sortBy);
        }
        if (this.state.selectedEntryId) {
            params.set('entry_id', this.state.selectedEntryId);
        }

        const url = params.toString() ? `?${params}` : window.location.pathname;
        window.history.pushState({ ...this.state }, '', url);
    }

    handleSectionToggle(e) {
        const header = e.currentTarget;
        const section = header.closest('.dict-groupings__section');
        if (!section) return;

        const isExpanded = section.getAttribute('data-expanded') === 'true';
        section.setAttribute('data-expanded', isExpanded ? 'false' : 'true');
    }

    handleGroupingClick(e) {
        const item = e.currentTarget;
        this.state.groupType = item.dataset.groupType || 'all';
        this.state.groupValue = item.dataset.groupValue || null;
        this.state.page = 1;

        // Update active state
        document.querySelectorAll('.dict-groupings__item').forEach((el) => {
            el.classList.remove('dict-groupings__item--active');
        });
        item.classList.add('dict-groupings__item--active');

        this.updateURL();
        this.loadWordList(false);
    }

    handleSearchInput(value) {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            this.state.searchQuery = value.trim();
            this.state.page = 1;
            this.updateURL();
            this.loadWordList(false);
        }, this.debounceDelay);
    }

    handleSortChange(value) {
        this.state.sortBy = value;
        this.state.page = 1;
        this.updateURL();
        this.loadWordList(false);
    }

    async loadWordList(append = false) {
        if (this.state.isLoadingList) return;
        this.state.isLoadingList = true;

        if (!append) {
            this.renderSkeleton();
        }

        try {
            const params = new URLSearchParams({
                page: this.state.page,
                per_page: this.perPage,
                sort: this.state.sortBy,
            });
            if (this.state.searchQuery) {
                params.set('search', this.state.searchQuery);
            }
            if (this.state.groupType !== 'all') {
                params.set('group_type', this.state.groupType);
            }
            if (this.state.groupValue) {
                params.set('group_value', this.state.groupValue);
            }

            const response = await fetch(`${this.apiUrl}/dictionary/browse?${params}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();

            this.state.total = data.total;
            this.renderWordList(data.items, append);
            this.updateLoadMoreButton(data);
        } catch (error) {
            console.error('Failed to load word list:', error);
            this.renderError();
        } finally {
            this.state.isLoadingList = false;
        }
    }

    async selectWord(entryId) {
        this.state.selectedEntryId = entryId;
        this.updateURL();

        // Update active state in word list
        document.querySelectorAll('.list-item').forEach((el) => {
            el.classList.toggle('list-item--active', el.dataset.entryId === entryId);
        });

        await this.loadWordDetail(entryId);
    }

    async loadWordDetail(entryId) {
        if (this.state.isLoadingDetail) return;
        this.state.isLoadingDetail = true;

        this.renderDetailSkeleton();

        try {
            const response = await fetch(`${this.apiUrl}/dictionary/${encodeURIComponent(entryId)}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            this.renderWordDetail(data);
        } catch (error) {
            console.error('Failed to load word detail:', error);
            this.renderDetailError();
        } finally {
            this.state.isLoadingDetail = false;
        }
    }

    renderWordList(items, append) {
        const html = items
            .map(
                (entry) => `
            <div class="list-item ${entry.entry_id === this.state.selectedEntryId ? 'list-item--active' : ''}"
                 data-entry-id="${this.escapeHtml(entry.entry_id)}"
                 tabindex="0"
                 role="button">
                <div class="list-item__header">
                    <span class="list-item__title">${this.escapeHtml(entry.citation_form || entry.headword)}</span>
                    ${entry.guide_word ? `<span class="list-item__subtitle">${this.escapeHtml(entry.guide_word)}</span>` : ''}
                </div>
                <div class="list-item__meta">
                    ${entry.pos ? `<span class="badge badge--sm badge--pos">${this.escapeHtml(entry.pos)}</span>` : ''}
                    ${entry.language ? `<span class="badge badge--sm badge--lang">${this.escapeHtml(entry.language)}</span>` : ''}
                    <span class="list-item__count">${entry.icount || 0}</span>
                </div>
            </div>
        `
            )
            .join('');

        if (append) {
            this.elements.wordList.insertAdjacentHTML('beforeend', html);
        } else {
            this.elements.wordList.innerHTML = html;
        }

        // Update count
        if (this.elements.wordCount) {
            this.elements.wordCount.querySelector('.count').textContent = this.state.total.toLocaleString();
        }

        // Re-apply active state if word is selected
        if (this.state.selectedEntryId) {
            document.querySelectorAll('.list-item').forEach((el) => {
                el.classList.toggle('list-item--active', el.dataset.entryId === this.state.selectedEntryId);
            });
        }
    }

    renderWordDetail(data) {
        const entry = data.entry;
        const variants = data.variants || [];
        const senses = data.senses || [];
        const attestations = data.attestations?.sample || [];
        const relatedWords = data.related_words || [];

        const html = `
            <div class="dict-detail">
                <div class="dict-detail__header">
                    <h2 class="dict-detail__headword">${this.escapeHtml(entry.citation_form || entry.headword)}</h2>
                    <div class="dict-detail__meta">
                        ${entry.pos ? `<span class="dict-detail__pos">${this.escapeHtml(entry.pos)}</span>` : ''}
                        ${entry.language ? `<span class="dict-detail__lang">${this.escapeHtml(entry.language)}</span>` : ''}
                        ${entry.icount ? `<span class="dict-detail__freq">${entry.icount} attestations</span>` : ''}
                    </div>
                </div>

                ${
                    entry.guide_word
                        ? `
                <div class="dict-detail__guide">
                    ${this.escapeHtml(entry.guide_word)}
                </div>
                `
                        : ''
                }

                ${
                    senses.length
                        ? `
                <div class="dict-detail__section">
                    <h3 class="dict-detail__section-title">Meanings</h3>
                    <ol class="dict-detail__senses">
                        ${senses
                            .map(
                                (sense) => `
                            <li class="dict-sense">
                                <strong class="dict-sense__guide">${this.escapeHtml(sense.guide_word || '')}</strong>
                                ${
                                    sense.definition
                                        ? `<p class="dict-sense__definition">${this.escapeHtml(sense.definition)}</p>`
                                        : ''
                                }
                            </li>
                        `
                            )
                            .join('')}
                    </ol>
                </div>
                `
                        : ''
                }

                ${
                    variants.length
                        ? `
                <div class="dict-detail__section">
                    <h3 class="dict-detail__section-title">Variants</h3>
                    <ul class="dict-detail__variants">
                        ${variants
                            .slice(0, 12)
                            .map(
                                (variant) => `
                            <li class="dict-variant">
                                <span class="dict-variant__form">${this.escapeHtml(variant.form)}</span>
                                <span class="dict-variant__count">${variant.count}</span>
                            </li>
                        `
                            )
                            .join('')}
                    </ul>
                    ${
                        variants.length > 12
                            ? `<p class="dict-detail__more">+ ${variants.length - 12} more variants</p>`
                            : ''
                    }
                </div>
                `
                        : ''
                }

                ${
                    attestations.length
                        ? `
                <div class="dict-detail__section">
                    <h3 class="dict-detail__section-title">Attestations</h3>
                    <ul class="dict-detail__attestations">
                        ${attestations
                            .slice(0, 10)
                            .map(
                                (att) => `
                            <li class="dict-attestation">
                                <a href="/tablets/${this.escapeHtml(att.p_number)}" class="dict-attestation__link">
                                    ${this.escapeHtml(att.p_number)}
                                </a>
                                <span class="dict-attestation__meta">
                                    ${att.period ? this.escapeHtml(att.period) : ''}
                                    ${att.period && att.provenience ? ' · ' : ''}
                                    ${att.provenience ? this.escapeHtml(att.provenience) : ''}
                                </span>
                            </li>
                        `
                            )
                            .join('')}
                    </ul>
                    ${
                        data.attestations.total_count > 10
                            ? `<p class="dict-detail__more">+ ${data.attestations.total_count - 10} more attestations</p>`
                            : ''
                    }
                </div>
                `
                        : ''
                }

                ${
                    relatedWords.length
                        ? `
                <div class="dict-detail__section">
                    <h3 class="dict-detail__section-title">Related Words</h3>
                    <ul class="dict-detail__related">
                        ${relatedWords
                            .slice(0, 8)
                            .map(
                                (rel) => `
                            <li class="dict-related">
                                <button class="dict-related__link" data-entry-id="${this.escapeHtml(rel.to_entry_id)}">
                                    ${this.escapeHtml(rel.citation_form || rel.to_entry_id)}
                                </button>
                                <span class="dict-related__type">${this.escapeHtml(rel.relationship_type || '')}</span>
                            </li>
                        `
                            )
                            .join('')}
                    </ul>
                </div>
                `
                        : ''
                }
            </div>
        `;

        this.elements.detail.innerHTML = html;

        // Attach click handlers for related words
        this.elements.detail.querySelectorAll('.dict-related__link').forEach((link) => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const entryId = link.dataset.entryId;
                if (entryId) {
                    this.selectWord(entryId);
                }
            });
        });
    }

    renderSkeleton() {
        const skeletons = Array(10)
            .fill(null)
            .map(
                () => `
            <div class="list-item list-item--skeleton">
                <div class="list-item__header">
                    <span class="list-item__title"></span>
                    <span class="list-item__subtitle"></span>
                </div>
                <div class="list-item__meta">
                    <span class="badge badge--sm"></span>
                </div>
            </div>
        `
            )
            .join('');

        this.elements.wordList.innerHTML = skeletons;
    }

    renderDetailSkeleton() {
        this.elements.detail.innerHTML = '<div class="dict-detail dict-detail--skeleton"></div>';
    }

    renderError() {
        this.elements.wordList.innerHTML = `
            <div class="dict-empty">
                <p>Failed to load dictionary entries. Please try again.</p>
            </div>
        `;
    }

    renderDetailError() {
        this.elements.detail.innerHTML = `
            <div class="dict-detail__error">
                <p>Failed to load word details. Please try again.</p>
            </div>
        `;
    }

    loadMore() {
        this.state.page += 1;
        this.loadWordList(true);
    }

    updateLoadMoreButton(data) {
        if (!this.elements.loadMoreBtn) return;

        const hasMore = data.page * data.per_page < data.total;
        this.elements.loadMoreBtn.hidden = !hasMore;
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    if (document.querySelector('[data-dict-browser]')) {
        new DictionaryBrowser();
    }
});
