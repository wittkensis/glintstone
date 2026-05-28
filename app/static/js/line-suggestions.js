/**
 * Line Translation Suggestions — Issue #56
 *
 * Lifecycle:
 *   1. ATF viewer finishes rendering → scan for untranslated lines in viewport
 *   2. Lazy-load suggestions for up to 5 lines at a time (staggered 50ms apart)
 *   3. Render suggestion inline under each line
 *   4. Scroll listener enqueues more lines in batches of 5
 *   5. Click a line → sidebar Summary tab shows that line's suggestion
 *
 * API: GET {apiUrl}/artifacts/{p}/lines/suggest?surface={s}&line={n}
 */

(function () {
    'use strict';

    const sidebar = document.getElementById('knowledge-sidebar');
    if (!sidebar) return;

    const pNumber = sidebar.dataset.pNumber;
    const apiUrl = sidebar.dataset.apiUrl || '';
    if (!pNumber) return;

    // ── State ──────────────────────────────────────────────────────────────────

    /** line key → {status: 'pending'|'loading'|'done'|'error', data: LineSuggestionPayload|null} */
    const lineCache = new Map();

    /** Set of line keys currently in the fetch queue */
    const fetchQueue = new Set();
    let fetchTimer = null;

    // ── Helpers ────────────────────────────────────────────────────────────────

    function lineKey(surface, lineNumber) {
        return `${surface}::${lineNumber}`;
    }

    function getAtfViewer() {
        const container = document.querySelector('.atf-viewer');
        return container ? container._viewer : null;
    }

    function isInViewport(el) {
        const rect = el.getBoundingClientRect();
        return rect.top < window.innerHeight + 200 && rect.bottom > -200;
    }

    // ── Scanning for untranslated lines ────────────────────────────────────────

    function findUntranslatedLines() {
        // The ATF viewer sets data-surface-name on .atf-content after each render.
        const surfaces = document.querySelectorAll('.atf-content[data-surface-name]');
        const candidates = [];

        surfaces.forEach((surfaceEl) => {
            const surfaceName = surfaceEl.dataset.surfaceName || 'obverse';
            const lineEls = surfaceEl.querySelectorAll('.atf-line[data-line]');

            lineEls.forEach((lineEl) => {
                const lineNumber = lineEl.dataset.line;
                if (!lineNumber) return;

                // Skip if already has a translation sibling
                const next = lineEl.nextElementSibling;
                if (next && next.classList.contains('atf-line__translation')) return;

                const key = lineKey(surfaceName, lineNumber);
                if (lineCache.has(key)) return; // already fetched or queued

                candidates.push({ surfaceName, lineNumber, lineEl, key });
            });
        });

        return candidates;
    }

    // ── Affordance rendering ───────────────────────────────────────────────────

    function renderAffordance(lineEl) {
        // Ghost affordance shown before the suggestion loads
        if (lineEl.nextElementSibling?.classList.contains('line-suggestion')) return;
        const affordance = document.createElement('div');
        affordance.className = 'line-suggestion line-suggestion--loading';
        affordance.setAttribute('aria-live', 'polite');
        affordance.innerHTML = '<span class="line-suggestion__loading-dot"></span>';
        lineEl.after(affordance);
        return affordance;
    }

    function renderSuggestion(lineEl, data) {
        // Remove existing affordance
        const existing = lineEl.nextElementSibling;
        if (existing?.classList.contains('line-suggestion')) existing.remove();

        if (!data || !data.language_supported) {
            // Unsupported language — show nothing (don't pollute the UI)
            return;
        }

        const suggestions = data.suggestions || [];
        if (!suggestions.length) return;

        const top = suggestions[0];
        const wrapper = document.createElement('div');
        wrapper.className = 'line-suggestion';
        wrapper.dataset.surfaceLine = lineEl.dataset.line;

        const confidenceClass = `line-suggestion__badge--${top.confidence_band}`;

        let missingHtml = '';
        if (data.missing_layers && data.missing_layers.length) {
            missingHtml = `<span class="line-suggestion__missing" title="${escHtml(data.missing_layers.join('; '))}">⚠</span>`;
        }

        wrapper.innerHTML = `
            <button class="line-suggestion__toggle" aria-expanded="false" aria-label="Show translation suggestion">
                <span class="line-suggestion__label">AI</span>
                <span class="line-suggestion__text">${escHtml(top.translation)}</span>
                <span class="line-suggestion__badge ${confidenceClass}">${top.confidence_band}</span>
                ${missingHtml}
                <svg class="line-suggestion__expand-icon" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M4 6l4 4 4-4"/></svg>
            </button>
            <div class="line-suggestion__detail" hidden>
                ${renderDetailHtml(data, suggestions)}
            </div>
        `;

        const toggle = wrapper.querySelector('.line-suggestion__toggle');
        const detail = wrapper.querySelector('.line-suggestion__detail');
        toggle.addEventListener('click', () => {
            const expanded = toggle.getAttribute('aria-expanded') === 'true';
            toggle.setAttribute('aria-expanded', String(!expanded));
            detail.hidden = expanded;
            wrapper.classList.toggle('line-suggestion--open', !expanded);
            if (!expanded) updateSidebar(data, lineEl.closest('.atf-content')?.dataset.surfaceName || 'obverse', lineEl.dataset.line);
        });

        lineEl.after(wrapper);
    }

    function renderDetailHtml(data, suggestions) {
        const chain = (data.token_chain || []).map((step) => {
            const band = step.confidence_band || 'unknown';
            const lemma = step.lemma ? `${step.lemma} (${step.guide_word || '?'})` : 'unknown';
            return `<span class="line-suggestion__token line-suggestion__token--${band}" title="${escHtml(lemma)}">${escHtml(step.raw_form)}</span>`;
        }).join(' ');

        const allSugs = suggestions.map((s, i) => {
            const caveat = s.caveat ? `<span class="line-suggestion__caveat">${escHtml(s.caveat)}</span>` : '';
            return `<li class="line-suggestion__alt ${i === 0 ? 'line-suggestion__alt--top' : ''}">
                <span class="line-suggestion__badge line-suggestion__badge--${s.confidence_band}">${s.confidence_band}</span>
                <span>${escHtml(s.translation)}</span>${caveat}
            </li>`;
        }).join('');

        const missing = (data.missing_layers || []).map(m =>
            `<li class="line-suggestion__missing-item">${escHtml(m)}</li>`
        ).join('');

        return `
            ${chain ? `<div class="line-suggestion__chain">${chain}</div>` : ''}
            <ol class="line-suggestion__alts">${allSugs}</ol>
            ${missing ? `<ul class="line-suggestion__missing-list">${missing}</ul>` : ''}
        `;
    }

    function escHtml(str) {
        return String(str || '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    }

    // ── Sidebar integration ────────────────────────────────────────────────────

    function updateSidebar(data, surfaceName, lineNumber) {
        const summaryContent = document.getElementById('artifact-summary-content');
        if (!summaryContent) return;

        let panel = document.getElementById('line-suggestion-sidebar');
        if (!panel) {
            panel = document.createElement('div');
            panel.id = 'line-suggestion-sidebar';
            panel.className = 'artifact-summary__line-suggestion';
            summaryContent.appendChild(panel);
        }

        if (!data || !data.suggestions?.length) {
            panel.hidden = true;
            return;
        }

        const top = data.suggestions[0];
        panel.hidden = false;
        panel.innerHTML = `
            <div class="artifact-summary__line-suggestion-header">
                <span class="artifact-summary__line-suggestion-label">Line ${lineNumber} suggestion</span>
                <span class="line-suggestion__badge line-suggestion__badge--${top.confidence_band}">${top.confidence_band}</span>
            </div>
            <p class="artifact-summary__line-suggestion-text">${escHtml(top.translation)}</p>
            ${top.caveat ? `<p class="artifact-summary__line-suggestion-caveat">${escHtml(top.caveat)}</p>` : ''}
        `;
    }

    // ── Fetching ───────────────────────────────────────────────────────────────

    function enqueue(candidates) {
        candidates.forEach(({ surfaceName, lineNumber, lineEl, key }) => {
            if (!lineCache.has(key)) {
                lineCache.set(key, { status: 'pending', data: null });
                fetchQueue.add({ surfaceName, lineNumber, lineEl, key });
            }
        });
        scheduleFetch();
    }

    function scheduleFetch() {
        if (fetchTimer) return;
        fetchTimer = setTimeout(flushQueue, 100);
    }

    async function flushQueue() {
        fetchTimer = null;
        const batch = Array.from(fetchQueue).slice(0, 5);
        batch.forEach(item => fetchQueue.delete(item));

        // Show affordances for all in batch
        batch.forEach(({ lineEl }) => renderAffordance(lineEl));

        // Staggered fetches
        for (let i = 0; i < batch.length; i++) {
            const { surfaceName, lineNumber, lineEl, key } = batch[i];
            lineCache.set(key, { status: 'loading', data: null });
            if (i > 0) await new Promise(r => setTimeout(r, 50));
            fetchLine(surfaceName, lineNumber, lineEl, key).catch(() => {});
        }

        if (fetchQueue.size > 0) scheduleFetch();
    }

    async function fetchLine(surfaceName, lineNumber, lineEl, key) {
        try {
            const url = `${apiUrl}/artifacts/${encodeURIComponent(pNumber)}/lines/suggest`
                + `?surface=${encodeURIComponent(surfaceName)}&line=${encodeURIComponent(lineNumber)}`;
            const res = await fetch(url);
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const json = await res.json();
            const data = json.data || null;
            lineCache.set(key, { status: 'done', data });

            // Remove affordance and render
            const affordance = lineEl.nextElementSibling;
            if (affordance?.classList.contains('line-suggestion')) affordance.remove();
            if (data) renderSuggestion(lineEl, data);
        } catch (err) {
            lineCache.set(key, { status: 'error', data: null });
            const affordance = lineEl.nextElementSibling;
            if (affordance?.classList.contains('line-suggestion')) affordance.remove();
        }
    }

    // ── Viewport scan + scroll ─────────────────────────────────────────────────

    function scanViewport() {
        const candidates = findUntranslatedLines().filter(({ lineEl }) => isInViewport(lineEl));
        if (candidates.length) enqueue(candidates.slice(0, 5));
    }

    let scrollTimer = null;
    window.addEventListener('scroll', () => {
        clearTimeout(scrollTimer);
        scrollTimer = setTimeout(scanViewport, 200);
    }, { passive: true });

    // ── Boot — wait for ATF viewer to render ───────────────────────────────────

    function waitForViewer() {
        // The viewer sets innerHTML on .atf-viewer__content; observe for that.
        const container = document.querySelector('.atf-viewer');
        if (!container) return;

        const observer = new MutationObserver((mutations) => {
            for (const m of mutations) {
                if (m.type === 'childList' && m.addedNodes.length) {
                    // Content was set — schedule a scan after a brief tick
                    setTimeout(scanViewport, 300);
                    // Keep observing for subsequent renders (mode switches, etc.)
                    break;
                }
            }
        });

        observer.observe(container, { childList: true, subtree: true });

        // Also fire immediately if already rendered
        if (container.querySelector('.atf-line')) {
            setTimeout(scanViewport, 100);
        }
    }

    waitForViewer();
})();
