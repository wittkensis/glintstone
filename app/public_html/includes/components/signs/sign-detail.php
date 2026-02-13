<?php
/**
 * Sign Detail Component
 * Column 3: Full sign detail view
 *
 * Required variables:
 * @var array $signDetail - Sign detail data with:
 *   - sign: Base sign info (sign_id, utf8, sign_type, most_common_value)
 *   - values: Grouped readings (logographic, syllabic, determinative, other)
 *   - words: Array of words using this sign
 *   - stats: Usage statistics (total_unique_words, total_corpus_occurrences)
 *   - homophones: Signs sharing reading values
 */

$sign = $signDetail['sign'];
$values = $signDetail['values'];
$words = $signDetail['words'];
$stats = $signDetail['stats'];
$homophones = $signDetail['homophones'];

$totalValues = count($values['logographic']) + count($values['syllabic'])
             + count($values['determinative']) + count($values['other']);

$signTypeLabels = [
    'simple' => 'Simple',
    'compound' => 'Compound',
    'variant' => 'Variant',
];
$signTypeLabel = $signTypeLabels[$sign['sign_type'] ?? ''] ?? ($sign['sign_type'] ?? 'Unknown');

// Unicode code point from UTF-8 character
$codePoint = '';
if (!empty($sign['utf8'])) {
    $codePoint = 'U+' . strtoupper(dechex(mb_ord($sign['utf8'], 'UTF-8')));
}
?>

<div class="sign-detail-content">
    <!-- Sign Header -->
    <div class="page-header sign-header">
        <div class="page-header-main">
            <div class="page-header-title">
                <h1>
                    <?php if (!empty($sign['utf8'])): ?>
                        <span class="sign-header__glyph-box"><span class="sign-header__glyph"><?= $sign['utf8'] ?></span></span>
                    <?php endif; ?>
                    <span class="sign-header__id"><?= htmlspecialchars($sign['sign_id']) ?></span>
                    <button class="btn btn--icon sign-share-btn" data-action="share" data-url="/dictionary/signs/?sign=<?= urlencode($sign['sign_id']) ?>" title="Copy link to clipboard">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8"/>
                            <polyline points="16 6 12 2 8 6"/>
                            <line x1="12" y1="2" x2="12" y2="15"/>
                        </svg>
                    </button>
                </h1>
                <?php if (!empty($sign['most_common_value'])): ?>
                    <p class="sign-header__value"><?= htmlspecialchars($sign['most_common_value']) ?></p>
                <?php endif; ?>
            </div>
        </div>
    </div>

    <!-- Sign Metadata -->
    <div class="word-meta">
        <dl class="word-meta__row">
            <div class="meta-item">
                <dt>Sign Type</dt>
                <dd><?= htmlspecialchars($signTypeLabel) ?></dd>
            </div>
            <?php if ($codePoint): ?>
            <div class="meta-item">
                <dt>Unicode</dt>
                <dd><code><?= $codePoint ?></code></dd>
            </div>
            <?php endif; ?>
            <div class="meta-item">
                <dt>Readings</dt>
                <dd><?= $totalValues ?></dd>
            </div>
            <div class="meta-item">
                <dt>Words</dt>
                <dd><?= number_format($stats['total_unique_words']) ?></dd>
            </div>
            <div class="meta-item">
                <dt>Occurrences</dt>
                <dd><?= number_format($stats['total_corpus_occurrences']) ?></dd>
            </div>
        </dl>
    </div>

    <!-- Readings (Values) -->
    <section class="word-section">
        <h2>Readings <?php if ($totalValues > 0): ?><span class="section-count-badge"><?= $totalValues ?></span><?php endif; ?></h2>
        <p class="section-description">How this sign is read in different contexts.</p>

        <?php if ($totalValues > 0): ?>
            <?php
            $allValues = array_merge($values['logographic'], $values['syllabic'], $values['determinative'], $values['other']);
            $maxFreq = 0;
            foreach ($allValues as $v) {
                $maxFreq = max($maxFreq, (int)($v['frequency'] ?? 0));
            }
            $visibleLimit = 12;
            $hasMore = count($allValues) > $visibleLimit;
            ?>

            <div class="variants-chart">
                <?php foreach ($allValues as $i => $v): ?>
                <?php $percentage = $maxFreq > 0 ? ((int)($v['frequency'] ?? 0) / $maxFreq) * 100 : 0; ?>
                <div class="variant-bar<?= ($hasMore && $i >= $visibleLimit) ? ' variants-hidden-item' : '' ?>">
                    <span class="variant-form"><?= htmlspecialchars($v['value']) ?></span>
                    <div class="variant-frequency-container">
                        <div class="variant-frequency" style="--bar-width: <?= $percentage ?>%"></div>
                    </div>
                    <?php if ((int)($v['frequency'] ?? 0) > 0): ?>
                    <span class="variant-count"><?= number_format((int)$v['frequency']) ?></span>
                    <?php endif; ?>
                </div>
                <?php endforeach; ?>
            </div>
            <?php if ($hasMore): ?>
            <button class="btn" data-action="toggle-readings"
                    data-show-text="Show all <?= $totalValues ?> readings"
                    data-hide-text="Show fewer"
                    style="margin-top: var(--space-4);">
                Show all <?= $totalValues ?> readings
            </button>
            <?php endif; ?>
        <?php else: ?>
            <p class="section-placeholder">No readings documented for this sign.</p>
        <?php endif; ?>
    </section>

    <!-- Homophones -->
    <?php if (!empty($homophones)): ?>
    <section class="word-section">
        <h2>Homophones <span class="section-count-badge"><?= count($homophones) ?></span></h2>
        <p class="section-description">Other signs that share one or more reading values with this sign.</p>
        <div class="related-words-grid">
            <?php foreach ($homophones as $h): ?>
            <a href="/dictionary/signs/?sign=<?= urlencode($h['sign_id']) ?>" class="list-item list-item--card sign-card" data-sign-id="<?= htmlspecialchars($h['sign_id']) ?>">
                <div class="sign-card__info">
                    <div class="list-item__header">
                        <span class="list-item__title"><?= htmlspecialchars($h['sign_id']) ?></span>
                        <?php if (!empty($h['most_common_value'])): ?>
                        <span class="list-item__subtitle"><?= htmlspecialchars($h['most_common_value']) ?></span>
                        <?php endif; ?>
                    </div>
                    <div class="list-item__meta">
                        <?php
                        $metaParts = [];
                        if (!empty($h['value_count'])) {
                            $metaParts[] = $h['value_count'] . ' reading' . ($h['value_count'] != 1 ? 's' : '');
                        }
                        if (!empty($h['word_count'])) {
                            $metaParts[] = $h['word_count'] . ' word' . ($h['word_count'] != 1 ? 's' : '');
                        }
                        echo htmlspecialchars(implode(' · ', $metaParts));
                        ?>
                    </div>
                </div>
                <?php if (!empty($h['utf8'])): ?>
                <span class="sign-card__glyph"><?= $h['utf8'] ?></span>
                <?php endif; ?>
            </a>
            <?php endforeach; ?>
        </div>
    </section>
    <?php endif; ?>

    <!-- Words Using This Sign -->
    <section class="word-section">
        <h2>Words <?php if (!empty($words)): ?><span class="section-count-badge"><?= count($words) ?></span><?php endif; ?></h2>
        <p class="section-description">Dictionary entries that use this sign in their written form.</p>
        <?php if (!empty($words)): ?>
        <?php
        $wordsLimit = 12;
        $hasMoreWords = count($words) > $wordsLimit;
        ?>
        <div class="related-words-grid related-words-grid--3col">
            <?php foreach ($words as $i => $w): ?>
            <a href="/dictionary/?word=<?= urlencode($w['entry_id']) ?>" class="list-item list-item--card<?= ($hasMoreWords && $i >= $wordsLimit) ? ' variants-hidden-item' : '' ?>" data-entry-id="<?= htmlspecialchars($w['entry_id']) ?>">
                <div class="list-item__header">
                    <span class="list-item__title"><?= htmlspecialchars($w['headword']) ?></span>
                    <?php if (!empty($w['guide_word'])): ?>
                    <span class="list-item__subtitle"><?= htmlspecialchars($w['guide_word']) ?></span>
                    <?php endif; ?>
                </div>
                <div class="list-item__meta">
                    <?php if (!empty($w['sign_value'])): ?>
                    <span class="badge badge--sm"><?= htmlspecialchars($w['sign_value']) ?></span>
                    <?php endif; ?>
                    <?php if (!empty($w['language'])): ?>
                    <span class="badge badge--sm"><?= htmlspecialchars(\Glintstone\Data\Labels::getLabel('language', $w['language'])) ?></span>
                    <?php endif; ?>
                    <?php if (($w['icount'] ?? 0) > 0): ?>
                    <span class="list-item__count"><?= number_format((int)$w['icount']) ?></span>
                    <?php endif; ?>
                </div>
            </a>
            <?php endforeach; ?>
        </div>
        <?php if ($hasMoreWords): ?>
        <button class="btn" data-action="toggle-words"
                data-show-text="Show all <?= count($words) ?> words"
                data-hide-text="Show fewer"
                style="margin-top: var(--space-4);">
            Show all <?= count($words) ?> words
        </button>
        <?php endif; ?>
        <?php else: ?>
        <p class="section-placeholder">No dictionary words linked to this sign yet.</p>
        <?php endif; ?>
    </section>
</div>
