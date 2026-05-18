/**
 * Filter sidebar behaviour.
 *
 * Idempotent: safe to load on any page. Returns early if no #filter-form exists.
 * Bind on DOMContentLoaded (or immediately if DOM already parsed).
 *
 * Previously lived as two inline <script> blocks inside _macros.html — one for
 * the tablet filter sidebar, one for the dictionary filter sidebar. Both did
 * substantially the same work; merged here. See issue #84 phase 3.
 */
(function () {
    'use strict';

    function init() {
        var form = document.getElementById('filter-form');
        if (!form) return;

        // Auto-submit on checkbox/radio change inside the filter form.
        form.querySelectorAll('input[type="checkbox"], input[type="radio"]').forEach(function (input) {
            input.addEventListener('change', function () { form.submit(); });
        });

        // External toggle (e.g. Has ML/OCR) is rendered outside the form but
        // posts via the form="filter-form" attribute. Bind separately.
        document.querySelectorAll('.stage-filter-bar__toggle input[type="checkbox"]').forEach(function (toggle) {
            toggle.addEventListener('change', function () { form.submit(); });
        });

        // "Show all" buttons reveal overflow items, then remove themselves.
        document.querySelectorAll('.filter-show-all').forEach(function (btn) {
            btn.addEventListener('click', function () {
                var container = this.parentElement;
                if (container) container.classList.remove('is-truncated');
                this.remove();
            });
        });

        // Animate <details> close (open is handled by CSS grid transition).
        document.querySelectorAll('.filter-group summary').forEach(function (summary) {
            summary.addEventListener('click', function (e) {
                var details = this.parentElement;
                if (!details || !details.open) return;
                var items = details.querySelector('.filter-group__items');
                if (!items) return;
                e.preventDefault();
                items.style.gridTemplateRows = '0fr';
                items.addEventListener('transitionend', function handler() {
                    details.removeAttribute('open');
                    items.style.gridTemplateRows = '';
                    items.removeEventListener('transitionend', handler);
                }, { once: true });
            });
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
