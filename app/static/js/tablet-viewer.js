/**
 * TabletViewer — sign-annotation overlay controller for the tablet detail page.
 *
 * PRD-005 (#58). This is the *annotation + surface* layer that sits on top of the
 * existing Zoombox component (zoombox.js, which owns image loading, zoom, pan,
 * minimap and the raw overlay-box DOM). TabletViewer does NOT re-implement
 * zoom/pan/minimap — it drives Zoombox.setOverlays() with the right data.
 *
 * Responsibilities:
 *   1. Fetch /artifacts/{p}/sign-annotations once, group by surface_type.
 *   2. Render only the annotations for the *currently displayed surface*
 *      (the raw endpoint returns obverse + reverse + edges together; drawing
 *      them all onto one image was the original overlay bug).
 *   3. Convert the stored bounding boxes into percentages for Zoombox.
 *   4. Build hover tooltips (sign name + MeZL number when present).
 *   5. Emit a `sign:selected` CustomEvent on click so the Translation Builder
 *      can highlight the matching token once token linkage data exists.
 *   6. Persist the viewer collapsed/expanded state to localStorage (FR13).
 *
 * ── Coordinate system (verified against live data 2026-06, P204982) ──────────
 * The schema yaml *describes* bbox_x/y/w/h as "0-100%", but the CompVis import
 * actually stored ABSOLUTE PIXEL coordinates (e.g. bbox_x=2856, bbox_w=267) —
 * matching the CompVis source `bbox: absolute [x1,y1,x2,y2]`. So we normalise to
 * percentages by dividing by the annotated image's pixel dimensions.
 *
 * surface_images.image_width/height are NULL in the current data, so we fall
 * back to the loaded image's naturalWidth/Height. This is correct *only when the
 * served image matches the CompVis source resolution*. If a tablet renders boxes
 * that are offset/scaled, that is the symptom of /image/{p} serving a different
 * composite than the one CompVis annotated — a backend image-per-surface gap,
 * not a bug in this file. AUTODETECT below guards the worst case: values that are
 * already <= 100 for every box are treated as pre-normalised percentages.
 */

(function (global) {
    'use strict';

    const STORAGE_KEY_PREFIX = 'glintstone:tablet-viewer:collapsed:';

    class TabletViewer {
        /**
         * @param {Object} opts
         * @param {Zoombox} opts.zoombox   - the live Zoombox instance to drive
         * @param {string}  opts.apiUrl    - API base (e.g. "/api/v2")
         * @param {string}  opts.pNumber   - artifact P-number
         */
        constructor(opts = {}) {
            this.zoombox = opts.zoombox || null;
            this.apiUrl = opts.apiUrl || '';
            this.pNumber = opts.pNumber || null;

            // annotationsBySurface: { obverse: [...], reverse: [...] }
            this.annotationsBySurface = {};
            this.surfaceOrder = [];
            this.currentSurface = null;
            this._loaded = false;

            this._onOverlayClick = this._onOverlayClick.bind(this);
        }

        // ── Public API ───────────────────────────────────────────────────────

        /** Fetch annotations and render the first/primary surface. */
        async load() {
            if (!this.zoombox || !this.apiUrl || !this.pNumber) return;

            let data;
            try {
                const res = await fetch(
                    `${this.apiUrl}/artifacts/${this.pNumber}/sign-annotations`
                );
                if (!res.ok) return;
                data = await res.json();
            } catch (err) {
                // Non-fatal: a tablet may simply have no OCR annotations.
                console.debug('[TabletViewer] no sign annotations:', err && err.message);
                return;
            }

            const annotations = (data && data.annotations) || [];
            if (!annotations.length) return;

            this.annotationsBySurface = this._groupBySurface(annotations);
            this.surfaceOrder = Object.keys(this.annotationsBySurface);
            this._loaded = true;

            // Hook the click handler once.
            if (this.zoombox.options) {
                this.zoombox.options.onOverlayClick = this._onOverlayClick;
            }

            // Render whichever surface is currently showing, or the first one.
            const initial = this.currentSurface || this.surfaceOrder[0];
            this.showSurface(initial);
        }

        /**
         * Switch the overlay to a given surface (obverse / reverse / edges).
         * Call this when the surface image carousel changes the visible image.
         * @param {string} surfaceType
         */
        showSurface(surfaceType) {
            if (!this._loaded || !this.zoombox) return;

            // Normalise: the carousel may report "Obverse" / "obverse" / "obv".
            const key = this._matchSurfaceKey(surfaceType);
            this.currentSurface = key;

            const anns = key ? this.annotationsBySurface[key] : null;
            if (!anns || !anns.length) {
                this.zoombox.clearOverlays();
                return;
            }
            const overlays = this._toOverlays(anns);
            this.zoombox.setOverlays(overlays);
            this._markLowConfidence(overlays);
        }

        /**
         * Zoombox renders boxes in DOM order; flag low-confidence detections
         * (dashed border) after render. Confidence < 0.5 is treated as low.
         */
        _markLowConfidence(overlays) {
            if (!this.zoombox.overlays) return;
            const boxes = this.zoombox.overlays.querySelectorAll('.zoombox__overlay-box');
            boxes.forEach((box, i) => {
                const raw = overlays[i] && overlays[i]._raw;
                const conf = raw && raw.confidence != null ? raw.confidence : 1;
                box.classList.toggle('is-low-confidence', conf < 0.5);
            });
        }

        /** Re-render the current surface (e.g. after the image reloads). */
        refresh() {
            if (this.currentSurface) this.showSurface(this.currentSurface);
        }

        // ── Collapse/expand persistence (FR13) ───────────────────────────────

        storageKey() {
            return STORAGE_KEY_PREFIX + (this.pNumber || 'default');
        }

        getStoredCollapsed() {
            try {
                return global.localStorage.getItem(this.storageKey()) === '1';
            } catch (_) {
                return false;
            }
        }

        setStoredCollapsed(collapsed) {
            try {
                global.localStorage.setItem(this.storageKey(), collapsed ? '1' : '0');
            } catch (_) {
                /* storage unavailable (private mode) — non-fatal */
            }
        }

        // ── Internals ────────────────────────────────────────────────────────

        _groupBySurface(annotations) {
            const groups = {};
            for (const a of annotations) {
                const surface = a.surface_type || 'unknown';
                (groups[surface] = groups[surface] || []).push(a);
            }
            return groups;
        }

        _matchSurfaceKey(surfaceType) {
            if (!surfaceType) return this.surfaceOrder[0] || null;
            const want = String(surfaceType).toLowerCase();
            // exact
            for (const k of this.surfaceOrder) {
                if (k.toLowerCase() === want) return k;
            }
            // prefix (obv -> obverse, rev -> reverse)
            for (const k of this.surfaceOrder) {
                if (k.toLowerCase().startsWith(want) || want.startsWith(k.toLowerCase())) {
                    return k;
                }
            }
            return this.surfaceOrder[0] || null;
        }

        /**
         * Convert stored bounding boxes to Zoombox overlay objects (percentages).
         * See coordinate-system note in the file header.
         */
        _toOverlays(anns) {
            const natW = this.zoombox.naturalWidth || 0;
            const natH = this.zoombox.naturalHeight || 0;

            // Detect whether values are already normalised percentages (0-100)
            // or absolute pixels. If every box fits within 0-100 on both axes,
            // treat as percentages; otherwise treat as pixels and divide by the
            // natural image dimensions.
            const alreadyPercent = anns.every(
                (a) =>
                    a.bbox_x <= 100 &&
                    a.bbox_y <= 100 &&
                    a.bbox_x + a.bbox_w <= 100.5 &&
                    a.bbox_y + a.bbox_h <= 100.5
            );

            const toPct = (val, dim) => {
                if (alreadyPercent) return val;
                if (!dim) return val; // no dimension known — best effort
                return (val / dim) * 100;
            };

            return anns.map((a) => {
                const sign = a.sign_id || '';
                const mzl = a.mzl_number != null ? a.mzl_number : null;
                return {
                    x: toPct(a.bbox_x, natW),
                    y: toPct(a.bbox_y, natH),
                    width: toPct(a.bbox_w, natW),
                    height: toPct(a.bbox_h, natH),
                    sign: this._tooltipLabel(sign, mzl),
                    surface: a.surface_type || '',
                    source: a.source || 'compvis',
                    // carry raw fields for the sign:selected payload
                    _raw: a,
                };
            });
        }

        _tooltipLabel(sign, mzl) {
            if (sign && mzl != null) return `${sign} · MZL ${mzl}`;
            return sign || '';
        }

        /**
         * Bridge a Zoombox overlay click to a DOM `sign:selected` event.
         * Payload includes token_id when the backend ever populates it (FR11/12).
         */
        _onOverlayClick(anno, boxEl) {
            const raw = (anno && anno._raw) || {};

            // visual: mark the clicked box highlighted, clear siblings
            if (boxEl && boxEl.parentElement) {
                boxEl.parentElement
                    .querySelectorAll('.zoombox__overlay-box.is-selected')
                    .forEach((el) => el.classList.remove('is-selected'));
                boxEl.classList.add('is-selected');
            }

            const detail = {
                signId: raw.sign_id || null,
                tokenId: raw.token_id != null ? raw.token_id : null, // null until backend adds it
                surface: raw.surface_type || null,
                lineNumber: raw.line_number != null ? raw.line_number : null,
                positionInLine: raw.position_in_line != null ? raw.position_in_line : null,
                pNumber: this.pNumber,
            };
            document.dispatchEvent(new CustomEvent('sign:selected', { detail }));
        }
    }

    global.TabletViewer = TabletViewer;

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = TabletViewer;
    }
})(typeof window !== 'undefined' ? window : globalThis);
