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
        this.sidebarTransitioning = false;
        this.transitionTimeout = null;

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

        // Lemma data for interlinear glossing
        this.lemmasData = {};  // Indexed by line_no and word_no
        this.lemmasLoaded = false;
        this.glossaryGlossCache = new Map();  // lookup → guide_word cache

        // Build initial structure
        this.render();
    }

    /**
     * Safely parse JSON response, handling PHP errors that return HTML
     * @param {Response} response - Fetch response object
     * @returns {Promise<Object>} Parsed JSON data
     * @throws {Error} If response is not JSON or parsing fails
     */
    async safeJsonParse(response) {
        const contentType = response.headers.get('content-type');

        // Check if response is actually JSON
        if (!contentType || !contentType.includes('application/json')) {
            const text = await response.text();

            // Check if it's a PHP error (HTML response)
            if (text.includes('<br') || text.includes('Fatal error') || text.includes('Warning:')) {
                console.error('Server returned HTML error instead of JSON:', text.substring(0, 500));
                throw new Error('Server error - API returned HTML instead of JSON. This may be a PHP error or configuration issue.');
            }

            console.error('Unexpected content type:', contentType, 'Response:', text.substring(0, 500));
            throw new Error(`Expected JSON but got ${contentType || 'unknown content type'}`);
        }

        try {
            return await response.json();
        } catch (err) {
            console.error('JSON parse error:', err.message);
            throw new Error(`Failed to parse JSON response: ${err.message}`);
        }
    }

    /**
     * Load ATF data for a tablet
     */
    async load(pNumber) {
        this.pNumber = pNumber;

        try {
            // Fetch parsed ATF
            const response = await fetch(`/api/artifacts/${pNumber}/atf`);
            if (!response.ok) throw new Error('ATF not available');

            const result = await this.safeJsonParse(response);
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

            // Load lemmas for interlinear glossing
            await this.loadLemmas();

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
            const response = await fetch(`/api/artifacts/${this.pNumber}/translation`);
            if (response.ok) {
                const result = await this.safeJsonParse(response);
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

        // Hide the separate translation section if we have ATF viewer with translation
        if (this.hasTranslation) {
            this.container.classList.add('atf-viewer--has-translation');
            const separateTranslationSection = document.querySelector('.translation-section');
            if (separateTranslationSection) {
                separateTranslationSection.classList.add('is-hidden');
            }
        }
    }

    /**
     * Load lemma data for interlinear glossing
     */
    async loadLemmas() {
        // Clear glossary cache on new tablet load
        this.glossaryGlossCache.clear();

        try {
            const response = await fetch(`/api/artifacts/${this.pNumber}/lemmas`);
            if (response.ok) {
                const result = await this.safeJsonParse(response);
                this.lemmasData = result.lemmas || {};
                this.lemmasLoaded = true;
            }
        } catch (err) {
            console.log('ATFViewer: Lemmas not available for glossing');
            this.lemmasLoaded = false;
            this.lemmasData = {};
        }
    }

    /**
     * Get gloss (guide word) for a word using priority chain:
     * 1. Lemma data (from lemmas table)
     * 2. Glossary API fallback
     * 3. Return null if neither available
     *
     * @returns {Object|null} { gloss: string, source: 'lemma'|'glossary' }
     */
    async getWordGloss(lineNo, wordNo, lookup) {
        // Priority 1: Check lemmas table
        const lineNoStr = String(lineNo);
        const wordNoStr = String(wordNo);

        if (this.lemmasData[lineNoStr]?.[wordNoStr]?.gw) {
            return {
                gloss: this.lemmasData[lineNoStr][wordNoStr].gw,
                source: 'lemma'
            };
        }

        // Priority 2: Fallback to glossary
        if (!lookup || lookup.length < 2) return null;

        // Check cache
        if (this.glossaryGlossCache.has(lookup)) {
            const cached = this.glossaryGlossCache.get(lookup);
            return cached ? { gloss: cached, source: 'glossary' } : null;
        }

        // Fetch from glossary API
        try {
            const response = await fetch(`/api/dictionary/words?search=q=${encodeURIComponent(lookup)}&limit=1`);
            const data = await this.safeJsonParse(response);

            if (data.entries && data.entries.length > 0) {
                const guideWord = data.entries[0].guide_word || null;
                this.glossaryGlossCache.set(lookup, guideWord);
                return guideWord ? { gloss: guideWord, source: 'glossary' } : null;
            }

            // No definition found
            this.glossaryGlossCache.set(lookup, null);
            return null;
        } catch (err) {
            // Glossary lookup failed
            return null;
        }
    }

    /**
     * Check if a line has an official translation (inline or external)
     */
    hasLineTranslation(surface, columnIdx, lineNumber) {
        const column = surface.columns[columnIdx];
        if (!column) return false;

        // Check inline translations (#tr.XX: in ATF)
        const line = column.lines.find(l => l.number === lineNumber);
        if (line?.translations && Object.keys(line.translations).length > 0) {
            return true;
        }

        // Check external translations (translations table)
        if (!this.translationLines) return false;

        const key = `${surface.name}_${column.number || 1}_${lineNumber}`;
        return !!this.translationLines[key];
    }

    /**
     * Attach interlinear glosses to all words
     * Only shows glosses for lines without official translations
     *
     * NOTE: For large tablets (100+ lines), consider optimizing by:
     * - Batching glossary API calls (collect all lookups, single request)
     * - Using IntersectionObserver for lazy glossing of off-screen words
     * - Debouncing gloss attachment after rapid mode switches
     */
    async attachWordGlosses() {
        if (!this.data?.surfaces[this.currentSurface]) return;

        const surface = this.data.surfaces[this.currentSurface];

        // Get column elements (if multi-column layout)
        const contentArea = this.container.querySelector('.atf-content');
        const columnEls = contentArea.querySelectorAll('.atf-column');
        const isSingleColumn = surface.columns.length === 1;

        for (let colIdx = 0; colIdx < surface.columns.length; colIdx++) {
            const column = surface.columns[colIdx];

            // Get the correct column element to scope queries
            const columnEl = isSingleColumn ? contentArea : columnEls[colIdx];
            if (!columnEl) continue;

            for (const line of column.lines) {
                if (line.type !== 'content') continue;

                // Skip lines with official translations
                if (this.hasLineTranslation(surface, colIdx, line.number)) {
                    continue;
                }

                // Query within the specific column to handle duplicate line numbers across columns
                const lineEl = columnEl.querySelector(`.atf-line[data-line="${line.number}"]`);
                if (!lineEl) continue;

                // Convert line number: "1." → 0, "2." → 1, "1'." → 0
                const lineNo = parseInt(line.number.replace(/[^0-9]/g, '')) - 1;

                let wordNo = 0;
                const wordEls = lineEl.querySelectorAll('.atf-word[data-lookup]');

                for (const wordEl of wordEls) {
                    const lookup = wordEl.dataset.lookup;
                    if (!lookup) {
                        wordNo++;
                        continue;
                    }

                    const glossData = await this.getWordGloss(lineNo, wordNo, lookup);

                    if (glossData) {
                        // Only add if not already glossed
                        if (!wordEl.querySelector('.atf-word__text')) {
                            const originalHtml = wordEl.innerHTML;
                            const glossClass = glossData.source === 'lemma'
                                ? 'atf-word__gloss atf-word__gloss--scholarly'
                                : 'atf-word__gloss atf-word__gloss--automatic';
                            wordEl.innerHTML = `
                                <span class="atf-word__text">${originalHtml}</span>
                                <span class="${glossClass}">${this.escapeHtml(glossData.gloss)}</span>
                            `;
                            wordEl.classList.add('atf-word--glossed');
                            wordEl.classList.add(glossData.source === 'lemma' ? 'atf-word--lemma' : 'atf-word--glossary');
                        }
                    }

                    wordNo++;
                }
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

        // Update toggle state
        const toggle = this.container.querySelector('.atf-mode-toggle');
        if (toggle) {
            toggle.checked = (mode === 'interactive');
        }

        // Update container class
        this.container.classList.remove('atf-viewer--mode-raw', 'atf-viewer--mode-interactive', 'atf-viewer--mode-parallel');
        this.container.classList.add(`atf-viewer--mode-${mode}`);

        // Show/hide legend based on mode
        const legendEl = this.container.querySelector('.atf-legend');
        if (legendEl) {
            legendEl.classList.toggle('is-hidden', mode !== 'interactive');
        }

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
            tab.setAttribute('aria-selected', i === index);
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
                    <button class="btn btn--icon btn--toggle viewer-toggle" aria-label="Toggle viewer size" aria-expanded="true" title="Expand/collapse tablet image">
                        <svg class="viewer-toggle__icon-expand" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                            <path d="M12.9998 6L11.5898 7.41L16.1698 12L11.5898 16.59L12.9998 18L18.9998 12L12.9998 6Z"/>
                            <path d="M6.41 6L5 7.41L9.58 12L5 16.59L6.41 18L12.41 12L6.41 6Z"/>
                        </svg>
                        <svg class="viewer-toggle__icon-collapse" width="24" height="24" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                            <path d="M11 18L12.41 16.59L7.83 12L12.41 7.41L11 6L5 12L11 18Z"/>
                            <path d="M17.5898 18L18.9998 16.59L14.4198 12L18.9998 7.41L17.5898 6L11.5898 12L17.5898 18Z"/>
                        </svg>
                    </button>
                    <nav class="tabs-nav tabs-nav-compact atf-tabs" role="tablist"></nav>
                </div>
                <div class="atf-viewer__body">
                    <div class="atf-content-column">
                        <div class="atf-view-settings">
                            <label class="toggle-switch">
                                <input type="checkbox" class="atf-mode-toggle" checked>
                                <span class="toggle-switch__slider"></span>
                                <span class="toggle-switch__label">Interactive ATF</span>
                            </label>
                        </div>
                        <div class="atf-legend">
                            <div class="atf-legend__items"></div>
                        </div>
                        <div class="atf-content"></div>
                    </div>
                </div>
            </div>
        `;

        // Event listeners
        const modeToggle = this.container.querySelector('.atf-mode-toggle');
        if (modeToggle) {
            modeToggle.addEventListener('change', (e) => {
                this.setMode(e.target.checked ? 'interactive' : 'raw');
            });
        }

        // Knowledge sidebar icon bar event listeners
        const knowledgeSidebar = document.getElementById('knowledge-sidebar');
        if (knowledgeSidebar) {
            knowledgeSidebar.querySelectorAll('.tabs-nav--vertical-icons .tab-button').forEach(btn => {
                btn.addEventListener('click', () => {
                    // Block clicks during transition
                    if (this.sidebarTransitioning) return;

                    const tab = btn.dataset.tab;
                    if (this.activeKnowledgeTab === tab && this.knowledgeSidebarOpen) {
                        // Clicking active tab closes sidebar
                        this.hideKnowledgeSidebar();
                    } else {
                        // Open sidebar to this tab
                        this.showKnowledgeSidebar(tab);
                    }
                });
            });
        }

        // Listen for tablet viewer state changes (mutual exclusivity)
        document.addEventListener('tablet-viewer-state', (e) => {
            if (e.detail.action === 'viewer-expanding' && this.knowledgeSidebarOpen) {
                this.hideKnowledgeSidebar();
            }
        });

        // Dictionary browse event listeners
        const searchInput = knowledgeSidebar?.querySelector('.knowledge-sidebar-search__input');
        const searchClear = knowledgeSidebar?.querySelector('.knowledge-sidebar-search__clear');
        const languageFilter = knowledgeSidebar?.querySelector('.knowledge-sidebar-filter[data-filter="language"]');
        const posFilter = knowledgeSidebar?.querySelector('.knowledge-sidebar-filter[data-filter="pos"]');
        const loadMoreBtn = knowledgeSidebar?.querySelector('.knowledge-sidebar-list__load-more');
        const backBtn = knowledgeSidebar?.querySelector('.knowledge-sidebar-word-header__back');

        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.searchDictionary(e.target.value);
                searchClear?.classList.toggle('is-hidden', !e.target.value);
            });
        }

        if (searchClear) {
            searchClear.addEventListener('click', () => {
                if (searchInput) searchInput.value = '';
                searchClear.classList.add('is-hidden');
                this.searchDictionary('');
            });
        }

        if (languageFilter) {
            languageFilter.addEventListener('change', (e) => {
                this.filterDictionary('language', e.target.value);
            });
        }

        if (posFilter) {
            posFilter.addEventListener('change', (e) => {
                this.filterDictionary('pos', e.target.value);
            });
        }

        if (loadMoreBtn) {
            loadMoreBtn.addEventListener('click', () => {
                this.loadDictionaryPage(this.dictionaryResultsOffset + this.dictionaryResultsLimit);
            });
        }

        if (backBtn) {
            backBtn.addEventListener('click', () => {
                this.backToBrowse();
            });
        }

        // Legend toggle state
        if (!this.options.showLegend) {
            this.container.querySelector('.atf-legend').open = false;
        }

        // Viewer toggle button
        const viewerToggle = this.container.querySelector('.viewer-toggle');
        if (viewerToggle) {
            viewerToggle.addEventListener('click', () => {
                // Dispatch event for tablet-detail.js to handle centrally
                document.dispatchEvent(new CustomEvent('viewer-toggle-requested', {
                    detail: { source: 'atf-viewer' }
                }));
            });
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
                <button class="tab-button atf-tab"
                        role="tab"
                        aria-selected="${i === 0}"
                        data-surface="${i}">
                    ${surface.label}
                    <span class="count-badge atf-tab__count">${lineCount}</span>
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
        const legendEl = this.container.querySelector('.atf-legend');

        if (!this.legend.length) {
            legendEl.classList.add('is-hidden');
            return;
        }

        legendContainer.innerHTML = this.legend.map(item => `
            <span class="atf-legend__item">
                <span class="atf-legend__swatch atf-legend__swatch--${item.class}">${item.symbol}</span>
                ${item.label}
            </span>
        `).join('');

        // Show legend in interactive mode (default)
        legendEl.classList.toggle('is-hidden', this.mode !== 'interactive');
    }

    /**
     * Update legend to include gloss type indicators
     * Called after glosses are attached to check which types are present
     */
    updateLegendWithGlossTypes() {
        const hasScholarlyGlosses = this.container.querySelectorAll('.atf-word--lemma').length > 0;
        const hasAutomaticGlosses = this.container.querySelectorAll('.atf-word--glossary').length > 0;

        if (!hasScholarlyGlosses && !hasAutomaticGlosses) return;

        const legendContainer = this.container.querySelector('.atf-legend__items');
        const legendEl = this.container.querySelector('.atf-legend');

        // Show legend if hidden
        legendEl.classList.remove('is-hidden');

        // Add gloss type legend items if not already present
        const glossLegendItems = [];

        if (hasScholarlyGlosses && !legendContainer.querySelector('.atf-legend__swatch--scholarly-gloss')) {
            glossLegendItems.push(`
                <span class="atf-legend__item">
                    <span class="atf-legend__swatch atf-legend__swatch--scholarly-gloss">word</span>
                    Scholarly lemma (ORACC)
                </span>
            `);
        }

        if (hasAutomaticGlosses && !legendContainer.querySelector('.atf-legend__swatch--automatic-gloss')) {
            glossLegendItems.push(`
                <span class="atf-legend__item">
                    <span class="atf-legend__swatch atf-legend__swatch--automatic-gloss">word</span>
                    Detected word
                </span>
            `);
        }

        if (glossLegendItems.length > 0) {
            legendContainer.innerHTML += glossLegendItems.join('');
        }
    }

    /**
     * Render content based on mode
     */
    async renderContent() {
        const contentArea = this.container.querySelector('.atf-content');

        if (this.mode === 'raw') {
            contentArea.textContent = this.rawATF;
            return;
        }

        if (!this.data?.surfaces[this.currentSurface]) {
            contentArea.innerHTML = '<p class="knowledge-sidebar-dictionary__empty">No content available</p>';
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

        // Always show translation column when available
        if (this.hasTranslation) {
            this.renderTranslationColumn(surface);
        }

        // Add interlinear glosses
        await this.attachWordGlosses();

        // Update legend with gloss types
        this.updateLegendWithGlossTypes();

        // Show data source footer when both glosses and translation panel are present
        this.updateDataSourceFooter();
    }

    /**
     * Show/hide the data source footer based on available data
     * Footer explains the difference between inline glosses and translation panel
     * Appends footer inside .atf-content so it scrolls with the content
     */
    updateDataSourceFooter() {
        const contentArea = this.container.querySelector('.atf-content');
        if (!contentArea) return;

        // Remove existing footer if present
        contentArea.querySelector('.atf-viewer__footer')?.remove();

        // Check for inline ATF translations (#tr.XX: lines in parsed data)
        let hasInlineTranslations = false;
        if (this.data?.surfaces[this.currentSurface]) {
            const surface = this.data.surfaces[this.currentSurface];
            for (const col of surface.columns) {
                for (const line of col.lines) {
                    if (line.translations && Object.keys(line.translations).length > 0) {
                        hasInlineTranslations = true;
                        break;
                    }
                }
                if (hasInlineTranslations) break;
            }
        }

        // Check for lemma-based glosses
        const hasLemmaGlosses = this.lemmasLoaded && Object.keys(this.lemmasData).length > 0;

        // Show footer when we have both:
        // 1. Any inline content (ATF translations OR lemma glosses)
        // 2. Translation panel data
        const hasInlineContent = hasInlineTranslations || hasLemmaGlosses;
        const showFooter = hasInlineContent && this.hasTranslation;

        if (showFooter) {
            const footer = document.createElement('footer');
            footer.className = 'atf-viewer__footer';
            footer.innerHTML = `
                <div class="atf-viewer__footer-content">
                    <svg class="atf-viewer__footer-icon" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
                    </svg>
                    <div class="atf-viewer__footer-text">
                        <strong>About these translations:</strong> The gray text below each line shows detected words with dictionary definitions. The translation panel shows scholarly translations from published sources. These may differ because detected words are literal meanings, while translations capture the intended sense in context.
                    </div>
                </div>
            `;
            contentArea.appendChild(footer);
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
                const surfaceForm = `data-surface-form="${this.escapeHtml(word.text)}"`;
                return `<span class="atf-word atf-logo" ${lookup} ${surfaceForm}>${this.escapeHtml(word.text)}</span>`;
            }

            if (word.type === 'determinative') {
                const detDisplay = word.detDisplay || `(${word.determinative})`;
                const detClass = `atf-det atf-det--${word.detType}`;
                const lookup = word.lookup ? `data-lookup="${this.escapeHtml(word.lookup)}"` : '';
                const surfaceForm = `data-surface-form="${this.escapeHtml(word.text)}"`;

                if (word.position === 'prefix') {
                    return `<span class="${detClass}">${detDisplay}</span><span class="atf-word" ${lookup} ${surfaceForm}>${this.escapeHtml(word.text)}</span>`;
                } else {
                    return `<span class="atf-word" ${lookup} ${surfaceForm}>${this.escapeHtml(word.text)}</span><span class="${detClass} atf-det--suffix">${detDisplay}</span>`;
                }
            }

            if (word.type === 'word') {
                const classes = ['atf-word'];
                if (word.damaged) classes.push('atf-word--damaged');
                if (word.uncertain) classes.push('atf-word--uncertain');
                if (word.corrected) classes.push('atf-word--corrected');

                const lookup = word.lookup ? `data-lookup="${this.escapeHtml(word.lookup)}"` : '';
                const surfaceForm = `data-surface-form="${this.escapeHtml(word.text)}"`;

                // Extract damage markers from end of text
                const markerMatch = word.text.match(/([#?!]+)$/);
                const markers = markerMatch ? markerMatch[1] : '';
                const displayText = word.text.replace(/[#?!]+$/, '');

                // Build HTML with markers as superscript
                let html = `<span class="${classes.join(' ')}" ${lookup} ${surfaceForm}>${this.escapeHtml(displayText)}`;
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
     * Render translation column (always shown when available)
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
                const surfaceForm = el.dataset.surfaceForm;
                if (lookup) {
                    this.showDictionary(lookup, surfaceForm);
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
            const response = await fetch('/api/dictionary/check', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ words: lookups })
            });

            const data = await this.safeJsonParse(response);

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
     * @param {string} surfaceForm - Optional surface form (e.g., "TIM" before normalization)
     */
    showKnowledgeSidebar(tab = null, word = null, surfaceForm = null) {
        // Set transition gate
        this.sidebarTransitioning = true;
        clearTimeout(this.transitionTimeout);

        const sidebar = document.getElementById('knowledge-sidebar');
        if (!sidebar) return;
        const tabToShow = tab || this.activeKnowledgeTab || 'dictionary';

        // Set data-state for CSS transitions
        sidebar.dataset.state = 'open';
        this.knowledgeSidebarOpen = true;

        // Switch to the tab
        this.setActiveKnowledgeTab(tabToShow);

        // Update panel title
        const titleEl = sidebar.querySelector('.knowledge-content-panel__title');
        if (titleEl) {
            titleEl.textContent = this.getTabTitle(tabToShow);
        }

        // Store surface form for use in dictionary display
        this.lastSurfaceForm = surfaceForm;

        // Notify tablet viewer to collapse (mutual exclusivity)
        this.container.dispatchEvent(new CustomEvent('knowledge-sidebar-state', {
            bubbles: true,
            detail: { action: 'knowledge-open' }
        }));

        // If word provided and dictionary tab, load definition
        if (word && (tabToShow === 'dictionary')) {
            this.loadDictionaryContent(word);
        } else if (!word && tabToShow === 'dictionary') {
            // Initialize browse mode if opening dictionary tab without a word
            if (this.dictionaryResults.length === 0) {
                this.setDictionaryMode('browse');
                this.initDictionaryBrowser();
            } else {
                // Already have results, just show browse mode
                this.setDictionaryMode('browse');
            }
        }

        // Release gate after transition completes
        this.transitionTimeout = setTimeout(() => {
            this.sidebarTransitioning = false;
        }, 300);
    }

    /**
     * Get human-readable tab title
     * @param {string} tabName - Tab identifier
     * @returns {string} Display title
     */
    getTabTitle(tabName) {
        const titles = {
            dictionary: 'Dictionary',
            research: 'Research',
            discussion: 'Discussion',
            context: 'Context'
        };
        return titles[tabName] || tabName;
    }

    /**
     * Hide knowledge sidebar
     */
    hideKnowledgeSidebar() {
        // Set transition gate
        this.sidebarTransitioning = true;
        clearTimeout(this.transitionTimeout);

        const sidebar = document.getElementById('knowledge-sidebar');
        if (!sidebar) return;

        // Set data-state for CSS transitions
        sidebar.dataset.state = 'closed';
        this.knowledgeSidebarOpen = false;

        // Clear all icon button selections
        sidebar.querySelectorAll('.tabs-nav--vertical-icons .tab-button').forEach(btn => {
            btn.setAttribute('aria-selected', 'false');
        });

        // Release gate after transition completes
        this.transitionTimeout = setTimeout(() => {
            this.sidebarTransitioning = false;
        }, 300);
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
        const sidebar = document.getElementById('knowledge-sidebar');
        if (!sidebar) return;

        // Update icon bar buttons
        sidebar.querySelectorAll('.tabs-nav--vertical-icons .tab-button').forEach(btn => {
            const isActive = btn.dataset.tab === tabName;
            btn.setAttribute('aria-selected', isActive);
        });

        // Update content panels
        sidebar.querySelectorAll('.knowledge-tab-content').forEach(content => {
            const isActive = content.dataset.content === tabName;
            content.classList.toggle('knowledge-tab-content--active', isActive);
        });

        // Update panel title
        const titleEl = sidebar.querySelector('.knowledge-content-panel__title');
        if (titleEl) {
            titleEl.textContent = this.getTabTitle(tabName);
        }

        this.activeKnowledgeTab = tabName;
    }

    /**
     * Load dictionary content
     * @param {string} word - Word to look up
     */
    async loadDictionaryContent(word) {
        const sidebar = document.getElementById('knowledge-sidebar');
        if (!sidebar) return;
        const dictContent = sidebar.querySelector('.knowledge-sidebar-word-content');

        this.lastDictionaryWord = word;

        // Switch to word mode
        this.setDictionaryMode('word');

        // Check cache first
        if (this.definitionCache.has(word)) {
            this.renderDictionaryContent(this.definitionCache.get(word), word);
            return;
        }

        // Show loading
        dictContent.innerHTML = '<div class="knowledge-sidebar-dictionary__loading">Loading...</div>';

        try {
            const response = await fetch(`/api/dictionary/words?search=q=${encodeURIComponent(word)}&full=1`);
            const data = await this.safeJsonParse(response);

            // Cache result
            this.definitionCache.set(word, data);

            this.renderDictionaryContent(data, word);

        } catch (err) {
            dictContent.innerHTML = '<div class="knowledge-sidebar-dictionary__empty">Failed to load definition</div>';
        }
    }

    /**
     * Set dictionary mode (browse or word)
     * @param {string} mode - 'browse' or 'word'
     */
    setDictionaryMode(mode) {
        this.dictionaryMode = mode;
        const sidebar = document.getElementById('knowledge-sidebar');
        if (!sidebar) return;

        const browseUI = sidebar.querySelector('.knowledge-sidebar-dictionary');
        const wordUI = sidebar.querySelector('.knowledge-sidebar-word-detail');

        if (browseUI) browseUI.classList.toggle('is-hidden', mode !== 'browse');
        if (wordUI) wordUI.classList.toggle('is-hidden', mode === 'browse');
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
        const sidebar = document.getElementById('knowledge-sidebar');
        if (!sidebar) return;

        const chipsContainer = sidebar.querySelector('.knowledge-sidebar-filter-chips');
        const chips = [];

        if (this.dictionaryFilters.language) {
            const select = sidebar.querySelector('.knowledge-sidebar-filter[data-filter="language"]');
            const option = select?.querySelector(`option[value="${this.dictionaryFilters.language}"]`);
            chips.push({
                type: 'language',
                label: option.textContent,
                value: this.dictionaryFilters.language
            });
        }

        if (this.dictionaryFilters.pos) {
            const select = sidebar.querySelector('.knowledge-sidebar-filter[data-filter="pos"]');
            const option = select?.querySelector(`option[value="${this.dictionaryFilters.pos}"]`);
            chips.push({
                type: 'pos',
                label: option.textContent,
                value: this.dictionaryFilters.pos
            });
        }

        if (chips.length > 0 && chipsContainer) {
            chipsContainer.innerHTML = chips.map(chip => `
                <span class="knowledge-sidebar-filter-chip" data-type="${chip.type}">
                    ${chip.label}
                    <button class="knowledge-sidebar-filter-chip__remove" data-type="${chip.type}" aria-label="Remove filter">&times;</button>
                </span>
            `).join('');
            chipsContainer.classList.remove('is-hidden');

            // Add remove handlers
            chipsContainer.querySelectorAll('.knowledge-sidebar-filter-chip__remove').forEach(btn => {
                btn.addEventListener('click', () => {
                    const filterType = btn.dataset.type;
                    this.dictionaryFilters[filterType] = null;
                    const select = sidebar.querySelector(`.knowledge-sidebar-filter[data-filter="${filterType}"]`);
                    if (select) select.value = '';
                    this.filterDictionary(filterType, '');
                });
            });
        } else if (chipsContainer) {
            chipsContainer.classList.add('is-hidden');
        }
    }

    /**
     * Load dictionary page
     * @param {number} offset - Page offset
     */
    async loadDictionaryPage(offset) {
        const sidebar = document.getElementById('knowledge-sidebar');
        if (!sidebar) return;

        const resultsList = sidebar.querySelector('.knowledge-sidebar-list__items');
        const countEl = sidebar.querySelector('.knowledge-sidebar-list__count');
        const loadMoreBtn = sidebar.querySelector('.knowledge-sidebar-list__load-more');

        // Show loading for first page
        if (offset === 0) {
            resultsList.innerHTML = '<div class="state-loading state-loading--compact">Loading...</div>';
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

            const response = await fetch(`/api/dictionary/words?${params}`);
            const data = await this.safeJsonParse(response);

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

            // Show footer and update count
            const footer = sidebar.querySelector('.knowledge-sidebar-list__footer');
            if (footer) footer.classList.remove('is-hidden');
            const showing = Math.min(this.dictionaryResults.length, this.dictionaryTotalCount);
            countEl.textContent = `Showing ${showing.toLocaleString()} of ${this.dictionaryTotalCount.toLocaleString()}`;

            // Show/hide load more button
            loadMoreBtn.classList.toggle('is-hidden', !data.hasMore);

        } catch (err) {
            console.error('Failed to load dictionary page:', err);
            resultsList.innerHTML = '<div class="state-error state-error--compact">Failed to load results</div>';
            // Hide footer on error
            const footer = sidebar.querySelector('.knowledge-sidebar-list__footer');
            if (footer) footer.classList.add('is-hidden');
        }
    }

    /**
     * Render dictionary results list
     */
    renderDictionaryResults() {
        const sidebar = document.getElementById('knowledge-sidebar');
        if (!sidebar) return;

        const resultsList = sidebar.querySelector('.knowledge-sidebar-list__items');

        if (this.dictionaryResults.length === 0) {
            resultsList.innerHTML = '<div class="state-empty state-empty--compact">No entries found</div>';
            return;
        }

        resultsList.innerHTML = this.dictionaryResults.map(entry =>
            WordListItem.render(entry, { compact: true })
        ).join('');

        // Add click handlers
        resultsList.querySelectorAll('.list-item').forEach(item => {
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
    async showDictionary(word, surfaceForm) {
        this.showKnowledgeSidebar('dictionary', word, surfaceForm);
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
        const sidebar = document.getElementById('knowledge-sidebar');
        if (!sidebar) return;
        const citationEl = sidebar.querySelector('.knowledge-sidebar-word-header__citation');
        const body = sidebar.querySelector('.knowledge-sidebar-word-content');

        if (!data.entries || data.entries.length === 0) {
            citationEl.textContent = word;
            body.innerHTML = `
                <div class="knowledge-sidebar-dictionary__empty">
                    No definition found
                    <div class="knowledge-sidebar-dictionary__empty-hint">This word may not be in the ORACC glossaries</div>
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
                <div class="knowledge-sidebar-word-definition">
                    <div class="knowledge-sidebar-word-definition__label">Meaning</div>
                    <div class="knowledge-sidebar-word-definition__text">${this.escapeHtml(entry.guide_word)}</div>
                </div>
            `;
        }

        // Sign Form Section (if surface form differs from citation form)
        if (this.lastSurfaceForm) {
            html += this.renderSignFormSection(this.lastSurfaceForm, entry);
        }

        // Metadata Fields
        html += '<dl class="knowledge-sidebar-word-fields">';

        if (entry.headword) {
            const fieldLabel = data.field_explanations?.headword ? 'Headword' : 'Dictionary Form';
            html += `
                <dt class="knowledge-sidebar-word-field-label">${fieldLabel}</dt>
                <dd class="knowledge-sidebar-word-field-value">${this.escapeHtml(entry.headword)}</dd>
            `;
        }

        if (entry.pos) {
            html += `
                <dt class="knowledge-sidebar-word-field-label">Part of Speech</dt>
                <dd class="knowledge-sidebar-word-field-value">${posLabel}</dd>
            `;
        }

        if (entry.language) {
            const langLabels = { akk: 'Akkadian', sux: 'Sumerian', qpc: 'Proto-Cuneiform' };
            html += `
                <dt class="knowledge-sidebar-word-field-label">Language</dt>
                <dd class="knowledge-sidebar-word-field-value">${langLabels[entry.language] || entry.language}</dd>
            `;
        }

        if (entry.icount) {
            html += `
                <dt class="knowledge-sidebar-word-field-label">Occurrences</dt>
                <dd class="knowledge-sidebar-word-field-value">${entry.icount.toLocaleString()} in corpus</dd>
            `;
        }

        html += '</dl>';

        // Variant forms
        const forms = data.forms?.[entry.entry_id];
        if (forms && forms.length > 0) {
            html += `
                <div class="knowledge-sidebar-variants">
                    <div class="knowledge-sidebar-variants__title">Variant Spellings (${forms.length})</div>
                    <div class="knowledge-sidebar-variants__list">
                        ${forms.slice(0, 10).map(f => `
                            <span class="knowledge-sidebar-variant">
                                ${this.escapeHtml(f.form)}
                                <span class="knowledge-sidebar-variant__count">${f.count || ''}</span>
                            </span>
                        `).join('')}
                        ${forms.length > 10 ? `<span class="knowledge-sidebar-variant">+${forms.length - 10} more</span>` : ''}
                    </div>
                </div>
            `;
        }

        // All entries (if more than one)
        if (data.entries.length > 1) {
            html += `
                <details class="knowledge-sidebar-entries">
                    <summary>All ${data.entries.length} entries for "${word}"</summary>
                    <div class="knowledge-sidebar-entries__list">
                        ${data.entries.map((e, i) => `
                            <div class="knowledge-sidebar-entry ${i === 0 ? 'knowledge-sidebar-entry--active' : ''}">
                                <div class="knowledge-sidebar-entry__head">
                                    <span class="knowledge-sidebar-entry__word">${this.escapeHtml(e.headword || word)}</span>
                                    ${e.pos ? `<span class="knowledge-sidebar-entry__pos">${e.pos}</span>` : ''}
                                </div>
                                <div class="knowledge-sidebar-entry__meaning">${this.escapeHtml(e.guide_word || 'No definition')}</div>
                            </div>
                        `).join('')}
                    </div>
                </details>
            `;
        }

        body.innerHTML = html;
    }

    /**
     * Render sign form section showing connection between surface form and citation form
     * @param {string} surfaceForm - Original sign form (e.g., "TIM")
     * @param {object} entry - Dictionary entry
     * @returns {string} HTML for sign form section
     */
    renderSignFormSection(surfaceForm, entry) {
        const citationForm = entry.citation_form || entry.headword;

        // Strip damage markers from surface form for comparison and display
        const cleanSurfaceForm = surfaceForm.replace(/[#?!]+$/, '');
        const cleanCitation = citationForm.toLowerCase();

        // Don't show section if forms are identical (case-insensitive)
        if (cleanSurfaceForm.toLowerCase() === cleanCitation) {
            return '';
        }

        const signType = this.detectSignType(cleanSurfaceForm, entry);
        const explanation = this.generateLinguisticExplanation(cleanSurfaceForm, entry, signType);

        const badgeHtml = signType === 'logogram'
            ? '<span class="knowledge-sidebar-sign-badge knowledge-sidebar-sign-badge--logo">Logogram</span>'
            : signType === 'phonogram'
            ? '<span class="knowledge-sidebar-sign-badge knowledge-sidebar-sign-badge--phono">Phonogram</span>'
            : '';

        return `
            <div class="knowledge-sidebar-sign-form">
                <div class="knowledge-sidebar-sign-form__header">
                    <span class="knowledge-sidebar-sign-form__label">Cuneiform Sign</span>
                    ${badgeHtml}
                </div>
                <div class="knowledge-sidebar-sign-form__text">${this.escapeHtml(cleanSurfaceForm)}</div>
                <div class="knowledge-sidebar-sign-form__explanation">${explanation}</div>
            </div>
        `;
    }

    /**
     * Detect sign type based on surface form and entry data
     * @param {string} surfaceForm - Original sign form
     * @param {object} entry - Dictionary entry
     * @returns {string} 'logogram', 'phonogram', or 'mixed'
     */
    detectSignType(surfaceForm, entry) {
        // Uppercase = logogram (TIM, GAL, LUGAL)
        const isUppercase = surfaceForm === surfaceForm.toUpperCase();

        // Contains hyphens = syllabic/phonetic (min-na-bi)
        const hasSyllabicMarkers = surfaceForm.includes('-');

        if (isUppercase && !hasSyllabicMarkers) {
            return 'logogram';
        } else if (hasSyllabicMarkers) {
            return 'phonogram';
        } else {
            return 'mixed';
        }
    }

    /**
     * Generate linguistic explanation of sign-word relationship
     * @param {string} surfaceForm - Original sign form
     * @param {object} entry - Dictionary entry
     * @param {string} signType - Type of sign ('logogram', 'phonogram', 'mixed')
     * @returns {string} HTML explanation
     */
    generateLinguisticExplanation(surfaceForm, entry, signType) {
        const citationForm = entry.citation_form || entry.headword;
        const guideWord = entry.guide_word;
        const language = entry.language;

        const langLabels = {
            'akk': 'Akkadian',
            'sux': 'Sumerian',
            'qpc': 'Proto-Cuneiform',
            'akk-x-stdbab': 'Standard Babylonian',
            'akk-x-oldass': 'Old Assyrian',
            'akk-x-neoass': 'Neo-Assyrian'
        };
        const langName = langLabels[language] || language;

        if (signType === 'logogram') {
            return `The cuneiform sign <strong>${this.escapeHtml(surfaceForm)}</strong> is a logographic writing of the ${langName} word <strong>${this.escapeHtml(citationForm)}</strong>, meaning "${this.escapeHtml(guideWord)}".`;
        } else if (signType === 'phonogram') {
            return `The syllabic spelling <strong>${this.escapeHtml(surfaceForm)}</strong> represents the ${langName} word <strong>${this.escapeHtml(citationForm)}</strong>, meaning "${this.escapeHtml(guideWord)}".`;
        } else {
            return `This form <strong>${this.escapeHtml(surfaceForm)}</strong> represents the ${langName} word <strong>${this.escapeHtml(citationForm)}</strong>, meaning "${this.escapeHtml(guideWord)}".`;
        }
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
        list.innerHTML = '<div class="knowledge-sidebar-dictionary__loading">Loading composite...</div>';

        try {
            // Fetch composite data
            const response = await fetch(`/api/composites/${qNumber}`);
            if (!response.ok) throw new Error('Failed to load composite');

            const data = await this.safeJsonParse(response);

            // Update panel header
            panel.querySelector('.atf-composite-panel__name').textContent =
                data.composite.designation || qNumber;

            // Render tablet list
            this.renderCompositeList(data.tablets);

        } catch (err) {
            console.error('ATFViewer: Failed to load composite', err);
            list.innerHTML = '<div class="knowledge-sidebar-dictionary__empty">Failed to load composite</div>';
        }
    }

    /**
     * Render list of tablets in composite
     */
    renderCompositeList(tablets) {
        const list = this.container.querySelector('.atf-composite-list');

        list.innerHTML = tablets.map((tablet, index) => {
            const isCurrent = tablet.p_number === this.pNumber;
            const thumbnailUrl = `/api/artifacts/${tablet.p_number}/thumbnail?size=64`;

            return `
                <div class="atf-composite-item ${isCurrent ? 'atf-composite-item--current' : ''}"
                     data-p-number="${tablet.p_number}">
                    <div class="atf-composite-thumbnail" data-p-number="${tablet.p_number}">
                        <img src="${thumbnailUrl}"
                             alt="${this.escapeHtml(tablet.designation)}"
                             loading="lazy"
                             onerror="this.classList.add('is-hidden'); this.parentElement.classList.add('atf-composite-thumbnail--empty'); this.parentElement.innerHTML='𒀭';">
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
                    window.location.href = `/tablets/${pNumber}`;
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

        // Determine error type and provide appropriate hint
        let hint = 'The transliteration may not be available for this tablet.';
        if (message.includes('Server error') || message.includes('PHP error')) {
            hint = 'There was a server configuration error. This may be due to a PHP error, missing file, or database issue. Check the browser console for details.';
        } else if (message.includes('JSON')) {
            hint = 'The server returned an invalid response. This may be a temporary issue - try refreshing the page.';
        }

        contentArea.innerHTML = `
            <div class="knowledge-sidebar-dictionary__empty">
                ${this.escapeHtml(message)}
                <div class="knowledge-sidebar-dictionary__empty-hint">${hint}</div>
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
