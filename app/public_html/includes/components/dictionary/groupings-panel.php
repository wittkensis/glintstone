<?php
/**
 * Dictionary Groupings Panel Component
 * Column 1: Category navigation with expandable sections
 *
 * Required variables:
 * @var array $counts - Grouping counts from API
 *   - all: Total count
 *   - pos: Array of POS => count
 *   - language: Array of language => count
 *   - frequency: Array of range => count
 *
 * Optional variables:
 * @var string $activeGroup - Currently active group type (default: 'all')
 * @var string $activeValue - Currently active group value (default: null)
 * @var array $expandedSections - Array of expanded section names (default: ['pos', 'language'])
 */

// Set defaults
$activeGroup = $activeGroup ?? 'all';
$activeValue = $activeValue ?? null;
$expandedSections = $expandedSections ?? ['pos', 'language'];

// Language labels for display
$languageLabels = [
    'akk' => 'Akkadian',
    'akk-x-stdbab' => 'Standard Babylonian',
    'akk-x-oldbab' => 'Old Babylonian',
    'akk-x-neoass' => 'Neo-Assyrian',
    'sux' => 'Sumerian',
    'sux-x-emesal' => 'Emesal (Sumerian)',
    'xhu' => 'Hurrian',
    'uga' => 'Ugaritic',
    'elx' => 'Elamite',
    'qpn' => 'Proper Nouns',
    'qpn-x-places' => 'Place Names'
];

// True Parts of Speech (linguistic categories)
$posLabels = [
    'N' => 'Noun',
    'V' => 'Verb',
    'V/t' => 'Verb (transitive)',
    'V/i' => 'Verb (intransitive)',
    'AJ' => 'Adjective',
    'AV' => 'Adverb',
    'NU' => 'Number',
    'PRP' => 'Preposition',
    'PP' => 'Postposition',
    'CNJ' => 'Conjunction',
    'DP' => 'Demonstrative',
    'IP' => 'Interrogative',
    'RP' => 'Relative Pronoun',
    'XP' => 'Indefinite Pronoun',
    'REL' => 'Relative',
    'DET' => 'Determiner',
    'MOD' => 'Modifier',
    'J' => 'Interjection',
    'SBJ' => 'Subjunction',
    'QP' => 'Quantifier',
    'MA' => 'Auxiliary',
    'O' => 'Other',
    'M' => 'Morpheme'
];

// Proper Noun Types (name categories) - stored in POS field but are name classifications
$nameTypeLabels = [
    'PN' => 'Personal Name',
    'DN' => 'Divine Name',
    'GN' => 'Geographic Name',
    'SN' => 'Settlement Name',
    'TN' => 'Temple Name',
    'WN' => 'Watercourse Name',
    'RN' => 'Royal Name',
    'EN' => 'Ethnic Name',
    'CN' => 'Celestial Name',
    'ON' => 'Object Name',
    'MN' => 'Month Name',
    'LN' => 'Line Name',
    'FN' => 'Field Name',
    'AN' => 'Artifact Name'
];

// Codes that are name types (to separate from true POS)
$nameTypeCodes = array_keys($nameTypeLabels);

// Frequency range labels
$frequencyLabels = [
    '1' => 'Hapax (1)',
    '2-10' => 'Rare (2-10)',
    '11-100' => 'Uncommon (11-100)',
    '101-500' => 'Common (101-500)',
    '500+' => 'Very Common (500+)'
];

/**
 * Render a grouping item
 */
function renderGroupingItem($type, $value, $label, $count, $activeGroup, $activeValue) {
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
    <div class="dict-groupings__header">
        <h2 class="dict-groupings__title">Browse</h2>
        <button class="dict-groupings__close" aria-label="Close groupings panel">
            <svg class="dict-groupings__close-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M6 18L18 6M6 6l12 12"/>
            </svg>
        </button>
    </div>

    <nav class="dict-groupings__nav">
        <!-- All Words -->
        <?= renderGroupingItem('all', null, 'All Words', number_format($counts['all'] ?? 0), $activeGroup, $activeValue) ?>

        <!-- By Part of Speech (true linguistic categories only) -->
        <div class="dict-groupings__section" data-expanded="<?= in_array('pos', $expandedSections) ? 'true' : 'false' ?>">
            <button class="dict-groupings__section-header">
                <span>Part of Speech</span>
                <svg class="dict-groupings__section-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M6 9l6 6 6-6"/>
                </svg>
            </button>
            <div class="dict-groupings__section-content">
                <?php if (!empty($counts['pos'])): ?>
                    <?php foreach ($counts['pos'] as $pos => $count): ?>
                        <?php if ($count > 0 && !in_array($pos, $nameTypeCodes)): ?>
                            <?= renderGroupingItem('pos', $pos, $posLabels[$pos] ?? $pos, number_format($count), $activeGroup, $activeValue) ?>
                        <?php endif; ?>
                    <?php endforeach; ?>
                <?php endif; ?>
            </div>
        </div>

        <!-- By Name Type (proper noun categories) -->
        <div class="dict-groupings__section" data-expanded="<?= in_array('nametype', $expandedSections) ? 'true' : 'false' ?>">
            <button class="dict-groupings__section-header">
                <span>Name Type</span>
                <svg class="dict-groupings__section-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M6 9l6 6 6-6"/>
                </svg>
            </button>
            <div class="dict-groupings__section-content">
                <?php if (!empty($counts['pos'])): ?>
                    <?php foreach ($counts['pos'] as $pos => $count): ?>
                        <?php if ($count > 0 && in_array($pos, $nameTypeCodes)): ?>
                            <?= renderGroupingItem('pos', $pos, $nameTypeLabels[$pos] ?? $pos, number_format($count), $activeGroup, $activeValue) ?>
                        <?php endif; ?>
                    <?php endforeach; ?>
                <?php endif; ?>
            </div>
        </div>

        <!-- By Language -->
        <div class="dict-groupings__section" data-expanded="<?= in_array('language', $expandedSections) ? 'true' : 'false' ?>">
            <button class="dict-groupings__section-header">
                <span>Language</span>
                <svg class="dict-groupings__section-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M6 9l6 6 6-6"/>
                </svg>
            </button>
            <div class="dict-groupings__section-content">
                <?php if (!empty($counts['language'])): ?>
                    <?php foreach ($counts['language'] as $lang => $count): ?>
                        <?php if ($count > 0): ?>
                            <?= renderGroupingItem('language', $lang, $languageLabels[$lang] ?? $lang, number_format($count), $activeGroup, $activeValue) ?>
                        <?php endif; ?>
                    <?php endforeach; ?>
                <?php endif; ?>
            </div>
        </div>

        <!-- By Frequency -->
        <div class="dict-groupings__section" data-expanded="<?= in_array('frequency', $expandedSections) ? 'true' : 'false' ?>">
            <button class="dict-groupings__section-header">
                <span>Frequency</span>
                <svg class="dict-groupings__section-chevron" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M6 9l6 6 6-6"/>
                </svg>
            </button>
            <div class="dict-groupings__section-content">
                <?php if (!empty($counts['frequency'])): ?>
                    <?php foreach ($frequencyLabels as $range => $label): ?>
                        <?php $count = $counts['frequency'][$range] ?? 0; ?>
                        <?php if ($count > 0): ?>
                            <?= renderGroupingItem('frequency', $range, $label, number_format($count), $activeGroup, $activeValue) ?>
                        <?php endif; ?>
                    <?php endforeach; ?>
                <?php endif; ?>
            </div>
        </div>
    </nav>
</div>
