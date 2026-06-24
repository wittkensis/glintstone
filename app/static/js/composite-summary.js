/**
 * Composition overview panel (#168 + #169).
 *
 * #168 — fetches the AI composition-level summary (multi-exemplar synthesis)
 *        and renders it with the trust UI: inline [n] citation markers, a
 *        "Grounded in" source list, an AI badge + model/fact-count meta, and
 *        thumbs up/down feedback. Never renders an ungrounded fabrication —
 *        an unsummarizable composition shows the honest "unavailable" state.
 *
 * #169 — once an interaction_id is known, reveals the scholar correction
 *        widget (capture-only Level-2 feedback). Submitting POSTs to
 *        /agentic/corrections, which records the correction (interaction_feedback
 *        + a new annotation_run). It is NOT auto-applied.
 *
 * API:
 *   GET  {apiUrl}/composites/{q}/summary
 *   POST {apiUrl}/agentic/feedback     { interaction_id, rating }
 *   POST {apiUrl}/agentic/corrections  { interaction_id, claim, correction, evidence, scholar_id }
 */

(function () {
    'use strict';

    const root = document.getElementById('composite-summary');
    if (!root) return;

    const qNumber = root.dataset.qNumber;
    const apiUrl = root.dataset.apiUrl || '';
    const scholarId = root.dataset.scholarId
        ? parseInt(root.dataset.scholarId, 10) : null;
    if (!qNumber) return;

    const loadingEl = document.getElementById('composite-summary-loading');
    const contentEl = document.getElementById('composite-summary-content');
    const textEl = document.getElementById('composite-summary-text');
    const sourcesEl = document.getElementById('composite-summary-sources');
    const sourcesListEl = document.getElementById('composite-summary-sources-list');
    const metaEl = document.getElementById('composite-summary-meta');
    const errorEl = document.getElementById('composite-summary-error');

    // #169 correction widget elements (present only for signed-in scholars)
    const correctionEl = document.getElementById('composite-correction');
    const correctionToggle = document.getElementById('composite-correction-toggle');
    const correctionForm = document.getElementById('composite-correction-form');
    const correctionCancel = document.getElementById('composite-correction-cancel');
    const correctionSubmit = document.getElementById('composite-correction-submit');
    const correctionStatus = document.getElementById('composite-correction-status');
    const claimInput = document.getElementById('composite-correction-claim');
    const textInput = document.getElementById('composite-correction-text');
    const evidenceInput = document.getElementById('composite-correction-evidence');

    let interactionId = null;

    function escHtml(str) {
        return String(str == null ? '' : str).replace(/[&<>"']/g, (c) => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
        }[c]));
    }

    function renderTextWithMarkers(text, citedNs) {
        return escHtml(text).replace(/\[(\d+)\]/g, (match, n) => {
            const num = parseInt(n, 10);
            if (!citedNs.has(num)) return match;
            return `<a class="cite-marker" href="#cs${num}">[${num}]</a>`;
        });
    }

    function sourceBadge(cit) {
        const id = String(cit.source_id || '').toLowerCase();
        const field = String(cit.retrieval_field || '').toLowerCase();
        if (id.includes('pipeline')) return { cls: 'cdli', label: 'Glintstone', tail: 'pipeline status' };
        if (id.includes('cdli') || field.includes('distribution') || field.includes('count'))
            return { cls: 'cdli', label: 'CDLI', tail: 'catalog' };
        if (id.includes('oracc')) return { cls: 'oracc', label: 'ORACC', tail: 'catalog' };
        return { cls: 'cdli', label: 'CDLI', tail: 'catalog' };
    }

    function renderSources(citations, citedNs) {
        if (!sourcesEl || !sourcesListEl) return;
        const shown = (citations || []).filter((c) => citedNs.has(c.n));
        if (!shown.length) { sourcesEl.classList.add('is-hidden'); return; }
        shown.sort((a, b) => a.n - b.n);

        sourcesListEl.innerHTML = shown.map((cit) => {
            const badge = sourceBadge(cit);
            const fieldLabel = cit.retrieval_field
                ? `<span class="ai-source__field">${escHtml(cit.retrieval_field.split(':')[0].replace(/_/g, ' '))}</span>`
                : '';
            const badgeHtml = badge
                ? `<span class="source-badge source-badge--${badge.cls}">${badge.label}</span> ${escHtml(badge.tail)}`
                : '';
            const parts = [fieldLabel, badgeHtml].filter(Boolean).join(' · ');
            return `<li class="ai-source" id="cs${cit.n}">`
                + `<span class="ai-source__n">[${cit.n}]</span>`
                + `<span class="ai-source__body">${parts}</span></li>`;
        }).join('');

        sourcesEl.classList.remove('is-hidden');
    }

    function renderFeedback() {
        if (!interactionId || !metaEl) return;
        const row = document.createElement('div');
        row.className = 'artifact-summary__feedback';
        row.setAttribute('aria-label', 'Rate this overview');
        ['up', 'down'].forEach((dir) => {
            const btn = document.createElement('button');
            btn.className = `artifact-summary__feedback-btn artifact-summary__feedback-btn--${dir}`;
            btn.dataset.rating = dir;
            btn.setAttribute('aria-label', dir === 'up' ? 'Helpful' : 'Not helpful');
            btn.innerHTML = dir === 'up'
                ? '<svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14"><path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z"/></svg>'
                : '<svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14"><path d="M15 3H6c-.83 0-1.54.5-1.84 1.22l-3.02 7.05c-.09.23-.14.47-.14.73v2c0 1.1.9 2 2 2h6.31l-.95 4.57-.03.32c0 .41.17.79.44 1.06L10.83 23l6.59-6.59c.36-.36.58-.86.58-1.41V5c0-1.1-.9-2-2-2zm4 0v12h4V3h-4z"/></svg>';
            btn.addEventListener('click', () => sendFeedback(dir, row));
            row.appendChild(btn);
        });
        metaEl.appendChild(row);
    }

    async function sendFeedback(rating, row) {
        row.querySelectorAll('button').forEach((b) => { b.disabled = true; });
        try {
            await fetch(`${apiUrl}/agentic/feedback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ interaction_id: interactionId, rating }),
            });
        } catch (_) { /* best-effort */ }
        row.innerHTML = '<span class="artifact-summary__feedback-thanks">Thanks</span>';
    }

    function renderSummary(data) {
        const card = data.data || {};

        // Ungroundable → honest unavailable state, never a fabrication.
        if (!card.synthesis) { showError(); return; }

        const citations = card.synthesis_citations || [];
        const citedNs = new Set(citations.map((c) => c.n));

        textEl.innerHTML = renderTextWithMarkers(card.synthesis, citedNs);
        renderSources(citations, citedNs);

        const factCount = citedNs.size;
        const metaBits = [];
        if (card.model) metaBits.push(escHtml(card.model));
        metaBits.push(`${factCount} ${factCount === 1 ? 'fact' : 'facts'} cited`);
        metaEl.innerHTML =
            '<span class="ai-badge"><span class="ai-badge__dot"></span> AI</span>'
            + '<span>' + metaBits.join(' <span class="ai-meta__sep">·</span> ') + '</span>';

        if (data.interaction_id) {
            interactionId = parseInt(data.interaction_id, 10) || null;
            if (interactionId) {
                renderFeedback();
                enableCorrection();
            }
        }

        loadingEl.classList.add('is-hidden');
        contentEl.classList.remove('is-hidden');
    }

    function showError() {
        loadingEl.classList.add('is-hidden');
        errorEl.classList.remove('is-hidden');
    }

    // ── #169 correction widget ────────────────────────────────────────────────

    function enableCorrection() {
        if (!correctionEl || !interactionId) return;
        correctionEl.classList.remove('is-hidden');
    }

    if (correctionToggle && correctionForm) {
        correctionToggle.addEventListener('click', () => {
            const open = correctionForm.classList.toggle('is-hidden');
            correctionToggle.setAttribute('aria-expanded', String(!open));
            if (!open) claimInput && claimInput.focus();
        });
    }
    if (correctionCancel && correctionForm) {
        correctionCancel.addEventListener('click', () => {
            correctionForm.classList.add('is-hidden');
            correctionToggle.setAttribute('aria-expanded', 'false');
        });
    }
    if (correctionForm) {
        correctionForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            if (!interactionId) return;
            const claim = (claimInput.value || '').trim();
            const correction = (textInput.value || '').trim();
            const evidence = (evidenceInput.value || '').trim();
            if (!claim || !correction) return;

            correctionSubmit.disabled = true;
            correctionStatus.classList.add('is-hidden');
            try {
                const res = await fetch(`${apiUrl}/agentic/corrections`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        interaction_id: interactionId,
                        claim,
                        correction,
                        evidence: evidence || null,
                        scholar_id: scholarId,
                    }),
                });
                if (res.ok) {
                    correctionForm.reset();
                    correctionForm.classList.add('is-hidden');
                    correctionToggle.setAttribute('aria-expanded', 'false');
                    correctionStatus.textContent =
                        'Correction recorded for review. Thank you.';
                    correctionStatus.classList.remove('is-hidden', 'ai-correction__status--error');
                } else {
                    throw new Error('submit failed');
                }
            } catch (_) {
                correctionStatus.textContent =
                    'Could not submit your correction. Please try again.';
                correctionStatus.classList.remove('is-hidden');
                correctionStatus.classList.add('ai-correction__status--error');
            } finally {
                correctionSubmit.disabled = false;
            }
        });
    }

    async function fetchSummary() {
        try {
            const res = await fetch(
                `${apiUrl}/composites/${encodeURIComponent(qNumber)}/summary`
            );
            if (!res.ok) { showError(); return; }
            renderSummary(await res.json());
        } catch (_) {
            showError();
        }
    }

    fetchSummary();
})();
