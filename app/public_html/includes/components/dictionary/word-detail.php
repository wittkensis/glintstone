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

// Load centralized educational text
$_edContent = require __DIR__ . '/../../educational-content.php';
$_sectionDesc = $_edContent['section_descriptions'];

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
                    <span class="word-header__citation"><?= htmlspecialchars($entry['citation_form']) ?></span>
                    <button class="btn btn--icon word-share-btn" data-action="share" data-url="/dictionary/?word=<?= urlencode($entry['entry_id']) ?>" title="Copy link to clipboard">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/>
                            <polyline points="16 6 12 2 8 6"/>
                            <line x1="12" y1="2" x2="12" y2="15"/>
                        </svg>
                    </button>
                </h1>
                <?php if (!empty($entry['guide_word'])): ?>
                <p class="word-header__guide-word"><?= htmlspecialchars($entry['guide_word']) ?></p>
                <?php endif; ?>
            </div>
        </div>
    </div>

    <!-- Word Metadata (follows tablet detail pattern) -->
    <div class="word-meta">
        <dl class="word-meta__row">
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
        <p class="section-description"><?= $_sectionDesc['meanings'] ?></p>
        <p class="section-description"><?= $_sectionDesc['senses_explanation'] ?></p>
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
        <p class="section-description"><?= $_sectionDesc['attested_forms'] ?></p>
        <?php if (!empty($variants)): ?>
        <div class="variants-chart" data-show-all="false">
            <?php foreach (array_slice($variants, 0, $maxFormsToShow) as $variant): ?>
            <?php $percentage = $maxCount > 0 ? ($variant['count'] / $maxCount) * 100 : 0; ?>
            <div class="variant-bar">
                <span class="variant-form"><?= htmlspecialchars($variant['form']) ?></span>
                <div class="variant-frequency-container">
                    <div class="variant-frequency" style="--bar-width: <?= $percentage ?>%"></div>
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
                        <div class="variant-frequency" style="--bar-width: <?= $percentage ?>%"></div>
                    </div>
                    <span class="variant-count"><?= $variant['count'] ?> attestations</span>
                </div>
                <?php endforeach; ?>
            </div>
            <?php endif; ?>
        </div>
        <?php if ($showMoreNeeded): ?>
        <button class="btn" data-action="toggle-variants" data-show-text="Show all <?= $totalForms ?> forms" data-hide-text="Show less" style="margin-top: var(--space-4);">
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
        <p class="section-description"><?= $_sectionDesc['cuneiform_signs'] ?></p>
        <?php if (!empty($signs)): ?>
        <div class="related-words-grid">
            <?php foreach ($signs as $sign): ?>
            <a href="/dictionary/signs/?sign=<?= urlencode($sign['sign_id']) ?>" class="list-item list-item--card sign-card" data-sign-id="<?= htmlspecialchars($sign['sign_id']) ?>">
                <div class="sign-card__info">
                    <div class="list-item__header">
                        <span class="list-item__title"><?= htmlspecialchars($sign['sign_id']) ?></span>
                        <?php if (!empty($sign['sign_value'])): ?>
                        <span class="list-item__subtitle"><?= htmlspecialchars($sign['sign_value']) ?></span>
                        <?php endif; ?>
                    </div>
                    <?php
                    $metaParts = [];
                    if (!empty($sign['value_type'])) $metaParts[] = $sign['value_type'];
                    if (!empty($sign['sign_type'])) $metaParts[] = $sign['sign_type'];
                    if (!empty($metaParts)): ?>
                    <div class="list-item__meta"><?= htmlspecialchars(implode(' · ', $metaParts)) ?></div>
                    <?php endif; ?>
                </div>
                <?php if (!empty($sign['utf8'])): ?>
                <span class="sign-card__glyph"><?= $sign['utf8'] ?></span>
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
        <p class="section-description"><?= $_sectionDesc['related_words'] ?></p>
        <?php if ($hasRelated): ?>

        <?php
        // Render a related word as a list-item--card
        $renderRelatedWord = function($rel) use ($languageLabels) {
            $langLabel = \Glintstone\Data\Labels::getLabel('language', $rel['language'] ?? null);
            $posLabel = \Glintstone\Data\Labels::getLabel('pos', $rel['pos'] ?? null);
            $href = '/dictionary/?word=' . urlencode($rel['entry_id']);
            ?>
            <a href="<?= $href ?>" class="list-item list-item--card" data-entry-id="<?= htmlspecialchars($rel['entry_id']) ?>">
                <div class="list-item__header">
                    <span class="list-item__title"><?= htmlspecialchars($rel['headword']) ?></span>
                    <?php if (!empty($rel['guide_word'])): ?>
                    <span class="list-item__subtitle"><?= htmlspecialchars($rel['guide_word']) ?></span>
                    <?php endif; ?>
                </div>
                <div class="list-item__meta">
                    <?php
                    $metaParts = [];
                    if (!empty($posLabel)) $metaParts[] = htmlspecialchars($posLabel);
                    if (!empty($langLabel)) $metaParts[] = htmlspecialchars($langLabel);
                    echo implode('<span class="list-item__sep" aria-hidden="true">&middot;</span>', array_map(fn($v) => "<span>{$v}</span>", $metaParts));
                    ?>
                    <?php if ($rel['icount']): ?>
                    <span class="list-item__count"><?= number_format($rel['icount']) ?></span>
                    <?php endif; ?>
                </div>
                <?php if (!empty($rel['notes'])): ?>
                <div class="list-item__notes"><?= htmlspecialchars($rel['notes']) ?></div>
                <?php endif; ?>
            </a>
            <?php
        };
        ?>

        <?php if (!empty($related['translations'])): ?>
        <div class="related-group">
            <h3>Bilingual Equivalents</h3>
            <div class="related-words-grid">
                <?php foreach ($related['translations'] as $rel): ?>
                <?php $renderRelatedWord($rel); ?>
                <?php endforeach; ?>
            </div>
        </div>
        <?php endif; ?>

        <?php if (!empty($related['synonyms'])): ?>
        <div class="related-group">
            <h3>Synonyms</h3>
            <div class="related-words-grid">
                <?php foreach ($related['synonyms'] as $rel): ?>
                <?php $renderRelatedWord($rel); ?>
                <?php endforeach; ?>
            </div>
        </div>
        <?php endif; ?>

        <?php if (!empty($related['cognates'])): ?>
        <div class="related-group">
            <h3>Cognates</h3>
            <div class="related-words-grid">
                <?php foreach ($related['cognates'] as $rel): ?>
                <?php $renderRelatedWord($rel); ?>
                <?php endforeach; ?>
            </div>
        </div>
        <?php endif; ?>

        <?php if (!empty($related['see_also'])): ?>
        <div class="related-group">
            <h3>See Also</h3>
            <div class="related-words-grid">
                <?php foreach ($related['see_also'] as $rel): ?>
                <?php $renderRelatedWord($rel); ?>
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
        <p class="section-description"><?= $_sectionDesc['tablets'] ?></p>
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
</div>
