/**
 * Artifact summary panel — fetches and renders the AI-generated tablet summary.
 *
 * Lifecycle:
 *   1. Sidebar opens → fetch summary from API if not already loaded
 *   2. Render synthesis text with [n] markers stripped (they're for citation
 *      tracking; not useful in the UI without a citation panel)
 *   3. If best_guess is present, render the hypothesis sentence separately
 *      with a visual "hypothesis" label so it's clearly provisional
 *
 * The API endpoint: GET /api/v2/artifacts/{p_number}/summary?focus=general
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

    function stripMarkers(text) {
        // Remove [n] citation markers — present for the LLM grounding contract,
        // not meaningful in a plain-prose UI without a linked citation panel.
        return text.replace(/\s*\[\d+\]/g, '');
    }

    function renderSummary(data) {
        const card = data.data;
        const synthesis = card.synthesis || data.summary || '';

        // Split hypothesis out if present
        const hypMatch = synthesis.match(/\(hypothesis\)[^.!?]*[.!?]/i);
        const mainText = hypMatch
            ? synthesis.replace(hypMatch[0], '').trim()
            : synthesis;

        textEl.textContent = stripMarkers(mainText);

        if (hypMatch) {
            hypothesisEl.textContent = stripMarkers(hypMatch[0]);
            hypothesisEl.classList.remove('is-hidden');
        }

        // Meta line: pipeline completeness badge + "AI-generated" notice
        const fields = card.fields || [];
        const completenessField = fields.find(
            (f) => f.label && f.label.toLowerCase().includes('completeness')
        );
        const metaParts = ['AI-generated summary'];
        if (completenessField) {
            metaParts.push(`pipeline ${completenessField.value}`);
        }
        if (card.best_guess) {
            metaParts.push('sparse — uses similar-tablet priors');
        }
        metaEl.textContent = metaParts.join(' · ');

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
            const url = `${apiUrl}/artifacts/${encodeURIComponent(pNumber)}/summary?focus=general`;
            const res = await fetch(url);
            if (!res.ok) {
                showError();
                return;
            }
            const data = await res.json();
            renderSummary(data);
        } catch (_) {
            showError();
        }
    }

    // Fetch when the sidebar opens for the first time.
    // The atf-viewer fires a custom 'knowledge-sidebar-state' event on the document.
    document.addEventListener('knowledge-sidebar-state', (e) => {
        if (e.detail && e.detail.action === 'knowledge-open') {
            fetchSummary();
        }
    });

    // Also fetch if sidebar is already open when the script runs (e.g. page reload with hash).
    if (sidebar.dataset.state === 'open') {
        fetchSummary();
    }
})();
