/**
 * header-auth.js — populate the header user chip from the current session.
 *
 * Extracted verbatim from the inline IIFE in base.html (frontend audit finding
 * F-5, #125): the script was tightly coupled to the header markup yet lived
 * inline, so it could not be cached, linted, or reasoned about on its own.
 *
 * Behaviour is unchanged. It calls the app-side `/_me` proxy (never the API host
 * directly — two-tier rule), and on a logged-in response reveals the
 * `#header-user` element and fills `#header-avatar` with either the user's
 * avatar image or their initial. A 204 (no session) or any error leaves the
 * header in its logged-out default. Load this AFTER the header markup is in the
 * DOM (it is referenced at the end of <body>, same position as the old inline
 * script).
 */
(function () {
    fetch('/_me')
        .then(function (r) { return r.status === 204 ? null : r.json(); })
        .then(function (user) {
            if (!user) return;
            var el = document.getElementById('header-user');
            var av = document.getElementById('header-avatar');
            if (!el || !av) return;
            var initial = ((user.display_name || user.email || '?')[0] || '?').toUpperCase();
            if (user.avatar_url) {
                var img = document.createElement('img');
                img.src = user.avatar_url;
                img.alt = initial;
                img.className = 'header-avatar__img';
                av.appendChild(img);
            } else {
                var span = document.createElement('span');
                span.textContent = initial;
                av.appendChild(span);
            }
            el.removeAttribute('hidden');
        })
        .catch(function () {});
})();
