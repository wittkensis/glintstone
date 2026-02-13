<?php
/**
 * Signs Groupings Panel Component
 * Column 1: Category navigation with expandable sections
 *
 * Required variables:
 * @var array $counts - Grouping counts from SignRepository::getGroupCounts()
 *   - total: Total sign count
 *   - polyphony: Array of range => count
 *   - usage: Array of range => count
 *   - word_count: Array of range => count
 *   - sign_type: Array of type => count
 *   - has_glyph: Array of yes/no => count
 *
 * Optional variables:
 * @var string $activeGroup - Currently active group type (default: 'all')
 * @var string $activeValue - Currently active group value (default: null)
 */

$activeGroup = $activeGroup ?? 'all';
$activeValue = $activeValue ?? null;

// Auto-expand section containing active filter
$expandedSections = [];
if ($activeGroup !== 'all') {
    $expandedSections[] = $activeGroup;
}

// Labels for each grouping dimension
$polyphonyLabels = [
    '0' => 'No readings',
    '1' => '1 reading',
    '2-5' => '2-5 readings',
    '6-10' => '6-10 readings',
    '11-20' => '11-20 readings',
    '20+' => '20+ readings',
];

$usageLabels = [
    '0' => 'Unattested',
    '1-10' => 'Rare (1-10)',
    '11-100' => 'Uncommon (11-100)',
    '101-1000' => 'Common (101-1000)',
    '1000+' => 'Very Common (1000+)',
];

$wordCountLabels = [
    '0' => 'No words',
    '1-5' => '1-5 words',
    '6-20' => '6-20 words',
    '20+' => '20+ words',
];

$signTypeLabels = [
    'simple' => 'Simple',
    'compound' => 'Compound',
    'variant' => 'Variant',
];

$hasGlyphLabels = [
    'yes' => 'Has Unicode glyph',
    'no' => 'No glyph available',
];

/**
 * Render a grouping item
 */
function renderSignGroupingItem($type, $value, $label, $count, $activeGroup, $activeValue) {
    $isActive = ($type === 'all' && $activeGroup === 'all') ||
                ($type === $activeGroup && $value === $activeValue);
    $activeClass = $isActive ? 'dict-groupings__item--active' : '';

    $dataAttrs = $type === 'all'
        ? 'data-group="all"'
        : 'data-group="' . htmlspecialchars($type) . '" data-value="' . htmlspecialchars($value) . '"';

    return <<<HTML
    <button class="dict-groupings__item {$activeClass}" {$dataAttrs}>
        <span class="dict-groupings__item-label">{$label}</span>
        <span class="dict-groupings__item-count">{$count}</span>
    </button>
HTML;
}
?>

<div class="dict-groupings">
    <button class="dict-groupings__close" aria-label="Close groupings panel">
        <svg class="dict-groupings__close-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M6 18L18 6M6 6l12 12"/>
        </svg>
    </button>

    <nav class="dict-groupings__nav">
        <!-- All Signs -->
        <?= renderSignGroupingItem('all', null, 'All Signs', number_format($counts['total'] ?? 0), $activeGroup, $activeValue) ?>

        <!-- By Polyphony (value count) -->
        <div class="dict-groupings__section" data-expanded="<?= in_array('polyphony', $expandedSections) ? 'true' : 'false' ?>">
            <button class="dict-groupings__section-header">
                <span>By Polyphony</span>
                <svg class="dict-groupings__section-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M6 9l6 6 6-6"/>
                </svg>
            </button>
            <div class="dict-groupings__section-content">
                <?php foreach ($polyphonyLabels as $range => $label): ?>
                    <?php $count = $counts['polyphony'][$range] ?? 0; ?>
                    <?php if ($count > 0): ?>
                        <?= renderSignGroupingItem('polyphony', $range, $label, number_format($count), $activeGroup, $activeValue) ?>
                    <?php endif; ?>
                <?php endforeach; ?>
            </div>
        </div>

        <!-- By Usage (corpus occurrences) -->
        <div class="dict-groupings__section" data-expanded="<?= in_array('usage', $expandedSections) ? 'true' : 'false' ?>">
            <button class="dict-groupings__section-header">
                <span>By Usage</span>
                <svg class="dict-groupings__section-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M6 9l6 6 6-6"/>
                </svg>
            </button>
            <div class="dict-groupings__section-content">
                <?php foreach ($usageLabels as $range => $label): ?>
                    <?php $count = $counts['usage'][$range] ?? 0; ?>
                    <?php if ($count > 0): ?>
                        <?= renderSignGroupingItem('usage', $range, $label, number_format($count), $activeGroup, $activeValue) ?>
                    <?php endif; ?>
                <?php endforeach; ?>
            </div>
        </div>

        <!-- By Word Count -->
        <div class="dict-groupings__section" data-expanded="<?= in_array('word_count', $expandedSections) ? 'true' : 'false' ?>">
            <button class="dict-groupings__section-header">
                <span>By Word Count</span>
                <svg class="dict-groupings__section-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M6 9l6 6 6-6"/>
                </svg>
            </button>
            <div class="dict-groupings__section-content">
                <?php foreach ($wordCountLabels as $range => $label): ?>
                    <?php $count = $counts['word_count'][$range] ?? 0; ?>
                    <?php if ($count > 0): ?>
                        <?= renderSignGroupingItem('word_count', $range, $label, number_format($count), $activeGroup, $activeValue) ?>
                    <?php endif; ?>
                <?php endforeach; ?>
            </div>
        </div>

        <!-- By Sign Type -->
        <div class="dict-groupings__section" data-expanded="<?= in_array('sign_type', $expandedSections) ? 'true' : 'false' ?>">
            <button class="dict-groupings__section-header">
                <span>By Sign Type</span>
                <svg class="dict-groupings__section-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M6 9l6 6 6-6"/>
                </svg>
            </button>
            <div class="dict-groupings__section-content">
                <?php foreach ($signTypeLabels as $type => $label): ?>
                    <?php $count = $counts['sign_type'][$type] ?? 0; ?>
                    <?php if ($count > 0): ?>
                        <?= renderSignGroupingItem('sign_type', $type, $label, number_format($count), $activeGroup, $activeValue) ?>
                    <?php endif; ?>
                <?php endforeach; ?>
            </div>
        </div>

        <!-- Has Glyph -->
        <div class="dict-groupings__section" data-expanded="<?= in_array('has_glyph', $expandedSections) ? 'true' : 'false' ?>">
            <button class="dict-groupings__section-header">
                <span>Has Glyph</span>
                <svg class="dict-groupings__section-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M6 9l6 6 6-6"/>
                </svg>
            </button>
            <div class="dict-groupings__section-content">
                <?php foreach ($hasGlyphLabels as $val => $label): ?>
                    <?php $count = $counts['has_glyph'][$val] ?? 0; ?>
                    <?php if ($count > 0): ?>
                        <?= renderSignGroupingItem('has_glyph', $val, $label, number_format($count), $activeGroup, $activeValue) ?>
                    <?php endif; ?>
                <?php endforeach; ?>
            </div>
        </div>
    </nav>
</div>
