<?php
/**
 * Dictionary Word Detail Component
 * Column 3: Full word detail view
 *
 * Required variables:
 * @var array $entry - Main entry data
 * @var array $variants - Variant forms with counts
 * @var array $signs - Cuneiform signs used in word
 * @var array $senses - Polysemic senses
 * @var array $attestations - Sample corpus attestations
 * @var array $related - Related words grouped by type
 * @var array|null $cad - CAD reference data (Akkadian only)
 *
 * Optional variables:
 * @var bool $embedded - Whether embedded in browser (default: false)
 */

// Set defaults
$embedded = $embedded ?? false;

// Language labels (full names, never codes)
$languageLabels = [
    'sux' => 'Sumerian',
    'sux-x-emesal' => 'Emesal',
    'akk' => 'Akkadian',
    'akk-x-stdbab' => 'Standard Babylonian',
    'akk-x-oldbab' => 'Old Babylonian',
    'akk-x-neoass' => 'Neo-Assyrian',
    'xhu' => 'Hurrian',
    'uga' => 'Ugaritic',
    'elx' => 'Elamite',
    'qpn' => 'Names',
    'qpn-x-places' => 'Place Names'
];

// POS labels
$posLabels = [
    'N' => 'Noun',
    'V' => 'Verb',
    'AJ' => 'Adjective',
    'AV' => 'Adverb',
    'NU' => 'Number',
    'PRP' => 'Preposition',
    'CNJ' => 'Conjunction',
    'PN' => 'Personal Name',
    'GN' => 'Geographic Name',
    'DN' => 'Divine Name',
    'SN' => 'Settlement Name',
    'TN' => 'Temple Name',
    'WN' => 'Watercourse Name',
    'RN' => 'Royal Name',
    'EN' => 'Ethnic Name',
    'CN' => 'Celestial Name',
    'ON' => 'Object Name',
    'MN' => 'Month Name',
    'AN' => 'Artifact Name'
];

// Check if we have secondary metadata
$hasSecondaryMeta = !empty($entry['semantic_category']) || !empty($entry['entry_id']);

$languageLabel = $languageLabels[$entry['language']] ?? $entry['language'];
$posLabel = $posLabels[$entry['pos']] ?? $entry['pos'];
?>

<div class="word-detail-content">
    <!-- Word Header -->
    <div class="page-header word-header">
        <div class="page-header-main">
            <div class="page-header-title">
                <?php if (!$embedded): ?>
                <a href="/dictionary/" class="back-link">← Back to Dictionary</a>
                <?php endif; ?>
                <h1>
                    <?= htmlspecialchars($entry['citation_form']) ?>
                    <button class="btn btn--icon word-share-btn" data-action="share" data-url="/dictionary/?word=<?= urlencode($entry['entry_id']) ?>" title="Copy link to clipboard">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/>
                            <polyline points="16 6 12 2 8 6"/>
                            <line x1="12" y1="2" x2="12" y2="15"/>
                        </svg>
                    </button>
                </h1>
            </div>
        </div>
    </div>

    <!-- Word Metadata (follows tablet detail pattern) -->
    <div class="word-meta">
        <dl class="word-meta__row">
            <div class="meta-item meta-item--primary">
                <dt>Guide Word</dt>
                <dd class="meta-guide-word"><?php if (!empty($entry['guide_word'])): ?><?= htmlspecialchars($entry['guide_word']) ?><?php else: ?><span class="meta-placeholder">—</span><?php endif; ?></dd>
            </div>
            <div class="meta-item">
                <dt>Language</dt>
                <dd><?= htmlspecialchars($languageLabel) ?></dd>
            </div>
            <div class="meta-item">
                <dt>Part of Speech</dt>
                <dd><?= htmlspecialchars($posLabel) ?></dd>
            </div>
            <div class="meta-item">
                <dt>Attestations</dt>
                <dd><?= number_format($entry['icount']) ?></dd>
            </div>
            <div class="meta-item">
                <button class="word-meta__toggle" id="word-meta-toggle" aria-expanded="false" aria-controls="word-meta-secondary">
                    <svg class="word-meta__toggle-icon" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <polyline points="9 18 15 12 9 6"/>
                    </svg>
                    More
                </button>
            </div>
        </dl>
        <dl class="word-meta__secondary" id="word-meta-secondary">
            <div class="meta-item">
                <dt>Entry ID</dt>
                <dd><?php if (!empty($entry['entry_id'])): ?><code><?= htmlspecialchars($entry['entry_id']) ?></code><?php else: ?><span class="meta-placeholder">—</span><?php endif; ?></dd>
            </div>
            <div class="meta-item">
                <dt>Semantic Category</dt>
                <dd><?php if (!empty($entry['semantic_category'])): ?><?= htmlspecialchars($entry['semantic_category']) ?><?php else: ?><span class="meta-placeholder">—</span><?php endif; ?></dd>
            </div>
        </dl>
    </div>

    <!-- Meanings (Polysemic Senses) -->
    <section class="word-section">
        <h2>Meanings <?php if (!empty($senses)): ?><span class="section-count-badge"><?= count($senses) ?></span><?php endif; ?></h2>
        <p class="section-description">Detailed senses with definitions, usage contexts, and frequency data. Different from the guide word above, which is a simple gloss for quick reference.</p>
        <?php if (!empty($senses)): ?>
        <ol class="meanings-list">
            <?php foreach ($senses as $sense): ?>
            <li class="meaning">
                <div class="meaning__header">
                    <strong><?= htmlspecialchars($sense['guide_word']) ?></strong>
                    <?php if ($sense['frequency_percentage']): ?>
                    <span class="meaning__usage"><?= round($sense['frequency_percentage']) ?>% of uses</span>
                    <?php endif; ?>
                </div>
                <?php if ($sense['definition']): ?>
                <p class="meaning__definition"><?= htmlspecialchars($sense['definition']) ?></p>
                <?php endif; ?>
                <?php if ($sense['usage_context']): ?>
                <p class="meaning__context"><?= htmlspecialchars($sense['usage_context']) ?></p>
                <?php endif; ?>
            </li>
            <?php endforeach; ?>
        </ol>
        <?php else: ?>
        <p class="section-placeholder">No meanings documented yet.</p>
        <?php endif; ?>
    </section>

    <!-- Attested Forms -->
    <?php
    $totalForms = !empty($variants) ? count($variants) : 0;
    $maxFormsToShow = 10;
    $showMoreNeeded = $totalForms > $maxFormsToShow;
    $maxCount = !empty($variants) ? max(array_column($variants, 'count')) : 0;
    ?>
    <section class="word-section">
        <h2>Attested Forms <?php if ($totalForms > 0): ?><span class="section-count-badge"><?= $totalForms ?></span><?php endif; ?></h2>
        <p class="section-description">Different spellings and grammatical forms found in the corpus, ordered by frequency.</p>
        <?php if (!empty($variants)): ?>
        <div class="variants-chart" data-show-all="false">
            <?php foreach (array_slice($variants, 0, $maxFormsToShow) as $variant): ?>
            <?php $percentage = $maxCount > 0 ? ($variant['count'] / $maxCount) * 100 : 0; ?>
            <div class="variant-bar">
                <span class="variant-form"><?= htmlspecialchars($variant['form']) ?></span>
                <div class="variant-frequency-container">
                    <div class="variant-frequency" style="width: <?= $percentage ?>%"></div>
                </div>
                <span class="variant-count"><?= $variant['count'] ?> attestations</span>
            </div>
            <?php endforeach; ?>
            <?php if ($showMoreNeeded): ?>
            <div class="variants-hidden" data-hidden-variants>
                <?php foreach (array_slice($variants, $maxFormsToShow) as $variant): ?>
                <?php $percentage = $maxCount > 0 ? ($variant['count'] / $maxCount) * 100 : 0; ?>
                <div class="variant-bar">
                    <span class="variant-form"><?= htmlspecialchars($variant['form']) ?></span>
                    <div class="variant-frequency-container">
                        <div class="variant-frequency" style="width: <?= $percentage ?>%"></div>
                    </div>
                    <span class="variant-count"><?= $variant['count'] ?> attestations</span>
                </div>
                <?php endforeach; ?>
            </div>
            <?php endif; ?>
        </div>
        <?php if ($showMoreNeeded): ?>
        <button class="show-more-toggle" data-action="toggle-variants" data-show-text="Show all <?= $totalForms ?> forms" data-hide-text="Show less">
            Show all <?= $totalForms ?> forms
        </button>
        <?php endif; ?>
        <?php else: ?>
        <p class="section-placeholder">No attested forms documented yet.</p>
        <?php endif; ?>
    </section>

    <!-- Cuneiform Signs -->
    <section class="word-section">
        <h2>Cuneiform Signs <?php if (!empty($signs)): ?><span class="section-count-badge"><?= count($signs) ?></span><?php endif; ?></h2>
        <p class="section-description">The signs used to write this word. Click a sign to explore all its readings.</p>
        <?php if (!empty($signs)): ?>
        <div class="sign-breakdown">
            <?php foreach ($signs as $sign): ?>
            <a href="/dictionary/sign/<?= urlencode($sign['sign_id']) ?>" class="sign-item">
                <span class="sign-cuneiform"><?= $sign['utf8'] ?? '' ?></span>
                <span class="sign-value"><?= htmlspecialchars($sign['sign_value']) ?></span>
                <?php if ($sign['value_type']): ?>
                <span class="sign-type"><?= htmlspecialchars($sign['value_type']) ?></span>
                <?php endif; ?>
            </a>
            <?php endforeach; ?>
        </div>
        <?php else: ?>
        <p class="section-placeholder">No cuneiform signs documented yet.</p>
        <?php endif; ?>
    </section>

    <!-- Related Words -->
    <?php
    $hasRelated = !empty($related['translations']) || !empty($related['synonyms']) ||
                  !empty($related['cognates']) || !empty($related['see_also']);
    ?>
    <section class="word-section">
        <h2>Related Words</h2>
        <p class="section-description">Bilingual equivalents, synonyms, and cognates across Sumerian and Akkadian.</p>
        <?php if ($hasRelated): ?>

        <?php if (!empty($related['translations'])): ?>
        <div class="related-group">
            <h3>Bilingual Equivalents</h3>
            <div class="related-words-grid">
                <?php foreach ($related['translations'] as $rel): ?>
                <a href="<?= $embedded ? '/dictionary/?word=' . urlencode($rel['entry_id']) : '/dictionary/?word=' . urlencode($rel['entry_id']) ?>"
                   class="card card-word"
                   data-entry-id="<?= htmlspecialchars($rel['entry_id']) ?>">
                    <div class="card-word__header">
                        <span class="card-word__headword"><?= htmlspecialchars($rel['headword']) ?></span>
                        <?php if ($rel['guide_word']): ?>
                        <span class="card-word__guide-word"><?= htmlspecialchars($rel['guide_word']) ?></span>
                        <?php endif; ?>
                    </div>
                    <div class="card-word__meta">
                        <span class="card-word__badge card-word__badge--lang"><?= htmlspecialchars($languageLabels[$rel['language']] ?? $rel['language']) ?></span>
                        <?php if ($rel['icount']): ?>
                        <span class="card-word__count"><?= number_format($rel['icount']) ?></span>
                        <?php endif; ?>
                    </div>
                    <?php if ($rel['notes']): ?>
                    <div class="card-word__notes"><?= htmlspecialchars($rel['notes']) ?></div>
                    <?php endif; ?>
                </a>
                <?php endforeach; ?>
            </div>
        </div>
        <?php endif; ?>

        <?php if (!empty($related['synonyms'])): ?>
        <div class="related-group">
            <h3>Synonyms</h3>
            <div class="related-words-grid">
                <?php foreach ($related['synonyms'] as $rel): ?>
                <a href="<?= $embedded ? '/dictionary/?word=' . urlencode($rel['entry_id']) : '/dictionary/?word=' . urlencode($rel['entry_id']) ?>"
                   class="card card-word"
                   data-entry-id="<?= htmlspecialchars($rel['entry_id']) ?>">
                    <div class="card-word__header">
                        <span class="card-word__headword"><?= htmlspecialchars($rel['headword']) ?></span>
                        <?php if ($rel['guide_word']): ?>
                        <span class="card-word__guide-word"><?= htmlspecialchars($rel['guide_word']) ?></span>
                        <?php endif; ?>
                    </div>
                    <div class="card-word__meta">
                        <?php if ($rel['icount']): ?>
                        <span class="card-word__count"><?= number_format($rel['icount']) ?></span>
                        <?php endif; ?>
                    </div>
                </a>
                <?php endforeach; ?>
            </div>
        </div>
        <?php endif; ?>

        <?php if (!empty($related['cognates'])): ?>
        <div class="related-group">
            <h3>Cognates</h3>
            <div class="related-words-grid">
                <?php foreach ($related['cognates'] as $rel): ?>
                <a href="<?= $embedded ? '/dictionary/?word=' . urlencode($rel['entry_id']) : '/dictionary/?word=' . urlencode($rel['entry_id']) ?>"
                   class="card card-word"
                   data-entry-id="<?= htmlspecialchars($rel['entry_id']) ?>">
                    <div class="card-word__header">
                        <span class="card-word__headword"><?= htmlspecialchars($rel['headword']) ?></span>
                    </div>
                    <div class="card-word__meta">
                        <span class="card-word__badge card-word__badge--lang"><?= htmlspecialchars($languageLabels[$rel['language']] ?? $rel['language']) ?></span>
                        <?php if ($rel['icount']): ?>
                        <span class="card-word__count"><?= number_format($rel['icount']) ?></span>
                        <?php endif; ?>
                    </div>
                </a>
                <?php endforeach; ?>
            </div>
        </div>
        <?php endif; ?>

        <?php if (!empty($related['see_also'])): ?>
        <div class="related-group">
            <h3>See Also</h3>
            <div class="related-words-grid">
                <?php foreach ($related['see_also'] as $rel): ?>
                <a href="<?= $embedded ? '/dictionary/?word=' . urlencode($rel['entry_id']) : '/dictionary/?word=' . urlencode($rel['entry_id']) ?>"
                   class="card card-word"
                   data-entry-id="<?= htmlspecialchars($rel['entry_id']) ?>">
                    <div class="card-word__header">
                        <span class="card-word__headword"><?= htmlspecialchars($rel['headword']) ?></span>
                        <?php if ($rel['guide_word']): ?>
                        <span class="card-word__guide-word"><?= htmlspecialchars($rel['guide_word']) ?></span>
                        <?php endif; ?>
                    </div>
                    <div class="card-word__meta">
                        <?php if ($rel['icount']): ?>
                        <span class="card-word__count"><?= number_format($rel['icount']) ?></span>
                        <?php endif; ?>
                    </div>
                </a>
                <?php endforeach; ?>
            </div>
        </div>
        <?php endif; ?>

        <?php else: ?>
        <p class="section-placeholder">No related words documented yet.</p>
        <?php endif; ?>
    </section>

    <!-- Tablets -->
    <section class="word-section">
        <h2>Tablets <?php if (!empty($attestations)): ?><span class="section-count-badge"><?= count($attestations) ?></span><?php endif; ?></h2>
        <p class="section-description">Ancient tablets where this word has been identified in the corpus.</p>
        <?php if (!empty($attestations)): ?>
        <div class="tablet-grid">
            <?php foreach ($attestations as $att): ?>
            <?php
            // Use simplified tablet card for dictionary context
            $tablet = [
                'p_number' => $att['p_number'],
                'period' => $att['period'] ?? null,
                'provenience' => $att['provenience'] ?? null,
                'genre' => $att['genre'] ?? null
            ];
            include __DIR__ . '/tablet-card-simple.php';
            ?>
            <?php endforeach; ?>
        </div>
        <?php else: ?>
        <p class="section-placeholder">No tablet attestations available yet.</p>
        <?php endif; ?>
    </section>

    <!-- CAD Reference -->
    <section class="word-section">
        <h2>Chicago Assyrian Dictionary</h2>
        <p class="section-description">Reference from the authoritative dictionary for Akkadian, published by the Oriental Institute.</p>
        <?php if ($cad): ?>
        <div class="cad-content">
            <div class="cad-header">
                <span class="volume-badge">CAD <?= htmlspecialchars($cad['volume']) ?>, pp. <?= $cad['page_start'] ?><?= $cad['page_end'] ? "-{$cad['page_end']}" : '' ?></span>
                <?php if ($cad['pdf_url']): ?>
                <a href="<?= htmlspecialchars($cad['pdf_url']) ?>/page/<?= $cad['page_start'] ?>" target="_blank" class="pdf-link">View PDF →</a>
                <?php endif; ?>
                <?php if ($cad['human_verified']): ?>
                <span class="verified-badge">✓ Verified</span>
                <?php endif; ?>
            </div>
            <?php if ($cad['etymology']): ?>
            <div class="cad-etymology">
                <strong>Etymology:</strong> <?= htmlspecialchars($cad['etymology']) ?>
            </div>
            <?php endif; ?>
            <?php if ($cad['semantic_notes']): ?>
            <div class="cad-notes"><?= htmlspecialchars($cad['semantic_notes']) ?></div>
            <?php endif; ?>
        </div>
        <?php else: ?>
        <p class="section-placeholder">No CAD reference available.</p>
        <?php endif; ?>
    </section>
</div>
