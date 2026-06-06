/**
 * sidebar.js — Summary panel fetch + thumbs feedback (PRD-006 Phase 1)
 *
 * Targets the #summary-panel element with data-summarize-url attribute.
 * This is a forward-compatibility module: the current tablet detail template
 * uses the #knowledge-sidebar / artifact-summary.js pattern (PRD-005).
 * When the template is migrated to the #summary-panel data attribute pattern
 * this file becomes the active controller.
 *
 * Feedback endpoint: POST /api/v2/agentic/feedback
 *   { output_id, kind: "explicit_rating", score: 1|0 }
 * (artifact-summary.js uses interaction_id / rating — different schema version)
 */

(function () {
    'use strict';

    const panel = document.getElementById('summary-panel');
    if (!panel) return;

    const skeletons = document.getElementById('summary-skeleton');
    const content = document.getElementById('summary-content');
    const url = panel.dataset.summarizeUrl;
    if (!url) return;

    let fetched = false;

    function fetchSummary() {
        if (fetched) return;
        fetched = true;
        fetch(url)
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (data) {
                if (!data) {
                    if (skeletons) skeletons.remove();
                    return;
                }
                if (skeletons) skeletons.style.display = 'none';
                if (content) {
                    content.innerHTML = renderSummary(data);
                    content.style.display = '';
                }
                wireThumbsFeedback(data.output_id);
            })
            .catch(function () {
                if (skeletons) skeletons.remove();
            });
    }

    function renderSummary(data) {
        var isHypothesis = data.best_guess_flag || data.best_guess;
        var html = '';
        if (isHypothesis) {
            html += '<div class="hypothesis-callout">Sparse data — AI summary is a hypothesis, not a verified reading.</div>';
        }
        html += '<p class="summary-text">' + escapeHtml(data.summary || (data.data && data.data.synthesis) || '') + '</p>';
        if (data.citations && data.citations.length) {
            html += '<ol class="summary-citations">';
            data.citations.forEach(function (c, i) {
                html += '<li>[' + (i + 1) + '] ' + escapeHtml(c.label || c.source || '') + ' — ' + escapeHtml(c.content || '') + '</li>';
            });
            html += '</ol>';
        }
        html += '<div class="ai-attribution"><span class="ai-badge">AI</span> Generated summary</div>';
        if (data.output_id) {
            html += '<div class="thumbs-feedback" data-output-id="' + escapeHtml(String(data.output_id)) + '">'
                + '<button class="thumb-btn" data-score="1" aria-label="Helpful">'
                + '<svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14"><path d="M1 21h4V9H1v12zm22-11c0-1.1-.9-2-2-2h-6.31l.95-4.57.03-.32c0-.41-.17-.79-.44-1.06L14.17 1 7.59 7.59C7.22 7.95 7 8.45 7 9v10c0 1.1.9 2 2 2h9c.83 0 1.54-.5 1.84-1.22l3.02-7.05c.09-.23.14-.47.14-.73v-2z"/></svg>'
                + '</button>'
                + '<button class="thumb-btn" data-score="0" aria-label="Not helpful">'
                + '<svg viewBox="0 0 24 24" fill="currentColor" width="14" height="14"><path d="M15 3H6c-.83 0-1.54.5-1.84 1.22l-3.02 7.05c-.09.23-.14.47-.14.73v2c0 1.1.9 2 2 2h6.31l-.95 4.57-.03.32c0 .41.17.79.44 1.06L10.83 23l6.59-6.59c.36-.36.58-.86.58-1.41V5c0-1.1-.9-2-2-2zm4 0v12h4V3h-4z"/></svg>'
                + '</button>'
                + '</div>';
        }
        return html;
    }

    function escapeHtml(s) {
        return String(s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }

    function wireThumbsFeedback(outputId) {
        if (!outputId) return;
        document.querySelectorAll('.thumbs-feedback[data-output-id] .thumb-btn').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var score = parseInt(this.dataset.score, 10);
                fetch('/api/v2/agentic/feedback', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ output_id: outputId, kind: 'explicit_rating', score: score }),
                }).then(function () {
                    document.querySelectorAll('.thumbs-feedback .thumb-btn').forEach(function (b) {
                        b.disabled = true;
                    });
                }).catch(function () {
                    // Best-effort; feedback failure is non-fatal
                });
            });
        });
    }

    // Fetch immediately if panel is always visible, or on sidebar open event
    if (panel.dataset.state !== 'closed') {
        fetchSummary();
    }
    document.addEventListener('knowledge-sidebar-state', function (e) {
        if (e.detail && e.detail.action === 'knowledge-open') fetchSummary();
    });
})();
