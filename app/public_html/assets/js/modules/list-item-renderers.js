/**
 * List Item Renderers
 * Shared rendering module for consistent list item HTML generation.
 * Depends on: window.DICTIONARY_LABELS (from Labels::toJavaScript())
 *
 * Renderers: WordListItem, TabletListItem, CollectionListItem
 */

/* =========================================================================
   Shared Utilities
   ========================================================================= */

const ListItemUtils = {
    escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    },

    getLangLabel(code) {
        if (!code) return '';
        return window.DICTIONARY_LABELS?.language?.[code] || code;
    },

    getPosLabel(code) {
        if (!code) return '';
        return window.DICTIONARY_LABELS?.pos?.[code] || code;
    },

    formatCount(n) {
        return (n || 0).toLocaleString();
    },

    /**
     * Join non-empty strings with a separator, returning HTML spans.
     * @param {string[]} items
     * @returns {string} HTML with separators
     */
    joinMeta(items) {
        const filtered = items.filter(Boolean);
        if (!filtered.length) return '';
        return filtered
            .map(v => `<span>${this.escapeHtml(v)}</span>`)
            .join('<span class="list-item__sep" aria-hidden="true">&middot;</span>');
    }
};

/* =========================================================================
   WordListItem Renderer
   ========================================================================= */

/**
 * Renders dictionary word entries as list items.
 * Used by: dictionary-browser.js, atf-viewer.js, search.js, word-detail-renderer.js
 */
const WordListItem = {
    /**
     * Render a word as a list item HTML string.
     *
     * @param {Object} entry - Word data
     * @param {string} entry.entry_id
     * @param {string} entry.headword
     * @param {string} [entry.citation_form]
     * @param {string} [entry.guide_word]
     * @param {string} [entry.pos]
     * @param {string} [entry.language]
     * @param {number} [entry.icount]
     *
     * @param {Object} [options]
     * @param {boolean} [options.active]    - Currently selected
     * @param {boolean} [options.compact]   - Sidebar compact mode
     * @param {boolean} [options.search]    - Search result (wraps in <a>, accent hover)
     * @param {boolean} [options.card]      - Card mode for grid contexts (wraps in <a>, border)
     * @param {boolean} [options.skeleton]  - Skeleton loading placeholder
     * @param {string}  [options.hideBadge] - 'pos'|'language' to conditionally hide a badge
     * @param {string}  [options.notes]     - Optional notes text
     * @returns {string} HTML string
     */
    render(entry, options = {}) {
        const e = ListItemUtils.escapeHtml;
        const langLabel = ListItemUtils.getLangLabel(entry.language);
        const posLabel = ListItemUtils.getPosLabel(entry.pos);
        const displayName = entry.citation_form || entry.headword || '';
        const count = ListItemUtils.formatCount(entry.icount);

        // Build modifier classes
        const mods = [];
        if (options.active) mods.push('list-item--active');
        if (options.compact) mods.push('list-item--compact');
        if (options.search) mods.push('list-item--search');
        if (options.card) mods.push('list-item--card');
        if (options.skeleton) mods.push('list-item--skeleton');
        const cls = `list-item ${mods.join(' ')}`.trim();

        const metaItems = [];
        if (options.hideBadge !== 'pos' && posLabel) metaItems.push(posLabel);
        if (options.hideBadge !== 'language' && langLabel) metaItems.push(langLabel);

        const inner = `
            <div class="list-item__header">
                <span class="list-item__title">${e(displayName)}</span>
                ${entry.guide_word ? `<span class="list-item__subtitle">${e(entry.guide_word)}</span>` : ''}
            </div>
            <div class="list-item__meta">
                ${ListItemUtils.joinMeta(metaItems)}
                <span class="list-item__count">${count}</span>
            </div>
            ${options.notes ? `<div class="list-item__notes">${e(options.notes)}</div>` : ''}
        `;

        // Link wrapper for search and card modes
        if (options.search || options.card) {
            const href = `/dictionary/?word=${encodeURIComponent(entry.entry_id || '')}`;
            return `<a href="${href}" class="${cls}" data-entry-id="${e(entry.entry_id)}" role="option">${inner}</a>`;
        }

        // Default: non-link interactive element
        return `<div class="${cls}" data-entry-id="${e(entry.entry_id || '')}"
                     ${!options.skeleton ? 'tabindex="0" role="button"' : ''}>${inner}</div>`;
    },

    /**
     * Render skeleton loading placeholders.
     * @param {number} [count=5]
     * @returns {string} HTML string
     */
    renderSkeletons(count = 5) {
        const placeholder = { headword: '\u00A0\u00A0\u00A0\u00A0\u00A0', guide_word: '\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0\u00A0', entry_id: '' };
        return Array.from({ length: count }, () =>
            this.render(placeholder, { skeleton: true })
        ).join('');
    }
};

/* =========================================================================
   TabletListItem Renderer
   ========================================================================= */

/**
 * Renders tablet entries as list items with optional thumbnail.
 * Used by: search.js
 */
const TabletListItem = {
    /**
     * Render a tablet as a list item HTML string.
     *
     * @param {Object} tablet - Tablet data
     * @param {string} tablet.p_number
     * @param {string} [tablet.period]
     * @param {string} [tablet.provenience]
     * @param {string} [tablet.genre]
     * @param {boolean} [tablet.has_image]
     * @param {string} [tablet.designation] - Optional subtitle
     *
     * @param {Object} [options]
     * @param {boolean} [options.search]   - Search result mode
     * @param {boolean} [options.compact]  - Sidebar compact mode
     * @param {boolean} [options.card]     - Card mode for grid contexts
     * @param {boolean} [options.active]   - Currently selected
     * @param {boolean} [options.skeleton] - Skeleton loading placeholder
     * @returns {string} HTML string
     */
    render(tablet, options = {}) {
        const e = ListItemUtils.escapeHtml;
        const pNumber = tablet.p_number || '';

        // Build modifier classes
        const mods = ['list-item--tablet'];
        if (options.active) mods.push('list-item--active');
        if (options.compact) mods.push('list-item--compact');
        if (options.search) mods.push('list-item--search');
        if (options.card) mods.push('list-item--card');
        if (options.skeleton) mods.push('list-item--skeleton');
        const cls = `list-item ${mods.join(' ')}`.trim();

        // Thumbnail
        const thumbSize = options.search ? 64 : (options.compact ? 48 : 64);
        const imgSrc = `/api/thumbnail.php?p=${encodeURIComponent(pNumber)}&size=${thumbSize}`;
        const thumbnailContent = tablet.has_image
            ? `<img src="${imgSrc}" alt="${e(pNumber)}" loading="lazy"
                    onerror="this.style.display='none';this.nextElementSibling.style.display='';">
               <span class="list-item__thumbnail-text" style="display:none;">\u{12000}</span>`
            : `<span class="list-item__thumbnail-text">\u{12000}</span>`;

        // Meta text
        const metaHtml = ListItemUtils.joinMeta([tablet.period, tablet.provenience, tablet.genre]);

        const inner = `
            <div class="list-item__thumbnail">${thumbnailContent}</div>
            <div class="list-item__body">
                <div class="list-item__header">
                    <span class="list-item__title">${e(pNumber)}</span>
                    ${tablet.designation ? `<span class="list-item__subtitle">${e(tablet.designation)}</span>` : ''}
                </div>
                ${metaHtml ? `<div class="list-item__meta">${metaHtml}</div>` : ''}
            </div>
        `;

        const href = `/tablets/detail.php?p=${encodeURIComponent(pNumber)}`;
        return `<a href="${href}" class="${cls}" data-p-number="${e(pNumber)}" role="option">${inner}</a>`;
    }
};

/* =========================================================================
   CollectionListItem Renderer
   ========================================================================= */

/**
 * Renders collection entries as list items.
 * Used by: search.js
 */
const CollectionListItem = {
    /**
     * Render a collection as a list item HTML string.
     *
     * @param {Object} collection - Collection data
     * @param {string|number} collection.collection_id
     * @param {string} collection.name
     * @param {number} [collection.tablet_count]
     * @param {string} [collection.description]
     *
     * @param {Object} [options]
     * @param {boolean} [options.search]   - Search result mode
     * @param {boolean} [options.compact]  - Sidebar compact mode
     * @param {boolean} [options.card]     - Card mode for grid contexts
     * @param {boolean} [options.active]   - Currently selected
     * @returns {string} HTML string
     */
    render(collection, options = {}) {
        const e = ListItemUtils.escapeHtml;
        const name = collection.name || '';
        const count = collection.tablet_count || 0;

        // Build modifier classes
        const mods = [];
        if (options.active) mods.push('list-item--active');
        if (options.compact) mods.push('list-item--compact');
        if (options.search) mods.push('list-item--search');
        if (options.card) mods.push('list-item--card');
        const cls = `list-item ${mods.join(' ')}`.trim();

        // Truncate description for subtitle
        const desc = collection.description || '';
        const subtitle = desc.length > 60 ? desc.substring(0, 60) + '...' : desc;

        const inner = `
            <div class="list-item__header">
                <span class="list-item__title">${e(name)}</span>
                ${subtitle ? `<span class="list-item__subtitle">${e(subtitle)}</span>` : ''}
            </div>
            <div class="list-item__meta">
                <span>${count} tablets</span>
            </div>
        `;

        const href = `/collections/detail.php?id=${encodeURIComponent(collection.collection_id || '')}`;
        return `<a href="${href}" class="${cls}" data-collection-id="${e(String(collection.collection_id || ''))}" role="option">${inner}</a>`;
    }
};
