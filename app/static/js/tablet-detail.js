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
                confidence: a.confidence || 0
            }));

            zoombox.setOverlays(overlays);
        })
        .catch(err => {
            console.log('Sign annotations not available:', err.message);
        });
}

// Load composite tablets from API
function loadCompositeTablets(qNumber) {
    if (!qNumber || !TabletPage.apiUrl) return;

    const listContainer = document.getElementById('composite-list');
    const countBadge = document.getElementById('composite-count');

    // Use correct endpoint for composite exemplars
    fetch(`${TabletPage.apiUrl}/composites/${qNumber}/exemplars`)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        })
        .then(data => {
            const exemplars = data.exemplars || [];

            if (exemplars.length === 0) {
                listContainer.innerHTML = '<div class="composite-panel__loading">No tablets</div>';
                return;
            }

            // Render actual tablet items with thumbnails
            listContainer.innerHTML = exemplars.map(tablet => {
                const isCurrent = tablet.p_number === TabletPage.pNumber;
                const thumbUrl = `${TabletPage.apiUrl}/image/${tablet.p_number}?size=64`;

                return `
                    <a href="/tablets/${tablet.p_number}"
                       class="composite-tablet-item ${isCurrent ? 'is-current' : ''}"
                       data-p-number="${tablet.p_number}">
                        <div class="composite-tablet-item__thumbnail">
                            <img src="${thumbUrl}"
                                 alt="${tablet.designation || tablet.p_number}"
                                 loading="lazy"
                                 onerror="this.style.display='none';">
                        </div>
                        <div class="composite-tablet-item__info">
                            <div class="composite-tablet-item__pnumber">${tablet.p_number}</div>
                            <div class="composite-tablet-item__designation">${tablet.designation || 'Unnamed'}</div>
                        </div>
                    </a>
                `;
            }).join('');

            // Update count badge
            if (countBadge) {
                countBadge.textContent = `${exemplars.length} tablet${exemplars.length !== 1 ? 's' : ''}`;
            }
        })
        .catch(err => {
            console.error('Composite load failed:', err);
            listContainer.innerHTML = '<div class="composite-panel__loading">Failed to load</div>';
        });
}
