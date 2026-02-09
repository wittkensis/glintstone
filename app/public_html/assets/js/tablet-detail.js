/**
 * Tablet Detail Page JavaScript
 * Handles image viewer, annotations, ATF word interactions, and glossary popups
 */

// ============================================
// TABLET PAGE STATE
// ============================================
const TabletPage = {
    zoombox: null,
    atfViewer: null,
    annotationData: null,
    annotationsVisible: false,
    currentImageType: 'photo',
    pNumber: null
};

// Initialize pNumber from data attribute
function initPNumber() {
    const container = document.getElementById('tablet-zoombox');
    if (container && container.dataset.pNumber) {
        TabletPage.pNumber = container.dataset.pNumber;
    }
}

// Update image source label
function updateImageSource(source) {
    const el = document.getElementById('image-source');
    if (el) el.textContent = 'Source: ' + source;
}

// ============================================
// ANNOTATION HANDLING
// ============================================

function onAnnotationsFetched(data) {
    TabletPage.annotationData = data;

    if (!data || data.count === 0) return;

    // Show toggle
    const toggle = document.getElementById('annotation-toggle');
    const countBadge = document.getElementById('annotation-count');
    const checkbox = document.getElementById('annotation-checkbox');

    if (toggle) {
        toggle.style.display = 'flex';
        if (countBadge) countBadge.textContent = data.count;

        // Enable by default, but only apply if image is loaded
        if (checkbox && !checkbox.checked) {
            checkbox.checked = true;
            TabletPage.annotationsVisible = true;
            // Only apply overlays if image has loaded (has dimensions)
            if (TabletPage.zoombox && TabletPage.zoombox.imageLoaded) {
                TabletPage.zoombox.setOverlays(data.annotations);
            }
            // Otherwise, overlays will be applied in onImageLoad callback
        }
    }

    // Show OCR explanation if no ATF
    showOcrExplanationIfNeeded();
}

function toggleAnnotations(visible) {
    TabletPage.annotationsVisible = visible;

    if (visible && TabletPage.annotationData && TabletPage.zoombox) {
        TabletPage.zoombox.setOverlays(TabletPage.annotationData.annotations);
    } else if (TabletPage.zoombox) {
        TabletPage.zoombox.clearOverlays();
    }
}

// ============================================
// IMAGE SWITCHING
// ============================================

function switchImage(type) {
    const container = document.getElementById('tablet-zoombox');
    if (!container || !TabletPage.zoombox) return;

    TabletPage.currentImageType = type;

    const sources = {
        local: type === 'photo' ? container.dataset.local : null,
        cdliPhoto: type === 'photo' ? container.dataset.cdliPhoto : null,
        cdliLineart: container.dataset.cdliLineart
    };

    updateImageSource(type === 'photo' ? 'CDLI Photo' : 'CDLI Line Art');

    TabletPage.zoombox.loadImage(sources).then(loaded => {
        if (loaded && TabletPage.annotationsVisible && TabletPage.annotationData) {
            TabletPage.zoombox.setOverlays(TabletPage.annotationData.annotations);
        }
    });
}

// ============================================
// INITIALIZATION
// ============================================

document.addEventListener('DOMContentLoaded', function() {
    // Initialize pNumber
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
    if (container) {
        TabletPage.zoombox = new Zoombox(container, {
            hoverThreshold: 2,
            onImageLoad: (img) => {
                // Apply pending annotations if they arrived before image loaded
                if (TabletPage.annotationsVisible && TabletPage.annotationData) {
                    TabletPage.zoombox.setOverlays(TabletPage.annotationData.annotations);
                }
                // Cache thumbnail if loaded from CDLI
                if (img.src.includes('cdli')) {
                    cacheThumbnail();
                }
            },
            onOverlayClick: (anno, box) => {
                showSignPopup(anno, box);
            }
        });

        // Load image with fallback chain
        TabletPage.zoombox.loadImage({
            local: container.dataset.local,
            cdliPhoto: container.dataset.cdliPhoto,
            cdliLineart: container.dataset.cdliLineart
        });
    }

    // Image type buttons
    document.getElementById('btn-photo')?.addEventListener('click', () => switchImage('photo'));
    document.getElementById('btn-lineart')?.addEventListener('click', () => switchImage('lineart'));

    // Annotation toggle
    document.getElementById('annotation-checkbox')?.addEventListener('change', function() {
        toggleAnnotations(this.checked);
    });

    // Initialize ATF Viewer
    const atfViewerContainer = document.getElementById('atf-viewer');
    if (atfViewerContainer && typeof ATFViewer !== 'undefined') {
        const pNumber = atfViewerContainer.dataset.pNumber;
        if (pNumber) {
            TabletPage.atfViewer = new ATFViewer(atfViewerContainer, {
                showLegend: true,
                defaultMode: 'interactive'
            });
            TabletPage.atfViewer.load(pNumber);
        }
    }

    // Actions menu toggle (for touch devices)
    const actionsMenu = document.querySelector('.actions-menu');
    const actionsDropdown = document.querySelector('.actions-menu__dropdown');
    const actionsTrigger = document.querySelector('.actions-menu__trigger');
    if (actionsMenu && actionsDropdown && actionsTrigger) {
        actionsTrigger.addEventListener('click', (e) => {
            e.stopPropagation();
            const isOpen = actionsDropdown.style.display === 'block';
            actionsDropdown.style.display = isOpen ? 'none' : 'block';
            actionsTrigger.setAttribute('aria-expanded', !isOpen);
        });
        // Close on outside click
        document.addEventListener('click', () => {
            actionsDropdown.style.display = 'none';
            actionsTrigger.setAttribute('aria-expanded', 'false');
        });
    }

    // Viewer toggle - wait for ATF viewer to render
    setTimeout(() => {
        setupViewerToggle();
    }, 300);

    // Composite panel toggle
    const compositeToggle = document.getElementById('composite-toggle');
    const compositePanel = document.getElementById('composite-panel');

    if (compositeToggle && compositePanel) {
        compositeToggle.addEventListener('click', () => {
            const isOpen = compositePanel.classList.contains('is-open');

            if (!isOpen) {
                compositePanel.classList.add('is-open');
                compositeToggle.setAttribute('aria-expanded', 'true');

                // Load composite tablets if not already loaded
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

    // Fetch sign annotations
    fetchAnnotations();
});

// Setup viewer toggle button
function setupViewerToggle() {
    const viewerToggle = document.querySelector('.viewer-toggle');
    const viewerContainer = document.querySelector('.tablet-detail-viewer');
    const viewerPanel = document.querySelector('.viewer-panel');
    const zoomControls = document.querySelector('.zoombox__controls');
    const minimapContainer = document.querySelector('.zoombox__minimap-container');

    console.log('setupViewerToggle:', { viewerToggle, viewerContainer, viewerPanel });

    if (viewerToggle && viewerContainer && viewerPanel) {
        let animationFrame = null;

        // Set initial state
        const initialState = viewerContainer.dataset.state || 'collapsed';
        viewerToggle.setAttribute('aria-expanded', initialState === 'expanded');

        // Listen for knowledge sidebar state changes (mutual exclusivity)
        document.addEventListener('knowledge-sidebar-state', (e) => {
            if (e.detail.action === 'knowledge-open' && viewerContainer.dataset.state === 'expanded') {
                // Collapse viewer when knowledge sidebar opens
                viewerContainer.dataset.state = 'collapsed';
                viewerToggle.setAttribute('aria-expanded', 'false');
                zoomControls?.classList.remove('is-visible');
                minimapContainer?.classList.remove('is-visible');

                // Update zoom after transition
                const handleCollapseEnd = (ev) => {
                    if (ev.propertyName === 'width' && ev.target === viewerPanel) {
                        if (TabletPage.zoombox) {
                            TabletPage.zoombox.resetZoom();
                        }
                        viewerPanel.removeEventListener('transitionend', handleCollapseEnd);
                    }
                };
                viewerPanel.addEventListener('transitionend', handleCollapseEnd);
            }
        });

        // Show controls if initially expanded
        if (initialState === 'expanded') {
            zoomControls?.classList.add('is-visible');
            minimapContainer?.classList.add('is-visible');
        }

        // Continuously update zoom during transition for smooth scaling
        function updateZoomDuringTransition() {
            if (TabletPage.zoombox) {
                TabletPage.zoombox.resetZoom();
            }
            animationFrame = requestAnimationFrame(updateZoomDuringTransition);
        }

        viewerToggle.addEventListener('click', () => {
            console.log('Toggle clicked!');
            const currentState = viewerContainer.dataset.state;
            const newState = currentState === 'collapsed' ? 'expanded' : 'collapsed';
            console.log('State change:', currentState, '->', newState);

            viewerContainer.dataset.state = newState;
            viewerToggle.setAttribute('aria-expanded', newState === 'expanded');

            // Notify knowledge sidebar when expanding (mutual exclusivity)
            if (newState === 'expanded') {
                document.dispatchEvent(new CustomEvent('tablet-viewer-state', {
                    detail: { action: 'viewer-expanding' }
                }));
            }

            // If collapsing, immediately fade out controls
            if (newState === 'collapsed') {
                zoomControls?.classList.remove('is-visible');
                minimapContainer?.classList.remove('is-visible');
            }

            // Cancel any existing animation
            if (animationFrame) {
                cancelAnimationFrame(animationFrame);
            }

            // Start continuous zoom updates during transition
            animationFrame = requestAnimationFrame(updateZoomDuringTransition);

            // Stop animation when transition completes
            const handleTransitionEnd = (e) => {
                if (e.propertyName === 'width' && e.target === viewerPanel) {
                    if (animationFrame) {
                        cancelAnimationFrame(animationFrame);
                        animationFrame = null;
                    }
                    // Final update to ensure perfect fit
                    if (TabletPage.zoombox) {
                        TabletPage.zoombox.resetZoom();
                    }

                    // If expanding, fade in controls after panel is fully expanded
                    if (newState === 'expanded') {
                        zoomControls?.classList.add('is-visible');
                        minimapContainer?.classList.add('is-visible');
                    }

                    viewerPanel.removeEventListener('transitionend', handleTransitionEnd);
                }
            };

            viewerPanel.addEventListener('transitionend', handleTransitionEnd);
        });

        // Allow clicking collapsed sidebar to expand (but not to collapse)
        viewerPanel.addEventListener('click', (e) => {
            const currentState = viewerContainer.dataset.state;

            // Only expand when collapsed, and don't trigger if clicking the toggle button
            if (currentState === 'collapsed' && !e.target.closest('.viewer-toggle')) {
                const newState = 'expanded';
                viewerContainer.dataset.state = newState;

                // Update toggle button if it exists
                if (viewerToggle) {
                    viewerToggle.setAttribute('aria-expanded', 'true');
                }

                // Notify knowledge sidebar when expanding (mutual exclusivity)
                document.dispatchEvent(new CustomEvent('tablet-viewer-state', {
                    detail: { action: 'viewer-expanding' }
                }));

                // Fade out controls (they'll fade in after expansion completes)
                zoomControls?.classList.remove('is-visible');
                minimapContainer?.classList.remove('is-visible');

                // Cancel any existing animation
                if (animationFrame) {
                    cancelAnimationFrame(animationFrame);
                }

                // Start continuous zoom updates during transition
                animationFrame = requestAnimationFrame(updateZoomDuringTransition);

                // Stop animation when transition completes
                const handleTransitionEnd = (e) => {
                    if (e.propertyName === 'width' && e.target === viewerPanel) {
                        if (animationFrame) {
                            cancelAnimationFrame(animationFrame);
                            animationFrame = null;
                        }
                        // Final update to ensure perfect fit
                        if (TabletPage.zoombox) {
                            TabletPage.zoombox.resetZoom();
                        }

                        // Fade in controls after panel is fully expanded
                        zoomControls?.classList.add('is-visible');
                        minimapContainer?.classList.add('is-visible');

                        viewerPanel.removeEventListener('transitionend', handleTransitionEnd);
                    }
                };

                viewerPanel.addEventListener('transitionend', handleTransitionEnd);
            }
        });
    }
}

// Fetch sign annotations for this tablet
function fetchAnnotations() {
    if (!TabletPage.pNumber) return;

    fetch(`/api/annotations.php?p=${TabletPage.pNumber}`)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        })
        .then(data => {
            onAnnotationsFetched(data);
        })
        .catch(err => {
            console.warn('Failed to fetch annotations:', err);
        });
}

// Show explanation when OCR exists but ATF doesn't
function showOcrExplanationIfNeeded() {
    const noAtfContainer = document.querySelector('.no-atf');
    const annotationData = TabletPage.annotationData;
    if (!noAtfContainer || !annotationData || annotationData.count === 0) return;

    // Check if explanation already exists
    if (document.getElementById('ocr-explanation')) return;

    const explanation = document.createElement('div');
    explanation.id = 'ocr-explanation';
    explanation.className = 'ocr-explanation';
    explanation.innerHTML = `
        <div class="ocr-info-box">
            <h4>Machine Vision Data Available</h4>
            <p>While no human transliteration exists for this tablet, <strong>${annotationData.count} cuneiform signs</strong> have been identified by computer vision (highlighted on the image).</p>
            <details>
                <summary>What does this mean?</summary>
                <div class="ocr-details">
                    <p><strong>OCR annotations</strong> identify <em>which</em> signs appear and <em>where</em> they are located, using MZL (sign list) reference numbers.</p>
                    <p><strong>What's missing:</strong> The <em>reading</em> of each sign in context. For example, MZL 839 can be read as "AN" (sky), "DINGIR" (god), or "ilu" depending on context.</p>
                    <p><strong>How to help:</strong> If you can read cuneiform, you could contribute a transliteration using the sign locations as a guide. The annotations show sign boundaries that can help with difficult passages.</p>
                    <p><strong>Future possibilities:</strong> These bounding boxes could train ML models to auto-generate transliterations, or help match this tablet to similar texts with known readings.</p>
                </div>
            </details>
        </div>
    `;

    // Insert before the buttons
    const buttons = noAtfContainer.querySelector('.contribute-buttons');
    if (buttons) {
        noAtfContainer.insertBefore(explanation, buttons);
    } else {
        noAtfContainer.appendChild(explanation);
    }
}

// Show popup with sign information
function showSignPopup(anno, targetEl) {
    // Remove any existing popup
    const existingPopup = document.querySelector('.glossary-popup');
    if (existingPopup) existingPopup.remove();

    const popup = document.createElement('div');
    popup.className = 'glossary-popup';
    popup.innerHTML = `
        <div class="popup-header">
            <strong>MZL ${anno.sign || '?'}</strong>
            ${anno.surface ? `<span class="popup-pos">${anno.surface}</span>` : ''}
        </div>
        <div class="popup-definition">
            Position: (${anno.x.toFixed(1)}%, ${anno.y.toFixed(1)}%)
        </div>
        <div class="popup-citation">Source: ${anno.source}</div>
    `;

    // Position popup
    const rect = targetEl.getBoundingClientRect();
    popup.style.position = 'fixed';
    popup.style.left = `${Math.min(rect.right + 5, window.innerWidth - 250)}px`;
    popup.style.top = `${rect.top}px`;

    document.body.appendChild(popup);

    // Close on click outside
    setTimeout(() => {
        document.addEventListener('click', function closePopup(e) {
            if (!popup.contains(e.target)) {
                popup.remove();
                document.removeEventListener('click', closePopup);
            }
        });
    }, 100);
}

// Cache thumbnail in background when viewing from CDLI
function cacheThumbnail() {
    if (!TabletPage.pNumber) return;
    // Prefetch thumbnail to cache it for list views
    const thumbnailUrl = `/api/thumbnail.php?p=${TabletPage.pNumber}&size=200`;
    fetch(thumbnailUrl, { method: 'GET' })
        .then(response => {
            if (response.ok) {
                console.log('Thumbnail cached for', TabletPage.pNumber);
            }
        })
        .catch(() => {
            // Silent fail - thumbnail caching is non-critical
        });
}

// Fetch ATF from CDLI API
function fetchATFFromCDLI() {
    if (!TabletPage.pNumber) return;

    const container = document.getElementById('atf-container');
    const loading = document.getElementById('atf-loading');

    if (loading) loading.style.display = 'block';

    fetch(`/api/atf.php?p=${TabletPage.pNumber}&fetch=1`)
        .then(response => response.json())
        .then(data => {
            if (data.atf) {
                // Format and display ATF
                const formattedATF = formatATF(data.atf);
                container.innerHTML = `
                    <div class="atf-display">${formattedATF}</div>
                    <p class="atf-source">Source: ${data.source} (just fetched)</p>
                `;
                // Update pipeline indicator
                const atfDot = document.querySelector('.pipeline-stage:nth-child(3) .stage-icon');
                if (atfDot) {
                    atfDot.classList.remove('missing');
                    atfDot.classList.add('complete');
                    atfDot.textContent = '✓';
                }
            } else {
                container.innerHTML = `
                    <div class="no-atf">
                        <p>ATF not available from CDLI</p>
                        <p class="hint">This tablet may not have been digitized yet.</p>
                    </div>
                `;
            }
        })
        .catch(err => {
            container.innerHTML = `
                <div class="no-atf">
                    <p>Failed to fetch ATF: ${err.message}</p>
                </div>
            `;
        });
}

// Load tablets from composite
function loadCompositeTablets(qNumber) {
    if (!qNumber) return;

    const listContainer = document.getElementById('composite-list');
    const countBadge = document.getElementById('composite-count');

    fetch(`/api/composite.php?q=${encodeURIComponent(qNumber)}`)
        .then(response => {
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return response.json();
        })
        .then(data => {
            if (data.tablets && data.tablets.length > 0) {
                renderCompositeTablets(data.tablets, listContainer);
                if (countBadge) {
                    countBadge.textContent = `${data.tablets.length} tablet${data.tablets.length !== 1 ? 's' : ''}`;
                }
            } else {
                listContainer.innerHTML = '<div class="composite-panel__loading">No tablets found in composite</div>';
            }
        })
        .catch(err => {
            console.error('Failed to load composite tablets:', err);
            listContainer.innerHTML = '<div class="composite-panel__loading">Failed to load tablets</div>';
        });
}

// Render composite tablets in horizontal list
function renderCompositeTablets(tablets, container) {
    const currentPNumber = TabletPage.pNumber;

    const html = tablets.map(tablet => {
        const isCurrent = tablet.p_number === currentPNumber;
        const thumbnailUrl = `/api/thumbnail.php?p=${tablet.p_number}&size=200`;

        return `
            <a href="/tablets/detail.php?p=${tablet.p_number}"
               class="composite-tablet-item ${isCurrent ? 'is-current' : ''}"
               data-p-number="${tablet.p_number}">
                <div class="composite-tablet-item__thumbnail">
                    ${tablet.has_image ? `<img src="${thumbnailUrl}" alt="${tablet.designation || tablet.p_number}">` : `<div class="composite-tablet-item__placeholder">𒀭</div>`}
                </div>
                <div class="composite-tablet-item__info">
                    <div class="composite-tablet-item__pnumber">${tablet.p_number}</div>
                    <div class="composite-tablet-item__designation">${tablet.designation || tablet.period || 'Unknown'}</div>
                </div>
            </a>
        `;
    }).join('');

    container.innerHTML = html;

    // Scroll to current tablet
    if (currentPNumber) {
        setTimeout(() => {
            const currentItem = container.querySelector('.is-current');
            if (currentItem) {
                currentItem.scrollIntoView({ behavior: 'smooth', block: 'nearest', inline: 'center' });
            }
        }, 100);
    }
}

// Format ATF with syntax highlighting
function formatATF(atf) {
    return atf.split('\n').map(line => {
        line = line.trim();
        const escaped = line.replace(/</g, '&lt;').replace(/>/g, '&gt;');
        if (line.startsWith('&') || line.startsWith('@') || line.startsWith('#') || line.startsWith('$')) {
            return `<span class="directive">${escaped}</span>`;
        } else if (line.startsWith('>>')) {
            return `<span class="composite-ref">${escaped}</span>`;
        }
        return escaped;
    }).join('\n');
}
