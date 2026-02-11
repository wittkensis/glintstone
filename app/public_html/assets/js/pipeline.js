/**
 * Pipeline Component Controller
 * Handles popover tooltips for pipeline segments
 */

const pipelinePopover = {
    el: null,
    hideTimeout: null,

    stageNames: {
        image: 'Image',
        signs: 'Sign Detection',
        atf: 'Transliteration (ATF)',
        transliteration: 'Transliteration (ATF)',
        lemmas: 'Lemmatization',
        translation: 'Translation'
    },

    statusDescriptions: {
        complete: 'Available',
        partial: 'Partial',
        inferred: 'Inferred from downstream data',
        skipped: 'Not captured (studied via other methods)',
        missing: 'Missing'
    },

    init() {
        this.el = document.getElementById('pipeline-popover');
        if (!this.el) return;

        // Bind to all expanded pipeline segments
        document.querySelectorAll('.pipeline--expanded .pipeline__segment').forEach(segment => {
            segment.addEventListener('mouseenter', (e) => this.show(e.currentTarget));
            segment.addEventListener('mouseleave', () => this.scheduleHide());
            segment.addEventListener('focus', (e) => this.show(e.currentTarget));
            segment.addEventListener('blur', () => this.scheduleHide());
        });

        // Keep popover visible when hovering over it
        this.el.addEventListener('mouseenter', () => this.cancelHide());
        this.el.addEventListener('mouseleave', () => this.scheduleHide());
    },

    show(segment) {
        this.cancelHide();

        const stage = segment.dataset.stage;
        const status = segment.dataset.status;
        const source = segment.dataset.source;
        const detail = segment.dataset.detail;
        const next = segment.dataset.next;

        // Build status text
        let statusText = this.statusDescriptions[status] || status;
        if (status === 'partial' && detail) {
            statusText = `Partial (${detail})`;
        }

        // Populate popover
        const headerEl = this.el.querySelector('.pipeline-popover__header');
        const statusEl = this.el.querySelector('.pipeline-popover__status');
        const sourceEl = this.el.querySelector('.pipeline-popover__source');
        const nextEl = this.el.querySelector('.pipeline-popover__next');

        if (headerEl) headerEl.textContent = this.stageNames[stage] || stage;
        if (statusEl) statusEl.textContent = statusText;
        if (sourceEl) sourceEl.textContent = source ? `Source: ${source}` : '';
        if (nextEl) nextEl.textContent = next || '';

        // Position below the segment
        const rect = segment.getBoundingClientRect();
        const popoverWidth = 180;
        let left = rect.left + (rect.width / 2) - (popoverWidth / 2);

        // Keep within viewport
        const margin = 8;
        if (left < margin) left = margin;
        if (left + popoverWidth > window.innerWidth - margin) {
            left = window.innerWidth - popoverWidth - margin;
        }

        this.el.style.left = `${left}px`;
        this.el.style.top = `${rect.bottom + 8}px`;

        this.el.classList.add('visible');
        this.el.setAttribute('aria-hidden', 'false');
    },

    scheduleHide() {
        this.hideTimeout = setTimeout(() => this.hide(), 150);
    },

    cancelHide() {
        if (this.hideTimeout) {
            clearTimeout(this.hideTimeout);
            this.hideTimeout = null;
        }
    },

    hide() {
        if (this.el) {
            this.el.classList.remove('visible');
            this.el.setAttribute('aria-hidden', 'true');
        }
    }
};

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => pipelinePopover.init());
} else {
    pipelinePopover.init();
}
