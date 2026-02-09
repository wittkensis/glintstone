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

        // Lemma data for interlinear glossing
        this.lemmasData = {};  // Indexed by line_no and word_no
        this.lemmasLoaded = false;
        this.glossaryGlossCache = new Map();  // lookup → guide_word cache

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

        // Hide the separate translation section if we have ATF viewer with translation
        if (this.hasTranslation) {
            this.container.classList.add('atf-viewer--has-translation');
            const separateTranslationSection = document.querySelector('.translation-section');
            if (separateTranslationSection) {
                separateTranslationSection.style.display = 'none';
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
            const response = await fetch(`/api/lemmas.php?p=${this.pNumber}`);
            if (response.ok) {
                const result = await response.json();
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
     */
    async getWordGloss(lineNo, wordNo, lookup) {
        // Priority 1: Check lemmas table
        const lineNoStr = String(lineNo);
        const wordNoStr = String(wordNo);

        if (this.lemmasData[lineNoStr]?.[wordNoStr]?.gw) {
            return this.lemmasData[lineNoStr][wordNoStr].gw;
        }

        // Priority 2: Fallback to glossary
        if (!lookup || lookup.length < 2) return null;

        // Check cache
        if (this.glossaryGlossCache.has(lookup)) {
            return this.glossaryGlossCache.get(lookup);
        }

        // Fetch from glossary API
        try {
            const response = await fetch(`/api/glossary.php?q=${encodeURIComponent(lookup)}&limit=1`);
            const data = await response.json();

            if (data.entries && data.entries.length > 0) {
                const guideWord = data.entries[0].guide_word || null;
                this.glossaryGlossCache.set(lookup, guideWord);
                return guideWord;
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

                    const gloss = await this.getWordGloss(lineNo, wordNo, lookup);

                    if (gloss) {
                        // Only add if not already glossed
                        if (!wordEl.querySelector('.atf-word__text')) {
                            const originalHtml = wordEl.innerHTML;
                            wordEl.innerHTML = `
                                <span class="atf-word__text">${originalHtml}</span>
                                <span class="atf-word__gloss">${this.escapeHtml(gloss)}</span>
                            `;
                            wordEl.classList.add('atf-word--glossed');
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
                    <button class="btn btn--icon btn--toggle viewer-toggle" aria-label="Toggle viewer size" aria-expanded="false" title="Expand/collapse tablet image">
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
                    <div class="atf-view-settings">
                        <div class="btn-group btn-group-stateful atf-modes">
                            <button class="btn btn-group-item atf-mode atf-mode--active" data-mode="interactive">Interactive</button>
                            <button class="btn btn-group-item atf-mode" data-mode="raw">Raw</button>
                        </div>
                    </div>
                    <div class="atf-content"></div>
                </div>
                <div class="atf-legend">
                    <div class="atf-legend__items"></div>
                </div>
            </div>
            <aside class="atf-knowledge-sidebar" data-state="closed">
                <!-- Vertical Icon Bar -->
                <nav class="tabs-nav tabs-nav--vertical-icons" role="tablist" aria-label="Knowledge panels">
                    <button class="tab-button" data-tab="dictionary" role="tab" aria-selected="false" title="Dictionary">
                        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                            <path d="M17.5 14.33C15.8 14.33 14.26 14.62 13 15.16V16.82C14.13 16.18 15.7 15.83 17.5 15.83C18.38 15.83 19.23 15.92 20 16.09V14.57C19.21 14.41 18.36 14.33 17.5 14.33Z"/>
                            <path d="M13 12.49V14.15C14.13 13.51 15.7 13.16 17.5 13.16C18.38 13.16 19.23 13.25 20 13.42V11.9C19.21 11.75 18.36 11.66 17.5 11.66C15.8 11.66 14.26 11.96 13 12.49Z"/>
                            <path d="M17.5 10.5C18.38 10.5 19.23 10.59 20 10.76V9.24C19.21 9.09 18.36 9 17.5 9C15.8 9 14.26 9.29 13 9.83V11.49C14.13 10.85 15.7 10.5 17.5 10.5Z"/>
                            <path d="M21 5C19.89 4.65 18.67 4.5 17.5 4.5C15.55 4.5 13.45 4.9 12 6C10.55 4.9 8.45 4.5 6.5 4.5C4.55 4.5 2.45 4.9 1 6V21.5C2.45 20.4 4.55 20 6.5 20C8.45 20 10.55 20.4 12 21.5C13.45 20.4 15.55 20 17.5 20C18.67 20 19.89 20.15 21 20.5C21.75 20.75 22.4 21.05 23 21.5V6C22.4 5.55 21.75 5.25 21 5ZM21 18.5C19.9 18.15 18.7 18 17.5 18C15.8 18 13.35 18.65 12 19.5V8C13.35 7.15 15.8 6.5 17.5 6.5C18.7 6.5 19.9 6.65 21 7V18.5Z"/>
                        </svg>
                    </button>
                    <button class="tab-button" data-tab="research" role="tab" aria-selected="false" title="Research">
                        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                            <path d="M5 13.18V17.18L12 21L19 17.18V13.18L12 17L5 13.18ZM12 3L1 9L12 15L21 10.09V17H23V9L12 3Z"/>
                        </svg>
                    </button>
                    <button class="tab-button" data-tab="discussion" role="tab" aria-selected="false" title="Discussion">
                        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                            <path d="M22 2H2.01L2 22L6 18H22V2ZM6 9H18V11H6V9ZM14 14H6V12H14V14ZM18 8H6V6H18V8Z"/>
                        </svg>
                    </button>
                    <button class="tab-button" data-tab="context" role="tab" aria-selected="false" title="Context">
                        <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                            <path d="M11.99 2C6.47 2 2 6.48 2 12C2 17.52 6.47 22 11.99 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 11.99 2ZM18.92 8H15.97C15.65 6.75 15.19 5.55 14.59 4.44C16.43 5.07 17.96 6.35 18.92 8ZM12 4.04C12.83 5.24 13.48 6.57 13.91 8H10.09C10.52 6.57 11.17 5.24 12 4.04ZM4.26 14C4.1 13.36 4 12.69 4 12C4 11.31 4.1 10.64 4.26 10H7.64C7.56 10.66 7.5 11.32 7.5 12C7.5 12.68 7.56 13.34 7.64 14H4.26ZM5.08 16H8.03C8.35 17.25 8.81 18.45 9.41 19.56C7.57 18.93 6.04 17.66 5.08 16ZM8.03 8H5.08C6.04 6.34 7.57 5.07 9.41 4.44C8.81 5.55 8.35 6.75 8.03 8ZM12 19.96C11.17 18.76 10.52 17.43 10.09 16H13.91C13.48 17.43 12.83 18.76 12 19.96ZM14.34 14H9.66C9.57 13.34 9.5 12.68 9.5 12C9.5 11.32 9.57 10.65 9.66 10H14.34C14.43 10.65 14.5 11.32 14.5 12C14.5 12.68 14.43 13.34 14.34 14ZM14.59 19.56C15.19 18.45 15.65 17.25 15.97 16H18.92C17.96 17.65 16.43 18.93 14.59 19.56ZM16.36 14C16.44 13.34 16.5 12.68 16.5 12C16.5 11.32 16.44 10.66 16.36 10H19.74C19.9 10.64 20 11.31 20 12C20 12.69 19.9 13.36 19.74 14H16.36Z"/>
                        </svg>
                    </button>
                </nav>
                <!-- Sliding Content Panel -->
                <div class="knowledge-content-panel">
                    <div class="knowledge-content-panel__header">
                        <span class="knowledge-content-panel__title">Dictionary</span>
                    </div>
                    <div class="knowledge-content-panel__body">
                    <!-- Dictionary Tab Content -->
                    <div class="knowledge-tab-content knowledge-tab-content--active" data-content="dictionary">
                        <!-- Browse Mode UI -->
                        <div class="knowledge-sidebar-dictionary">
                            <!-- Search Bar -->
                            <div class="knowledge-sidebar-search">
                                <input type="text" class="knowledge-sidebar-search__input" placeholder="Search dictionary..." aria-label="Search dictionary">
                                <button class="knowledge-sidebar-search__clear" aria-label="Clear search" style="display: none;">&times;</button>
                            </div>

                            <!-- Filter Bar -->
                            <div class="knowledge-sidebar-filters">
                                <select class="knowledge-sidebar-filter" data-filter="language" aria-label="Filter by language">
                                    <option value="">All Languages</option>
                                    <option value="akk">Akkadian (11,357)</option>
                                    <option value="sux">Sumerian (5,271)</option>
                                    <option value="qpn">Personal Names (4,039)</option>
                                    <option value="sux-x-emesal">Emesal (146)</option>
                                    <option value="xhu">Hurrian (137)</option>
                                    <option value="uga">Ugaritic (100)</option>
                                </select>
                                <select class="knowledge-sidebar-filter" data-filter="pos" aria-label="Filter by part of speech">
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
                            <div class="knowledge-sidebar-filter-chips" style="display: none;"></div>

                            <!-- Results List -->
                            <div class="knowledge-sidebar-list">
                                <div class="knowledge-sidebar-list__items"></div>
                                <div class="knowledge-sidebar-list__footer" style="display: none;">
                                    <span class="knowledge-sidebar-list__count"></span>
                                    <button class="btn btn-sm knowledge-sidebar-list__load-more" style="display: none;">Load more</button>
                                </div>
                            </div>
                        </div>

                        <!-- Word Detail UI (for word clicks) -->
                        <div class="knowledge-sidebar-word-detail" style="display: none;">
                            <div class="knowledge-sidebar-word-header">
                                <button class="knowledge-sidebar-word-header__back" aria-label="Back to browse">
                                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                        <path d="M19 12H5M12 19l-7-7 7-7"/>
                                    </svg>
                                    <span class="knowledge-sidebar-word-header__citation"></span>
                                </button>
                            </div>
                            <div class="knowledge-sidebar-word-content"></div>
                        </div>
                    </div>
                    <!-- Research Tab Content -->
                    <div class="knowledge-tab-content" data-content="research">
                        <div class="knowledge-sidebar-placeholder">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                                <path d="M5 13.18V17.18L12 21L19 17.18V13.18L12 17L5 13.18ZM12 3L1 9L12 15L21 10.09V17H23V9L12 3Z"/>
                            </svg>
                            <h3>Research Notes</h3>
                            <p>Cross-references, parallel texts, and scholarly notes will appear here.</p>
                        </div>
                    </div>
                    <!-- Discussion Tab Content -->
                    <div class="knowledge-tab-content" data-content="discussion">
                        <div class="knowledge-sidebar-placeholder">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                                <path d="M22 2H2.01L2 22L6 18H22V2ZM6 9H18V11H6V9ZM14 14H6V12H14V14ZM18 8H6V6H18V8Z"/>
                            </svg>
                            <h3>Discussion</h3>
                            <p>Community interpretations and scholarly discussions will appear here.</p>
                        </div>
                    </div>
                    <!-- Context Tab Content -->
                    <div class="knowledge-tab-content" data-content="context">
                        <div class="knowledge-sidebar-placeholder">
                            <svg width="48" height="48" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                                <path d="M11.99 2C6.47 2 2 6.48 2 12C2 17.52 6.47 22 11.99 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 11.99 2ZM18.92 8H15.97C15.65 6.75 15.19 5.55 14.59 4.44C16.43 5.07 17.96 6.35 18.92 8ZM12 4.04C12.83 5.24 13.48 6.57 13.91 8H10.09C10.52 6.57 11.17 5.24 12 4.04ZM4.26 14C4.1 13.36 4 12.69 4 12C4 11.31 4.1 10.64 4.26 10H7.64C7.56 10.66 7.5 11.32 7.5 12C7.5 12.68 7.56 13.34 7.64 14H4.26ZM5.08 16H8.03C8.35 17.25 8.81 18.45 9.41 19.56C7.57 18.93 6.04 17.66 5.08 16ZM8.03 8H5.08C6.04 6.34 7.57 5.07 9.41 4.44C8.81 5.55 8.35 6.75 8.03 8ZM12 19.96C11.17 18.76 10.52 17.43 10.09 16H13.91C13.48 17.43 12.83 18.76 12 19.96ZM14.34 14H9.66C9.57 13.34 9.5 12.68 9.5 12C9.5 11.32 9.57 10.65 9.66 10H14.34C14.43 10.65 14.5 11.32 14.5 12C14.5 12.68 14.43 13.34 14.34 14ZM14.59 19.56C15.19 18.45 15.65 17.25 15.97 16H18.92C17.96 17.65 16.43 18.93 14.59 19.56ZM16.36 14C16.44 13.34 16.5 12.68 16.5 12C16.5 11.32 16.44 10.66 16.36 10H19.74C19.9 10.64 20 11.31 20 12C20 12.69 19.9 13.36 19.74 14H16.36Z"/>
                            </svg>
                            <h3>Historical Context</h3>
                            <p>Period information, archaeological context, and related materials will appear here.</p>
                        </div>
                    </div>
                    </div>
                </div>
            </aside>
        `;

        // Event listeners
        this.container.querySelectorAll('.atf-mode').forEach(btn => {
            btn.addEventListener('click', () => this.setMode(btn.dataset.mode));
        });

        // Knowledge sidebar icon bar event listeners
        this.container.querySelectorAll('.tabs-nav--vertical-icons .tab-button').forEach(btn => {
            btn.addEventListener('click', () => {
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

        // Listen for tablet viewer state changes (mutual exclusivity)
        document.addEventListener('tablet-viewer-state', (e) => {
            if (e.detail.action === 'viewer-expanding' && this.knowledgeSidebarOpen) {
                this.hideKnowledgeSidebar();
            }
        });

        // Dictionary browse event listeners
        const searchInput = this.container.querySelector('.knowledge-sidebar-search__input');
        const searchClear = this.container.querySelector('.knowledge-sidebar-search__clear');
        const languageFilter = this.container.querySelector('.knowledge-sidebar-filter[data-filter="language"]');
        const posFilter = this.container.querySelector('.knowledge-sidebar-filter[data-filter="pos"]');
        const loadMoreBtn = this.container.querySelector('.knowledge-sidebar-list__load-more');
        const backBtn = this.container.querySelector('.knowledge-sidebar-word-header__back');

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
        this.attachWordGlosses();
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
     * @param {string} surfaceForm - Optional surface form (e.g., "TIM" before normalization)
     */
    showKnowledgeSidebar(tab = null, word = null, surfaceForm = null) {
        const sidebar = this.container.querySelector('.atf-knowledge-sidebar');
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
        const sidebar = this.container.querySelector('.atf-knowledge-sidebar');

        // Set data-state for CSS transitions
        sidebar.dataset.state = 'closed';
        this.knowledgeSidebarOpen = false;

        // Clear all icon button selections
        sidebar.querySelectorAll('.tabs-nav--vertical-icons .tab-button').forEach(btn => {
            btn.setAttribute('aria-selected', 'false');
        });
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
        const sidebar = this.container.querySelector('.atf-knowledge-sidebar');

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
        const sidebar = this.container.querySelector('.atf-knowledge-sidebar');
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
            const response = await fetch(`/api/glossary.php?q=${encodeURIComponent(word)}&full=1`);
            const data = await response.json();

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
        const browseUI = this.container.querySelector('.knowledge-sidebar-dictionary');
        const wordUI = this.container.querySelector('.knowledge-sidebar-word-detail');

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
        const chipsContainer = this.container.querySelector('.knowledge-sidebar-filter-chips');
        const chips = [];

        if (this.dictionaryFilters.language) {
            const select = this.container.querySelector('.knowledge-sidebar-filter[data-filter="language"]');
            const option = select.querySelector(`option[value="${this.dictionaryFilters.language}"]`);
            chips.push({
                type: 'language',
                label: option.textContent,
                value: this.dictionaryFilters.language
            });
        }

        if (this.dictionaryFilters.pos) {
            const select = this.container.querySelector('.knowledge-sidebar-filter[data-filter="pos"]');
            const option = select.querySelector(`option[value="${this.dictionaryFilters.pos}"]`);
            chips.push({
                type: 'pos',
                label: option.textContent,
                value: this.dictionaryFilters.pos
            });
        }

        if (chips.length > 0) {
            chipsContainer.innerHTML = chips.map(chip => `
                <span class="knowledge-sidebar-filter-chip" data-type="${chip.type}">
                    ${chip.label}
                    <button class="knowledge-sidebar-filter-chip__remove" data-type="${chip.type}" aria-label="Remove filter">&times;</button>
                </span>
            `).join('');
            chipsContainer.style.display = 'flex';

            // Add remove handlers
            chipsContainer.querySelectorAll('.knowledge-sidebar-filter-chip__remove').forEach(btn => {
                btn.addEventListener('click', () => {
                    const filterType = btn.dataset.type;
                    this.dictionaryFilters[filterType] = null;
                    const select = this.container.querySelector(`.knowledge-sidebar-filter[data-filter="${filterType}"]`);
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
        const resultsList = this.container.querySelector('.knowledge-sidebar-list__items');
        const countEl = this.container.querySelector('.knowledge-sidebar-list__count');
        const loadMoreBtn = this.container.querySelector('.knowledge-sidebar-list__load-more');

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

            // Show footer and update count
            const footer = this.container.querySelector('.knowledge-sidebar-list__footer');
            footer.style.display = 'flex';
            const showing = Math.min(this.dictionaryResults.length, this.dictionaryTotalCount);
            countEl.textContent = `Showing ${showing.toLocaleString()} of ${this.dictionaryTotalCount.toLocaleString()}`;

            // Show/hide load more button
            loadMoreBtn.style.display = data.hasMore ? 'inline-block' : 'none';

        } catch (err) {
            console.error('Failed to load dictionary page:', err);
            resultsList.innerHTML = '<div class="state-error state-error--compact">Failed to load results</div>';
            // Hide footer on error
            const footer = this.container.querySelector('.knowledge-sidebar-list__footer');
            footer.style.display = 'none';
        }
    }

    /**
     * Render dictionary results list
     */
    renderDictionaryResults() {
        const resultsList = this.container.querySelector('.knowledge-sidebar-list__items');

        if (this.dictionaryResults.length === 0) {
            resultsList.innerHTML = '<div class="state-empty state-empty--compact">No entries found</div>';
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
                <div class="knowledge-sidebar-list__item" data-entry-id="${entry.entry_id}">
                    <div class="knowledge-sidebar-list__item-title">${mainText}</div>
                    <div class="knowledge-sidebar-list__item-meta">
                        ${language} · ${guideWord} · ${pos} · ${icount.toLocaleString()} occurrences
                    </div>
                </div>
            `;
        }).join('');

        // Add click handlers
        resultsList.querySelectorAll('.knowledge-sidebar-list__item').forEach(item => {
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
        const sidebar = this.container.querySelector('.atf-knowledge-sidebar');
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
            <div class="knowledge-sidebar-dictionary__empty">
                ${this.escapeHtml(message)}
                <div class="knowledge-sidebar-dictionary__empty-hint">The transliteration may not be available for this tablet.</div>
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
