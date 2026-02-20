/**
 * Tablet Detail Page JavaScript (v2)
 * Handles image viewer, metadata toggle, composite panel, actions menu
 */

const TabletPage = {
    zoombox: null,
    pNumber: null,
    apiUrl: null
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
});

// Load composite tablets from API
function loadCompositeTablets(qNumber) {
    if (!qNumber || !TabletPage.apiUrl) return;

    const listContainer = document.getElementById('composite-list');
    const countBadge = document.getElementById('composite-count');

    fetch(`${TabletPage.apiUrl}/artifacts/${TabletPage.pNumber}`)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        })
        .then(data => {
            const composites = data.composites || [];
            const target = composites.find(c => c.q_number === qNumber);
            if (target) {
                // For now, show composite info; full tablet list requires separate endpoint
                listContainer.innerHTML = `<div class="composite-panel__loading">${target.exemplar_count || '?'} exemplar tablets</div>`;
                if (countBadge) {
                    countBadge.textContent = `${target.exemplar_count || '?'} tablets`;
                }
            } else {
                listContainer.innerHTML = '<div class="composite-panel__loading">No composite data</div>';
            }
        })
        .catch(err => {
            console.error('Failed to load composite:', err);
            listContainer.innerHTML = '<div class="composite-panel__loading">Failed to load</div>';
        });
}
