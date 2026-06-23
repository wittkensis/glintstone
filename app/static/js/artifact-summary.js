/**
 * Artifact summary panel — fetches and renders the AI-generated tablet summary.
 *
 * Lifecycle:
 *   1. Sidebar opens → fetch summary from API if not already loaded
 *   2. Render pipeline bar + language badge in header
 *   3. Render synthesis text (or unsupported-language notice)
 *   4. Render hypothesis sentence separately (visually distinct, provisional)
 *   5. Show thumbs up/down feedback buttons; POST rating on click
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
    const headerEl = document.getElementById('artifact-summary-header');
    const unsupportedEl = document.getElementById('artifact-summary-unsupported');
    const textEl = document.getElementById('artifact-summary-text');
    const hypothesisEl = document.getElementById('artifact-summary-hypothesis');
    const sourcesEl = document.getElementById('artifact-summary-sources');
    const sourcesListEl = document.getElementById('artifact-summary-sources-list');
    const metaEl = document.getElementById('artifact-summary-meta');
    const errorEl = document.getElementById('artifact-summary-error');

    let fetched = false;
    let interactionId = null;

    function escHtml(str) {
        return String(str == null ? '' : str).replace(/[&<>"']/g, (c) => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
        }[c]));
    }

    // Render synthesis prose with inline [n] markers kept as clickable anchors
    // to their evidence row. cited.has(n) gates anchoring to real citations only.
    function renderTextWithMarkers(text, citedNs) {
        return escHtml(text).replace(/\[(\d+)\]/g, (match, n) => {
            const num = parseInt(n, 10);
            if (!citedNs.has(num)) return match; // unbound marker — leave as plain text
            return `<a class="cite-marker" href="#s${num}">[${num}]</a>`;
        });
    }

    // Map a Citation to its source-badge variant. Provenance is carried in the
    // source_id tag ('cdli_catalog', 'oracc_lemmatization', ...) and the
    // retrieval_field; fall back to ORACC for lemma/lexical facts.
    function sourceBadge(cit) {
        const id = String(cit.source_id || '').toLowerCase();
        const field = String(cit.retrieval_field || '').toLowerCase();
        if (id.includes('cdli')) return { cls: 'cdli', label: 'CDLI', tail: 'catalog' };
        if (id.includes('epsd') || field.startsWith('sense')) return { cls: 'epsd2', label: 'ePSD2', tail: 'lexicon' };
        if (id.includes('oracc') || field.startsWith('lemma')) return { cls: 'oracc', label: 'ORACC', tail: 'lemmatization' };
        if (cit.scholar_name || cit.publication_short) return null; // scholar-attributed; no source badge
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
                ? `<span class="ai-source__field">${escHtml(cit.retrieval_field.split(':')[0])}</span>`
                : '';
            const badgeHtml = badge
                ? `<span class="source-badge source-badge--${badge.cls}">${badge.label}</span> ${escHtml(badge.tail)}`
                : '';
            const scholarHtml = cit.scholar_name
                ? `<span class="ai-source__scholar">${escHtml(cit.scholar_name)}${cit.year ? ' ' + escHtml(cit.year) : ''}</span>`
                : '';
            const pubHtml = (!cit.scholar_name && cit.publication_short)
                ? `<span class="ai-source__scholar">${escHtml(cit.publication_short)}</span>`
                : '';
            // annotation-run provenance link when present (competing-reading runs etc.)
            const runHtml = cit.annotation_run_id
                ? ` · <a href="${apiUrl ? escHtml(apiUrl) : ''}/annotation-runs/${escHtml(cit.annotation_run_id)}">annotation run</a>`
                : '';

            const parts = [fieldLabel, badgeHtml, scholarHtml, pubHtml]
                .filter(Boolean).join(' · ');
            return `<li class="ai-source" id="s${cit.n}">`
                + `<span class="ai-source__n">[${cit.n}]</span>`
                + `<span class="ai-source__body">${parts}${runHtml}</span></li>`;
        }).join('');

        sourcesEl.classList.remove('is-hidden');
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

    function renderHeader(card) {
        if (!headerEl) return;
        headerEl.innerHTML = '';

        // Pipeline completeness bar
        const completeness = (card.badges || []).find((b) => b.kind === 'completeness');
        if (completeness) {
            const match = completeness.label.match(/(\d+)\/(\d+)/);
            if (match) {
                const score = parseInt(match[1], 10);
                const total = parseInt(match[2], 10);
                const bar = document.createElement('div');
                bar.className = 'artifact-summary__pipeline';
                bar.setAttribute('aria-label', `Pipeline completeness ${score} of ${total}`);
                for (let i = 0; i < total; i++) {
                    const dot = document.createElement('span');
                    dot.className = 'artifact-summary__pipeline-dot' +
                        (i < score ? ' artifact-summary__pipeline-dot--complete' : '');
                    bar.appendChild(dot);
                }
                const lbl = document.createElement('span');
                lbl.className = 'artifact-summary__pipeline-label';
                lbl.textContent = `${score}/${total}`;
                bar.appendChild(lbl);
                headerEl.appendChild(bar);
            }
        }

        // Language badge
        const langField = (card.fields || []).find(
            (f) => f.label && f.label.toLowerCase().includes('primary language')
        );
        if (langField && langField.value) {
            const badge = document.createElement('span');
            badge.className = 'artifact-summary__lang';
            badge.textContent = langField.value;
            headerEl.appendChild(badge);
        }
    }

    function renderSummary(data) {
        const card = data.data;

        renderHeader(card);

        // Gate on language support
        if (card.language_supported === false) {
            const langField = (card.fields || []).find(
                (f) => f.label && f.label.toLowerCase().includes('primary language')
            );
            const langName = langField ? langField.value : 'this language';
            unsupportedEl.textContent = `AI suggestions not available for ${langName}.`;
            unsupportedEl.classList.remove('is-hidden');
            loadingEl.classList.add('is-hidden');
            contentEl.classList.remove('is-hidden');
            return;
        }

        const synthesis = card.synthesis || data.summary || '';

        // If we have no grounded synthesis at all, this is an ungroundable
        // result — show the honest "Summary unavailable" state, never a fabrication.
        if (!card.synthesis) {
            showError();
            return;
        }

        const citations = card.synthesis_citations || [];
        const citedNs = new Set(citations.map((c) => c.n));

        const hypMatch = synthesis.match(/\(hypothesis\)[^.!?]*[.!?]/i);
        const mainText = hypMatch
            ? synthesis.replace(hypMatch[0], '').trim()
            : synthesis;

        // Keep [n] markers visible & clickable — the trust regression to undo.
        textEl.innerHTML = renderTextWithMarkers(mainText, citedNs);

        if (hypMatch) {
            hypothesisEl.innerHTML = renderTextWithMarkers(hypMatch[0].trim(), citedNs);
            hypothesisEl.classList.remove('is-hidden');
        }

        // "Grounded in" attribution list — every cited claim traceable.
        renderSources(citations, citedNs);

        // Badge-anchored meta footer: [• AI] · model · N facts cited
        const factCount = citedNs.size;
        const metaBits = [];
        if (card.model) metaBits.push(escHtml(card.model));
        metaBits.push(`${factCount} ${factCount === 1 ? 'fact' : 'facts'} cited`);
        if (card.best_guess) metaBits.push('sparse — uses similar-tablet priors');
        metaEl.innerHTML =
            '<span class="ai-badge"><span class="ai-badge__dot"></span> AI</span>'
            + '<span>' + metaBits.join(' <span class="ai-meta__sep">·</span> ') + '</span>';

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
