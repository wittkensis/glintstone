/**
 * Translation Builder
 * ====================
 * A unified, structured view of a tablet's translation chain that composes on
 * top of the existing ATF viewer's data layers. For each surface it renders
 * Column → Line → Token, with:
 *   - Surface tabs (only surfaces that have content)
 *   - Per-line: line number, token row, inline translation
 *   - "Show Details" toggle (per-line + global) revealing lemma rows
 *     (citation form, guide word, POS, language, damage state)
 *   - Token hover/click → lemma detail popover
 *   - Language selector for the translation column
 *   - "Show Language Switches" highlighting where script/language changes
 *   - Collapsed "Unmatched" section for translations with no line_id
 *
 * Data source: GET /artifacts/{p}/surfaces and GET /artifacts/{p}/lines.
 * The panel is additive — it never mutates the ATF viewer's DOM or state.
 */

class TranslationBuilder {
    constructor(container, options = {}) {
        this.container = typeof container === 'string'
            ? document.querySelector(container)
            : container;
        if (!this.container) {
            console.error('TranslationBuilder: container not found');
            return;
        }

        this.options = {
            apiUrl: '',
            ...options,
        };

        // State
        this.pNumber = null;
        this.surfaces = [];           // [{surface_type, label, line_count}]
        this.currentSurface = null;   // surface_type string
        this.data = null;             // {columns: [...], languages, ...}
        this.translationLang = 'en';
        this.availableLangs = ['en'];
        this.showDetails = false;
        this.showLangSwitches = false;
        this.lineCache = new Map();   // surface_type → data (per active language)

        this.render();
    }

    async safeJson(response) {
        const ct = response.headers.get('content-type') || '';
        if (!ct.includes('application/json')) {
            throw new Error('Expected JSON');
        }
        return response.json();
    }

    async load(pNumber) {
        this.pNumber = pNumber;
        try {
            const resp = await fetch(
                `${this.options.apiUrl}/artifacts/${pNumber}/surfaces`
            );
            if (!resp.ok) throw new Error('Surfaces unavailable');
            const result = await this.safeJson(resp);
            this.surfaces = result.surfaces || [];

            if (this.surfaces.length === 0) {
                this.renderEmpty('No transliteration is available for this tablet.');
                return;
            }

            this.currentSurface = this.surfaces[0].surface_type;
            this.renderTabs();
            await this.loadSurface(this.currentSurface);
        } catch (err) {
            console.error('TranslationBuilder: load failed', err);
            this.renderEmpty('Could not load the translation builder.');
        }
    }

    async loadSurface(surfaceType) {
        this.currentSurface = surfaceType;
        const cacheKey = `${surfaceType}::${this.translationLang}`;

        // Update tab selection state immediately
        this.container.querySelectorAll('.tb-tab').forEach(tab => {
            tab.setAttribute(
                'aria-selected',
                tab.dataset.surface === surfaceType ? 'true' : 'false'
            );
        });

        const body = this.container.querySelector('.tb-body');

        if (this.lineCache.has(cacheKey)) {
            this.data = this.lineCache.get(cacheKey);
            this.renderContent();
            return;
        }

        body.innerHTML = '<div class="tb-loading">Loading lines…</div>';

        try {
            const params = new URLSearchParams({
                surface: surfaceType,
                translation_lang: this.translationLang,
            });
            const resp = await fetch(
                `${this.options.apiUrl}/artifacts/${this.pNumber}/lines?${params}`
            );
            if (!resp.ok) throw new Error('Lines unavailable');
            this.data = await this.safeJson(resp);

            // Refresh language selector from whatever languages exist on the tablet
            if (this.data.languages && this.data.languages.length) {
                this.availableLangs = this.data.languages;
                this.renderLanguageSelector();
            }

            this.lineCache.set(cacheKey, this.data);
            this.renderContent();
        } catch (err) {
            console.error('TranslationBuilder: surface load failed', err);
            body.innerHTML =
                '<div class="tb-empty">Could not load lines for this surface.</div>';
        }
    }

    // ── Structure ────────────────────────────────────────────

    render() {
        this.container.classList.add('translation-builder');
        this.container.innerHTML = `
            <div class="tb-header">
                <h2 class="tb-title">Translation Builder</h2>
                <div class="tb-controls">
                    <label class="tb-toggle">
                        <input type="checkbox" class="tb-toggle__input tb-details-toggle">
                        <span class="tb-toggle__label">Show Details</span>
                    </label>
                    <label class="tb-toggle">
                        <input type="checkbox" class="tb-toggle__input tb-langswitch-toggle">
                        <span class="tb-toggle__label">Show Language Switches</span>
                    </label>
                    <label class="tb-lang">
                        <span class="tb-lang__label">Translation</span>
                        <select class="tb-lang__select" aria-label="Translation language"></select>
                    </label>
                </div>
            </div>
            <nav class="tb-tabs" role="tablist" aria-label="Surfaces"></nav>
            <div class="tb-body"></div>
        `;

        const detailsToggle = this.container.querySelector('.tb-details-toggle');
        detailsToggle.addEventListener('change', (e) => {
            this.showDetails = e.target.checked;
            this.applyDetailsState();
        });

        const langSwitchToggle = this.container.querySelector('.tb-langswitch-toggle');
        langSwitchToggle.addEventListener('change', (e) => {
            this.showLangSwitches = e.target.checked;
            this.container.querySelector('.tb-body')
                ?.classList.toggle('tb-body--lang-switches', this.showLangSwitches);
        });

        const langSelect = this.container.querySelector('.tb-lang__select');
        langSelect.addEventListener('change', (e) => {
            this.translationLang = e.target.value;
            this.loadSurface(this.currentSurface);
        });

        this.renderLanguageSelector();
    }

    renderLanguageSelector() {
        const select = this.container.querySelector('.tb-lang__select');
        if (!select) return;
        const labels = {
            en: 'English', de: 'German', fr: 'French', it: 'Italian',
            es: 'Spanish', tr: 'Turkish', ar: 'Arabic', hu: 'Hungarian',
        };
        select.innerHTML = this.availableLangs.map(lang =>
            `<option value="${this.escapeHtml(lang)}"${lang === this.translationLang ? ' selected' : ''}>${this.escapeHtml(labels[lang] || lang.toUpperCase())}</option>`
        ).join('');
        // Hide the selector entirely when there's at most one language
        const wrap = select.closest('.tb-lang');
        if (wrap) wrap.classList.toggle('is-hidden', this.availableLangs.length <= 1);
    }

    renderTabs() {
        const tabs = this.container.querySelector('.tb-tabs');
        tabs.innerHTML = this.surfaces.map((s, i) => `
            <button class="tb-tab"
                    role="tab"
                    data-surface="${this.escapeHtml(s.surface_type)}"
                    aria-selected="${i === 0 ? 'true' : 'false'}">
                ${this.escapeHtml(s.label)}
                <span class="tb-tab__count">${s.line_count}</span>
            </button>
        `).join('');

        tabs.querySelectorAll('.tb-tab').forEach(tab => {
            tab.addEventListener('click', () => {
                if (tab.dataset.surface !== this.currentSurface) {
                    this.loadSurface(tab.dataset.surface);
                }
            });
        });

        // Single surface → no need to show the tab strip
        tabs.classList.toggle('is-hidden', this.surfaces.length <= 1);
    }

    // ── Content ──────────────────────────────────────────────

    renderContent() {
        const body = this.container.querySelector('.tb-body');
        if (!this.data || !this.data.columns || this.data.columns.length === 0) {
            body.innerHTML = '<div class="tb-empty">No lines on this surface.</div>';
            return;
        }

        let html = '';
        const multiColumn = this.data.columns.length > 1;

        for (const col of this.data.columns) {
            html += '<div class="tb-column">';
            if (multiColumn && col.column > 0) {
                html += `<div class="tb-column__header">Column ${this.toRoman(col.column)}</div>`;
            }
            for (const line of col.lines) {
                html += this.renderLine(line);
            }
            html += '</div>';
        }

        body.innerHTML = html;
        body.classList.toggle('tb-body--details', this.showDetails);
        body.classList.toggle('tb-body--lang-switches', this.showLangSwitches);

        this.attachTokenHandlers();
        this.attachLineToggleHandlers();
    }

    renderLine(line) {
        if (line.is_structural) {
            return '<div class="tb-rule" aria-hidden="true"></div>';
        }

        const tokensHtml = (line.tokens || []).map((tok, idx) => {
            const prev = line.tokens[idx - 1];
            const langSwitch = prev && this.normLang(prev.language) !== this.normLang(tok.language);
            return this.renderToken(tok, langSwitch);
        }).join('');

        // Inline translation row
        let translationHtml = '';
        if (line.translation && line.translation.text) {
            const src = line.translation.source
                ? `<span class="tb-line__trans-source">${this.escapeHtml(line.translation.source)}</span>`
                : '';
            translationHtml = `
                <div class="tb-line__translation">
                    <span class="tb-line__translation-text">${this.escapeHtml(line.translation.text)}</span>
                    ${src}
                </div>`;
        }

        // Normalization (scholarly transliteration) shown in detail mode
        let normHtml = '';
        if (line.normalization) {
            normHtml = `<div class="tb-line__norm">${this.escapeHtml(line.normalization)}</div>`;
        }

        const hasLemmas = (line.tokens || []).some(t => t.lemma);

        return `
            <div class="tb-line" data-line-id="${line.line_id}">
                <div class="tb-line__gutter">
                    <span class="tb-line__number">${this.escapeHtml(line.line_number || '')}</span>
                    ${hasLemmas ? `<button class="tb-line__toggle" type="button" aria-expanded="false" aria-label="Show details for line ${this.escapeHtml(line.line_number || '')}" title="Show details">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><polyline points="6 9 12 15 18 9"/></svg>
                    </button>` : ''}
                </div>
                <div class="tb-line__main">
                    <div class="tb-line__tokens">${tokensHtml}</div>
                    ${normHtml}
                </div>
                <div class="tb-line__trans-col">${translationHtml}</div>
            </div>`;
    }

    renderToken(tok, langSwitch) {
        const damage = tok.damage || 'intact';
        const sf = tok.sign_function || '';
        const classes = ['tb-token', `tb-token--damage-${damage}`];
        if (sf) classes.push(`tb-token--${sf}`);
        if (langSwitch) classes.push('tb-token--lang-switch');
        const langBase = this.normLang(tok.language);
        if (langBase) classes.push(`tb-token--lang-${langBase}`);

        const surface = tok.raw_form || tok.reading || '';
        const reading = tok.reading || '';

        // Collapsed: surface (transliteration) form on top, reading below.
        // Expanded (detail mode): lemma block appended (citation/gw/pos/lang).
        const lemma = tok.lemma;
        let lemmaHtml = '';
        if (lemma) {
            const gw = lemma.guide_word
                ? `<span class="tb-token__gw">${this.escapeHtml(lemma.guide_word)}</span>` : '';
            const cf = lemma.citation_form
                ? `<span class="tb-token__cf">${this.escapeHtml(lemma.citation_form)}</span>` : '';
            const pos = lemma.pos
                ? `<span class="tb-token__pos">${this.escapeHtml(lemma.pos)}</span>` : '';
            lemmaHtml = `<div class="tb-token__lemma">${cf}${gw}${pos}</div>`;
        }

        const dataAttrs = [
            `data-position="${tok.position != null ? tok.position : ''}"`,
            lemma && lemma.citation_form ? `data-cf="${this.escapeHtml(lemma.citation_form)}"` : '',
            lemma && lemma.guide_word ? `data-gw="${this.escapeHtml(lemma.guide_word)}"` : '',
            lemma && lemma.pos ? `data-pos="${this.escapeHtml(lemma.pos)}"` : '',
            tok.language ? `data-lang="${this.escapeHtml(tok.language)}"` : '',
            `data-damage="${this.escapeHtml(damage)}"`,
            sf ? `data-sign-function="${this.escapeHtml(sf)}"` : '',
        ].filter(Boolean).join(' ');

        return `
            <div class="${classes.join(' ')}" ${dataAttrs} tabindex="0" role="button">
                <span class="tb-token__form">${this.escapeHtml(surface)}</span>
                ${reading ? `<span class="tb-token__reading">${this.escapeHtml(reading)}</span>` : ''}
                ${lemmaHtml}
            </div>`;
    }

    // ── Interaction ──────────────────────────────────────────

    applyDetailsState() {
        const body = this.container.querySelector('.tb-body');
        if (body) body.classList.toggle('tb-body--details', this.showDetails);
        // Global toggle also drives per-line toggles' expanded state for a11y
        this.container.querySelectorAll('.tb-line__toggle').forEach(btn => {
            btn.setAttribute('aria-expanded', this.showDetails ? 'true' : 'false');
        });
    }

    attachLineToggleHandlers() {
        this.container.querySelectorAll('.tb-line__toggle').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.stopPropagation();
                const line = btn.closest('.tb-line');
                const open = line.classList.toggle('tb-line--details');
                btn.setAttribute('aria-expanded', open ? 'true' : 'false');
            });
        });
    }

    attachTokenHandlers() {
        this.container.querySelectorAll('.tb-token').forEach(el => {
            // Native title gives an immediate hover affordance even before the popover
            const cf = el.dataset.cf;
            const gw = el.dataset.gw;
            if (cf || gw) {
                el.setAttribute('title',
                    [cf, gw ? `"${gw}"` : '', el.dataset.pos || '']
                        .filter(Boolean).join(' '));
            }

            el.addEventListener('mouseenter', () => this.showTokenPopover(el));
            el.addEventListener('mouseleave', () => this.hideTokenPopover());
            el.addEventListener('focus', () => this.showTokenPopover(el));
            el.addEventListener('blur', () => this.hideTokenPopover());
            el.addEventListener('click', () => this.showTokenPopover(el, true));
        });
    }

    showTokenPopover(el, sticky = false) {
        const cf = el.dataset.cf;
        const gw = el.dataset.gw;
        const pos = el.dataset.pos;
        const lang = el.dataset.lang;
        const damage = el.dataset.damage;
        const sf = el.dataset.signFunction;

        // Nothing meaningful to show
        if (!cf && !gw && !pos && !lang) return;

        this.hideTokenPopover();

        const langLabels = { akk: 'Akkadian', sux: 'Sumerian', qpc: 'Proto-Cuneiform' };
        const posLabels = {
            N: 'Noun', V: 'Verb', AJ: 'Adjective', AV: 'Adverb', PN: 'Personal name',
            DN: 'Divine name', GN: 'Geographic name', RN: 'Royal name', NU: 'Numeral',
        };

        const rows = [];
        if (cf) rows.push(`<div class="tb-pop__row"><dt>Citation</dt><dd>${this.escapeHtml(cf)}</dd></div>`);
        if (gw) rows.push(`<div class="tb-pop__row"><dt>Guide word</dt><dd>${this.escapeHtml(gw)}</dd></div>`);
        if (pos) rows.push(`<div class="tb-pop__row"><dt>POS</dt><dd>${this.escapeHtml(posLabels[pos] || pos)}</dd></div>`);
        if (lang) {
            const base = this.normLang(lang);
            rows.push(`<div class="tb-pop__row"><dt>Language</dt><dd>${this.escapeHtml(langLabels[base] || lang)}</dd></div>`);
        }
        if (damage && damage !== 'intact') {
            rows.push(`<div class="tb-pop__row"><dt>Damage</dt><dd>${this.escapeHtml(damage)}</dd></div>`);
        }
        if (sf) {
            rows.push(`<div class="tb-pop__row"><dt>Sign function</dt><dd>${this.escapeHtml(sf)}</dd></div>`);
        }

        const pop = document.createElement('div');
        pop.className = 'tb-pop';
        pop.setAttribute('role', 'tooltip');
        pop.innerHTML = `<dl class="tb-pop__list">${rows.join('')}</dl>`;
        this.container.appendChild(pop);
        this._popover = pop;

        // Position above the token, clamped to the container
        const elRect = el.getBoundingClientRect();
        const cRect = this.container.getBoundingClientRect();
        const top = elRect.top - cRect.top - pop.offsetHeight - 8;
        let left = elRect.left - cRect.left + (elRect.width / 2) - (pop.offsetWidth / 2);
        left = Math.max(4, Math.min(left, cRect.width - pop.offsetWidth - 4));
        pop.style.top = `${Math.max(4, top)}px`;
        pop.style.left = `${left}px`;
        pop.classList.add('tb-pop--visible');
    }

    hideTokenPopover() {
        if (this._popover) {
            this._popover.remove();
            this._popover = null;
        }
    }

    // ── Helpers ──────────────────────────────────────────────

    normLang(lang) {
        if (!lang) return '';
        return String(lang).split('-')[0];
    }

    toRoman(num) {
        const vals = [10, 9, 5, 4, 1];
        const syms = ['x', 'ix', 'v', 'iv', 'i'];
        let out = '';
        for (let i = 0; i < vals.length; i++) {
            while (num >= vals[i]) { out += syms[i]; num -= vals[i]; }
        }
        return out;
    }

    renderEmpty(message) {
        const body = this.container.querySelector('.tb-body');
        if (body) {
            body.innerHTML = `<div class="tb-empty">${this.escapeHtml(message)}</div>`;
        }
        // Hide controls/tabs when there's nothing to build
        this.container.querySelector('.tb-tabs')?.classList.add('is-hidden');
        this.container.querySelector('.tb-controls')?.classList.add('is-hidden');
    }

    escapeHtml(text) {
        if (text == null) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

if (typeof module !== 'undefined' && module.exports) {
    module.exports = TranslationBuilder;
}
