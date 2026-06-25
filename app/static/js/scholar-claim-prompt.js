/**
 * scholar-claim-prompt.js — the post-login scholar-claim prompt (#17).
 *
 * A single dismissible banner shown once after login, mounted into
 * #scholar-claim-prompt-mount. Two variants:
 *   - ORCID auto-match: the user's ORCID matched an unclaimed scholar record.
 *     "Yes, this is me" POSTs the claim (instant verified for an ORCID match) and
 *     flips the card to a success state.
 *   - manual nudge: no ORCID match AND the user has no claim yet → a quieter
 *     "Are you a published scholar?" card linking to the scholars index in claim
 *     mode (/scholars?claim=1).
 *
 * Self-gating, so it degrades quietly:
 *   - only runs on home / scholars listing / account (not deep in a record);
 *   - only for a logged-in user (the /_me proxy returns identity or 204);
 *   - dismissed per-scholar (ORCID) or globally (manual) via localStorage so it
 *     never nags;
 *   - any probe error → no banner (spec: degrade quietly, never a crash).
 *
 * Two-tier: it only ever calls the app-side /_me* proxies, never the API host.
 */
(function () {
    'use strict';

    var path = window.location.pathname;
    // Show only on light, top-level surfaces — not while reading a record.
    var allowed = path === '/' || path === '/scholars' || path === '/account';
    if (!allowed) return;
    // Suppress on the scholars index when it's already in claim mode.
    if (path === '/scholars' && window.location.search.indexOf('claim=1') !== -1) return;

    var mount = document.getElementById('scholar-claim-prompt-mount');
    if (!mount) return;

    function dismissed(key) {
        try { return localStorage.getItem(key) === '1'; } catch (e) { return false; }
    }
    function dismiss(key) {
        try { localStorage.setItem(key, '1'); } catch (e) { /* ignore */ }
    }

    // 1) Are we logged in? /_me returns 204 when there's no session.
    fetch('/_me')
        .then(function (r) { return r.status === 204 ? null : r.json(); })
        .then(function (user) {
            if (!user) return;  // logged out → no prompt
            return fetch('/_me/orcid-match')
                .then(function (r) { return r.ok ? r.json() : { match: null }; })
                .then(function (om) {
                    if (om && om.match && !dismissed('claimPrompt:scholar:' + om.match.id)) {
                        renderOrcid(om.match);
                        return;
                    }
                    // No ORCID match → manual nudge, but only if no claim yet.
                    if (dismissed('claimPrompt:manual')) return;
                    return fetch('/_me/scholar-claims')
                        .then(function (r) { return r.ok ? r.json() : { items: [] }; })
                        .then(function (cl) {
                            var items = (cl && cl.items) || [];
                            if (items.length === 0) renderManual();
                        });
                });
        })
        .catch(function () { /* degrade quietly */ });

    function show(html) {
        mount.innerHTML = html;
        mount.removeAttribute('hidden');
    }

    function esc(s) {
        return String(s == null ? '' : s)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;')
            .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function renderOrcid(match) {
        var meta = esc(match.name);
        if (match.institution) meta += ' · ' + esc(match.institution);
        if (match.publication_count) meta += ' · ' + match.publication_count + ' publications on record';
        show(
            '<div class="claim-prompt" style="margin-top:var(--space-5)">' +
              '<div class="claim-prompt__icon" aria-hidden="true">' +
                '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 6 9 17l-5-5"/></svg>' +
              '</div>' +
              '<div class="claim-prompt__body">' +
                '<p class="claim-prompt__title">We found your scholar record</p>' +
                '<p class="claim-prompt__match">Your ORCID matches <strong>' + esc(match.name) + '</strong>' +
                  (match.institution ? ' · ' + esc(match.institution) : '') +
                  (match.publication_count ? ' · ' + match.publication_count + ' publications on record.' : '.') +
                '</p>' +
                '<div class="claim-prompt__actions">' +
                  '<button class="btn btn--sm btn--primary" id="claim-prompt-yes">Yes, this is me</button>' +
                  '<button class="btn btn--sm btn--ghost" id="claim-prompt-no">Not me</button>' +
                '</div>' +
              '</div>' +
            '</div>'
        );
        document.getElementById('claim-prompt-no').addEventListener('click', function () {
            dismiss('claimPrompt:scholar:' + match.id);
            mount.setAttribute('hidden', '');
        });
        document.getElementById('claim-prompt-yes').addEventListener('click', function () {
            var btn = document.getElementById('claim-prompt-yes');
            btn.disabled = true;
            fetch('/_me/scholar-claims', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ scholar_id: match.id }),
            }).then(function (res) {
                if (res.ok) {
                    dismiss('claimPrompt:scholar:' + match.id);
                    mount.querySelector('.claim-prompt__title').textContent = 'Verified ✓';
                    mount.querySelector('.claim-prompt__match').innerHTML =
                        'You are now the verified scholar for <strong>' + esc(match.name) + '</strong>. ' +
                        '<a href="/account#scholar-identity">Edit your profile</a>.';
                    mount.querySelector('.claim-prompt__actions').innerHTML = '';
                } else {
                    btn.disabled = false;
                }
            }).catch(function () { btn.disabled = false; });
        });
    }

    function renderManual() {
        show(
            '<div class="claim-prompt claim-prompt--manual" style="margin-top:var(--space-5)">' +
              '<div class="claim-prompt__icon" aria-hidden="true">' +
                '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="7"/><path d="m21 21-4.3-4.3"/></svg>' +
              '</div>' +
              '<div class="claim-prompt__body">' +
                '<p class="claim-prompt__title">Are you a published scholar?</p>' +
                '<p class="claim-prompt__match">Claim your record so your contributions are attributed to you and you can maintain your profile.</p>' +
                '<div class="claim-prompt__actions">' +
                  '<a class="btn btn--sm btn--secondary" href="/scholars?claim=1">Find my record</a>' +
                  '<button class="btn btn--sm btn--ghost" id="claim-prompt-dismiss">Dismiss</button>' +
                '</div>' +
              '</div>' +
            '</div>'
        );
        document.getElementById('claim-prompt-dismiss').addEventListener('click', function () {
            dismiss('claimPrompt:manual');
            mount.setAttribute('hidden', '');
        });
    }
})();
