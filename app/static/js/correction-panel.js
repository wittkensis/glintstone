/**
 * Scholar Correction panel (#532) — client gating + submission.
 *
 * For every [data-correction-panel] on the page this script:
 *   1. Fetches the signed-in user's claims (/_me/scholar-claims) once and decides
 *      visibility:
 *        · no approved claim → panel stays hidden (the affordance never appears
 *          for non-scholars)
 *        · a pending claim (and no approved) → panel shown but disabled, with a
 *          status line explaining the claim is still under review
 *        · an approved claim → panel shown and enabled
 *   2. Wires the live char counter (0 / 500).
 *   3. Submits to the same-origin proxy POST /_me/scholar-corrections, surfacing
 *      the API's validation/permission message on failure.
 *
 * Anonymous users (204 from the proxy) see no panel. The panel for an
 * `interpretation` target reads its target_id from data-target-id, which the
 * token popover sets at click-time; a panel with an empty target_id refuses to
 * submit (the caller must stamp the token id first).
 */
(function () {
    'use strict';

    var panels = Array.prototype.slice.call(
        document.querySelectorAll('[data-correction-panel]')
    );
    if (panels.length === 0) return;

    function setStatus(panel, message, tone) {
        var el = panel.querySelector('[data-correction-status]');
        if (!el) return;
        el.textContent = message || '';
        if (tone) { el.setAttribute('data-tone', tone); }
        else { el.removeAttribute('data-tone'); }
    }

    function enable(panel) {
        panel.classList.remove('is-hidden');
        panel.hidden = false;
        panel.removeAttribute('data-state');
        setStatus(panel, '', null);
    }

    function showDisabled(panel, message) {
        panel.classList.remove('is-hidden');
        panel.hidden = false;
        panel.setAttribute('data-state', 'disabled');
        var controls = panel.querySelectorAll('textarea, select, input, button');
        controls.forEach(function (c) { c.disabled = true; });
        setStatus(panel, message, null);
    }

    function wireCounter(panel) {
        var ta = panel.querySelector('[data-correction-text]');
        var count = panel.querySelector('[data-correction-count]');
        if (!ta || !count) return;
        ta.addEventListener('input', function () {
            count.textContent = String(ta.value.length);
        });
    }

    function wireSubmit(panel) {
        var btn = panel.querySelector('[data-correction-submit]');
        if (!btn) return;
        btn.addEventListener('click', function () {
            var text = (panel.querySelector('[data-correction-text]') || {}).value || '';
            var reason = (panel.querySelector('[data-correction-reason]') || {}).value || '';
            var citation = (panel.querySelector('[data-correction-citation]') || {}).value || '';
            var targetType = panel.getAttribute('data-target-type');
            var targetId = panel.getAttribute('data-target-id');

            text = text.trim();
            if (!text) { setStatus(panel, 'A correction is required.', 'error'); return; }
            if (!targetId) {
                setStatus(panel, 'Select what to correct first.', 'error');
                return;
            }

            btn.disabled = true;
            setStatus(panel, 'Submitting…', null);

            fetch('/_me/scholar-corrections', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    target_type: targetType,
                    target_id: targetId,
                    correction_text: text,
                    reason: reason,
                    citation: citation.trim() || null,
                }),
            }).then(function (res) {
                if (res.ok) {
                    setStatus(panel, 'Thank you — your correction was submitted for review.', 'success');
                    var ta = panel.querySelector('[data-correction-text]');
                    var ct = panel.querySelector('[data-correction-citation]');
                    if (ta) ta.value = '';
                    if (ct) ct.value = '';
                    var count = panel.querySelector('[data-correction-count]');
                    if (count) count.textContent = '0';
                    btn.disabled = false;
                    return;
                }
                return res.json().then(function (j) {
                    setStatus(panel, (j && j.detail) || 'Could not file the correction.', 'error');
                    btn.disabled = false;
                }).catch(function () {
                    setStatus(panel, 'Could not file the correction.', 'error');
                    btn.disabled = false;
                });
            }).catch(function () {
                setStatus(panel, 'Could not file the correction.', 'error');
                btn.disabled = false;
            });
        });
    }

    // One claims probe drives every panel's gating.
    fetch('/_me/scholar-claims', { headers: { Accept: 'application/json' } })
        .then(function (res) {
            if (!res.ok) return { items: [] };
            return res.json().catch(function () { return { items: [] }; });
        })
        .then(function (data) {
            var items = (data && data.items) || [];
            var hasApproved = items.some(function (c) { return c.status === 'approved'; });
            var hasPending = items.some(function (c) { return c.status === 'pending'; });

            panels.forEach(function (panel) {
                if (hasApproved) {
                    enable(panel);
                    wireCounter(panel);
                    wireSubmit(panel);
                } else if (hasPending) {
                    showDisabled(panel,
                        'Your scholar claim is still under review — corrections unlock once it is approved.');
                }
                // else: no claim → leave hidden.
            });
        })
        .catch(function () {
            // Probe failed → leave all panels hidden (degrade quietly).
        });
})();
