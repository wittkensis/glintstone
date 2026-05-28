/**
 * Artifact summary panel — fetches and renders the AI-generated tablet summary.
 *
 * Lifecycle:
 *   1. Sidebar opens → fetch summary from API if not already loaded
 *   2. Render synthesis text with [n] markers stripped
 *   3. Render hypothesis sentence separately (visually distinct, provisional)
 *   4. Show thumbs up/down feedback buttons; POST rating on click
 *
 * API:
 *   GET  {apiUrl}/artifacts/{p}/summary?focus=general
 *   POST {apiUrl}/agentic/feedback  { interaction_id, rating: 'up'|'down' }
 */

(function () {
    'use strict';

    const sidebar = document.getElementById('knowledge-sidebar');
    if (!sidebar) return;

    const pNumber = sidebar.dataset.pNumber;
    const apiUrl = sidebar.dataset.apiUrl || '';
    if (!pNumber) return;

    const loadingEl = document.getElementById('artifact-summary-loading');
    const contentEl = document.getElementById('artifact-summary-content');
    const textEl = document.getElementById('artifact-summary-text');
    const hypothesisEl = document.getElementById('artifact-summary-hypothesis');
    const metaEl = document.getElementById('artifact-summary-meta');
    const errorEl = document.getElementById('artifact-summary-error');

    let fetched = false;
    let interactionId = null;

    function stripMarkers(text) {
        return text.replace(/\s*\[\d+\]/g, '');
    }

    function renderFeedback() {
        if (!interactionId) return;

        const row = document.createElement('div');
        row.className = 'artifact-summary__feedback';
        row.setAttribute('aria-label', 'Rate this summary');

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
        } catch (_) {
            // Silent fail — feedback is best-effort
        }
        row.innerHTML = '<span class="artifact-summary__feedback-thanks">Thanks</span>';
    }

    function renderSummary(data) {
        const card = data.data;
        const synthesis = card.synthesis || data.summary || '';

        const hypMatch = synthesis.match(/\(hypothesis\)[^.!?]*[.!?]/i);
        const mainText = hypMatch
            ? synthesis.replace(hypMatch[0], '').trim()
            : synthesis;

        textEl.textContent = stripMarkers(mainText);

        if (hypMatch) {
            hypothesisEl.textContent = stripMarkers(hypMatch[0]);
            hypothesisEl.classList.remove('is-hidden');
        }

        const metaParts = ['AI-generated'];
        if (card.best_guess) metaParts.push('sparse — uses similar-tablet priors');
        metaEl.textContent = metaParts.join(' · ');

        // Store interaction_id for feedback; render buttons if available
        if (data.interaction_id) {
            interactionId = parseInt(data.interaction_id, 10) || null;
            if (interactionId) renderFeedback();
        }

        loadingEl.classList.add('is-hidden');
        contentEl.classList.remove('is-hidden');
    }

    function showError() {
        loadingEl.classList.add('is-hidden');
        errorEl.classList.remove('is-hidden');
    }

    async function fetchSummary() {
        if (fetched) return;
        fetched = true;
        try {
            const res = await fetch(
                `${apiUrl}/artifacts/${encodeURIComponent(pNumber)}/summary?focus=general`
            );
            if (!res.ok) { showError(); return; }
            renderSummary(await res.json());
        } catch (_) {
            showError();
        }
    }

    document.addEventListener('knowledge-sidebar-state', (e) => {
        if (e.detail && e.detail.action === 'knowledge-open') fetchSummary();
    });

    if (sidebar.dataset.state === 'open') fetchSummary();
})();
