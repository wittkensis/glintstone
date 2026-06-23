/**
 * Tablet Detail Page JavaScript (v2)
 * Handles image viewer, metadata toggle, composite panel, actions menu
 */

const TabletPage = {
    zoombox: null,
    pNumber: null,
    apiUrl: null,
    viewerExpanded: true
};

function initPNumber() {
    const container = document.getElementById('tablet-zoombox');
    if (container) {
        TabletPage.pNumber = container.dataset.pNumber;
        TabletPage.apiUrl = container.dataset.apiUrl || '';
    }
}

function updateImageSource(source) {
    const el = document.getElementById('image-source');
    if (el) el.textContent = 'Source: ' + source;
}

/**
 * Update viewer toggle button state
 */
function updateViewerToggleButton() {
    const viewerToggle = document.querySelector('.viewer-toggle');
    if (viewerToggle) {
        viewerToggle.setAttribute('aria-expanded', TabletPage.viewerExpanded);
    }
}

/**
 * Collapse the tablet viewer
 */
function collapseViewer() {
    const viewerContainer = document.querySelector('.tablet-detail-viewer');
    if (!viewerContainer) return;

    viewerContainer.dataset.viewerState = 'collapsed';
    TabletPage.viewerExpanded = false;
    updateViewerToggleButton();
}

/**
 * Expand the tablet viewer (and collapse knowledge sidebar)
 */
function expandViewer() {
    const viewerContainer = document.querySelector('.tablet-detail-viewer');

    if (!viewerContainer) return;

    viewerContainer.dataset.viewerState = 'expanded';
    TabletPage.viewerExpanded = true;
    updateViewerToggleButton();

    // Notify ATFViewer to collapse knowledge sidebar (mutual exclusivity)
    document.dispatchEvent(new CustomEvent('tablet-viewer-state', {
        detail: { action: 'viewer-expanding' }
    }));
}

/**
 * Toggle the tablet viewer collapse/expand
 */
function toggleViewer() {
    if (TabletPage.viewerExpanded) {
        collapseViewer();
    } else {
        expandViewer();
    }
}

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    initPNumber();

    // Metadata toggle
    const metaToggle = document.getElementById('meta-toggle');
    const metaSecondary = document.getElementById('meta-secondary');
    if (metaToggle && metaSecondary) {
        metaToggle.addEventListener('click', () => {
            const isExpanded = metaToggle.getAttribute('aria-expanded') === 'true';
            metaToggle.setAttribute('aria-expanded', !isExpanded);
            metaSecondary.classList.toggle('is-open', !isExpanded);
        });
    }

    // Initialize Zoombox
    const container = document.getElementById('tablet-zoombox');
    if (container && typeof Zoombox !== 'undefined') {
        TabletPage.zoombox = new Zoombox(container, {
            hoverThreshold: 2,
            onImageLoad: () => {
                updateImageSource('Loaded');
                loadSignAnnotations();
            },
            onOverlayClick: (anno, box) => {
                // Toggle selection: clicking the active box deselects it.
                const wasActive = box.classList.contains('is-selected');
                document.querySelectorAll('.zoombox__overlay-box.is-selected')
                    .forEach(b => b.classList.remove('is-selected'));

                if (wasActive) {
                    document.dispatchEvent(new CustomEvent('sign:selected', {
                        detail: { tokenId: null, sign: anno.sign || null }
                    }));
                    return;
                }

                box.classList.add('is-selected');
                // tokenId is null when the sign annotation has no matched token
                // (legacy rows / no token mapping); the listener tolerates that.
                document.dispatchEvent(new CustomEvent('sign:selected', {
                    detail: {
                        tokenId: anno.tokenId != null ? anno.tokenId : null,
                        sign: anno.sign || null
                    }
                }));
            }
        });

        // Load image from API
        const apiUrl = TabletPage.apiUrl;
        const pNumber = TabletPage.pNumber;
        if (apiUrl && pNumber) {
            TabletPage.zoombox.loadImage({
                local: `${apiUrl}/image/${pNumber}`,
                cdliPhoto: `https://cdli.earth/dl/photo/${pNumber}.jpg`,
                cdliLineart: `https://cdli.earth/dl/lineart/${pNumber}.jpg`
            });
        }
    }

    // Initialize ATF Viewer
    const atfContainer = document.querySelector('.atf-panel');
    if (atfContainer && typeof ATFViewer !== 'undefined') {
        TabletPage.atfViewer = new ATFViewer(atfContainer, {
            apiUrl: TabletPage.apiUrl,
            language: atfContainer.dataset.language || null,
        });
        if (TabletPage.pNumber) {
            TabletPage.atfViewer.load(TabletPage.pNumber);
        }
    }

    // Actions menu toggle
    const actionsMenu = document.querySelector('.actions-menu');
    const actionsDropdown = document.querySelector('.actions-menu__dropdown');
    const actionsTrigger = document.querySelector('.actions-menu__trigger');
    if (actionsMenu && actionsDropdown && actionsTrigger) {
        actionsTrigger.addEventListener('click', (e) => {
            e.stopPropagation();
            const isOpen = actionsDropdown.classList.contains('is-open');
            actionsDropdown.classList.toggle('is-open', !isOpen);
            actionsTrigger.setAttribute('aria-expanded', !isOpen);
        });
        document.addEventListener('click', () => {
            actionsDropdown.classList.remove('is-open');
            actionsTrigger.setAttribute('aria-expanded', 'false');
        });
    }

    // Composite panel toggle
    const compositeToggle = document.getElementById('composite-toggle');
    const compositePanel = document.getElementById('composite-panel');

    if (compositeToggle && compositePanel) {
        compositeToggle.addEventListener('click', () => {
            const isOpen = compositePanel.classList.contains('is-open');

            if (!isOpen) {
                compositePanel.classList.add('is-open');
                compositeToggle.setAttribute('aria-expanded', 'true');

                if (!compositePanel.dataset.loaded) {
                    loadCompositeTablets(compositePanel.dataset.qNumber);
                    compositePanel.dataset.loaded = 'true';
                }
            } else {
                compositePanel.classList.remove('is-open');
                compositeToggle.setAttribute('aria-expanded', 'false');
            }
        });
    }

    // Listen for knowledge sidebar open events
    document.addEventListener('knowledge-sidebar-state', (e) => {
        if (e.detail && e.detail.action === 'knowledge-open') {
            collapseViewer();
        }
    });

    // Listen for viewer toggle button clicks (from ATF viewer)
    document.addEventListener('viewer-toggle-requested', () => {
        toggleViewer();
    });

    // Make collapsed viewer clickable to expand
    const viewerPanel = document.querySelector('.viewer-panel');
    if (viewerPanel) {
        viewerPanel.addEventListener('click', () => {
            // Only expand if viewer is collapsed
            if (!TabletPage.viewerExpanded) {
                expandViewer();
            }
        });
    }

});

// Load sign annotations (OCR overlay) after image loads
function loadSignAnnotations() {
    const zoombox = TabletPage.zoombox;
    if (!zoombox || !zoombox.imageLoaded || !TabletPage.apiUrl || !TabletPage.pNumber) return;

    fetch(`${TabletPage.apiUrl}/artifacts/${TabletPage.pNumber}/sign-annotations`)
        .then(r => r.json())
        .then(data => {
            if (!data.annotations || data.annotations.length === 0) return;

            const natW = zoombox.naturalWidth;
            const natH = zoombox.naturalHeight;
            if (!natW || !natH) return;

            const overlays = data.annotations.map(a => ({
                x: (a.bbox_x / natW) * 100,
                y: (a.bbox_y / natH) * 100,
                width: (a.bbox_w / natW) * 100,
                height: (a.bbox_h / natH) * 100,
                sign: a.sign_id || '',
                surface: a.surface_type || '',
                confidence: a.confidence || 0,
                tokenId: a.token_id != null ? a.token_id : null
            }));

            zoombox.setOverlays(overlays);
        })
        .catch(err => {
            console.log('Sign annotations not available:', err.message);
        });
}

// #404 Concept B — sibling-witness strip.
// On panel-open, fetch the composite's exemplars and render the OTHER tablets
// witnessing the same text as a horizontal strip of navigable cards (the current
// tablet highlighted, non-link). Best-preserved siblings first; capped to 8 with
// a "+N more" card → the composition page. Coverage dot maps translation status.
const SIBLING_CAP = 8;

function htmlEscape(s) {
    const d = document.createElement('div');
    d.textContent = s == null ? '' : String(s);
    return d.innerHTML;
}

function siblingCoverage(t) {
    // Mirror the composition route's _coverage(): semantic_complete is canonical
    // (binary today), has_translation the fallback.
    let score;
    const raw = t.semantic_complete;
    if (raw != null && raw !== '' && !isNaN(parseFloat(raw))) {
        score = parseFloat(raw);
    } else {
        score = t.has_translation ? 1 : 0;
    }
    if (score >= 0.99) return 'translated';
    if (score > 0) return 'partial';
    return 'untranslated';
}

function loadCompositeTablets(qNumber) {
    if (!qNumber || !TabletPage.apiUrl) return;

    const wrap = document.getElementById('composite-siblings');
    const listContainer = document.getElementById('composite-list');
    const countBadge = document.getElementById('composite-count');
    const label = wrap ? wrap.querySelector('.witness-siblings__label') : null;
    if (!listContainer) return;

    fetch(`${TabletPage.apiUrl}/composites/${qNumber}/exemplars`)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        })
        .then(data => {
            const exemplars = data.exemplars || [];

            if (countBadge) {
                countBadge.textContent =
                    `${exemplars.length} witness${exemplars.length !== 1 ? 'es' : ''} in Glintstone`;
            }

            // Only witness linked: collapse the strip to a single statement.
            if (exemplars.length <= 1) {
                if (label) {
                    label.textContent =
                        'This is the only witness of this text linked in Glintstone.';
                }
                listContainer.remove();
                return;
            }

            // Best-preserved siblings first (most readable ATF lines) — the
            // strongest comparanda surface first (spec default).
            const sorted = exemplars.slice().sort(
                (a, b) => (b.atf_line_count || 0) - (a.atf_line_count || 0)
            );

            // Current tablet first (highlighted), then capped siblings.
            const current = sorted.filter(t => t.p_number === TabletPage.pNumber);
            const others = sorted.filter(t => t.p_number !== TabletPage.pNumber);
            const shown = current.concat(others.slice(0, SIBLING_CAP));
            const overflow = others.length - Math.min(others.length, SIBLING_CAP);

            const cards = shown.map(t => {
                const isCurrent = t.p_number === TabletPage.pNumber;
                const cov = siblingCoverage(t);
                const period = t.period || 'Period unknown';
                const prov = t.provenience ? ` · ${htmlEscape(t.provenience)}` : '';
                const ref = isCurrent
                    ? (t.line_ref ? `this tablet · ${htmlEscape(t.line_ref)}` : 'this tablet')
                    : (t.line_ref ? htmlEscape(t.line_ref) : '');
                const inner =
                    `<span class="sibling-card__top">` +
                    `<span class="sibling-card__cov sibling-card__cov--${cov}"></span>` +
                    `<span class="sibling-card__pnum">${htmlEscape(t.p_number)}</span></span>` +
                    `<span class="sibling-card__period">${htmlEscape(period)}${prov}</span>` +
                    (ref ? `<span class="sibling-card__ref">${ref}</span>` : '');
                return isCurrent
                    ? `<div class="sibling-card is-current">${inner}</div>`
                    : `<a class="sibling-card" href="/tablets/${htmlEscape(t.p_number)}">${inner}</a>`;
            });

            if (overflow > 0) {
                cards.push(
                    `<a class="sibling-card sibling-card--more" ` +
                    `href="/compositions/${htmlEscape(qNumber)}">+ ${overflow} more ›</a>`
                );
            }

            listContainer.innerHTML = cards.join('');
            listContainer.setAttribute('aria-busy', 'false');
        })
        .catch(err => {
            console.error('Composite siblings load failed:', err);
            listContainer.innerHTML =
                '<div class="composite-panel__loading">Failed to load other witnesses</div>';
            listContainer.setAttribute('aria-busy', 'false');
        });
}
