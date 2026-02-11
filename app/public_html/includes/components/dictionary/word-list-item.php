<?php
/**
 * Dictionary Word List Item Component
 * Reusable word item for Column 2 word list
 *
 * Required variables:
 * @var array $word - Word data with:
 *   - entry_id: Unique identifier
 *   - headword: Display form
 *   - citation_form: Scholarly citation form
 *   - guide_word: English meaning
 *   - pos: Part of speech code
 *   - language: Language code
 *   - icount: Attestation count
 *
 * Optional variables:
 * @var bool $isActive - Whether this item is selected (default: false)
 * @var bool $isSkeleton - Render as skeleton loading state (default: false)
 * @var string $activeGroup - Currently active filter group (default: 'all')
 * @var string $activeValue - Currently active filter value (default: null)
 */

// Set defaults
$isActive = $isActive ?? false;
$isSkeleton = $isSkeleton ?? false;
$activeGroup = $activeGroup ?? 'all';
$activeValue = $activeValue ?? null;

// Determine which badges to show based on active filter
$showPosBadge = ($activeGroup !== 'pos');
$showLangBadge = ($activeGroup !== 'language');

// Language labels (full names, never codes)
$languageLabels = [
    'akk' => 'Akkadian',
    'akk-x-stdbab' => 'Standard Babylonian',
    'akk-x-oldbab' => 'Old Babylonian',
    'akk-x-neoass' => 'Neo-Assyrian',
    'sux' => 'Sumerian',
    'sux-x-emesal' => 'Emesal',
    'xhu' => 'Hurrian',
    'uga' => 'Ugaritic',
    'elx' => 'Elamite',
    'qpn' => 'Names',
    'qpn-x-places' => 'Places'
];

// POS labels - abbreviated for grammatical, full for name types
$posLabels = [
    'N' => 'Noun',
    'V' => 'Verb',
    'AJ' => 'Adj',
    'AV' => 'Adv',
    'NU' => 'Num',
    'PRP' => 'Prep',
    'CNJ' => 'Conj',
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

// Build class list
$classes = ['dict-word-item'];
if ($isActive) $classes[] = 'dict-word-item--active';
if ($isSkeleton) $classes[] = 'dict-word-item--skeleton';
$classString = implode(' ', $classes);

// Get labels
$langLabel = $languageLabels[$word['language'] ?? ''] ?? ($word['language'] ?? '');
$posLabel = $posLabels[$word['pos'] ?? ''] ?? ($word['pos'] ?? '');
?>

<div class="<?= $classString ?>"
     data-entry-id="<?= htmlspecialchars($word['entry_id'] ?? '') ?>"
     <?php if (!$isSkeleton): ?>tabindex="0" role="button"<?php endif; ?>>

    <div class="dict-word-item__header">
        <span class="dict-word-item__headword"><?= htmlspecialchars($word['citation_form'] ?? $word['headword'] ?? '') ?></span>
        <?php if (!empty($word['guide_word'])): ?>
            <span class="dict-word-item__guide-word"><?= htmlspecialchars($word['guide_word']) ?></span>
        <?php endif; ?>
    </div>

    <div class="dict-word-item__meta">
        <?php if ($showPosBadge && !empty($posLabel)): ?>
            <span class="dict-word-item__badge dict-word-item__badge--pos"><?= htmlspecialchars($posLabel) ?></span>
        <?php endif; ?>
        <?php if ($showLangBadge && !empty($langLabel)): ?>
            <span class="dict-word-item__badge dict-word-item__badge--lang"><?= htmlspecialchars($langLabel) ?></span>
        <?php endif; ?>
        <span class="dict-word-item__count"><?= number_format($word['icount'] ?? 0) ?></span>
    </div>
</div>
