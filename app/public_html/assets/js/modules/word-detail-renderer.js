/**
 * Word Detail Renderer
 *
 * Shared module for rendering dictionary entry data in both:
 * - Knowledge Dictionary sidebar (compact mode)
 * - Dictionary word detail page (full mode)
 *
 * Mirrors the structure of word-detail.php so both surfaces
 * look like versions of the same view. Section descriptions
 * are loaded from centralized educational-content.php.
 */

class WordDetailRenderer {
    constructor(options = {}) {
        this.compact = options.compact ?? false;
        this.educationalContent = null;
        this._loadPromise = null;
    }

    /**
     * Load educational content from server
     */
    async loadEducationalContent() {
        if (this.educationalContent) return;

        // Share with global educational help system if available
        if (window.educationalHelp?.educationalContent) {
            this.educationalContent = window.educationalHelp.educationalContent;
            return;
        }

        if (this._loadPromise) {
            await this._loadPromise;
            return;
        }

        this._loadPromise = fetch('/api/educational-content.php')
            .then(r => r.ok ? r.json() : {})
            .then(data => { this.educationalContent = data; })
            .catch(() => { this.educationalContent = {}; });

        await this._loadPromise;
    }

    /**
     * Get a section description by key
     */
    sd(key) {
        return this.educationalContent?.section_descriptions?.[key] || '';
    }

    /**
     * Render complete word detail view
     */
    async render(data, container) {
        await this.loadEducationalContent();

        const html = [
            this.renderHeader(data.entry),
            this.renderMeta(data.entry),
            this.renderSenses(data.senses),
            this.renderVariants(data.variants),
            this.renderSigns(data.signs),
            this.renderRelatedWords(data.related_words),
            !this.compact ? this.renderAttestations(data.attestations) : '',
            this.renderCAD(data.cad)
        ].filter(Boolean).join('');

        container.innerHTML = html;
        this.attachEventListeners(container);
    }

    /**
     * Render header with headword and metadata badges
     */
    renderHeader(entry) {
        const languageLabel = this.getLanguageLabel(entry.language);
        const posLabel = this.getPOSLabel(entry.pos);
        const headingTag = this.compact ? 'h3' : 'h1';

        return `
            <header class="word-detail__header">
                <${headingTag} class="word-detail__headword">
                    ${this.escapeHtml(entry.citation_form || entry.headword)}
                </${headingTag}>
                <div class="word-detail__badges">
                    <span title="${posLabel.definition || ''}">${posLabel.label}</span>
                    <span class="list-item__sep" aria-hidden="true">&middot;</span>
                    <span>${languageLabel.label}</span>
                    <span class="list-item__sep" aria-hidden="true">&middot;</span>
                    <span>${(entry.icount || 0).toLocaleString()} attestations</span>
                </div>
            </header>
        `;
    }

    /**
     * Render metadata section (mirrors word-detail.php word-meta)
     */
    renderMeta(entry) {
        const languageLabel = this.getLanguageLabel(entry.language);
        const posLabel = this.getPOSLabel(entry.pos);

        return `
            <div class="word-meta">
                <dl class="word-meta__row">
                    <div class="meta-item">
                        <dt>Language</dt>
                        <dd>${languageLabel.label}</dd>
                    </div>
                    <div class="meta-item">
                        <dt>Part of Speech</dt>
                        <dd>${posLabel.label}</dd>
                    </div>
                    <div class="meta-item">
                        <dt>Attestations</dt>
                        <dd>${(entry.icount || 0).toLocaleString()}</dd>
                    </div>
                </dl>
            </div>
        `;
    }

    /**
     * Render polysemic senses / meanings
     */
    renderSenses(senses) {
        if (!senses || senses.length === 0) return '';

        // Sort by frequency descending for compact (show top 3)
        const sorted = [...senses].sort((a, b) =>
            (b.frequency_percentage || 0) - (a.frequency_percentage || 0)
        );
        const maxToShow = this.compact ? 3 : senses.length;
        const visible = sorted.slice(0, maxToShow);
        const hasMore = sorted.length > maxToShow;

        const sensesHtml = visible.map(sense => `
            <li class="meaning">
                <div class="meaning__header">
                    <strong>${this.escapeHtml(sense.guide_word)}</strong>
                    ${sense.frequency_percentage ? `<span class="meaning__usage">${Math.round(sense.frequency_percentage)}% of uses</span>` : ''}
                </div>
                ${sense.definition ? `<p class="meaning__definition">${this.escapeHtml(sense.definition)}</p>` : ''}
                ${sense.usage_context ? `<p class="meaning__context">${this.escapeHtml(sense.usage_context)}</p>` : ''}
            </li>
        `).join('');

        const hiddenHtml = hasMore ? sorted.slice(maxToShow).map(sense => `
            <li class="meaning meaning--hidden is-hidden">
                <div class="meaning__header">
                    <strong>${this.escapeHtml(sense.guide_word)}</strong>
                    ${sense.frequency_percentage ? `<span class="meaning__usage">${Math.round(sense.frequency_percentage)}% of uses</span>` : ''}
                </div>
                ${sense.definition ? `<p class="meaning__definition">${this.escapeHtml(sense.definition)}</p>` : ''}
                ${sense.usage_context ? `<p class="meaning__context">${this.escapeHtml(sense.usage_context)}</p>` : ''}
            </li>
        `).join('') : '';

        return `
            <section class="word-detail__meanings word-section">
                <h2>Meanings ${senses.length > 0 ? `<span class="section-count-badge">${senses.length}</span>` : ''}</h2>
                <p class="section-description">${this.sd('meanings')}</p>
                <p class="section-description">${this.sd('senses_explanation')}</p>
                <ol class="meanings-list">
                    ${sensesHtml}
                    ${hiddenHtml}
                </ol>
                ${hasMore ? `
                    <button class="btn" data-action="toggle-senses"
                            data-show-text="Show all ${senses.length} senses"
                            data-hide-text="Show top 3 senses"
                            style="margin-top: var(--space-4);">
                        Show all ${senses.length} senses
                    </button>
                ` : ''}
            </section>
        `;
    }

    /**
     * Render variant forms
     * Compact: chips. Full: bar chart.
     */
    renderVariants(variants) {
        if (!variants || variants.length === 0) return '';

        const sorted = [...variants].sort((a, b) => b.count - a.count);

        if (this.compact) {
            const maxToShow = 5;
            const visible = sorted.slice(0, maxToShow);
            const remaining = sorted.length - visible.length;

            return `
                <section class="word-detail__variants word-section">
                    <h2>Attested Forms <span class="section-count-badge">${variants.length}</span></h2>
                    <p class="section-description">${this.sd('attested_forms')}</p>
                    <div class="knowledge-sidebar-variants__list">
                        ${visible.map(v => `
                            <span class="knowledge-sidebar-variant">
                                ${this.escapeHtml(v.form)}
                                <span class="knowledge-sidebar-variant__count">${v.count}</span>
                            </span>
                        `).join('')}
                        ${remaining > 0 ? `<span class="knowledge-sidebar-variant knowledge-sidebar-variant--more">+${remaining} more</span>` : ''}
                    </div>
                </section>
            `;
        }

        // Full bar chart
        const maxCount = sorted[0].count;
        return `
            <section class="word-detail__variants word-section">
                <h2>Attested Forms <span class="section-count-badge">${variants.length}</span></h2>
                <p class="section-description">${this.sd('attested_forms')}</p>
                <div class="variants-chart">
                    ${sorted.map(v => {
                        const pct = maxCount > 0 ? (v.count / maxCount) * 100 : 0;
                        return `
                            <div class="variant-bar">
                                <span class="variant-form">${this.escapeHtml(v.form)}</span>
                                <div class="variant-frequency-container">
                                    <div class="variant-frequency" style="--bar-width: ${pct}%"></div>
                                </div>
                                <span class="variant-count">${v.count} attestations</span>
                            </div>
                        `;
                    }).join('')}
                </div>
            </section>
        `;
    }

    /**
     * Render cuneiform signs breakdown
     */
    renderSigns(signs) {
        if (!signs || signs.length === 0) return '';

        return `
            <section class="word-detail__signs word-section">
                <h2>Cuneiform Signs <span class="section-count-badge">${signs.length}</span></h2>
                <p class="section-description">${this.sd('cuneiform_signs')}</p>
                <div class="related-words-grid">
                    ${signs.map(sign => {
                        const metaParts = [];
                        if (sign.value_type) metaParts.push(this.escapeHtml(sign.value_type));
                        if (sign.sign_type) metaParts.push(this.escapeHtml(sign.sign_type));
                        return `
                        <a href="/dictionary/signs/?sign=${encodeURIComponent(sign.sign_id)}" class="list-item list-item--card sign-card" data-sign-id="${this.escapeHtml(sign.sign_id)}">
                            <div class="sign-card__info">
                                <div class="list-item__header">
                                    <span class="list-item__title">${this.escapeHtml(sign.sign_id)}</span>
                                    ${sign.sign_value ? `<span class="list-item__subtitle">${this.escapeHtml(sign.sign_value)}</span>` : ''}
                                </div>
                                ${metaParts.length > 0 ? `<div class="list-item__meta">${metaParts.join(' · ')}</div>` : ''}
                            </div>
                            ${sign.utf8 ? `<span class="sign-card__glyph">${sign.utf8}</span>` : ''}
                        </a>`;
                    }).join('')}
                </div>
            </section>
        `;
    }

    /**
     * Render related words
     * Compact: list items. Full: card grid.
     */
    renderRelatedWords(relatedWords) {
        if (!relatedWords) return '';

        const groups = [];
        if (relatedWords.translations?.length > 0) groups.push({ title: 'Bilingual Equivalents', words: relatedWords.translations });
        if (relatedWords.synonyms?.length > 0) groups.push({ title: 'Synonyms', words: relatedWords.synonyms });
        if (relatedWords.cognates?.length > 0) groups.push({ title: 'Cognates', words: relatedWords.cognates });
        if (relatedWords.see_also?.length > 0) groups.push({ title: 'See Also', words: relatedWords.see_also });

        if (groups.length === 0) return '';

        const groupsHtml = groups.map(group => {
            const wordsHtml = group.words.map(word => {
                if (this.compact && typeof WordListItem !== 'undefined') {
                    return WordListItem.render(word, { compact: true });
                }
                if (typeof WordListItem !== 'undefined') {
                    return WordListItem.render(word, { card: true, notes: word.notes });
                }
                // Fallback if WordListItem not loaded
                return `
                    <a href="/dictionary/?word=${encodeURIComponent(word.entry_id)}" class="list-item ${this.compact ? 'list-item--compact' : 'list-item--card'}">
                        <div class="list-item__header">
                            <span class="list-item__title">${this.escapeHtml(word.headword)}</span>
                            ${word.guide_word ? `<span class="list-item__subtitle">${this.escapeHtml(word.guide_word)}</span>` : ''}
                        </div>
                        <div class="list-item__meta">
                            ${[word.pos ? this.getPOSLabel(word.pos).label : '', word.language ? this.getLanguageLabel(word.language).label : '']
                                .filter(Boolean)
                                .map(v => `<span>${this.escapeHtml(v)}</span>`)
                                .join('<span class="list-item__sep" aria-hidden="true">&middot;</span>')}
                        </div>
                    </a>
                `;
            }).join('');

            return `
                <div class="related-group">
                    <h3>${group.title}</h3>
                    <div class="${this.compact ? 'related-words-list' : 'related-words-grid'}">
                        ${wordsHtml}
                    </div>
                </div>
            `;
        }).join('');

        return `
            <section class="word-detail__related word-section">
                <h2>Related Words</h2>
                <p class="section-description">${this.sd('related_words')}</p>
                ${groupsHtml}
            </section>
        `;
    }

    /**
     * Render corpus attestations (full mode only)
     */
    renderAttestations(attestations) {
        if (!attestations?.sample || attestations.sample.length === 0) return '';

        const attestationsHtml = attestations.sample.map(att => `
            <div class="example-item">
                <div class="example-header">
                    <a href="/tablets/detail.php?p=${encodeURIComponent(att.p_number)}" class="p-number">${att.p_number}</a>
                    ${att.period || att.provenience ? `<span class="example-meta">${[att.period, att.provenience].filter(Boolean).join(' \u2022 ')}</span>` : ''}
                </div>
                <div class="example-content">
                    <span class="transliteration">${this.escapeHtml(att.form)}</span>
                </div>
            </div>
        `).join('');

        return `
            <section class="word-detail__examples word-section">
                <h2>Corpus Examples</h2>
                <p class="section-description">${this.sd('tablets')}</p>
                <div class="examples-list">
                    ${attestationsHtml}
                </div>
                <p class="examples-footer">
                    Showing ${attestations.showing} of ${attestations.total_count} attestations
                </p>
            </section>
        `;
    }

    /**
     * Render CAD reference
     */
    renderCAD(cad) {
        if (!cad) return '';

        if (this.compact) {
            return `
                <section class="word-detail__cad word-section">
                    <h2>CAD Reference</h2>
                    <p class="section-description">${this.sd('cad')}</p>
                    <div class="cad-content cad-content--compact">
                        <span class="volume-badge">CAD ${this.escapeHtml(String(cad.volume))}, pp. ${cad.page_start}${cad.page_end ? `-${cad.page_end}` : ''}</span>
                        ${cad.pdf_url ? `<a href="${this.escapeHtml(cad.pdf_url)}/page/${cad.page_start}" target="_blank" class="pdf-link">View PDF</a>` : ''}
                        ${cad.human_verified ? '<span class="verified-badge">Verified</span>' : ''}
                    </div>
                    ${cad.etymology ? `<div class="cad-etymology"><strong>Etymology:</strong> ${this.escapeHtml(cad.etymology)}</div>` : ''}
                </section>
            `;
        }

        return `
            <section class="word-detail__cad word-section">
                <h2>Chicago Assyrian Dictionary</h2>
                <p class="section-description">${this.sd('cad')}</p>
                <div class="cad-content">
                    <div class="cad-header">
                        <span class="volume-badge">CAD ${this.escapeHtml(String(cad.volume))}, pp. ${cad.page_start}${cad.page_end ? `-${cad.page_end}` : ''}</span>
                        ${cad.pdf_url ? `<a href="${this.escapeHtml(cad.pdf_url)}/page/${cad.page_start}" target="_blank" class="pdf-link">View PDF \u2192</a>` : ''}
                        ${cad.human_verified ? '<span class="verified-badge">\u2713 Verified</span>' : ''}
                    </div>
                    ${cad.etymology ? `<div class="cad-etymology"><strong>Etymology:</strong> ${this.escapeHtml(cad.etymology)}</div>` : ''}
                    ${cad.semantic_notes ? `<div class="cad-notes">${this.escapeHtml(cad.semantic_notes)}</div>` : ''}
                </div>
            </section>
        `;
    }

    /**
     * Get help text for a field
     */
    getHelpText(fieldKey) {
        if (!this.educationalContent?.field_help) return '';
        return this.educationalContent.field_help[fieldKey] || '';
    }

    /**
     * Get POS label and definition
     */
    getPOSLabel(posCode) {
        if (!this.educationalContent?.pos_codes) {
            return { label: posCode || '', definition: '' };
        }
        return this.educationalContent.pos_codes[posCode] || { label: posCode || '', definition: '' };
    }

    /**
     * Get language label
     */
    getLanguageLabel(langCode) {
        if (!this.educationalContent?.language_codes) {
            return { label: langCode || '' };
        }
        return this.educationalContent.language_codes[langCode] || { label: langCode || '' };
    }

    /**
     * Attach event listeners for interactive elements
     */
    attachEventListeners(container) {
        // Help toggle buttons
        container.querySelectorAll('.help-toggle').forEach(button => {
            button.addEventListener('click', (e) => {
                e.preventDefault();
                const field = button.dataset.field;
                const helpDiv = container.querySelector(`.field-help[data-field="${field}"]`);
                if (helpDiv) {
                    helpDiv.hidden = !helpDiv.hidden;
                    button.setAttribute('aria-expanded', !helpDiv.hidden);
                }
            });
        });

        // Show more/less toggles for senses
        container.querySelectorAll('[data-action="toggle-senses"]').forEach(button => {
            button.addEventListener('click', () => {
                const list = container.querySelector('.meanings-list');
                if (!list) return;
                const hidden = list.querySelectorAll('.meaning--hidden');
                const isShowing = hidden[0]?.classList.contains('is-hidden');
                hidden.forEach(el => el.classList.toggle('is-hidden', !isShowing));
                button.textContent = isShowing
                    ? button.dataset.hideText
                    : button.dataset.showText;
            });
        });
    }

    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WordDetailRenderer;
}
