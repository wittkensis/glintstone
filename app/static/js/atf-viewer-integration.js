/**
 * ATF Viewer Dictionary Integration
 *
 * This file extends the ATF Viewer with dictionary browser integration:
 * - Uses shared WordDetailRenderer for dictionary content
 * - Adds "View in Dictionary" links
 * - Integrates with educational help system
 *
 * Usage: Include after atf-viewer.js and shared modules
 */

(function() {
    'use strict';

    // Store original methods
    const originalRenderDictionaryContent = ATFViewer.prototype.renderDictionaryContent;
    const originalLoadDictionaryContent = ATFViewer.prototype.loadDictionaryContent;

    /**
     * Enhanced loadDictionaryContent that fetches full word detail
     */
    ATFViewer.prototype.loadDictionaryContent = async function(word) {
        const sidebar = document.getElementById('knowledge-sidebar');
        if (!sidebar) return;
        const dictContent = sidebar.querySelector('.knowledge-sidebar-word-content');

        this.lastDictionaryWord = word;

        // Set mode to word detail
        this.setDictionaryMode('word');

        // Check cache first (for backward compatibility)
        if (this.definitionCache.has(word)) {
            const cachedData = this.definitionCache.get(word);

            // If cached data has entry_id, fetch full detail from new API
            if (cachedData.entries && cachedData.entries.length > 0 && cachedData.entries[0].entry_id) {
                const entryId = cachedData.entries[0].entry_id;
                await this.loadWordDetailFromDictionary(entryId, word, cachedData);
                return;
            }

            // Otherwise use old rendering
            this.renderDictionaryContentLegacy(cachedData, word);
            return;
        }

        // Show loading state
        dictContent.innerHTML = '<div class="knowledge-sidebar-dictionary__loading">Loading definition...</div>';

        try {
            // Fetch from glossary API (existing endpoint)
            const response = await fetch(`/api/glossary.php?q=${encodeURIComponent(word)}`);
            if (!response.ok) throw new Error('API error');

            const data = await response.json();
            this.definitionCache.set(word, data);

            // If we have an entry_id, fetch full detail
            if (data.entries && data.entries.length > 0 && data.entries[0].entry_id) {
                const entryId = data.entries[0].entry_id;
                await this.loadWordDetailFromDictionary(entryId, word, data);
            } else {
                this.renderDictionaryContentLegacy(data, word);
            }
        } catch (error) {
            console.error('Error loading dictionary:', error);
            dictContent.innerHTML = `
                <div class="knowledge-sidebar-dictionary__empty">
                    Error loading definition
                    <div class="knowledge-sidebar-dictionary__empty-hint">Please try again</div>
                </div>
            `;
        }
    };

    /**
     * Load full word detail from library API
     */
    ATFViewer.prototype.loadWordDetailFromDictionary = async function(entryId, word, fallbackData) {
        const sidebar = document.getElementById('knowledge-sidebar');
        if (!sidebar) return;
        const citationEl = sidebar.querySelector('.knowledge-sidebar-word-header__citation');
        const dictContent = sidebar.querySelector('.knowledge-sidebar-word-content');

        try {
            // Fetch from word-detail API
            const response = await fetch(`/api/dictionary/word-detail.php?entry_id=${encodeURIComponent(entryId)}`);
            if (!response.ok) throw new Error('API error');

            const data = await response.json();

            // Update header
            citationEl.textContent = data.entry.citation_form || data.entry.headword || word;

            // Create container for word detail renderer
            const container = document.createElement('div');
            container.className = 'word-detail-container compact';

            // Initialize renderer
            const renderer = new WordDetailRenderer({
                compact: true
            });

            // Render word detail
            await renderer.render(data, container);

            // Add "View in Library" button
            const viewInLibraryBtn = document.createElement('div');
            viewInLibraryBtn.className = 'knowledge-sidebar-library-link';
            viewInLibraryBtn.innerHTML = `
                <a href="/dictionary/word.php?id=${encodeURIComponent(entryId)}" class="btn btn--ghost" target="_blank">
                    View in Dictionary →
                </a>
            `;
            container.appendChild(viewInLibraryBtn);

            // Add sign form section if surface form differs
            if (this.lastSurfaceForm) {
                const signFormSection = this.renderSignFormSection(this.lastSurfaceForm, data.entry);
                if (signFormSection) {
                    const signFormDiv = document.createElement('div');
                    signFormDiv.innerHTML = signFormSection;
                    container.insertBefore(signFormDiv.firstElementChild, container.firstChild);
                }
            }

            // Update content
            dictContent.innerHTML = '';
            dictContent.appendChild(container);

        } catch (error) {
            console.error('Error loading word detail from library:', error);

            // Fallback to legacy rendering
            if (fallbackData) {
                this.renderDictionaryContentLegacy(fallbackData, word);
            } else {
                dictContent.innerHTML = `
                    <div class="knowledge-sidebar-dictionary__empty">
                        Error loading full definition
                        <div class="knowledge-sidebar-dictionary__empty-hint">Showing basic information</div>
                    </div>
                `;
            }
        }
    };

    /**
     * Legacy dictionary content rendering (fallback)
     */
    ATFViewer.prototype.renderDictionaryContentLegacy = function(data, word) {
        // Call original method
        originalRenderDictionaryContent.call(this, data, word);

        // Add "View in Library" link if we have entry_id
        if (data.entries && data.entries.length > 0 && data.entries[0].entry_id) {
            const sidebar = document.getElementById('knowledge-sidebar');
            if (!sidebar) return;
            const dictContent = sidebar.querySelector('.knowledge-sidebar-word-content');

            const entryId = data.entries[0].entry_id;
            const viewInLibraryBtn = document.createElement('div');
            viewInLibraryBtn.className = 'knowledge-sidebar-library-link';
            viewInLibraryBtn.innerHTML = `
                <a href="/dictionary/word.php?id=${encodeURIComponent(entryId)}" class="btn btn--ghost" target="_blank">
                    View in Dictionary →
                </a>
            `;
            dictContent.appendChild(viewInLibraryBtn);
        }
    };

    /**
     * Enhance word click handling to show library link
     */
    const originalSetupWordClickHandlers = ATFViewer.prototype.setupWordClickHandlers;
    if (originalSetupWordClickHandlers) {
        ATFViewer.prototype.setupWordClickHandlers = function() {
            originalSetupWordClickHandlers.call(this);

            // Add additional handling for library links
            this.container.addEventListener('click', (e) => {
                if (e.target.closest('.knowledge-sidebar-library-link a')) {
                    // Link will open in new tab, no special handling needed
                }
            });
        };
    }

    console.log('ATF Viewer library integration loaded');
})();
