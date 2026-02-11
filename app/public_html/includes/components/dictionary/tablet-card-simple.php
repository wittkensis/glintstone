<?php
/**
 * Simple Tablet Card Component (Dictionary Context)
 * Minimal card for showing tablets in word detail view
 * Without pipeline status indicator
 *
 * Required variables:
 * @var array $tablet - Tablet data with p_number, period, provenience, genre
 */
?>
<a href="/tablets/detail.php?p=<?= urlencode($tablet['p_number']) ?>"
   class="card tablet-card"
   data-p-number="<?= htmlspecialchars($tablet['p_number']) ?>">

    <!-- Full-card Image -->
    <div class="card-image">
        <img src="/api/thumbnail.php?p=<?= urlencode($tablet['p_number']) ?>&size=200"
             alt="<?= htmlspecialchars($tablet['p_number']) ?>"
             loading="lazy"
             onerror="this.parentElement.classList.add('no-image')">
        <div class="card-placeholder">
            <span class="cuneiform-icon">𒀭</span>
        </div>
    </div>

    <!-- Overlay Info Panel -->
    <div class="card-details card-overlay">
        <span class="card-eyebrow p-number"><?= htmlspecialchars($tablet['p_number']) ?></span>
        <?php if (!empty($tablet['period'])): ?>
        <span class="card-primary meta-period"><?= htmlspecialchars(truncateText($tablet['period'], 25)) ?></span>
        <?php endif; ?>
        <?php if (!empty($tablet['provenience'])): ?>
        <span class="card-meta"><?= htmlspecialchars(truncateText($tablet['provenience'], 20)) ?></span>
        <?php endif; ?>
        <?php if (!empty($tablet['genre'])): ?>
        <span class="card-meta"><?= htmlspecialchars(truncateText($tablet['genre'], 20)) ?></span>
        <?php endif; ?>
    </div>
</a>
