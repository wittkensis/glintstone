<?php
/**
 * Dictionary Word List Item Component
 * Reusable word item using shared .list-item component
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

use Glintstone\Data\Labels;

// Set defaults
$isActive = $isActive ?? false;
$isSkeleton = $isSkeleton ?? false;
$activeGroup = $activeGroup ?? 'all';
$activeValue = $activeValue ?? null;

// Determine which badges to show based on active filter
$showPosBadge = ($activeGroup !== 'pos');
$showLangBadge = ($activeGroup !== 'language');

// Build class list
$classes = ['list-item'];
if ($isActive) $classes[] = 'list-item--active';
if ($isSkeleton) $classes[] = 'list-item--skeleton';
$classString = implode(' ', $classes);

// Get labels from centralized source
$langLabel = Labels::getLabel('language', $word['language'] ?? null);
$posLabel = Labels::getLabel('pos', $word['pos'] ?? null);
?>

<div class="<?= $classString ?>"
     data-entry-id="<?= htmlspecialchars($word['entry_id'] ?? '') ?>"
     <?php if (!$isSkeleton): ?>tabindex="0" role="button"<?php endif; ?>>

    <div class="list-item__header">
        <span class="list-item__title"><?= htmlspecialchars($word['citation_form'] ?? $word['headword'] ?? '') ?></span>
        <?php if (!empty($word['guide_word'])): ?>
            <span class="list-item__subtitle"><?= htmlspecialchars($word['guide_word']) ?></span>
        <?php endif; ?>
    </div>

    <div class="list-item__meta">
        <?php
        $metaParts = [];
        if ($showPosBadge && !empty($posLabel)) $metaParts[] = htmlspecialchars($posLabel);
        if ($showLangBadge && !empty($langLabel)) $metaParts[] = htmlspecialchars($langLabel);
        echo implode('<span class="list-item__sep" aria-hidden="true">&middot;</span>', array_map(fn($v) => "<span>{$v}</span>", $metaParts));
        ?>
        <span class="list-item__count"><?= number_format($word['icount'] ?? 0) ?></span>
    </div>
</div>
