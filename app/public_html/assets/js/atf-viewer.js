/**
 * ATF Viewer Component
 * Interactive transliteration viewer with surface tabs, dictionary panel, and view modes
 */

class ATFViewer {
    constructor(container, options = {}) {
        this.container = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        if (!this.container) {
            console.error('ATFViewer: Container not found');
            return;
        }

        this.options = {
            showLegend: true,
            defaultMode: 'interactive',
            onWordClick: null,
            ...options
        };

        // State
        this.pNumber = null;
        this.rawATF = '';
        this.data = null;
        this.legend = [];
        this.mode = this.options.defaultMode;
        this.currentSurface = 0;
        this.translationLines = null;
        this.hasTranslation = false;

        // Definition cache
        this.definitionCache = new Map();
        this.checkedWords = new Set();

        // Knowledge sidebar state
        this.knowledgeSidebarOpen = false;
        this.activeKnowledgeTab = 'dictionary';
        this.lastDictionaryWord = null;

        // Dictionary browser state
        this.dictionaryMode = 'browse'; // 'browse' | 'word'
        this.dictionarySearch = '';
        this.dictionaryFilters = {
            language: null,
            pos: null
        };
        this.dictionaryResults = [];
        this.dictionaryResultsOffset = 0;
        this.dictionaryResultsLimit = 50;
        this.dictionaryTotalCount = 0;
        this.selectedEntryId = null;
        this.dictionarySearchTimeout = null;

        // Build initial structure
        this.render();
    }

    /**
     * Load ATF data for a tablet
     */
    async load(pNumber) {
        this.pNumber = pNumber;

        try {
            // Fetch parsed ATF
            const response = await fetch(`/api/atf.php?p=${pNumber}&parsed=1`);
            if (!response.ok) throw new Error('ATF not available');

            const result = await response.json();
            this.rawATF = result.atf;
            this.data = result.parsed;
            this.legend = result.legend || [];

            // Update UI state flags
            this.container.classList.toggle('atf-viewer--single-surface',
                !this.data.hasMultipleSurfaces);
            this.container.classList.toggle('atf-viewer--single-column',
                !this.data.hasMultipleColumns);

            // Set initial surface
            this.currentSurface = 0;

            // Check for translation
            await this.loadTranslation();

            // Render content
            this.renderTabs();
            this.renderLegend();
            this.renderContent();

            // Check definitions for all words
            this.checkDefinitions();

        } catch (err) {
            console.error('ATFViewer: Failed to load ATF', err);
            this.renderError(err.message);
        }
    }

    /**
     * Load translation data
     */
    async loadTranslation() {
        try {
            const response = await fetch(`/api/translation-lines.php?p=${this.pNumber}`);
            if (response.ok) {
                const result = await response.json();
                if (result.has_translation) {
                    this.translationLines = result.lines;
                    this.translationRaw = result.raw;
                    this.translationLanguage = result.language;
                    this.hasTranslation = true;
                }
            }
        } catch (err) {
            // Translation not available - that's fine
            this.hasTranslation = false;
        }

        // Update parallel mode button
        const parallelBtn = this.container.querySelector('[data-mode="parallel"]');
        if (parallelBtn) {
            parallelBtn.disabled = !this.hasTranslation;
            parallelBtn.title = this.hasTranslation ? '' : 'No translation available';
        }

        // Hide the separate translation section if we have ATF viewer with translation
        if (this.hasTranslation) {
            const separateTranslationSection = document.querySelector('.translation-section');
            if (separateTranslationSection) {
                separateTranslationSection.style.display = 'none';
            }
        }
    }

    /**
     * Set view mode
     */
    setMode(mode) {
        if (mode === this.mode) return;
        if (mode === 'parallel' && !this.hasTranslation) return;

        this.mode = mode;

        // Update button states
        this.container.querySelectorAll('.atf-mode').forEach(btn => {
            btn.classList.toggle('atf-mode--active', btn.dataset.mode === mode);
        });

        // Update container class
        this.container.classList.remove('atf-viewer--mode-raw', 'atf-viewer--mode-interactive', 'atf-viewer--mode-parallel');
        this.container.classList.add(`atf-viewer--mode-${mode}`);

        // Re-render content for mode
        this.renderContent();
    }

    /**
     * Set current surface
     */
    setSurface(index) {
        if (index === this.currentSurface) return;
        if (!this.data?.surfaces[index]) return;

        this.currentSurface = index;

        // Update tab states
        this.container.querySelectorAll('.atf-tab').forEach((tab, i) => {
            tab.classList.toggle('atf-tab--active', i === index);
        });

        // Re-render content
        this.renderContent();
    }

    /**
     * Build initial DOM structure
     */
    render() {
        this.container.classList.add('atf-viewer');
        this.container.innerHTML = `
            <div class="atf-viewer__main">
                <div class="atf-viewer__header">
                    <button class="viewer-toggle" aria-label="Toggle viewer size" aria-expanded="false" title="Expand/collapse tablet image">
                        <svg class="viewer-toggle__icon-expand" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                            <path d="M12.9998 6L11.5898 7.41L16.1698 12L11.5898 16.59L12.9998 18L18.9998 12L12.9998 6Z"/>
                            <path d="M6.41 6L5 7.41L9.58 12L5 16.59L6.41 18L12.41 12L6.41 6Z"/>
                        </svg>
                        <svg class="viewer-toggle__icon-collapse" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                            <path d="M11 18L12.41 16.59L7.83 12L12.41 7.41L11 6L5 12L11 18Z"/>
                            <path d="M17.5898 18L18.9998 16.59L14.4198 12L18.9998 7.41L17.5898 6L11.5898 12L17.5898 18Z"/>
                        </svg>
                    </button>
                    <nav class="atf-tabs" role="tablist"></nav>
                    <div class="atf-modes">
                        <button class="atf-mode atf-mode--active" data-mode="interactive">Interactive</button>
                        <button class="atf-mode" data-mode="raw">Raw</button>
                        <button class="atf-mode" data-mode="parallel" disabled title="No translation available">+ Translation</button>
                    </div>
                    <button class="btn btn--icon-only btn--toggle" aria-label="Toggle knowledge sidebar" aria-expanded="false" title="Open knowledge sidebar">
                        <svg viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
                            <path d="M17.5 14.3301C15.8 14.3301 14.26 14.6201 13 15.1601V16.8201C14.13 16.1801 15.7 15.8301 17.5 15.8301C18.38 15.8301 19.23 15.9201 20 16.0901V14.5701C19.21 14.4101 18.36 14.3301 17.5 14.3301Z" fill="currentColor"/>
                            <path d="M13 12.4902V14.1502C14.13 13.5102 15.7 13.1602 17.5 13.1602C18.38 13.1602 19.23 13.2502 20 13.4202V11.9002C19.21 11.7502 18.36 11.6602 17.5 11.6602C15.8 11.6602 14.26 11.9602 13 12.4902Z" fill="currentColor"/>
                            <path d="M17.5 10.5C18.38 10.5 19.23 10.59 20 10.76V9.24C19.21 9.09 18.36 9 17.5 9C15.8 9 14.26 9.29 13 9.83V11.49C14.13 10.85 15.7 10.5 17.5 10.5Z" fill="currentColor"/>
                            <path d="M21 5C19.89 4.65 18.67 4.5 17.5 4.5C15.55 4.5 13.45 4.9 12 6C10.55 4.9 8.45 4.5 6.5 4.5C4.55 4.5 2.45 4.9 1 6V21.5C2.45 20.4 4.55 20 6.5 20C8.45 20 10.55 20.4 12 21.5C13.45 20.4 15.55 20 17.5 20C18.67 20 19.89 20.15 21 20.5C21.75 20.75 22.4 21.05 23 21.5V6C22.4 5.55 21.75 5.25 21 5ZM21 18.5C19.9 18.15 18.7 18 17.5 18C15.8 18 13.35 18.65 12 19.5V8C13.35 7.15 15.8 6.5 17.5 6.5C18.7 6.5 19.9 6.65 21 7V18.5Z" fill="currentColor"/>
                        </svg>
                    </button>
                </div>
                <div class="atf-viewer__body">
                    <div class="atf-content"></div>
                </div>
                <div class="atf-legend">
                    <div class="atf-legend__items"></div>
                </div>
            </div>
            <aside class="atf-knowledge-sidebar atf-knowledge-sidebar--hidden">
                <div class="atf-knowledge-sidebar__header">
                    <nav class="knowledge-tabs" role="tablist">
                        <button class="knowledge-tab knowledge-tab--active" data-tab="dictionary" role="tab" aria-selected="true">Dictionary</button>
                        <button class="knowledge-tab" data-tab="research" role="tab" aria-selected="false">Research</button>
                        <button class="knowledge-tab" data-tab="discussion" role="tab" aria-selected="false">Discussion</button>
                        <button class="knowledge-tab" data-tab="context" role="tab" aria-selected="false">Context</button>
                    </nav>
                    <button class="atf-knowledge-sidebar__close" aria-label="Close">&times;</button>
                </div>
                <div class="atf-knowledge-sidebar__body">
                    <!-- Dictionary Tab Content -->
                    <div class="knowledge-tab-content knowledge-tab-content--active" data-content="dictionary">
                        <!-- Browse Mode UI -->
                        <div class="dictionary-browse">
                            <!-- Search Bar -->
                            <div class="dictionary-search">
                                <input type="text" class="dictionary-search__input" placeholder="Search dictionary..." aria-label="Search dictionary">
                                <button class="dictionary-search__clear" aria-label="Clear search" style="display: none;">&times;</button>
                            </div>

                            <!-- Filter Bar -->
                            <div class="dictionary-filters">
                                <select class="dictionary-filter__language" aria-label="Filter by language">
                                    <option value="">All Languages</option>
                                    <option value="akk">Akkadian (11,357)</option>
                                    <option value="sux">Sumerian (5,271)</option>
                                    <option value="qpn">Personal Names (4,039)</option>
                                    <option value="sux-x-emesal">Emesal (146)</option>
                                    <option value="xhu">Hurrian (137)</option>
                                    <option value="uga">Ugaritic (100)</option>
                                </select>
                                <select class="dictionary-filter__pos" aria-label="Filter by part of speech">
                                    <option value="">All Parts of Speech</option>
                                    <optgroup label="Words">
                                        <option value="N">Noun</option>
                                        <option value="V">Verb</option>
                                        <option value="AJ">Adjective</option>
                                        <option value="AV">Adverb</option>
                                        <option value="NU">Number</option>
                                    </optgroup>
                                    <optgroup label="Pronouns">
                                        <option value="DP">Demonstrative</option>
                                        <option value="IP">Independent</option>
                                        <option value="PP">Personal</option>
                                        <option value="RP">Relative</option>
                                        <option value="XP">Indefinite</option>
                                        <option value="QP">Interrogative</option>
                                    </optgroup>
                                    <optgroup label="Function Words">
                                        <option value="CNJ">Conjunction</option>
                                        <option value="PRP">Preposition</option>
                                        <option value="DET">Determiner</option>
                                        <option value="MOD">Modal</option>
                                        <option value="REL">Relative</option>
                                    </optgroup>
                                    <optgroup label="Proper Names">
                                        <option value="DN">Divine Name</option>
                                        <option value="PN">Personal Name</option>
                                        <option value="RN">Royal Name</option>
                                        <option value="GN">Geographic Name</option>
                                        <option value="TN">Temple Name</option>
                                        <option value="WN">Watercourse Name</option>
                                        <option value="FN">Field Name</option>
                                        <option value="MN">Month Name</option>
                                        <option value="ON">Object Name</option>
                                        <option value="AN">Agricultural Name</option>
                                    </optgroup>
                                </select>
                            </div>

                            <!-- Active Filter Chips -->
                            <div class="dictionary-filter-chips" style="display: none;"></div>

                            <!-- Results List -->
                            <div class="dictionary-results">
                                <div class="dictionary-results__list"></div>
                                <div class="dictionary-results__footer">
                                    <span class="dictionary-results__count">Loading...</span>
                                    <button class="dictionary-results__load-more" style="display: none;">Load more</button>
                                </div>
                            </div>
                        </div>

                        <!-- Word Detail UI (for word clicks) -->
                        <div class="dictionary-word-detail" style="display: none;">
                            <div class="dictionary-word-header">
                                <button class="dictionary-word-detail__back" aria-label="Back to browse">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M19 12H5M12 19l-7-7 7-7"/>
                                    </svg>
                                    <span class="dictionary-word-header__citation"></span>
                                </button>
                            </div>
                            <div class="dictionary-content"></div>
                        </div>
                    </div>
                    <!-- Research Tab Content -->
                    <div class="knowledge-tab-content" data-content="research">
                        <div class="knowledge-tab-placeholder">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>
                            </svg>
                            <h3>Research Notes</h3>
                            <p>Cross-references, parallel texts, and scholarly notes will appear here.</p>
                        </div>
                    </div>
                    <!-- Discussion Tab Content -->
                    <div class="knowledge-tab-content" data-content="discussion">
                        <div class="knowledge-tab-placeholder">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
                            </svg>
                            <h3>Discussion</h3>
                            <p>Community interpretations and scholarly discussions will appear here.</p>
                        </div>
                    </div>
                    <!-- Context Tab Content -->
                    <div class="knowledge-tab-content" data-content="context">
                        <div class="knowledge-tab-placeholder">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/>
                                <rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
                            </svg>
                            <h3>Historical Context</h3>
                            <p>Period information, archaeological context, and related materials will appear here.</p>
                        </div>
                    </div>
                </div>
            </aside>
        `;

        // Event listeners
        this.container.querySelectorAll('.atf-mode').forEach(btn => {
            btn.addEventListener('click', () => this.setMode(btn.dataset.mode));
        });

        // Knowledge sidebar event listeners
        this.container.querySelector('.atf-viewer__header .btn.btn--toggle').addEventListener('click', () => {
            this.toggleKnowledgeSidebar();
        });

        this.container.querySelector('.atf-knowledge-sidebar__close').addEventListener('click', () => {
            this.hideKnowledgeSidebar();
        });

        this.container.querySelectorAll('.knowledge-tab').forEach(btn => {
            btn.addEventListener('click', () => {
                this.setActiveKnowledgeTab(btn.dataset.tab);
            });
        });

        // Dictionary browse event listeners
        const searchInput = this.container.querySelector('.dictionary-search__input');
        const searchClear = this.container.querySelector('.dictionary-search__clear');
        const languageFilter = this.container.querySelector('.dictionary-filter__language');
        const posFilter = this.container.querySelector('.dictionary-filter__pos');
        const loadMoreBtn = this.container.querySelector('.dictionary-results__load-more');
        const backBtn = this.container.querySelector('.dictionary-word-detail__back');

        searchInput.addEventListener('input', (e) => {
            this.searchDictionary(e.target.value);
            searchClear.style.display = e.target.value ? 'block' : 'none';
        });

        searchClear.addEventListener('click', () => {
            searchInput.value = '';
            searchClear.style.display = 'none';
            this.searchDictionary('');
        });

        languageFilter.addEventListener('change', (e) => {
            this.filterDictionary('language', e.target.value);
        });

        posFilter.addEventListener('change', (e) => {
            this.filterDictionary('pos', e.target.value);
        });

        loadMoreBtn.addEventListener('click', () => {
            this.loadDictionaryPage(this.dictionaryResultsOffset + this.dictionaryResultsLimit);
        });

        backBtn.addEventListener('click', () => {
            this.backToBrowse();
        });

        // Legend toggle state
        if (!this.options.showLegend) {
            this.container.querySelector('.atf-legend').open = false;
        }
    }

    /**
     * Render surface tabs
     */
    renderTabs() {
        const tabsContainer = this.container.querySelector('.atf-tabs');
        if (!this.data?.surfaces) return;

        tabsContainer.innerHTML = this.data.surfaces.map((surface, i) => {
            const lineCount = surface.columns.reduce((sum, col) =>
                sum + col.lines.filter(l => l.type === 'content').length, 0);

            return `
                <button class="atf-tab ${i === 0 ? 'atf-tab--active' : ''}"
                        role="tab"
                        aria-selected="${i === 0}"
                        data-surface="${i}">
                    ${surface.label}
                    <span class="atf-tab__count">${lineCount}</span>
                </button>
            `;
        }).join('');

        // Tab click handlers
        tabsContainer.querySelectorAll('.atf-tab').forEach((tab, i) => {
            tab.addEventListener('click', () => this.setSurface(i));
        });
    }

    /**
     * Render legend
     */
    renderLegend() {
        const legendContainer = this.container.querySelector('.atf-legend__items');
        if (!this.legend.length) {
            this.container.querySelector('.atf-legend').style.display = 'none';
            return;
        }

        legendContainer.innerHTML = this.legend.map(item => `
            <span class="atf-legend__item">
                <span class="atf-legend__swatch atf-legend__swatch--${item.class}">${item.symbol}</span>
                ${item.label}
            </span>
        `).join('');
    }

    /**
     * Render content based on mode
     */
    renderContent() {
        const contentArea = this.container.querySelector('.atf-content');

        if (this.mode === 'raw') {
            contentArea.textContent = this.rawATF;
            return;
        }

        if (!this.data?.surfaces[this.currentSurface]) {
            contentArea.innerHTML = '<p class="atf-dictionary__empty">No content available</p>';
            return;
        }

        const surface = this.data.surfaces[this.currentSurface];
        let html = '';

        // Render columns
        if (surface.columns.length > 1) {
            html = '<div class="atf-columns">';
            surface.columns.forEach(col => {
                html += `
                    <div class="atf-column">
                        <div class="atf-column__header">Column ${col.number || ''}</div>
                        ${this.renderLines(col.lines)}
                    </div>
                `;
            });
            html += '</div>';
        } else if (surface.columns.length === 1) {
            html = this.renderLines(surface.columns[0].lines);
        }

        contentArea.innerHTML = html;

        // Add word click handlers
        this.attachWordHandlers();

        // Add composite click handlers
        this.attachCompositeHandlers();

        // Parallel mode: add translation column
        if (this.mode === 'parallel' && this.hasTranslation) {
            this.renderTranslationColumn(surface);
        }
    }

    /**
     * Render lines
     */
    renderLines(lines) {
        return lines.map(line => {
            if (line.type === 'state') {
                return `<div class="atf-state">$ ${this.escapeHtml(line.text)}</div>`;
            }

            if (line.type === 'content') {
                const numberClass = line.isPrime ? 'atf-line__number--prime' : '';
                const wordsHtml = this.renderWords(line.words);
                const compositeHtml = line.composite
                    ? `<span class="atf-composite"><svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-hidden="true"><path d="M4 6H2V22H18V20H4V6ZM22 2H6V18H22V2ZM20 12L17.5 10.5L15 12V4H20V12Z"/></svg>${line.composite.line}</span>`
                    : '';

                // Inline translation (from #tr.XX: lines in ATF)
                let translationHtml = '';
                if (line.translations) {
                    // Prefer English, fall back to first available
                    const transText = line.translations.en || Object.values(line.translations)[0];
                    if (transText) {
                        translationHtml = `<div class="atf-line__translation">${this.escapeHtml(transText)}</div>`;
                    }
                }

                return `
                    <div class="atf-line" data-line="${line.number}">
                        <span class="atf-line__number ${numberClass}">${line.number.replace('.', '').replace(/'+/g, '')}</span>
                        <span class="atf-line__content">${wordsHtml}</span>
                    </div>
                    ${translationHtml}
                    ${compositeHtml}
                `;
            }

            return '';
        }).join('');
    }

    /**
     * Render words with appropriate classes
     */
    renderWords(words) {
        return words.map(word => {
            if (word.type === 'punctuation') {
                return this.escapeHtml(word.text);
            }

            if (word.type === 'broken') {
                return `<span class="atf-broken">${this.escapeHtml(word.text)}</span>`;
            }

            if (word.type === 'logogram') {
                const lookup = word.lookup ? `data-lookup="${this.escapeHtml(word.lookup)}"` : '';
                return `<span class="atf-word atf-logo" ${lookup}>${this.escapeHtml(word.text)}</span>`;
            }

            if (word.type === 'determinative') {
                const detDisplay = word.detDisplay || `(${word.determinative})`;
                const detClass = `atf-det atf-det--${word.detType}`;
                const lookup = word.lookup ? `data-lookup="${this.escapeHtml(word.lookup)}"` : '';

                if (word.position === 'prefix') {
                    return `<span class="${detClass}">${detDisplay}</span><span class="atf-word" ${lookup}>${this.escapeHtml(word.text)}</span>`;
                } else {
                    return `<span class="atf-word" ${lookup}>${this.escapeHtml(word.text)}</span><span class="${detClass} atf-det--suffix">${detDisplay}</span>`;
                }
            }

            if (word.type === 'word') {
                const classes = ['atf-word'];
                if (word.damaged) classes.push('atf-word--damaged');
                if (word.uncertain) classes.push('atf-word--uncertain');
                if (word.corrected) classes.push('atf-word--corrected');

                const lookup = word.lookup ? `data-lookup="${this.escapeHtml(word.lookup)}"` : '';

                // Extract damage markers from end of text
                const markerMatch = word.text.match(/([#?!]+)$/);
                const markers = markerMatch ? markerMatch[1] : '';
                const displayText = word.text.replace(/[#?!]+$/, '');

                // Build HTML with markers as superscript
                let html = `<span class="${classes.join(' ')}" ${lookup}>${this.escapeHtml(displayText)}`;
                if (markers) {
                    html += `<sup class="atf-markers">${this.escapeHtml(markers)}</sup>`;
                }
                html += `</span>`;

                return html;
            }

            return this.escapeHtml(word.text || '');
        }).join(' ');
    }

    /**
     * Render translation column for parallel mode
     * Shows full translation as a block since line-by-line matching is unreliable
     */
    renderTranslationColumn(surface) {
        const body = this.container.querySelector('.atf-viewer__body');

        // Remove existing translation column
        body.querySelector('.atf-translation-column')?.remove();

        const transCol = document.createElement('div');
        transCol.className = 'atf-translation-column';

        const langLabel = this.translationLanguage?.toUpperCase() || 'EN';

        // Check if we have any line-matched translations
        let hasLineMatches = false;
        if (this.translationLines) {
            surface.columns.forEach(col => {
                col.lines.forEach(line => {
                    if (line.type !== 'content') return;
                    const key = `${surface.name}_${col.number || 1}_${line.number}`;
                    if (this.translationLines[key]) {
                        hasLineMatches = true;
                    }
                });
            });
        }

        let html = `<div class="atf-translation-column__header">Translation (${langLabel})</div>`;

        if (hasLineMatches) {
            // Show line-by-line if we have matches
            surface.columns.forEach(col => {
                col.lines.forEach(line => {
                    if (line.type !== 'content') return;

                    const key = `${surface.name}_${col.number || 1}_${line.number}`;
                    const trans = this.translationLines?.[key];

                    html += `
                        <div class="atf-translation-line" data-line="${line.number}">
                            <span class="atf-translation-line__number">${line.number.replace('.', '')}</span>
                            <span class="atf-translation-line__text">${trans ? this.escapeHtml(trans.text) : '—'}</span>
                        </div>
                    `;
                });
            });
        } else if (this.translationRaw) {
            // Show full translation as a block
            html += `
                <div class="atf-translation-block">
                    ${this.escapeHtml(this.translationRaw).replace(/\n/g, '<br>')}
                </div>
            `;
        } else {
            html += `<div class="atf-translation-empty">Translation not available for this surface</div>`;
        }

        transCol.innerHTML = html;
        body.appendChild(transCol);
    }

    /**
     * Attach click handlers to words
     */
    attachWordHandlers() {
        this.container.querySelectorAll('.atf-word[data-lookup]').forEach(el => {
            el.addEventListener('click', (e) => {
                e.preventDefault();
                const lookup = el.dataset.lookup;
                if (lookup) {
                    this.showDictionary(lookup, el);
                }
            });
        });
    }

    /**
     * Check definitions for all words (batch)
     */
    async checkDefinitions() {
        const words = this.container.querySelectorAll('.atf-word[data-lookup]');
        if (!words.length) return;

        // Collect unique lookups not already checked
        const lookups = [...new Set(
            Array.from(words)
                .map(el => el.dataset.lookup)
                .filter(w => w && w.length > 1 && !this.checkedWords.has(w))
        )];

        if (!lookups.length) return;

        try {
            const response = await fetch('/api/glossary-check.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ words: lookups })
            });

            const data = await response.json();

            if (data.definitions) {
                words.forEach(el => {
                    const lookup = el.dataset.lookup;
                    if (!lookup) return;

                    this.checkedWords.add(lookup);

                    if (data.definitions[lookup]) {
                        el.classList.add('atf-word--has-definition');
                    } else {
                        el.classList.add('atf-word--no-definition');
                    }
                });
            }
        } catch (err) {
            console.warn('ATFViewer: Failed to check definitions', err);
            words.forEach(el => el.classList.add('atf-word--no-definition'));
        }
    }

    /**
     * Show knowledge sidebar
     * @param {string} tab - Tab to activate ('dictionary', 'research', 'discussion', 'context')
     * @param {string} word - Optional word for dictionary tab
     */
    showKnowledgeSidebar(tab = null, word = null) {
        const sidebar = this.container.querySelector('.atf-knowledge-sidebar');
        const toggleBtn = this.container.querySelector('.atf-viewer__header .btn.btn--toggle');

        // Show sidebar
        sidebar.classList.remove('atf-knowledge-sidebar--hidden');
        this.knowledgeSidebarOpen = true;

        // Update toggle button state
        if (toggleBtn) {
            toggleBtn.classList.add('btn--active');
            toggleBtn.setAttribute('aria-expanded', 'true');
        }

        // If tab specified, switch to it
        if (tab) {
            this.setActiveKnowledgeTab(tab);
        }

        // If word provided and dictionary tab, load definition
        if (word && (tab === 'dictionary' || this.activeKnowledgeTab === 'dictionary')) {
            this.loadDictionaryContent(word);
        } else if (!word && this.activeKnowledgeTab === 'dictionary') {
            // Initialize browse mode if opening dictionary tab without a word
            if (this.dictionaryResults.length === 0) {
                this.setDictionaryMode('browse');
                this.initDictionaryBrowser();
            } else {
                // Already have results, just show browse mode
                this.setDictionaryMode('browse');
            }
        }
    }

    /**
     * Hide knowledge sidebar
     */
    hideKnowledgeSidebar() {
        const sidebar = this.container.querySelector('.atf-knowledge-sidebar');
        const toggleBtn = this.container.querySelector('.atf-viewer__header .btn.btn--toggle');

        sidebar.classList.add('atf-knowledge-sidebar--hidden');
        this.knowledgeSidebarOpen = false;

        // Update toggle button state
        if (toggleBtn) {
            toggleBtn.classList.remove('btn--active');
            toggleBtn.setAttribute('aria-expanded', 'false');
        }
    }

    /**
     * Toggle knowledge sidebar
     */
    toggleKnowledgeSidebar() {
        if (this.knowledgeSidebarOpen) {
            this.hideKnowledgeSidebar();
        } else {
            // Open to last active tab (or dictionary by default)
            this.showKnowledgeSidebar(this.activeKnowledgeTab);
        }
    }

    /**
     * Set active knowledge tab
     * @param {string} tabName - Tab to activate
     */
    setActiveKnowledgeTab(tabName) {
        if (this.activeKnowledgeTab === tabName) return;

        const sidebar = this.container.querySelector('.atf-knowledge-sidebar');

        // Update tab buttons
        sidebar.querySelectorAll('.knowledge-tab').forEach(btn => {
            const isActive = btn.dataset.tab === tabName;
            btn.classList.toggle('knowledge-tab--active', isActive);
            btn.setAttribute('aria-selected', isActive);
        });

        // Update content panels
        sidebar.querySelectorAll('.knowledge-tab-content').forEach(content => {
            const isActive = content.dataset.content === tabName;
            content.classList.toggle('knowledge-tab-content--active', isActive);
        });

        this.activeKnowledgeTab = tabName;
    }

    /**
     * Load dictionary content
     * @param {string} word - Word to look up
     */
    async loadDictionaryContent(word) {
        const sidebar = this.container.querySelector('.atf-knowledge-sidebar');
        const dictContent = sidebar.querySelector('.dictionary-content');

        this.lastDictionaryWord = word;

        // Switch to word mode
        this.setDictionaryMode('word');

        // Check cache first
        if (this.definitionCache.has(word)) {
            this.renderDictionaryContent(this.definitionCache.get(word), word);
            return;
        }

        // Show loading
        dictContent.innerHTML = '<div class="atf-dictionary__loading">Loading...</div>';

        try {
            const response = await fetch(`/api/glossary.php?q=${encodeURIComponent(word)}&full=1`);
            const data = await response.json();

            // Cache result
            this.definitionCache.set(word, data);

            this.renderDictionaryContent(data, word);

        } catch (err) {
            dictContent.innerHTML = '<div class="atf-dictionary__empty">Failed to load definition</div>';
        }
    }

    /**
     * Set dictionary mode (browse or word)
     * @param {string} mode - 'browse' or 'word'
     */
    setDictionaryMode(mode) {
        this.dictionaryMode = mode;
        const browseUI = this.container.querySelector('.dictionary-browse');
        const wordUI = this.container.querySelector('.dictionary-word-detail');

        if (mode === 'browse') {
            browseUI.style.display = 'flex';
            wordUI.style.display = 'none';
        } else {
            browseUI.style.display = 'none';
            wordUI.style.display = 'block';
        }
    }

    /**
     * Initialize dictionary browser with initial results
     */
    async initDictionaryBrowser() {
        // Load initial results (first 50 entries alphabetically)
        await this.loadDictionaryPage(0);
    }

    /**
     * Search dictionary
     * @param {string} query - Search query
     */
    searchDictionary(query) {
        // Debounce search
        clearTimeout(this.dictionarySearchTimeout);
        this.dictionarySearchTimeout = setTimeout(async () => {
            this.dictionarySearch = query;
            this.dictionaryResultsOffset = 0; // Reset to first page
            await this.loadDictionaryPage(0);
        }, 300);
    }

    /**
     * Filter dictionary
     * @param {string} filterType - 'language' or 'pos'
     * @param {string} value - Filter value
     */
    async filterDictionary(filterType, value) {
        this.dictionaryFilters[filterType] = value || null;
        this.dictionaryResultsOffset = 0; // Reset to first page
        await this.loadDictionaryPage(0);
        this.updateFilterChips();
    }

    /**
     * Update filter chips display
     */
    updateFilterChips() {
        const chipsContainer = this.container.querySelector('.dictionary-filter-chips');
        const chips = [];

        if (this.dictionaryFilters.language) {
            const select = this.container.querySelector('.dictionary-filter__language');
            const option = select.querySelector(`option[value="${this.dictionaryFilters.language}"]`);
            chips.push({
                type: 'language',
                label: option.textContent,
                value: this.dictionaryFilters.language
            });
        }

        if (this.dictionaryFilters.pos) {
            const select = this.container.querySelector('.dictionary-filter__pos');
            const option = select.querySelector(`option[value="${this.dictionaryFilters.pos}"]`);
            chips.push({
                type: 'pos',
                label: option.textContent,
                value: this.dictionaryFilters.pos
            });
        }

        if (chips.length > 0) {
            chipsContainer.innerHTML = chips.map(chip => `
                <span class="dictionary-filter-chip" data-type="${chip.type}">
                    ${chip.label}
                    <button class="dictionary-filter-chip__remove" data-type="${chip.type}" aria-label="Remove filter">&times;</button>
                </span>
            `).join('');
            chipsContainer.style.display = 'flex';

            // Add remove handlers
            chipsContainer.querySelectorAll('.dictionary-filter-chip__remove').forEach(btn => {
                btn.addEventListener('click', () => {
                    const filterType = btn.dataset.type;
                    this.dictionaryFilters[filterType] = null;
                    const select = this.container.querySelector(`.dictionary-filter__${filterType}`);
                    select.value = '';
                    this.filterDictionary(filterType, '');
                });
            });
        } else {
            chipsContainer.style.display = 'none';
        }
    }

    /**
     * Load dictionary page
     * @param {number} offset - Page offset
     */
    async loadDictionaryPage(offset) {
        const resultsList = this.container.querySelector('.dictionary-results__list');
        const countEl = this.container.querySelector('.dictionary-results__count');
        const loadMoreBtn = this.container.querySelector('.dictionary-results__load-more');

        // Show loading for first page
        if (offset === 0) {
            resultsList.innerHTML = '<div class="dictionary-results__loading">Loading...</div>';
        }

        try {
            const params = new URLSearchParams({
                offset: offset,
                limit: this.dictionaryResultsLimit
            });

            if (this.dictionarySearch) {
                params.append('search', this.dictionarySearch);
            }
            if (this.dictionaryFilters.language) {
                params.append('language', this.dictionaryFilters.language);
            }
            if (this.dictionaryFilters.pos) {
                params.append('pos', this.dictionaryFilters.pos);
            }

            const response = await fetch(`/api/glossary-browse.php?${params}`);
            const data = await response.json();

            this.dictionaryResultsOffset = offset;
            this.dictionaryTotalCount = data.total;

            if (offset === 0) {
                // Replace results
                this.dictionaryResults = data.entries;
            } else {
                // Append results
                this.dictionaryResults = [...this.dictionaryResults, ...data.entries];
            }

            this.renderDictionaryResults();

            // Update count
            const showing = Math.min(this.dictionaryResults.length, this.dictionaryTotalCount);
            countEl.textContent = `Showing ${showing.toLocaleString()} of ${this.dictionaryTotalCount.toLocaleString()}`;

            // Show/hide load more button
            loadMoreBtn.style.display = data.hasMore ? 'inline-block' : 'none';

        } catch (err) {
            console.error('Failed to load dictionary page:', err);
            resultsList.innerHTML = '<div class="dictionary-results__error">Failed to load results</div>';
        }
    }

    /**
     * Render dictionary results list
     */
    renderDictionaryResults() {
        const resultsList = this.container.querySelector('.dictionary-results__list');

        if (this.dictionaryResults.length === 0) {
            resultsList.innerHTML = '<div class="dictionary-results__empty">No entries found</div>';
            return;
        }

        resultsList.innerHTML = this.dictionaryResults.map(entry => {
            const headword = entry.headword || '';
            const citationForm = entry.citation_form || '';
            const guideWord = entry.guide_word || '';
            const pos = entry.pos || '';
            const language = entry.language || '';
            const icount = entry.icount || 0;

            // Format display based on language
            const mainText = citationForm && citationForm !== headword
                ? `${headword} ${citationForm}`
                : headword;

            return `
                <div class="dictionary-results__item" data-entry-id="${entry.entry_id}">
                    <div class="dictionary-results__item-headword">${mainText}</div>
                    <div class="dictionary-results__item-meta">
                        ${guideWord} · ${pos} · ${language} · ${icount.toLocaleString()} occurrences
                    </div>
                </div>
            `;
        }).join('');

        // Add click handlers
        resultsList.querySelectorAll('.dictionary-results__item').forEach(item => {
            item.addEventListener('click', () => {
                const entryId = item.dataset.entryId;
                const entry = this.dictionaryResults.find(e => e.entry_id === entryId);
                if (entry) {
                    this.showDictionaryEntry(entry);
                }
            });
        });
    }

    /**
     * Show dictionary entry detail
     * @param {Object} entry - Dictionary entry
     */
    async showDictionaryEntry(entry) {
        // Load full definition for this entry's headword
        const word = entry.headword || entry.citation_form;
        if (word) {
            await this.loadDictionaryContent(word);
        }
    }

    /**
     * Return to browse mode
     */
    backToBrowse() {
        this.setDictionaryMode('browse');
    }

    /**
     * Show dictionary panel for a word (backward compatibility wrapper)
     */
    async showDictionary(word, targetEl) {
        this.showKnowledgeSidebar('dictionary', word);
    }

    /**
     * Hide dictionary panel (backward compatibility wrapper)
     */
    hideDictionary() {
        this.hideKnowledgeSidebar();
    }

    /**
     * Render dictionary panel content
     */
    renderDictionaryContent(data, word) {
        const sidebar = this.container.querySelector('.atf-knowledge-sidebar');
        const citationEl = sidebar.querySelector('.dictionary-word-header__citation');
        const body = sidebar.querySelector('.dictionary-content');

        if (!data.entries || data.entries.length === 0) {
            citationEl.textContent = word;
            body.innerHTML = `
                <div class="atf-dictionary__empty">
                    No definition found
                    <div class="atf-dictionary__empty-hint">This word may not be in the ORACC glossaries</div>
                </div>
            `;
            return;
        }

        const entry = data.entries[0];
        const posLabel = data.pos_labels?.[entry.pos] || entry.pos || '';

        // Header - show citation form
        citationEl.textContent = entry.citation_form || entry.headword || word;

        // Body content
        let html = '';

        // Prominent definition (guide_word)
        if (entry.guide_word) {
            html += `
                <div class="dictionary-definition">
                    <div class="dictionary-definition__text">${this.escapeHtml(entry.guide_word)}</div>
                </div>
            `;
        }

        // Metadata Fields
        html += '<dl class="atf-dictionary__fields">';

        if (entry.headword) {
            const fieldLabel = data.field_explanations?.headword ? 'Headword' : 'Dictionary Form';
            html += `
                <dt class="atf-dictionary__field-label">${fieldLabel}</dt>
                <dd class="atf-dictionary__field-value">${this.escapeHtml(entry.headword)}</dd>
            `;
        }

        if (entry.pos) {
            html += `
                <dt class="atf-dictionary__field-label">Part of Speech</dt>
                <dd class="atf-dictionary__field-value">${posLabel}</dd>
            `;
        }

        if (entry.language) {
            const langLabels = { akk: 'Akkadian', sux: 'Sumerian', qpc: 'Proto-Cuneiform' };
            html += `
                <dt class="atf-dictionary__field-label">Language</dt>
                <dd class="atf-dictionary__field-value">${langLabels[entry.language] || entry.language}</dd>
            `;
        }

        if (entry.icount) {
            html += `
                <dt class="atf-dictionary__field-label">Occurrences</dt>
                <dd class="atf-dictionary__field-value">${entry.icount.toLocaleString()} in corpus</dd>
            `;
        }

        html += '</dl>';

        // Variant forms
        const forms = data.forms?.[entry.entry_id];
        if (forms && forms.length > 0) {
            html += `
                <div class="atf-dictionary__variants">
                    <div class="atf-dictionary__variants-title">Variant Spellings (${forms.length})</div>
                    <div class="atf-dictionary__variants-list">
                        ${forms.slice(0, 10).map(f => `
                            <span class="atf-dictionary__variant">
                                ${this.escapeHtml(f.form)}
                                <span class="atf-dictionary__variant-count">${f.count || ''}</span>
                            </span>
                        `).join('')}
                        ${forms.length > 10 ? `<span class="atf-dictionary__variant">+${forms.length - 10} more</span>` : ''}
                    </div>
                </div>
            `;
        }

        // All entries (if more than one)
        if (data.entries.length > 1) {
            html += `
                <details class="atf-dictionary__entries">
                    <summary>All ${data.entries.length} entries for "${word}"</summary>
                    <div class="atf-dictionary__entries-list">
                        ${data.entries.map((e, i) => `
                            <div class="atf-dictionary__entry ${i === 0 ? 'atf-dictionary__entry--active' : ''}">
                                <div class="atf-dictionary__entry-head">
                                    <span class="atf-dictionary__entry-word">${this.escapeHtml(e.headword || word)}</span>
                                    ${e.pos ? `<span class="atf-dictionary__entry-pos">${e.pos}</span>` : ''}
                                </div>
                                <div class="atf-dictionary__entry-meaning">${this.escapeHtml(e.guide_word || 'No definition')}</div>
                            </div>
                        `).join('')}
                    </div>
                </details>
            `;
        }

        body.innerHTML = html;
    }

    /**
     * Hide dictionary panel
     */
    hideDictionary() {
        this.container.querySelector('.atf-dictionary').classList.add('atf-dictionary--hidden');
    }

    /**
     * Check if tablet belongs to composite and load if so
     */
    async checkComposites() {
        if (!this.data?.composites || this.data.composites.length === 0) {
            return;
        }

        // Load first composite (most tablets belong to one)
        const firstComposite = this.data.composites[0].q_number;
        await this.showCompositePanel(firstComposite);
    }

    /**
     * Show composite panel
     */
    async showCompositePanel(qNumber) {
        const panel = this.container.querySelector('.atf-composite-panel');
        const list = panel.querySelector('.atf-composite-list');

        // Show panel
        panel.classList.remove('atf-composite-panel--hidden');

        // Close dictionary if open to avoid clutter
        this.hideDictionary();

        // Show loading state
        list.innerHTML = '<div class="atf-dictionary__loading">Loading composite...</div>';

        try {
            // Fetch composite data
            const response = await fetch(`/api/composite.php?q=${qNumber}`);
            if (!response.ok) throw new Error('Failed to load composite');

            const data = await response.json();

            // Update panel header
            panel.querySelector('.atf-composite-panel__name').textContent =
                data.composite.designation || qNumber;

            // Render tablet list
            this.renderCompositeList(data.tablets);

        } catch (err) {
            console.error('ATFViewer: Failed to load composite', err);
            list.innerHTML = '<div class="atf-dictionary__empty">Failed to load composite</div>';
        }
    }

    /**
     * Render list of tablets in composite
     */
    renderCompositeList(tablets) {
        const list = this.container.querySelector('.atf-composite-list');

        list.innerHTML = tablets.map((tablet, index) => {
            const isCurrent = tablet.p_number === this.pNumber;
            const thumbnailUrl = `/api/thumbnail.php?p=${tablet.p_number}&size=64`;

            return `
                <div class="atf-composite-item ${isCurrent ? 'atf-composite-item--current' : ''}"
                     data-p-number="${tablet.p_number}">
                    <div class="atf-composite-thumbnail" data-p-number="${tablet.p_number}">
                        <img src="${thumbnailUrl}"
                             alt="${this.escapeHtml(tablet.designation)}"
                             loading="lazy"
                             onerror="this.style.display='none'; this.parentElement.classList.add('atf-composite-thumbnail--empty'); this.parentElement.innerHTML='𒀭';">
                    </div>
                    <div class="atf-composite-item__info">
                        <div class="atf-composite-item__pnumber">${this.escapeHtml(tablet.p_number)}</div>
                        <div class="atf-composite-item__designation">${this.escapeHtml(tablet.designation || 'Unknown')}</div>
                        <div class="atf-composite-item__position">${index + 1}/${tablets.length}</div>
                    </div>
                </div>
            `;
        }).join('');

        // Add click handlers
        list.querySelectorAll('.atf-composite-item').forEach(item => {
            item.addEventListener('click', () => {
                const pNumber = item.dataset.pNumber;
                if (pNumber !== this.pNumber) {
                    window.location.href = `/tablets/detail.php?p=${pNumber}`;
                }
            });
        });
    }

    /**
     * Attach click handlers to composite references
     */
    attachCompositeHandlers() {
        this.container.querySelectorAll('.atf-composite').forEach(el => {
            el.addEventListener('click', async (e) => {
                e.preventDefault();
                // Extract Q-number from text (>>Q000002 030)
                const match = el.textContent.match(/Q\d+/);
                if (match) {
                    await this.showCompositePanel(match[0]);
                }
            });
        });
    }

    /**
     * Render error state
     */
    renderError(message) {
        const contentArea = this.container.querySelector('.atf-content');
        contentArea.innerHTML = `
            <div class="atf-dictionary__empty">
                ${this.escapeHtml(message)}
                <div class="atf-dictionary__empty-hint">The transliteration may not be available for this tablet.</div>
            </div>
        `;
    }

    /**
     * Escape HTML special characters
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ATFViewer;
}
