<?php
/**
 * Tablet Card Component
 * Reusable card for displaying tablet metadata
 *
 * Required variables:
 * @var array $tablet - Tablet data with metadata
 *
 * Optional variables:
 * @var bool $selectable - Show checkbox for multi-select (default: false)
 * @var int $collection_id - If set, shows remove button for collection context
 */

// Set defaults
$selectable = $selectable ?? false;
$hasCollectionId = isset($collection_id);

// Get language abbreviation
$langAbbr = getLanguageAbbreviation($tablet['language']);
?>
<a href="/tablets/detail.php?p=<?= urlencode($tablet['p_number']) ?>"
   class="tablet-card <?= $selectable ? 'selectable' : '' ?>"
   data-p-number="<?= htmlspecialchars($tablet['p_number']) ?>">

    <?php if ($selectable): ?>
    <label class="card-checkbox-wrapper" onclick="event.preventDefault(); event.stopPropagation();">
        <input type="checkbox"
               class="card-checkbox"
               name="p_numbers[]"
               value="<?= htmlspecialchars($tablet['p_number']) ?>"
               data-p-number="<?= htmlspecialchars($tablet['p_number']) ?>">
    </label>
    <?php endif; ?>

    <?php if ($hasCollectionId): ?>
    <form method="POST" action="/collections/remove-tablet.php" class="card-remove-form">
        <input type="hidden" name="collection_id" value="<?= $collection_id ?>">
        <input type="hidden" name="p_number" value="<?= htmlspecialchars($tablet['p_number']) ?>">
        <button type="submit" class="card-remove-btn" onclick="event.preventDefault(); event.stopPropagation(); if(confirm('Remove this tablet from the collection?')) this.form.submit();" title="Remove from collection">×</button>
    </form>
    <?php endif; ?>

    <!-- Language Badge -->
    <?php if ($langAbbr): ?>
    <span class="lang-badge" title="<?= htmlspecialchars($tablet['language']) ?>"><?= $langAbbr ?></span>
    <?php endif; ?>

    <!-- Full-card Image -->
    <div class="card-image">
        <img src="/api/thumbnail.php?p=<?= urlencode($tablet['p_number']) ?>&size=200"
             alt="<?= htmlspecialchars($tablet['designation'] ?? $tablet['p_number']) ?>"
             loading="lazy"
             onerror="this.parentElement.classList.add('no-image')">
        <div class="card-placeholder">
            <span class="cuneiform-icon">𒀭</span>
        </div>
    </div>

    <!-- Overlay Info Panel -->
    <div class="card-overlay">

        <!-- Pipeline Status Bar -->
        <div class="card-pipeline-bar">
            <span class="pipeline-segment" data-status="<?= getPipelineSegmentStatus('image', $tablet) ?>" title="Image"></span>
            <span class="pipeline-segment" data-status="<?= getPipelineSegmentStatus('signs', $tablet) ?>" title="Sign Detection"></span>
            <span class="pipeline-segment" data-status="<?= getPipelineSegmentStatus('transliteration', $tablet) ?>" title="Transliteration"></span>
            <span class="pipeline-segment" data-status="<?= getPipelineSegmentStatus('lemmas', $tablet) ?>" title="Lemmas"></span>
            <span class="pipeline-segment" data-status="<?= getPipelineSegmentStatus('translation', $tablet) ?>" title="Translation"></span>
        </div>


        <span class="card-p-number"><?= htmlspecialchars($tablet['p_number']) ?></span>
        <?php if ($tablet['period']): ?>
        <span class="meta-period"><?= htmlspecialchars(truncateText($tablet['period'], 25)) ?></span>
        <?php endif; ?>
        <?php if ($tablet['provenience']): ?>
        <span class="meta-site"><?= htmlspecialchars(truncateText($tablet['provenience'], 20)) ?></span>
        <?php endif; ?>
        <?php if ($tablet['genre']): ?>
        <span class="meta-genre"><?= htmlspecialchars(truncateText($tablet['genre'], 20)) ?></span>
        <?php endif; ?>
        <!--<div class="card-designation"><?= htmlspecialchars($tablet['designation'] ?? 'Unknown') ?></div>-->
    </div>
</a>
