<?php
/**
 * Sign List Item Component
 * Reusable sign item for the signs browser list panel
 *
 * Required variables:
 * @var array $sign - Sign data with:
 *   - sign_id: Unique identifier (e.g. "KA", "|A.AN|")
 *   - utf8: Unicode cuneiform character
 *   - sign_type: simple/compound/variant
 *   - most_common_value: Primary reading
 *   - value_count: Number of distinct readings
 *   - word_count: Number of words using this sign
 *   - total_occurrences: Corpus occurrence count
 *
 * Optional variables:
 * @var bool $isActive - Whether this item is selected (default: false)
 * @var string $activeGroup - Currently active filter group (default: 'all')
 */

$isActive = $isActive ?? false;
$activeGroup = $activeGroup ?? 'all';

// Conditionally hide badges that match the active filter
$showValueBadge = ($activeGroup !== 'polyphony');
$showWordBadge = ($activeGroup !== 'word_count');

$classes = ['list-item', 'sign-list-item'];
if ($isActive) $classes[] = 'list-item--active';
$classString = implode(' ', $classes);
?>

<div class="<?= $classString ?>"
     data-sign-id="<?= htmlspecialchars($sign['sign_id'] ?? '') ?>"
     tabindex="0" role="button">

    <div class="sign-list-item__info">
        <div class="list-item__header">
            <span class="list-item__title"><?= htmlspecialchars($sign['sign_id'] ?? '') ?></span>
            <?php if (!empty($sign['most_common_value'])): ?>
                <span class="list-item__subtitle"><?= htmlspecialchars($sign['most_common_value']) ?></span>
            <?php endif; ?>
        </div>
        <div class="list-item__meta">
            <?php if ($showValueBadge && ($sign['value_count'] ?? 0) > 0): ?>
                <span class="badge badge--sm"><?= (int)$sign['value_count'] ?>v</span>
            <?php endif; ?>
            <?php if ($showWordBadge && ($sign['word_count'] ?? 0) > 0): ?>
                <span class="badge badge--sm"><?= (int)$sign['word_count'] ?>w</span>
            <?php endif; ?>
        </div>
    </div>

    <div class="sign-list-item__aside">
        <span class="sign-list-item__glyph"><?= $sign['utf8'] ?? '' ?></span>
        <?php if (($sign['total_occurrences'] ?? 0) > 0): ?>
            <span class="sign-list-item__count"><?= number_format((int)$sign['total_occurrences']) ?></span>
        <?php endif; ?>
    </div>
</div>
