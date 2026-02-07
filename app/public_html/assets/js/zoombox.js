/**
 * Zoombox - Cuneiform Tablet Image Viewer
 *
 * A modular zoom/pan component with:
 * - Image loading with fallback chain
 * - OCR overlay support (percentage-based positioning)
 * - Minimap with viewport indicator
 * - Smooth transitions
 * - Touch/gesture support
 */

class Zoombox {
    constructor(container, options = {}) {
        // Container can be element or selector
        this.container = typeof container === 'string'
            ? document.querySelector(container)
            : container;

        if (!this.container) {
            console.error('[Zoombox] Container not found');
            return;
        }

        // Options with defaults
        this.options = {
            minScale: 0.5,          // Will be recalculated to fit
            maxScale: 5,
            zoomStep: 0.15,
            hoverThreshold: 2,      // Enable hover popups above this zoom level
            onImageLoad: null,      // Callback when image loads
            onImageError: null,     // Callback when all sources fail
            onZoomChange: null,     // Callback on zoom/pan change
            onOverlayClick: null,   // Callback when overlay box is clicked
            ...options
        };

        // State
        this.scale = 1;
        this.coverScale = 1;  // Reference scale for 100% display
        this.panX = 0;
        this.panY = 0;
        this.imageLoaded = false;
        this.naturalWidth = 0;
        this.naturalHeight = 0;

        // Drag state
        this.isDragging = false;
        this.dragStart = { x: 0, y: 0 };
        this.panStart = { x: 0, y: 0 };

        // Minimap drag state
        this.isMinimapDragging = false;

        // Touch state
        this.lastTouchDist = 0;
        this.lastTouchCenter = { x: 0, y: 0 };

        // DOM refs (set in init)
        this.viewport = null;
        this.transform = null;
        this.image = null;
        this.overlays = null;
        this.loading = null;
        this.placeholder = null;
        this.minimap = null;
        this.minimapCanvas = null;
        this.minimapViewport = null;
        this.levelDisplay = null;
        this.btnZoomIn = null;
        this.btnZoomOut = null;

        // Initialize
        this._init();
    }

    // =========================================================================
    // Initialization
    // =========================================================================

    _init() {
        this._cacheElements();
        this._bindEvents();
        this.container.classList.add('is-loading');
    }

    _cacheElements() {
        this.viewport = this.container.querySelector('.zoombox__viewport');
        this.transform = this.container.querySelector('.zoombox__transform');
        this.image = this.container.querySelector('.zoombox__image');
        this.overlays = this.container.querySelector('.zoombox__overlays');
        this.loading = this.container.querySelector('.zoombox__loading');
        this.placeholder = this.container.querySelector('.zoombox__placeholder');
        this.minimap = this.container.querySelector('.zoombox__minimap');
        this.minimapCanvas = this.container.querySelector('.zoombox__minimap-canvas');
        this.minimapViewport = this.container.querySelector('.zoombox__minimap-viewport');
        this.btnZoomIn = this.container.querySelector('[data-action="zoom-in"]');
        this.btnZoomOut = this.container.querySelector('[data-action="zoom-out"]');
    }

    _bindEvents() {
        if (!this.viewport) return;

        // Wheel zoom
        this.viewport.addEventListener('wheel', this._onWheel.bind(this), { passive: false });

        // Pan drag (mouse)
        this.viewport.addEventListener('mousedown', this._onMouseDown.bind(this));
        document.addEventListener('mousemove', this._onMouseMove.bind(this));
        document.addEventListener('mouseup', this._onMouseUp.bind(this));

        // Touch support
        this.viewport.addEventListener('touchstart', this._onTouchStart.bind(this), { passive: true });
        this.viewport.addEventListener('touchmove', this._onTouchMove.bind(this), { passive: false });
        this.viewport.addEventListener('touchend', this._onTouchEnd.bind(this));

        // Zoom buttons
        this.btnZoomIn?.addEventListener('click', () => this.zoomIn());
        this.btnZoomOut?.addEventListener('click', () => this.zoomOut());
        this.container.querySelector('[data-action="reset"]')?.addEventListener('click', () => this.reset());

        // Minimap interactions
        if (this.minimap) {
            this.minimap.addEventListener('mousedown', this._onMinimapMouseDown.bind(this));
        }

        // Keyboard
        this.viewport.setAttribute('tabindex', '0');
        this.viewport.addEventListener('keydown', this._onKeyDown.bind(this));

        // Window resize
        window.addEventListener('resize', this._onResize.bind(this));
    }

    // =========================================================================
    // Image Loading
    // =========================================================================

    /**
     * Load image with fallback chain
     * @param {Object} sources - { local, cdliPhoto, cdliLineart }
     */
    async loadImage(sources) {
        this.container.classList.add('is-loading');
        this.container.classList.remove('is-placeholder');

        const chain = [sources.local, sources.cdliPhoto, sources.cdliLineart].filter(Boolean);

        for (const src of chain) {
            try {
                const result = await this._tryLoadImage(src);
                // Pass dimensions from the test image (which has loaded)
                this._onImageLoaded(result.width, result.height);
                return true;
            } catch (e) {
                // Continue to next source
            }
        }

        // All sources failed
        this._showPlaceholder();
        return false;
    }

    _tryLoadImage(src) {
        return new Promise((resolve, reject) => {
            const testImg = new Image();
            testImg.onload = () => {
                this.image.src = src;
                // Return dimensions from the loaded test image
                // (the DOM image hasn't loaded yet, just started)
                resolve({
                    src,
                    width: testImg.naturalWidth,
                    height: testImg.naturalHeight
                });
            };
            testImg.onerror = () => reject(new Error('Failed to load: ' + src));
            testImg.src = src;
        });
    }

    _onImageLoaded(width, height) {
        this.imageLoaded = true;
        this.naturalWidth = width;
        this.naturalHeight = height;

        // Set explicit dimensions on both transform layer AND image
        // This ensures the image can render at full natural size before transform
        this.transform.style.width = width + 'px';
        this.transform.style.height = height + 'px';
        this.image.style.width = width + 'px';
        this.image.style.height = height + 'px';

        // Double rAF ensures layout is fully complete before measuring
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                // Calculate and apply cover scale
                this._calculateFitScale();
                this.transform.style.transition = 'none';
                this._updateTransform();
                this._updateMinimap();

                // Force a reflow
                this.transform.offsetHeight;

                // Show the image
                this.image.classList.remove('is-loading');
                this.image.classList.add('is-loaded');
                this.container.classList.remove('is-loading');
                this.container.classList.remove('is-placeholder');

                // Re-enable transitions
                requestAnimationFrame(() => {
                    this.transform.style.transition = '';
                });

                // Callback
                if (this.options.onImageLoad) {
                    this.options.onImageLoad(this.image);
                }
            });
        });
    }

    _showPlaceholder() {
        this.imageLoaded = false;
        this.container.classList.remove('is-loading');
        this.container.classList.add('is-placeholder');
        this.image.classList.add('is-error');

        if (this.options.onImageError) {
            this.options.onImageError();
        }
    }

    // =========================================================================
    // Zoom / Pan
    // =========================================================================

    _calculateFitScale() {
        if (!this.viewport || !this.naturalWidth || !this.naturalHeight) return;

        const viewportRect = this.viewport.getBoundingClientRect();
        if (viewportRect.width === 0 || viewportRect.height === 0) return;

        const scaleToFitWidth = viewportRect.width / this.naturalWidth;
        const scaleToFitHeight = viewportRect.height / this.naturalHeight;

        // minScale = contain (see whole image), coverScale = fill viewport
        this.options.minScale = Math.min(scaleToFitWidth, scaleToFitHeight);
        this.coverScale = Math.max(scaleToFitWidth, scaleToFitHeight);
        this.scale = this.coverScale;

        // Pan values directly position image top-left in viewport
        // Center: place scaled image center at viewport center
        const scaledWidth = this.naturalWidth * this.scale;
        const scaledHeight = this.naturalHeight * this.scale;
        this.panX = (viewportRect.width - scaledWidth) / 2;
        this.panY = (viewportRect.height - scaledHeight) / 2;

    }

    zoomAt(viewportX, viewportY, delta) {
        const oldScale = this.scale;
        const newScale = Math.max(this.options.minScale, Math.min(this.options.maxScale, oldScale + delta));

        if (newScale === oldScale) return;

        const ratio = newScale / oldScale;

        // Keep the point under cursor stationary (established formula from panzoom libraries)
        this.panX = viewportX - ratio * (viewportX - this.panX);
        this.panY = viewportY - ratio * (viewportY - this.panY);
        this.scale = newScale;

        this._clampPan();
        this._updateTransform();
    }

    zoomIn() {
        const rect = this.viewport.getBoundingClientRect();
        this.zoomAt(rect.width / 2, rect.height / 2, this.options.zoomStep);
    }

    zoomOut() {
        const rect = this.viewport.getBoundingClientRect();
        this.zoomAt(rect.width / 2, rect.height / 2, -this.options.zoomStep);
    }

    reset() {
        this._calculateFitScale();
        this._updateTransform();
    }

    /**
     * Recalculate dimensions and reset zoom (public method)
     * Use this when the container size changes (e.g., layout toggle)
     */
    resetZoom() {
        if (!this.imageLoaded) return;

        // Recalculate cover scale for new container size
        const vpWidth = this.viewport.offsetWidth;
        const vpHeight = this.viewport.offsetHeight;

        const scaleX = vpWidth / this.naturalWidth;
        const scaleY = vpHeight / this.naturalHeight;
        this.coverScale = Math.max(scaleX, scaleY);
        this.options.minScale = this.coverScale * 0.5;

        // Reset to fit and center
        this.scale = this.coverScale;
        const scaledWidth = this.naturalWidth * this.scale;
        const scaledHeight = this.naturalHeight * this.scale;
        this.panX = (vpWidth - scaledWidth) / 2;
        this.panY = (vpHeight - scaledHeight) / 2;

        this._clampPan();
        this._updateTransform();
        this._updateMinimap();
    }

    panBy(dx, dy) {
        this.panX += dx;
        this.panY += dy;
        this._clampPan();
        this._updateTransform();
    }

    _clampPan() {
        if (!this.viewport || !this.naturalWidth) return;

        const viewportRect = this.viewport.getBoundingClientRect();
        const scaledWidth = this.naturalWidth * this.scale;
        const scaledHeight = this.naturalHeight * this.scale;

        // If image larger than viewport: edges must not leave viewport
        // If image smaller than viewport: center it
        if (scaledWidth >= viewportRect.width) {
            const maxX = 0;  // Left edge at most at x=0
            const minX = viewportRect.width - scaledWidth;  // Right edge at least at viewport right
            this.panX = Math.max(minX, Math.min(maxX, this.panX));
        } else {
            this.panX = (viewportRect.width - scaledWidth) / 2;  // Center
        }

        if (scaledHeight >= viewportRect.height) {
            const maxY = 0;
            const minY = viewportRect.height - scaledHeight;
            this.panY = Math.max(minY, Math.min(maxY, this.panY));
        } else {
            this.panY = (viewportRect.height - scaledHeight) / 2;
        }
    }

    _updateTransform() {
        if (!this.transform) return;

        // Direct transform: panX/panY are the translate values
        this.transform.style.transform = `translate(${this.panX}px, ${this.panY}px) scale(${this.scale})`;

        // Update zoomed state class
        const isZoomed = this.scale > this.options.minScale;
        this.container.classList.toggle('is-zoomed', isZoomed);
        this.viewport?.classList.toggle('is-zoomed', isZoomed);

        // Update button states
        this.btnZoomIn?.toggleAttribute('disabled', this.scale >= this.options.maxScale);
        this.btnZoomOut?.toggleAttribute('disabled', this.scale <= this.options.minScale);

        // Update hover mode for overlays
        this._updateHoverMode();

        // Update minimap
        this._updateMinimap();

        // Callback
        if (this.options.onZoomChange) {
            this.options.onZoomChange({ scale: this.scale, panX: this.panX, panY: this.panY });
        }
    }

    // =========================================================================
    // Minimap
    // =========================================================================

    _updateMinimap() {
        if (!this.minimapCanvas || !this.minimapViewport || !this.imageLoaded) return;

        const ctx = this.minimapCanvas.getContext('2d');
        const canvas = this.minimapCanvas;

        // Draw image to canvas
        if (this.image.complete && this.naturalWidth > 0) {
            const aspectRatio = this.naturalWidth / this.naturalHeight;
            const containerWidth = 100;  // Reduced from 120
            const containerHeight = 67;   // Maintain 3:2 aspect ratio (100 * 2/3)

            if (aspectRatio > containerWidth / containerHeight) {
                canvas.width = containerWidth;
                canvas.height = containerWidth / aspectRatio;
            } else {
                canvas.height = containerHeight;
                canvas.width = containerHeight * aspectRatio;
            }

            ctx.drawImage(this.image, 0, 0, canvas.width, canvas.height);
        }

        // Update viewport indicator for new coordinate system
        const viewportRect = this.viewport.getBoundingClientRect();

        // Visible area in image coordinates (panX/panY are top-left position)
        const visibleLeft = -this.panX / this.scale;
        const visibleTop = -this.panY / this.scale;
        const visibleWidth = viewportRect.width / this.scale;
        const visibleHeight = viewportRect.height / this.scale;

        // As percentages of natural image dimensions
        const leftPct = Math.max(0, (visibleLeft / this.naturalWidth) * 100);
        const topPct = Math.max(0, (visibleTop / this.naturalHeight) * 100);
        const widthPct = Math.min(100, (visibleWidth / this.naturalWidth) * 100);
        const heightPct = Math.min(100, (visibleHeight / this.naturalHeight) * 100);

        this.minimapViewport.style.left = leftPct + '%';
        this.minimapViewport.style.top = topPct + '%';
        this.minimapViewport.style.width = widthPct + '%';
        this.minimapViewport.style.height = heightPct + '%';
    }

    // =========================================================================
    // Overlays (OCR annotations)
    // =========================================================================

    /**
     * Set overlay annotations
     * @param {Array} annotations - Array of { x, y, width, height, sign, surface, source }
     *                              x, y, width, height are percentages (0-100)
     */
    setOverlays(annotations) {
        if (!this.overlays) return;

        this.overlays.innerHTML = '';

        if (!annotations || !annotations.length) {
            this.overlays.classList.remove('is-active');
            return;
        }

        // Size overlay to match natural image dimensions
        this.overlays.style.width = this.naturalWidth + 'px';
        this.overlays.style.height = this.naturalHeight + 'px';

        annotations.forEach(anno => {
            const box = document.createElement('div');
            box.className = 'zoombox__overlay-box';

            // Percentage-based positioning (scales with transform)
            box.style.left = `${anno.x}%`;
            box.style.top = `${anno.y}%`;
            box.style.width = `${anno.width}%`;
            box.style.height = `${anno.height}%`;

            // Data attributes
            box.dataset.sign = anno.sign || '';
            box.dataset.surface = anno.surface || '';
            box.dataset.source = anno.source || '';
            box.title = `MZL ${anno.sign}` + (anno.surface ? ` (${anno.surface})` : '');

            // Click handler
            box.addEventListener('click', (e) => {
                e.stopPropagation();
                if (this.options.onOverlayClick) {
                    this.options.onOverlayClick(anno, box);
                }
            });

            // Hover handlers for zoomed state
            box.addEventListener('mouseenter', () => {
                if (this.scale >= this.options.hoverThreshold && this.options.onOverlayClick) {
                    this.options.onOverlayClick(anno, box);
                }
            });

            this.overlays.appendChild(box);
        });

        this.overlays.classList.add('is-active');
    }

    clearOverlays() {
        if (!this.overlays) return;
        this.overlays.innerHTML = '';
        this.overlays.classList.remove('is-active');
    }

    _updateHoverMode() {
        if (!this.overlays) return;
        this.overlays.classList.toggle('is-hover-enabled', this.scale >= this.options.hoverThreshold);
    }

    // =========================================================================
    // Event Handlers - Mouse
    // =========================================================================

    _onWheel(e) {
        e.preventDefault();
        const delta = e.deltaY > 0 ? -0.08 : 0.08;
        const rect = this.viewport.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        this.zoomAt(x, y, delta);
    }

    _onMouseDown(e) {
        if (e.button !== 0) return;
        if (this.scale <= this.options.minScale) return;

        this.isDragging = true;
        this.dragStart = { x: e.clientX, y: e.clientY };
        this.panStart = { x: this.panX, y: this.panY };
        this.transform?.classList.add('is-dragging');
        this.viewport?.classList.add('is-dragging');
    }

    _onMouseMove(e) {
        if (this.isDragging) {
            const dx = e.clientX - this.dragStart.x;
            const dy = e.clientY - this.dragStart.y;
            this.panX = this.panStart.x + dx;
            this.panY = this.panStart.y + dy;
            this._clampPan();
            this._updateTransform();
        }

        if (this.isMinimapDragging) {
            this._minimapDrag(e);
        }
    }

    _onMouseUp() {
        this.isDragging = false;
        this.isMinimapDragging = false;
        this.transform?.classList.remove('is-dragging');
        this.viewport?.classList.remove('is-dragging');
    }

    // =========================================================================
    // Event Handlers - Minimap
    // =========================================================================

    _onMinimapMouseDown(e) {
        e.preventDefault();
        this.isMinimapDragging = true;
        this._minimapDrag(e);
    }

    _minimapDrag(e) {
        if (!this.minimapCanvas || !this.naturalWidth) return;

        const rect = this.minimapCanvas.getBoundingClientRect();
        const viewportRect = this.viewport.getBoundingClientRect();

        // Click position as fraction 0-1 of image
        const clickX = (e.clientX - rect.left) / rect.width;
        const clickY = (e.clientY - rect.top) / rect.height;

        // Target point in image coordinates
        const imageX = clickX * this.naturalWidth;
        const imageY = clickY * this.naturalHeight;

        // Calculate pan to put imageX,imageY at viewport center
        this.panX = viewportRect.width / 2 - imageX * this.scale;
        this.panY = viewportRect.height / 2 - imageY * this.scale;

        this._clampPan();
        this._updateTransform();
    }

    // =========================================================================
    // Event Handlers - Touch
    // =========================================================================

    _onTouchStart(e) {
        if (e.touches.length === 2) {
            // Pinch zoom
            this.lastTouchDist = this._getTouchDistance(e.touches);
            this.lastTouchCenter = this._getTouchCenter(e.touches);
        } else if (e.touches.length === 1 && this.scale > this.options.minScale) {
            // Pan
            this.isDragging = true;
            this.dragStart = { x: e.touches[0].clientX, y: e.touches[0].clientY };
            this.panStart = { x: this.panX, y: this.panY };
            this.transform?.classList.add('is-dragging');
        }
    }

    _onTouchMove(e) {
        if (e.touches.length === 2) {
            e.preventDefault();
            const dist = this._getTouchDistance(e.touches);
            const center = this._getTouchCenter(e.touches);
            const rect = this.viewport.getBoundingClientRect();
            const delta = (dist - this.lastTouchDist) / 200;
            this.zoomAt(center.x - rect.left, center.y - rect.top, delta);
            this.lastTouchDist = dist;
            this.lastTouchCenter = center;
        } else if (e.touches.length === 1 && this.isDragging) {
            const dx = e.touches[0].clientX - this.dragStart.x;
            const dy = e.touches[0].clientY - this.dragStart.y;
            this.panX = this.panStart.x + dx;
            this.panY = this.panStart.y + dy;
            this._clampPan();
            this._updateTransform();
        }
    }

    _onTouchEnd() {
        this.isDragging = false;
        this.transform?.classList.remove('is-dragging');
    }

    _getTouchDistance(touches) {
        const dx = touches[0].clientX - touches[1].clientX;
        const dy = touches[0].clientY - touches[1].clientY;
        return Math.sqrt(dx * dx + dy * dy);
    }

    _getTouchCenter(touches) {
        return {
            x: (touches[0].clientX + touches[1].clientX) / 2,
            y: (touches[0].clientY + touches[1].clientY) / 2
        };
    }

    // =========================================================================
    // Event Handlers - Keyboard
    // =========================================================================

    _onKeyDown(e) {
        const step = 50;
        switch (e.key) {
            case '+':
            case '=':
                this.zoomIn();
                e.preventDefault();
                break;
            case '-':
                this.zoomOut();
                e.preventDefault();
                break;
            case '0':
            case 'Escape':
                this.reset();
                e.preventDefault();
                break;
            case 'ArrowUp':
                this.panBy(0, step);
                e.preventDefault();
                break;
            case 'ArrowDown':
                this.panBy(0, -step);
                e.preventDefault();
                break;
            case 'ArrowLeft':
                this.panBy(step, 0);
                e.preventDefault();
                break;
            case 'ArrowRight':
                this.panBy(-step, 0);
                e.preventDefault();
                break;
        }
    }

    // =========================================================================
    // Event Handlers - Resize
    // =========================================================================

    _onResize() {
        if (!this.imageLoaded) return;

        clearTimeout(this._resizeTimer);
        this._resizeTimer = setTimeout(() => {
            const viewportRect = this.viewport.getBoundingClientRect();
            if (viewportRect.width === 0) return;

            const scaleToFitWidth = viewportRect.width / this.naturalWidth;
            const scaleToFitHeight = viewportRect.height / this.naturalHeight;

            const oldCoverScale = this.coverScale;
            this.options.minScale = Math.min(scaleToFitWidth, scaleToFitHeight);
            this.coverScale = Math.max(scaleToFitWidth, scaleToFitHeight);

            // Maintain relative zoom level
            if (oldCoverScale > 0) {
                const relativeZoom = this.scale / oldCoverScale;
                this.scale = Math.max(this.options.minScale, relativeZoom * this.coverScale);
            }

            // Recenter at new scale
            const scaledWidth = this.naturalWidth * this.scale;
            const scaledHeight = this.naturalHeight * this.scale;
            this.panX = (viewportRect.width - scaledWidth) / 2;
            this.panY = (viewportRect.height - scaledHeight) / 2;

            this._clampPan();
            this._updateTransform();
        }, 100);
    }

    // =========================================================================
    // Public Methods
    // =========================================================================

    /**
     * Get current state
     */
    getState() {
        return {
            scale: this.scale,
            coverScale: this.coverScale,
            panX: this.panX,
            panY: this.panY,
            minScale: this.options.minScale,
            maxScale: this.options.maxScale,
            imageLoaded: this.imageLoaded,
            naturalWidth: this.naturalWidth,
            naturalHeight: this.naturalHeight
        };
    }

    /**
     * Destroy instance and clean up event listeners
     */
    destroy() {
        window.removeEventListener('resize', this._onResize.bind(this));
        document.removeEventListener('mousemove', this._onMouseMove.bind(this));
        document.removeEventListener('mouseup', this._onMouseUp.bind(this));
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = Zoombox;
}
