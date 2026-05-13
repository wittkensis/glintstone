/**
 * Global search drawer — state machine + keyboard nav.
 *
 * Wires the markup in partials/global_search.html to the /_search/suggest
 * proxy route. No framework; one closure per page; idempotent re-init guards.
 *
 * States:
 *   RESTING           — drawer closed, input not focused
 *   FOCUSED_EMPTY     — drawer open, no query (shows recents OR record-self)
 *   FOCUSED_TYPING    — drawer open, query > 0 (shows loading then results)
 *
 * Storage:
 *   localStorage["glintstone:recent_searches"]  ::= JSON list of strings (cap 12)
 */
(function () {
    'use strict';

    const ROOT_SELECTOR = '.global-search';
    const RECENTS_KEY = 'glintstone:recent_searches';
    const RECENTS_CAP = 12;
    const DEBOUNCE_MS = 180;
    const BLUR_CLOSE_DELAY_MS = 150;

    function init(root) {
        if (!root || root.__gsBound) return;
        root.__gsBound = true;

        const form = root.querySelector('.global-search__form');
        const input = root.querySelector('.global-search__input');
        const drawer = root.querySelector('.global-search__drawer');
        const bodySlot = drawer.querySelector('[data-role="body"]');
        const scopeChips = Array.from(drawer.querySelectorAll('.scope-chip'));
        const inputWrap = root.querySelector('.global-search__input-wrap');
        const prefix = root.querySelector('.global-search__prefix');

        const recordMode = root.dataset.recordMode === 'true';
        const recordId = root.dataset.recordId || '';
        const recordScope = root.dataset.recordScope || 'all';
        const scopeDefault = root.dataset.scopeDefault || 'all';

        let currentScope = scopeDefault === 'all' && !recordMode ? 'all' : scopeDefault;
        let openCloseTimer = null;
        let fetchTimer = null;
        let inflight = null;
        let lastQuery = '';
        let lastScope = '';
        let resultIndex = -1;

        // ---- Helpers --------------------------------------------------------

        function openDrawer() {
            root.classList.add('is-open');
            drawer.hidden = false;
            input.setAttribute('aria-expanded', 'true');
        }

        function closeDrawer() {
            root.classList.remove('is-open');
            drawer.hidden = true;
            input.setAttribute('aria-expanded', 'false');
            resultIndex = -1;
        }

        function setScope(next) {
            currentScope = next;
            scopeChips.forEach(c => c.classList.toggle('is-active', c.dataset.scope === next));
            // Also update the prefix chip label when scope is single-entity
            if (prefix) {
                if (next === 'all') {
                    prefix.hidden = true;
                } else {
                    prefix.hidden = false;
                    const label = root.querySelector('.global-search__prefix-label');
                    if (label) {
                        const chip = scopeChips.find(c => c.dataset.scope === next);
                        if (chip) label.textContent = chip.textContent.trim();
                    }
                }
            }
            // Re-fetch if the query is non-empty
            if (input.value.trim().length > 0) {
                fetchSuggestions(input.value.trim(), true);
            } else {
                renderEmptyState();
            }
        }

        function readRecents() {
            try {
                const raw = localStorage.getItem(RECENTS_KEY);
                return raw ? JSON.parse(raw) : [];
            } catch (_) {
                return [];
            }
        }

        function writeRecents(list) {
            try {
                localStorage.setItem(RECENTS_KEY, JSON.stringify(list.slice(0, RECENTS_CAP)));
            } catch (_) {}
        }

        function pushRecent(q) {
            const trimmed = q.trim();
            if (!trimmed) return;
            const cur = readRecents().filter(x => x.toLowerCase() !== trimmed.toLowerCase());
            cur.unshift(trimmed);
            writeRecents(cur);
        }

        function tmpl(name) {
            const t = root.querySelector(`template[data-tmpl="${name}"]`);
            return t ? t.content.cloneNode(true) : null;
        }

        // ---- Renderers ------------------------------------------------------

        function renderEmptyState() {
            bodySlot.innerHTML = '';
            // Record-mode: show the current record as the sole result.
            if (recordMode) {
                const n = tmpl('record-self');
                if (n) {
                    bodySlot.appendChild(n);
                    return;
                }
            }
            const recents = readRecents();
            if (recents.length === 0) {
                const n = tmpl('recents-empty');
                if (n) bodySlot.appendChild(n);
                return;
            }
            const n = tmpl('recents');
            if (!n) return;
            const list = n.querySelector('[data-role="recents-list"]');
            recents.forEach((q, i) => {
                const li = document.createElement('li');
                li.className = 'search-recents__item';
                li.tabIndex = -1;
                li.dataset.resultIndex = String(i);
                li.dataset.query = q;
                li.innerHTML = `
                    <svg class="search-recents__icon" width="14" height="14" viewBox="0 0 16 16" fill="none" aria-hidden="true">
                        <circle cx="7" cy="7" r="5" stroke="currentColor" stroke-width="1.5"/>
                        <path d="M11 11L14 14" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
                    </svg>
                    <span>${escapeHtml(q)}</span>
                `;
                li.addEventListener('mousedown', (ev) => {
                    ev.preventDefault();
                    input.value = q;
                    fetchSuggestions(q);
                });
                list.appendChild(li);
            });
            bodySlot.appendChild(n);
        }

        function renderLoading() {
            bodySlot.innerHTML = '';
            const n = tmpl('loading');
            if (n) bodySlot.appendChild(n);
        }

        function renderError() {
            bodySlot.innerHTML = '';
            const div = document.createElement('div');
            div.className = 'search-empty';
            div.textContent = 'Search is temporarily unavailable.';
            bodySlot.appendChild(div);
        }

        function renderHtml(html) {
            bodySlot.innerHTML = html;
            resultIndex = -1;
        }

        function escapeHtml(s) {
            return String(s).replace(/[&<>"']/g, c => ({
                '&': '&amp;', '<': '&lt;', '>': '&gt;',
                '"': '&quot;', "'": '&#39;'
            }[c]));
        }

        // ---- Fetch ---------------------------------------------------------

        function fetchSuggestions(q, immediate = false) {
            if (fetchTimer) clearTimeout(fetchTimer);
            if (inflight) inflight.abort();

            const trimmed = q.trim();
            if (!trimmed) {
                renderEmptyState();
                return;
            }

            const run = () => {
                lastQuery = trimmed;
                lastScope = currentScope;
                renderLoading();
                const ctrl = new AbortController();
                inflight = ctrl;
                const url = `/_search/suggest?q=${encodeURIComponent(trimmed)}&scope=${encodeURIComponent(currentScope)}&limit=8`;
                fetch(url, { signal: ctrl.signal, credentials: 'same-origin', cache: 'no-store' })
                    .then(r => {
                        if (r.status === 204) return '';
                        if (!r.ok) throw new Error('http ' + r.status);
                        return r.text();
                    })
                    .then(html => {
                        // Race-protect: only render if state hasn't moved on
                        if (lastQuery !== trimmed || lastScope !== currentScope) return;
                        if (!html) { renderEmptyState(); return; }
                        renderHtml(html);
                    })
                    .catch(err => {
                        if (err.name === 'AbortError') return;
                        renderError();
                    })
                    .finally(() => {
                        if (inflight === ctrl) inflight = null;
                    });
            };

            if (immediate) run();
            else fetchTimer = setTimeout(run, DEBOUNCE_MS);
        }

        // ---- Keyboard nav --------------------------------------------------

        function rows() {
            return Array.from(bodySlot.querySelectorAll('.search-row, .search-recents__item'));
        }

        function highlight(next) {
            const all = rows();
            if (!all.length) return;
            const max = all.length - 1;
            if (next < 0) next = max;
            if (next > max) next = 0;
            all.forEach((el, i) => el.classList.toggle('is-selected', i === next));
            resultIndex = next;
            const sel = all[next];
            if (sel && typeof sel.scrollIntoView === 'function') {
                sel.scrollIntoView({ block: 'nearest' });
            }
        }

        function activateSelected() {
            const all = rows();
            if (!all.length) {
                // Fall back to /tablets?search=<q>
                const q = input.value.trim();
                if (q) {
                    pushRecent(q);
                    form.submit();
                }
                return;
            }
            const target = resultIndex >= 0 ? all[resultIndex] : all[0];
            if (target.dataset.query) {
                // Recent search row: rehydrate query and search
                input.value = target.dataset.query;
                fetchSuggestions(target.dataset.query, true);
            } else if (target.href) {
                pushRecent(input.value.trim());
                window.location.href = target.href;
            }
        }

        function cycleScope(delta) {
            const idx = scopeChips.findIndex(c => c.dataset.scope === currentScope);
            const next = scopeChips[(idx + delta + scopeChips.length) % scopeChips.length];
            if (next) setScope(next.dataset.scope);
        }

        // ---- Event wiring --------------------------------------------------

        input.addEventListener('focus', () => {
            if (openCloseTimer) { clearTimeout(openCloseTimer); openCloseTimer = null; }
            openDrawer();
            // On a record page, the placeholder shows the record id; on first
            // focus we clear it visually (placeholder remains as the prompt).
            if (recordMode && !input.value) {
                input.placeholder = 'Search artifacts, signs, words…';
                if (prefix) prefix.hidden = false;
            }
            if (input.value.trim().length > 0) {
                fetchSuggestions(input.value.trim(), true);
            } else {
                renderEmptyState();
            }
        });

        input.addEventListener('blur', () => {
            // Delay so result clicks register before the drawer closes.
            openCloseTimer = setTimeout(closeDrawer, BLUR_CLOSE_DELAY_MS);
        });

        input.addEventListener('input', () => {
            const v = input.value;
            // Typing collapses the record-mode prefix chip (Figma: "Special
            // record styling removed when typing").
            if (recordMode && prefix && v.length > 0) {
                prefix.hidden = true;
            } else if (recordMode && prefix && v.length === 0 && currentScope !== 'all') {
                prefix.hidden = false;
            }
            fetchSuggestions(v);
        });

        input.addEventListener('keydown', (ev) => {
            switch (ev.key) {
                case 'ArrowDown':
                    ev.preventDefault();
                    highlight(resultIndex + 1);
                    break;
                case 'ArrowUp':
                    ev.preventDefault();
                    highlight(resultIndex - 1);
                    break;
                case 'Enter':
                    ev.preventDefault();
                    activateSelected();
                    break;
                case 'Escape':
                    ev.preventDefault();
                    closeDrawer();
                    input.blur();
                    break;
                case 'Tab':
                    if (drawer.hidden) return;
                    ev.preventDefault();
                    cycleScope(ev.shiftKey ? -1 : 1);
                    break;
            }
        });

        // Outside-click closes the drawer
        document.addEventListener('mousedown', (ev) => {
            if (!root.contains(ev.target)) closeDrawer();
        });

        // Scope chip clicks
        scopeChips.forEach(c => {
            c.addEventListener('mousedown', (ev) => {
                ev.preventDefault();  // keep input focus
                setScope(c.dataset.scope);
            });
        });

        // Cmd/Ctrl+K from anywhere on the page
        document.addEventListener('keydown', (ev) => {
            if ((ev.metaKey || ev.ctrlKey) && ev.key.toLowerCase() === 'k') {
                ev.preventDefault();
                input.focus();
                input.select();
            }
        });

        // Form submission — store recent + let the browser navigate
        form.addEventListener('submit', () => {
            const q = input.value.trim();
            if (q) pushRecent(q);
            // The form action="/tablets" GET will navigate to /tablets?search=<q>;
            // for non-tablets scopes we redirect to the matching listing page.
            if (currentScope === 'collections') form.action = '/collections';
            else if (currentScope === 'dictionary') form.action = '/dictionary';
            else if (currentScope === 'scholars') form.action = '/scholars';
            else form.action = '/tablets';
        });
    }

    function bootstrap() {
        document.querySelectorAll(ROOT_SELECTOR).forEach(init);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', bootstrap);
    } else {
        bootstrap();
    }
})();
