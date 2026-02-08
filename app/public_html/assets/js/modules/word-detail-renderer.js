/**
 * Word Detail Renderer
 *
 * Shared module for rendering dictionary entry data in both:
 * - Knowledge Dictionary sidebar (compact mode)
 * - Dictionary word detail page (full mode)
 *
 * Ensures consistent field display and educational tooltips across contexts.
 */

class WordDetailRenderer {
    constructor(options = {}) {
        this.compact = options.compact ?? false; // true for sidebar
        this.showHelp = options.showHelp ?? true;
        this.educationalContent = null; // Will be loaded from educational-content.php
    }

    /**
     * Load educational content from server
     */
    async loadEducationalContent() {
        if (this.educationalContent) return;

        try {
            const response = await fetch('/includes/educational-content.php');
            if (!response.ok) throw new Error('Failed to load educational content');

            const text = await response.text();
            // Parse PHP output (returns JSON)
            this.educationalContent = JSON.parse(text);
        } catch (error) {
            console.error('Error loading educational content:', error);
            this.educationalContent = {}; // Fallback to empty
        }
    }

    /**
     * Render complete word detail view
     */
    async render(data, container) {
        await this.loadEducationalContent();

        const html = `
            ${this.renderHeader(data.entry)}
            ${this.renderCoreInfo(data.entry)}
            ${data.senses.length > 0 ? this.renderSenses(data.senses) : ''}
            ${data.variants.length > 0 ? this.renderVariants(data.variants) : ''}
            ${data.signs.length > 0 ? this.renderSigns(data.signs) : ''}
            ${this.renderRelatedWords(data.related_words)}
            ${!this.compact && data.attestations.sample.length > 0 ? this.renderAttestations(data.attestations) : ''}
            ${data.cad ? this.renderCAD(data.cad) : ''}
        `;

        container.innerHTML = html;
        this.attachEventListeners(container);
    }

    /**
     * Render header with headword and metadata badges
     */
    renderHeader(entry) {
        const languageLabel = this.getLanguageLabel(entry.language);
        const posLabel = this.getPOSLabel(entry.pos);

        return `
            <header class="word-detail__header">
                <h${this.compact ? '3' : '1'} class="word-detail__headword">
                    ${this.escapeHtml(entry.headword)}
                    ${entry.guide_word ? `<span class="guide-word">[${this.escapeHtml(entry.guide_word)}]</span>` : ''}
                </h${this.compact ? '3' : '1'}>
                <div class="word-detail__meta">
                    <span class="badge badge--pos" title="${posLabel.definition || ''}">${posLabel.label}</span>
                    <span class="badge badge--language">${languageLabel.label}</span>
                    ${!this.compact ? `<span class="badge badge--frequency" title="Appears ${entry.icount} times in corpus">${entry.icount} attestations</span>` : ''}
                </div>
            </header>
        `;
    }

    /**
     * Render core information fields
     */
    renderCoreInfo(entry) {
        if (this.compact) return ''; // Skip in sidebar compact mode

        const fields = [
            { key: 'headword', label: 'Headword', value: entry.headword },
            { key: 'citation_form', label: 'Citation Form', value: entry.citation_form },
            { key: 'guide_word', label: 'Guide Word', value: entry.guide_word },
            { key: 'pos', label: 'Part of Speech', value: this.getPOSLabel(entry.pos).label },
            { key: 'language', label: 'Language', value: this.getLanguageLabel(entry.language).label },
            { key: 'frequency', label: 'Frequency (icount)', value: `${entry.icount} occurrences` }
        ];

        const fieldRows = fields.map(field => this.renderFieldRow(field)).join('');

        return `
            <section class="word-detail__core">
                <h2>Core Information</h2>
                <dl class="field-list">
                    ${fieldRows}
                </dl>
            </section>
        `;
    }

    /**
     * Render a single field row with optional help tooltip
     */
    renderFieldRow(field) {
        const helpText = this.getHelpText(field.key);
        const showHelpIcon = this.showHelp && helpText;

        return `
            <dt>
                ${field.label}
                ${showHelpIcon ? `<button class="help-toggle" data-field="${field.key}" aria-label="Explain ${field.label}">ⓘ</button>` : ''}
            </dt>
            <dd>
                ${this.escapeHtml(field.value)}
                ${showHelpIcon ? `<div class="field-help" data-field="${field.key}" hidden>${helpText}</div>` : ''}
            </dd>
        `;
    }

    /**
     * Render polysemic senses
     */
    renderSenses(senses) {
        if (!senses || senses.length === 0) return '';

        const sensesHtml = senses.map((sense, index) => `
            <li class="meaning">
                <div class="meaning__header">
                    <strong>${this.escapeHtml(sense.guide_word)}</strong>
                    ${sense.frequency_percentage ? `<span class="meaning__usage">${Math.round(sense.frequency_percentage)}% of uses</span>` : ''}
                </div>
                ${sense.definition ? `<p class="meaning__definition">${this.escapeHtml(sense.definition)}</p>` : ''}
                ${sense.usage_context ? `<p class="meaning__context">${this.escapeHtml(sense.usage_context)}</p>` : ''}
            </li>
        `).join('');

        return `
            <section class="word-detail__meanings">
                <h2>Meanings</h2>
                <ol class="meanings-list">
                    ${sensesHtml}
                </ol>
            </section>
        `;
    }

    /**
     * Render variant forms with frequencies
     */
    renderVariants(variants) {
        if (!variants || variants.length === 0) return '';

        // Sort by count descending
        const sortedVariants = [...variants].sort((a, b) => b.count - a.count);
        const maxCount = sortedVariants[0].count;

        const variantsHtml = sortedVariants.map(variant => {
            const percentage = maxCount > 0 ? (variant.count / maxCount) * 100 : 0;
            return `
                <div class="variant-bar">
                    <span class="variant-form">${this.escapeHtml(variant.form)}</span>
                    <div class="variant-frequency-container">
                        <div class="variant-frequency" style="width: ${percentage}%"></div>
                    </div>
                    <span class="variant-count">${variant.count} times</span>
                </div>
            `;
        }).join('');

        return `
            <section class="word-detail__variants">
                <h${this.compact ? '4' : '2'}>Attested Forms</h${this.compact ? '4' : '2'}>
                <div class="variants-chart">
                    ${variantsHtml}
                </div>
            </section>
        `;
    }

    /**
     * Render cuneiform signs breakdown
     */
    renderSigns(signs) {
        if (!signs || signs.length === 0) return '';

        const signsHtml = signs.map(sign => `
            <div class="sign-item">
                <a href="/dictionary/sign/${encodeURIComponent(sign.sign_id)}" class="sign-link">
                    <span class="sign-cuneiform">${sign.utf8 || ''}</span>
                    <span class="sign-id">${this.escapeHtml(sign.sign_id)}</span>
                    <span class="sign-value">${this.escapeHtml(sign.sign_value)}</span>
                    ${sign.value_type ? `<span class="sign-type">${this.escapeHtml(sign.value_type)}</span>` : ''}
                </a>
            </div>
        `).join('');

        return `
            <section class="word-detail__signs">
                <h${this.compact ? '4' : '2'}>Cuneiform Signs</h${this.compact ? '4' : '2'}>
                <div class="sign-breakdown">
                    ${signsHtml}
                </div>
            </section>
        `;
    }

    /**
     * Render related words (translations, synonyms, etc.)
     */
    renderRelatedWords(relatedWords) {
        if (!relatedWords) return '';

        const sections = [];

        // Translations (bilingual equivalents)
        if (relatedWords.translations && relatedWords.translations.length > 0) {
            sections.push(this.renderRelatedSection('Bilingual Equivalents', relatedWords.translations));
        }

        // Synonyms
        if (relatedWords.synonyms && relatedWords.synonyms.length > 0) {
            sections.push(this.renderRelatedSection('Synonyms', relatedWords.synonyms));
        }

        // Cognates
        if (relatedWords.cognates && relatedWords.cognates.length > 0) {
            sections.push(this.renderRelatedSection('Cognates', relatedWords.cognates));
        }

        // See also
        if (relatedWords.see_also && relatedWords.see_also.length > 0) {
            sections.push(this.renderRelatedSection('See Also', relatedWords.see_also));
        }

        if (sections.length === 0) return '';

        return `
            <section class="word-detail__related">
                <h${this.compact ? '4' : '2'}>Related Words</h${this.compact ? '4' : '2'}>
                ${sections.join('')}
            </section>
        `;
    }

    /**
     * Render a subsection of related words
     */
    renderRelatedSection(title, words) {
        const wordsHtml = words.map(word => `
            <li>
                <a href="/dictionary/word.php?id=${encodeURIComponent(word.entry_id)}" class="related-word">
                    <strong>${this.escapeHtml(word.headword)}</strong>
                    ${word.guide_word ? `<span class="guide-word">[${this.escapeHtml(word.guide_word)}]</span>` : ''}
                    <span class="badge badge--language">${this.getLanguageLabel(word.language).label}</span>
                </a>
                ${word.notes ? `<span class="related-notes">${this.escapeHtml(word.notes)}</span>` : ''}
            </li>
        `).join('');

        return `
            <div class="related-group">
                <h5>${title}</h5>
                <ul class="related-list">
                    ${wordsHtml}
                </ul>
            </div>
        `;
    }

    /**
     * Render corpus attestations
     */
    renderAttestations(attestations) {
        if (!attestations.sample || attestations.sample.length === 0) return '';

        const attestationsHtml = attestations.sample.map(att => `
            <div class="example-item">
                <div class="example-header">
                    <a href="/tablets/detail.php?p=${encodeURIComponent(att.p_number)}" class="p-number">${att.p_number}</a>
                    ${att.period || att.provenience ? `<span class="example-meta">${[att.period, att.provenience].filter(Boolean).join(' • ')}</span>` : ''}
                </div>
                <div class="example-content">
                    <span class="transliteration">${this.escapeHtml(att.form)}</span>
                </div>
            </div>
        `).join('');

        return `
            <section class="word-detail__examples">
                <h2>Corpus Examples</h2>
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

        return `
            <section class="word-detail__cad">
                <h2>Chicago Assyrian Dictionary</h2>
                <div class="cad-header">
                    <span class="volume-badge">CAD ${cad.volume}, pp. ${cad.page_start}${cad.page_end ? `-${cad.page_end}` : ''}</span>
                    ${cad.pdf_url ? `<a href="${cad.pdf_url}/page/${cad.page_start}" target="_blank" class="pdf-link">View PDF →</a>` : ''}
                    ${cad.human_verified ? '<span class="verified-badge">✓ Verified</span>' : ''}
                </div>
                ${cad.etymology ? `<div class="cad-etymology"><strong>Etymology:</strong> ${this.escapeHtml(cad.etymology)}</div>` : ''}
                ${cad.semantic_notes ? `<div class="cad-notes">${this.escapeHtml(cad.semantic_notes)}</div>` : ''}
            </section>
        `;
    }

    /**
     * Get help text for a field
     */
    getHelpText(fieldKey) {
        if (!this.educationalContent || !this.educationalContent.field_help) return '';

        const helpData = this.educationalContent.field_help[fieldKey];
        return helpData || ''; // Simple string lookup (unified help system)
    }

    /**
     * Get POS label and definition
     */
    getPOSLabel(posCode) {
        if (!this.educationalContent || !this.educationalContent.pos_codes) {
            return { label: posCode, definition: '' };
        }

        const posData = this.educationalContent.pos_codes[posCode];
        return posData ? posData : { label: posCode, definition: '' };
    }

    /**
     * Get language label
     */
    getLanguageLabel(langCode) {
        if (!this.educationalContent || !this.educationalContent.language_codes) {
            return { label: langCode };
        }

        const langData = this.educationalContent.language_codes[langCode];
        return langData ? langData : { label: langCode };
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
