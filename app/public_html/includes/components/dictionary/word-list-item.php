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
 */

// Set defaults
$isActive = $isActive ?? false;
$isSkeleton = $isSkeleton ?? false;

// Language labels
$languageLabels = [
    'akk' => 'Akkadian',
    'akk-x-stdbab' => 'Std. Bab.',
    'akk-x-oldbab' => 'Old Bab.',
    'akk-x-neoass' => 'Neo-Ass.',
    'sux' => 'Sumerian',
    'sux-x-emesal' => 'Emesal',
    'qpn' => 'Names',
    'qpn-x-places' => 'Places'
];

// POS labels (abbreviated)
$posLabels = [
    'N' => 'N',
    'V' => 'V',
    'AJ' => 'Adj',
    'AV' => 'Adv',
    'NU' => 'Num',
    'PRP' => 'Prep',
    'CNJ' => 'Conj',
    'PN' => 'PN',
    'DN' => 'DN',
    'GN' => 'GN',
    'RN' => 'RN',
    'TN' => 'TN'
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
        <span class="dict-word-item__headword"><?= htmlspecialchars($word['headword'] ?? '') ?></span>
        <?php if (!empty($word['citation_form']) && $word['citation_form'] !== $word['headword']): ?>
            <span class="dict-word-item__citation"><?= htmlspecialchars($word['citation_form']) ?></span>
        <?php endif; ?>
        <?php if (!empty($word['guide_word'])): ?>
            <span class="dict-word-item__guide-word">[<?= htmlspecialchars($word['guide_word']) ?>]</span>
        <?php endif; ?>
    </div>

    <div class="dict-word-item__meta">
        <?php if (!empty($posLabel)): ?>
            <span class="dict-word-item__badge dict-word-item__badge--pos"><?= htmlspecialchars($posLabel) ?></span>
        <?php endif; ?>
        <?php if (!empty($langLabel)): ?>
            <span class="dict-word-item__badge dict-word-item__badge--lang"><?= htmlspecialchars($langLabel) ?></span>
        <?php endif; ?>
        <span class="dict-word-item__count"><?= number_format($word['icount'] ?? 0) ?></span>
    </div>
</div>
