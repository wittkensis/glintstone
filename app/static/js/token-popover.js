/**
 * TokenPopover
 * Inline popover anchored to a clicked ATF word token.
 * Shows lemma data (citation form, guide word, POS, language, source)
 * and a competing-readings indicator when multiple annotation runs disagree.
 *
 * Usage:
 *   TokenPopover.show(el, pNumber, lookup, surfaceForm, apiUrl, cache?)
 *
 * cache (optional): { lemmasData, competingData } — pre-loaded by ATFViewer
 *   to avoid redundant fetches. Falls back to fetching /lemmas and
 *   /competing-lemmas if not supplied.
 */
class TokenPopover {
    /** Currently open popover element, or null */
    static _current = null;
    /** The token element that owns the open popover */
    static _anchor = null;

    /**
     * Show a popover anchored to `el`.
     * If the same element is clicked again, dismiss instead (toggle).
     *
     * @param {Element} el         - .atf-word element that was clicked
     * @param {string}  pNumber    - Artifact P-number (e.g. "P123456")
     * @param {string}  lookup     - citation_form from data-lookup
     * @param {string}  surfaceForm - raw ATF text from data-surface-form
     * @param {string}  apiUrl     - API base URL (no trailing slash)
     * @param {Object}  [cache]    - { lemmasData, competingData } from ATFViewer
     */
    static show(el, pNumber, lookup, surfaceForm, apiUrl, cache = {}) {
        // Toggle off if the same token is clicked again
        if (TokenPopover._anchor === el) {
            TokenPopover.dismiss();
            return;
        }

        // Dismiss any previously open popover
        TokenPopover.dismiss();

        const popover = TokenPopover._build(surfaceForm);
        TokenPopover._current = popover;
        TokenPopover._anchor = el;

        // Anchor to the token element
        document.body.appendChild(popover);
        TokenPopover._position(popover, el);

        // Resolve lemma entry from pre-loaded cache or fetch
        TokenPopover._resolve(el, pNumber, lookup, apiUrl, cache)
            .then(({ lemmaEntry, competing }) => {
                TokenPopover._populate(popover, surfaceForm, lookup, lemmaEntry, competing);
                // Reposition after content is populated (height may change)
                TokenPopover._position(popover, el);
            })
            .catch(() => {
                // Silently leave the popover with just the surface form
            });

        // PRD-020: grounded AI token interpretation. The lexical panel above is
        // the primary, database-backed content; the AI interpretation is
        // supplementary and clearly labeled. It loads independently so a slow
        // (2-5 s) Claude call never blocks the lexical data, and a failure never
        // removes it. Only fires when the ATF render stamped a real token_id.
        const tokenId = el.dataset.tokenId;
        if (tokenId && tokenId !== '0' && /^\d+$/.test(tokenId)) {
            TokenPopover._fetchInterpretation(popover, el, pNumber, tokenId, apiUrl);
        }

        // Dismiss on outside click
        setTimeout(() => {
            document.addEventListener('click', TokenPopover._onDocClick, { capture: true, once: true });
        }, 0);

        // Dismiss on Escape
        document.addEventListener('keydown', TokenPopover._onEsc);
    }

    /**
     * Dismiss the currently open popover, if any.
     */
    static dismiss() {
        if (TokenPopover._current) {
            TokenPopover._current.remove();
            TokenPopover._current = null;
            TokenPopover._anchor = null;
        }
        document.removeEventListener('keydown', TokenPopover._onEsc);
        document.removeEventListener('click', TokenPopover._onDocClick, { capture: true });
    }

    // ── Private helpers ────────────────────────────────────────

    /** Outside-click handler — dismiss unless click is inside the popover */
    static _onDocClick = (e) => {
        if (TokenPopover._current && !TokenPopover._current.contains(e.target)) {
            TokenPopover.dismiss();
        }
    };

    /** Escape key handler */
    static _onEsc = (e) => {
        if (e.key === 'Escape') TokenPopover.dismiss();
    };

    /**
     * Build the initial popover shell (shown immediately, populated async).
     * @param {string} surfaceForm
     * @returns {Element}
     */
    static _build(surfaceForm) {
        const div = document.createElement('div');
        div.className = 'token-popover';
        div.setAttribute('role', 'tooltip');
        div.setAttribute('aria-live', 'polite');
        div.innerHTML = `
            <div class="token-popover__surface">${TokenPopover._esc(surfaceForm)}</div>
            <div class="token-popover__body">
                <div class="token-popover__loading">Loading…</div>
            </div>
        `;
        return div;
    }

    /**
     * Populate the popover body with resolved lemma data.
     * @param {Element} popover
     * @param {string}  surfaceForm
     * @param {string}  lookup
     * @param {Object|null} lemmaEntry  - { gw, cf, pos, lang } from lemmasData
     * @param {Array|null}  competing   - competing readings array
     */
    static _populate(popover, surfaceForm, lookup, lemmaEntry, competing) {
        const body = popover.querySelector('.token-popover__body');
        if (!body) return;

        const parts = [];

        // citation_form · guide_word
        const cf = lemmaEntry?.cf || lookup;
        const gw = lemmaEntry?.gw;
        if (cf || gw) {
            const cfHtml = `<span class="token-popover__cf">${TokenPopover._esc(cf)}</span>`;
            const gwHtml = gw
                ? ` <span class="token-popover__sep">·</span> <span class="token-popover__gw">${TokenPopover._esc(gw)}</span>`
                : '';
            parts.push(`<div class="token-popover__row token-popover__row--head">${cfHtml}${gwHtml}</div>`);
        }

        // pos · language
        const pos = lemmaEntry?.pos;
        const lang = lemmaEntry?.lang;
        if (pos || lang) {
            const posHtml = pos ? `<span class="token-popover__pos">${TokenPopover._esc(pos)}</span>` : '';
            const langHtml = lang
                ? `<span class="token-popover__lang">${TokenPopover._esc(TokenPopover._langLabel(lang))}</span>`
                : '';
            const sep = pos && lang ? `<span class="token-popover__sep">·</span>` : '';
            parts.push(`<div class="token-popover__row token-popover__row--meta">${posHtml}${sep}${langHtml}</div>`);
        }

        // Competing readings indicator
        if (competing && competing.length > 1) {
            parts.push(`<div class="token-popover__row token-popover__row--competing">
                <span class="token-popover__competing-badge">⚡ ${competing.length} competing readings</span>
            </div>`);
        }

        if (parts.length === 0) {
            parts.push(`<div class="token-popover__empty">No lemma data available</div>`);
        }

        body.innerHTML = parts.join('');
    }

    /**
     * PRD-020 — fetch and render the grounded AI interpretation for a token.
     *
     * Appends an "AI interpretation" panel below the lexical data. Renders the
     * step-by-step reasoning chain (each step: label · value · confidence) and,
     * when the token has no lemmatization, the provisional hypotheses. Every
     * panel carries an explicit AI trust badge so a scholar never mistakes an
     * AI inference for an attested reading.
     *
     * Degrades silently on error (network, 4xx/5xx, abort): the lexical panel
     * remains the source of truth. Guards against the popover having been
     * dismissed (or a different token clicked) before the fetch resolves.
     *
     * @param {Element} popover  - the open popover element
     * @param {Element} el       - the anchor token element (for repositioning)
     * @param {string}  pNumber  - artifact P-number
     * @param {string}  tokenId  - integer token PK as a string
     * @param {string}  apiUrl   - API base URL (no trailing slash)
     */
    static async _fetchInterpretation(popover, el, pNumber, tokenId, apiUrl) {
        const body = popover.querySelector('.token-popover__body');
        if (!body) return;

        // Loading section — appended so the lexical panel stays visible.
        const panel = document.createElement('div');
        panel.className = 'token-popover__ai-panel';
        panel.innerHTML =
            `<div class="token-popover__ai-head">`
            + TokenPopover._aiBadge()
            + `</div>`
            + `<div class="token-popover__ai-loading">Interpreting in context…</div>`;
        body.appendChild(panel);
        TokenPopover._position(popover, el);

        let data;
        try {
            const res = await fetch(
                `${apiUrl}/artifacts/${encodeURIComponent(pNumber)}`
                + `/tokens/${encodeURIComponent(tokenId)}/interpret`
            );
            if (!res.ok) throw new Error(`interpret ${res.status}`);
            data = await res.json();
        } catch {
            // Popover may have been dismissed; only mutate if still ours.
            if (TokenPopover._current === popover) panel.remove();
            return;
        }

        // Bail if the popover was dismissed or replaced while we waited.
        if (TokenPopover._current !== popover || !panel.isConnected) return;

        const payload = (data && data.data) || {};
        const steps = Array.isArray(payload.steps) ? payload.steps : [];
        const hypotheses = Array.isArray(payload.hypotheses) ? payload.hypotheses : [];

        if (steps.length === 0 && hypotheses.length === 0) {
            // Nothing grounded to show — don't leave an empty AI shell.
            panel.remove();
            TokenPopover._position(popover, el);
            return;
        }

        const parts = [`<div class="token-popover__ai-head">${TokenPopover._aiBadge()}</div>`];

        if (steps.length) {
            const rows = steps.map((s) => {
                const conf =
                    typeof s.confidence === 'number'
                        ? TokenPopover._confPillFromScore(s.confidence)
                        : '';
                return `<li class="token-popover__ai-step">`
                    + `<span class="token-popover__ai-label">${TokenPopover._esc(s.label)}</span>`
                    + `<span class="token-popover__ai-value">${TokenPopover._esc(s.value)}</span>`
                    + conf
                    + `</li>`;
            }).join('');
            parts.push(`<ol class="token-popover__ai-chain">${rows}</ol>`);
        }

        if (hypotheses.length) {
            const hyps = hypotheses.map((h) => {
                const band = h.confidence_band || 'low';
                const evidence = Array.isArray(h.evidence_chain) && h.evidence_chain.length
                    ? `<div class="token-popover__ai-evidence">${
                        h.evidence_chain.map((f) => TokenPopover._esc(f)).join(' · ')
                      }</div>`
                    : '';
                return `<div class="token-popover__hypothesis">`
                    + `<span class="token-popover__hypothesis-prefix">Hypothesis:</span> `
                    + `${TokenPopover._esc(h.reading)} `
                    + TokenPopover._confPill(band)
                    + evidence
                    + `</div>`;
            }).join('');
            parts.push(hyps);
        }

        panel.innerHTML = parts.join('');
        TokenPopover._position(popover, el);
    }

    /** AI trust badge — mirrors the ai-trust.css header badge from the trust UI. */
    static _aiBadge() {
        return `<span class="ai-badge ai-badge--header" `
            + `title="Generated by AI from available scholarly data. Not peer-reviewed.">`
            + `<span class="ai-badge__dot"></span>AI interpretation</span>`;
    }

    /** Confidence pill matching the trust-UI .conf-pill (3 bars + word, a11y-safe). */
    static _confPill(band) {
        const safe = band === 'high' || band === 'medium' ? band : 'low';
        const word = safe === 'high' ? 'high' : safe === 'medium' ? 'medium' : 'low confidence';
        return `<span class="conf-pill conf-pill--${safe}">`
            + `<span class="conf-pill__bars">`
            + `<span class="conf-pill__bar"></span>`
            + `<span class="conf-pill__bar"></span>`
            + `<span class="conf-pill__bar"></span></span>`
            + `${TokenPopover._esc(word)}</span>`;
    }

    /** Map a 0..1 step confidence to the same three-band pill. */
    static _confPillFromScore(score) {
        const band = score >= 0.75 ? 'high' : score >= 0.5 ? 'medium' : 'low';
        return TokenPopover._confPill(band);
    }

    /**
     * Resolve lemma entry and competing data for the clicked element.
     * Uses pre-loaded cache when available; fetches from API otherwise.
     *
     * @returns {Promise<{lemmaEntry: Object|null, competing: Array|null}>}
     */
    static async _resolve(el, pNumber, lookup, apiUrl, cache) {
        const { lemmaEntry, competing } = await TokenPopover._fromCache(el, cache);

        // If we got something from cache, return it
        if (lemmaEntry !== undefined) {
            return { lemmaEntry: lemmaEntry || null, competing: competing || null };
        }

        // Fallback: fetch /lemmas (rare — cache should always be present)
        try {
            const [lemmasResp, competingResp] = await Promise.all([
                fetch(`${apiUrl}/artifacts/${pNumber}/lemmas`),
                fetch(`${apiUrl}/artifacts/${pNumber}/competing-lemmas`),
            ]);

            let fetchedLemmas = {};
            let fetchedCompeting = {};

            if (lemmasResp.ok) {
                const d = await lemmasResp.json();
                fetchedLemmas = d.lemmas || {};
            }
            if (competingResp.ok) {
                const d = await competingResp.json();
                fetchedCompeting = d.competing || {};
            }

            const { lineIdx, wordPos } = TokenPopover._wordPosition(el);
            const entry = lineIdx !== null
                ? fetchedLemmas[String(lineIdx)]?.[String(wordPos)]
                : null;
            const comp = lineIdx !== null
                ? fetchedCompeting[String(lineIdx)]?.[String(wordPos)]
                : null;

            return { lemmaEntry: entry || null, competing: comp || null };
        } catch {
            return { lemmaEntry: null, competing: null };
        }
    }

    /**
     * Look up lemma data from the pre-loaded cache using the token's DOM position.
     * Returns `{lemmaEntry: undefined, competing: undefined}` when position
     * can't be determined (caller falls back to fetching).
     */
    static _fromCache(el, cache) {
        const { lemmasData, competingData } = cache;
        if (!lemmasData) {
            return Promise.resolve({ lemmaEntry: undefined, competing: undefined });
        }

        const { lineIdx, wordPos } = TokenPopover._wordPosition(el);
        if (lineIdx === null) {
            return Promise.resolve({ lemmaEntry: undefined, competing: undefined });
        }

        const entry = lemmasData[String(lineIdx)]?.[String(wordPos)];
        const comp = competingData?.[String(lineIdx)]?.[String(wordPos)];

        return Promise.resolve({ lemmaEntry: entry || null, competing: comp || null });
    }

    /**
     * Determine (lineIdx, wordPos) for `el` using the same index scheme as ATFViewer.
     * lineIdx: 0-based integer (line number string "1." → 0)
     * wordPos: 0-based position among .atf-word[data-lookup] siblings in the line
     *
     * @returns {{ lineIdx: number|null, wordPos: number }}
     */
    static _wordPosition(el) {
        const lineEl = el.closest('.atf-line[data-line]');
        if (!lineEl) return { lineIdx: null, wordPos: 0 };

        const lineNum = lineEl.dataset.line || '';
        // "1." → 0, "1'." → 0, "10." → 9
        const lineIdx = parseInt(lineNum.replace(/[^0-9]/g, '')) - 1;
        if (isNaN(lineIdx) || lineIdx < 0) return { lineIdx: null, wordPos: 0 };

        // Count this element's position among word spans with data-lookup in the line
        const wordEls = Array.from(lineEl.querySelectorAll('.atf-word[data-lookup]'));
        const wordPos = wordEls.indexOf(el);

        return { lineIdx, wordPos: Math.max(wordPos, 0) };
    }

    /**
     * Position the popover above the anchor element, keeping it within the viewport.
     * @param {Element} popover
     * @param {Element} anchor
     */
    static _position(popover, anchor) {
        const anchorRect = anchor.getBoundingClientRect();
        const popRect = popover.getBoundingClientRect();
        const scrollX = window.scrollX || window.pageXOffset;
        const scrollY = window.scrollY || window.pageYOffset;

        // Default: above the token, left-aligned
        let top = anchorRect.top + scrollY - popRect.height - 8;
        let left = anchorRect.left + scrollX;

        // Clamp to viewport (with 8px margin)
        const maxLeft = window.innerWidth - popRect.width - 8;
        if (left > maxLeft) left = maxLeft;
        if (left < 8) left = 8;

        // If above viewport, flip below
        if (top < scrollY + 8) {
            top = anchorRect.bottom + scrollY + 8;
        }

        popover.style.top = `${top}px`;
        popover.style.left = `${left}px`;
    }

    /** Map language codes to readable labels */
    static _langLabel(lang) {
        const labels = {
            akk: 'Akkadian', sux: 'Sumerian', qpc: 'Proto-Cuneiform',
            'akk-x-oldbab': 'Old Babylonian', 'akk-x-stdbab': 'Standard Babylonian',
            'akk-x-oldass': 'Old Assyrian', 'akk-x-neoass': 'Neo-Assyrian',
            'akk-x-neobab': 'Neo-Babylonian', 'akk-x-midbab': 'Middle Babylonian',
            'sux-x-emesal': 'Emesal',
        };
        return labels[lang] || lang;
    }

    /** Escape HTML special characters */
    static _esc(text) {
        if (!text) return '';
        const d = document.createElement('div');
        d.textContent = text;
        return d.innerHTML;
    }
}
