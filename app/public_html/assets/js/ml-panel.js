/**
 * ML Detection Panel
 * Handles cuneiform sign detection via local ML service
 *
 * Dependencies:
 * - TabletPage (from tablet-detail.js)
 * - Zoombox setOverlays method
 */

class MLPanel {
    constructor(options = {}) {
        this.pNumber = options.pNumber || null;
        this.container = options.container || null;
        this.zoombox = options.zoombox || null;

        this.state = 'idle'; // idle | loading | results | error
        this.results = null;
        this.originalAnnotations = null; // Store original annotations to restore on discard

        // Create panel element
        this.panel = null;
        this._createPanel();
    }

    _createPanel() {
        // Create panel container
        this.panel = document.createElement('div');
        this.panel.className = 'ml-panel';
        this.panel.dataset.state = 'hidden';

        this.panel.innerHTML = `
            <div class="ml-panel__header">
                <h3 class="ml-panel__title">Sign Detection</h3>
                <button class="btn btn--icon btn--ghost ml-panel__close" data-action="close" title="Close">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <line x1="18" y1="6" x2="6" y2="18"></line>
                        <line x1="6" y1="6" x2="18" y2="18"></line>
                    </svg>
                </button>
            </div>

            <div class="ml-panel__content">
                <!-- Loading state -->
                <div class="ml-panel__loading" data-view="loading">
                    <div class="ml-panel__spinner"></div>
                    <p class="ml-panel__loading-message">Detecting signs...</p>
                    <p class="ml-panel__loading-hint">First run may take 10-30 seconds to load model</p>
                    <p class="ml-panel__loading-elapsed" style="color: var(--text-secondary); font-size: 0.875rem; margin-top: 0.5rem;"></p>
                </div>

                <!-- Results state -->
                <div class="ml-panel__results" data-view="results" style="display: none;">
                    <div class="ml-panel__model-info" style="margin-bottom: 1rem; padding: 0.75rem; background: var(--surface-2); border-radius: 8px; font-size: 0.875rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                            <span style="color: var(--text-secondary);">Model:</span>
                            <span class="ml-panel__model-name" style="font-family: var(--font-mono); color: var(--text-primary);"></span>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.25rem;">
                            <span style="color: var(--text-secondary);">Inference Time:</span>
                            <span class="ml-panel__inference-time" style="color: var(--text-primary);"></span>
                        </div>
                        <div style="display: flex; justify-content: space-between;">
                            <span style="color: var(--text-secondary);">Device:</span>
                            <span class="ml-panel__device" style="color: var(--text-primary);"></span>
                        </div>
                    </div>
                    <div class="ml-panel__summary">
                        <span class="ml-panel__count"></span>
                        <span class="ml-panel__confidence"></span>
                        <span class="ml-panel__mock-badge" style="display: none;">Mock Data</span>
                    </div>
                    <div class="ml-panel__list-container">
                        <ul class="ml-panel__list"></ul>
                    </div>
                </div>

                <!-- Error state -->
                <div class="ml-panel__error" data-view="error" style="display: none;">
                    <div class="ml-panel__error-icon" style="font-size: 2rem; margin-bottom: 1rem;">⚠️</div>
                    <p class="ml-panel__error-message" style="margin-bottom: 1rem;"></p>
                    <p class="ml-panel__error-hint" style="color: var(--text-secondary); font-size: 0.875rem; margin-bottom: 1rem;"></p>
                    <button class="btn" data-action="retry">Retry</button>
                </div>
            </div>

            <div class="ml-panel__actions">
                <button class="btn" data-action="discard">Discard</button>
                <button class="btn btn--primary" data-action="save">Save to Database</button>
            </div>
        `;

        // Append to container or body
        if (this.container) {
            this.container.appendChild(this.panel);
        } else {
            document.body.appendChild(this.panel);
        }

        // Bind events
        this._bindEvents();
    }

    _bindEvents() {
        // Close button
        this.panel.querySelector('[data-action="close"]')?.addEventListener('click', () => {
            this.hide();
        });

        // Discard button
        this.panel.querySelector('[data-action="discard"]')?.addEventListener('click', () => {
            this.discard();
        });

        // Save button
        this.panel.querySelector('[data-action="save"]')?.addEventListener('click', () => {
            this.save();
        });

        // Retry button
        this.panel.querySelector('[data-action="retry"]')?.addEventListener('click', () => {
            this.detect();
        });

        // List item hover to highlight overlay
        this.panel.querySelector('.ml-panel__list')?.addEventListener('mouseover', (e) => {
            const item = e.target.closest('.ml-panel__item');
            if (item) {
                const index = parseInt(item.dataset.index, 10);
                this._highlightOverlay(index);
            }
        });

        this.panel.querySelector('.ml-panel__list')?.addEventListener('mouseout', (e) => {
            const item = e.target.closest('.ml-panel__item');
            if (item) {
                this._unhighlightOverlay();
            }
        });
    }

    show() {
        this.panel.dataset.state = 'visible';
    }

    hide() {
        this.panel.dataset.state = 'hidden';
        // Restore original annotations if we have results but didn't save
        if (this.results && this.originalAnnotations !== null) {
            this._restoreOriginalAnnotations();
        }
        this.results = null;
    }

    _setView(view) {
        // Hide all views
        this.panel.querySelectorAll('[data-view]').forEach(el => {
            el.style.display = 'none';
        });
        // Show requested view
        const viewEl = this.panel.querySelector(`[data-view="${view}"]`);
        if (viewEl) viewEl.style.display = '';

        // Show/hide actions based on view
        const actions = this.panel.querySelector('.ml-panel__actions');
        if (actions) {
            actions.style.display = view === 'results' ? '' : 'none';
        }
    }

    async detect() {
        if (!this.pNumber) {
            console.error('[MLPanel] No P-number set');
            return;
        }

        this.state = 'loading';
        this.show();
        this._setView('loading');

        // Store current annotations to restore on discard
        if (this.zoombox && typeof TabletPage !== 'undefined' && TabletPage.annotationData) {
            this.originalAnnotations = TabletPage.annotationData.annotations || [];
        } else {
            this.originalAnnotations = [];
        }

        // Track elapsed time
        const startTime = Date.now();
        let elapsedInterval = null;

        // Update elapsed time display
        const updateElapsed = () => {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const elapsedEl = this.panel.querySelector('.ml-panel__loading-elapsed');
            if (elapsedEl) {
                if (elapsed < 10) {
                    elapsedEl.textContent = `Initializing... (${elapsed}s)`;
                } else if (elapsed < 30) {
                    elapsedEl.textContent = `Loading model... (${elapsed}s)`;
                } else {
                    elapsedEl.textContent = `Running detection... (${elapsed}s)`;
                }
            }
        };

        updateElapsed();
        elapsedInterval = setInterval(updateElapsed, 1000);

        try {
            const response = await fetch(`/api/ml/detect-signs.php?p=${this.pNumber}`);

            clearInterval(elapsedInterval);

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const error = new Error(errorData.error || `HTTP ${response.status}`);
                error.detail = errorData;
                throw error;
            }

            const data = await response.json();

            if (!data.success) {
                throw new Error(data.error || 'Detection failed');
            }

            this.results = data;
            this.state = 'results';
            this._renderResults();
            this._applyOverlays();
            this._setView('results');

        } catch (err) {
            clearInterval(elapsedInterval);

            this.state = 'error';
            this._setView('error');

            const errorMessageEl = this.panel.querySelector('.ml-panel__error-message');
            const errorHintEl = this.panel.querySelector('.ml-panel__error-hint');

            // Enhanced error messages
            if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
                errorMessageEl.textContent = 'ML Service Not Running';
                errorHintEl.innerHTML = `
                    The local ML service is not responding. To start it:<br><br>
                    <code style="background: var(--surface-2); padding: 0.5rem; border-radius: 4px; display: block; font-family: var(--font-mono); font-size: 0.875rem;">
                    cd ml-service<br>
                    python app.py
                    </code>
                `;
            } else if (err.message.includes('No image')) {
                errorMessageEl.textContent = 'Image Not Available';
                errorHintEl.textContent = 'This tablet does not have an image file available for detection.';
            } else if (err.message.includes('Failed to download') || err.message.includes('too small') || err.message.includes('too large') || err.message.includes('not a valid image')) {
                errorMessageEl.textContent = 'Image Download Failed';
                errorHintEl.textContent = err.detail?.detail || 'The remote image could not be downloaded or is corrupted.';
            } else if (err.detail && err.detail.hint) {
                errorMessageEl.textContent = err.message;
                errorHintEl.textContent = err.detail.hint;
            } else {
                errorMessageEl.textContent = err.message;
                errorHintEl.textContent = 'Check the browser console for more details.';
            }

            console.error('[MLPanel] Detection failed:', err);
        }
    }

    _renderResults() {
        if (!this.results) return;

        const detections = this.results.detections || [];
        const isMock = detections.some(d => d.mock);

        // Model metadata
        const modelNameEl = this.panel.querySelector('.ml-panel__model-name');
        const inferenceTimeEl = this.panel.querySelector('.ml-panel__inference-time');
        const deviceEl = this.panel.querySelector('.ml-panel__device');

        if (modelNameEl && this.results.model_name) {
            modelNameEl.textContent = `${this.results.model_name} (epoch ${this.results.model_epoch || 'unknown'})`;
        }
        if (inferenceTimeEl && this.results.inference_time_ms) {
            inferenceTimeEl.textContent = `${this.results.inference_time_ms}ms`;
        }
        if (deviceEl && this.results.model_device) {
            deviceEl.textContent = this.results.model_device.toUpperCase();
        }

        // Summary
        const countEl = this.panel.querySelector('.ml-panel__count');
        const confEl = this.panel.querySelector('.ml-panel__confidence');
        const mockBadge = this.panel.querySelector('.ml-panel__mock-badge');

        if (countEl) {
            countEl.textContent = `${detections.length} signs detected`;
        }

        if (confEl && detections.length > 0) {
            const avgConf = detections.reduce((sum, d) => sum + d.confidence, 0) / detections.length;
            confEl.textContent = `Avg: ${(avgConf * 100).toFixed(0)}%`;
        }

        if (mockBadge) {
            mockBadge.style.display = isMock ? '' : 'none';
        }

        // List items
        const listEl = this.panel.querySelector('.ml-panel__list');
        if (!listEl) return;

        listEl.innerHTML = detections.map((det, idx) => `
            <li class="ml-panel__item" data-index="${idx}">
                <span class="ml-panel__item-sign">${det.unicode || ''}</span>
                <span class="ml-panel__item-name">${det.class_name}</span>
                <span class="ml-panel__item-confidence">${(det.confidence * 100).toFixed(0)}%</span>
            </li>
        `).join('');
    }

    _applyOverlays() {
        if (!this.zoombox || !this.results) return;

        const detections = this.results.detections || [];
        const imageWidth = this.results.image_width;
        const imageHeight = this.results.image_height;

        // Convert detections to overlay format
        // ML service returns bbox as [x_min, y_min, x_max, y_max] in pixels
        const annotations = detections.map(det => {
            const bbox = det.bbox || [];
            if (bbox.length !== 4) return null;

            // Convert to percentages
            const x = (bbox[0] / imageWidth) * 100;
            const y = (bbox[1] / imageHeight) * 100;
            const width = ((bbox[2] - bbox[0]) / imageWidth) * 100;
            const height = ((bbox[3] - bbox[1]) / imageHeight) * 100;

            return {
                x,
                y,
                width,
                height,
                sign: det.class_name,
                surface: 'obverse',
                source: 'ebl_ocr_preview'
            };
        }).filter(Boolean);

        this.zoombox.setOverlays(annotations);
    }

    _restoreOriginalAnnotations() {
        if (!this.zoombox) return;

        if (this.originalAnnotations && this.originalAnnotations.length > 0) {
            this.zoombox.setOverlays(this.originalAnnotations);
        } else {
            this.zoombox.clearOverlays();
        }
    }

    _highlightOverlay(index) {
        const overlays = this.zoombox?.overlays;
        if (!overlays) return;

        const boxes = overlays.querySelectorAll('.zoombox__overlay-box');
        boxes.forEach((box, i) => {
            box.classList.toggle('is-highlighted', i === index);
        });
    }

    _unhighlightOverlay() {
        const overlays = this.zoombox?.overlays;
        if (!overlays) return;

        overlays.querySelectorAll('.zoombox__overlay-box').forEach(box => {
            box.classList.remove('is-highlighted');
        });
    }

    async save() {
        if (!this.results || !this.pNumber) return;

        const saveBtn = this.panel.querySelector('[data-action="save"]');
        if (saveBtn) {
            saveBtn.disabled = true;
            saveBtn.classList.add('btn--loading');
            saveBtn.textContent = 'Saving...';
        }

        try {
            const response = await fetch('/api/ml/save-results.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    p_number: this.pNumber,
                    detections: this.results.detections,
                    source: 'ebl_ocr',
                    image_width: this.results.image_width,
                    image_height: this.results.image_height,
                    replace_existing: true
                })
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
                throw new Error(data.error || 'Save failed');
            }

            // Success - update UI
            this._showSaveSuccess(data.inserted);

            // Update TabletPage annotation data to match saved results
            if (typeof TabletPage !== 'undefined') {
                const detections = this.results.detections || [];
                const imageWidth = this.results.image_width;
                const imageHeight = this.results.image_height;

                TabletPage.annotationData = {
                    count: detections.length,
                    annotations: detections.map(det => {
                        const bbox = det.bbox || [];
                        return {
                            x: (bbox[0] / imageWidth) * 100,
                            y: (bbox[1] / imageHeight) * 100,
                            width: ((bbox[2] - bbox[0]) / imageWidth) * 100,
                            height: ((bbox[3] - bbox[1]) / imageHeight) * 100,
                            sign: det.class_name,
                            surface: 'obverse',
                            source: 'ebl_ocr'
                        };
                    })
                };
                TabletPage.annotationsVisible = true;

                // Update annotation toggle
                const toggle = document.getElementById('annotation-toggle');
                const countBadge = document.getElementById('annotation-count');
                const checkbox = document.getElementById('annotation-checkbox');

                if (toggle) toggle.style.display = 'flex';
                if (countBadge) countBadge.textContent = detections.length;
                if (checkbox) checkbox.checked = true;
            }

            // Clear results so discard doesn't restore
            this.originalAnnotations = null;
            this.results = null;

            // Hide panel after delay
            setTimeout(() => {
                this.hide();
            }, 1500);

        } catch (err) {
            console.error('[MLPanel] Save failed:', err);
            if (saveBtn) {
                saveBtn.disabled = false;
                saveBtn.classList.remove('btn--loading');
                saveBtn.textContent = 'Save to Database';
            }
            alert('Save failed: ' + err.message);
        }
    }

    _showSaveSuccess(count) {
        const content = this.panel.querySelector('.ml-panel__content');
        if (content) {
            content.innerHTML = `
                <div class="ml-panel__success">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="20 6 9 17 4 12"></polyline>
                    </svg>
                    <p>Saved ${count} annotations</p>
                </div>
            `;
        }

        const actions = this.panel.querySelector('.ml-panel__actions');
        if (actions) actions.style.display = 'none';
    }

    discard() {
        this._restoreOriginalAnnotations();
        this.results = null;
        this.hide();
    }

    destroy() {
        if (this.panel && this.panel.parentNode) {
            this.panel.parentNode.removeChild(this.panel);
        }
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MLPanel;
}
