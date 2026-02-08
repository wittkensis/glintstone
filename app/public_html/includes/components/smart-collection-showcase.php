<?php
/**
 * Smart Collection Showcase Component
 *
 * Generic component for displaying a Smart Collection on the homepage
 * Shows tablet cards with explanatory blurbs for why they're included
 *
 * Required variables:
 * @var array $collection - Smart Collection data from smart_collections table
 * @var array $tablets - Array of tablets from executeSmartCollection()
 * @var int $totalCount - Total count of tablets in this Smart Collection
 *
 * Optional variables:
 * @var int $columns - Number of columns in grid (default: 4)
 */

if (!isset($collection) || !isset($tablets)) {
    throw new Exception('Smart Collection Showcase requires $collection and $tablets variables');
}

$columns = $columns ?? 4;
$totalCount = $totalCount ?? count($tablets);

// Load required helpers
require_once __DIR__ . '/../helpers/display.php';
require_once __DIR__ . '/../helpers/smart-collections.php';
?>

<section class="smart-collection-showcase" role="region"
         aria-labelledby="collection-<?= $collection['smart_collection_id'] ?>-heading">

    <div class="section-header">
        <div class="section-header__content">
            <h2 id="collection-<?= $collection['smart_collection_id'] ?>-heading">
                <span class="collection-icon" aria-hidden="true"><?= $collection['icon'] ?></span>
                <?= htmlspecialchars($collection['name']) ?>
            </h2>
            <p class="section-description">
                <?= htmlspecialchars($collection['description']) ?>
            </p>
        </div>
        <div class="section-stats">
            <span class="stat-badge"><?= number_format($totalCount) ?> tablets</span>
        </div>
    </div>

    <?php if (empty($tablets)): ?>
    <div class="empty-state">
        <div class="empty-icon">📚</div>
        <h3>No tablets found</h3>
        <p>This collection doesn't have any tablets matching the criteria yet.</p>
    </div>
    <?php else: ?>
    <div class="tablet-grid tablet-grid--<?= $columns ?>col">
        <?php foreach ($tablets as $tablet):
            $reason = getTabletNoteworthyReason($tablet);
            $noteworthy_type = $tablet['noteworthy_reason'] ?? '';
        ?>
        <div class="smart-tablet-card-wrapper">
            <?php
            // Render tablet card using existing component
            require __DIR__ . '/tablet-card.php';
            ?>

            <!-- Explanatory Blurb -->
            <?php if ($reason): ?>
            <div class="noteworthy-badge noteworthy-badge--<?= $noteworthy_type ?>">
                <?php if ($noteworthy_type === 'literary'): ?>
                    <span class="badge-icon">📖</span>
                <?php elseif ($noteworthy_type === 'quality'): ?>
                    <span class="badge-icon">✨</span>
                <?php elseif ($noteworthy_type === 'connected'): ?>
                    <span class="badge-icon">🔗</span>
                <?php elseif ($noteworthy_type === 'pipeline'): ?>
                    <span class="badge-icon">🎯</span>
                <?php elseif ($noteworthy_type === 'temporal'): ?>
                    <span class="badge-icon">⚡</span>
                <?php endif; ?>
                <span class="badge-text"><?= htmlspecialchars($reason) ?></span>
            </div>
            <?php endif; ?>
        </div>
        <?php endforeach; ?>
    </div>

    <div class="showcase-footer">
        <a href="/tablets/list.php?collection=<?= $collection['smart_collection_id'] ?>&smart=1"
           class="btn btn--primary">
            View All <?= htmlspecialchars($collection['name']) ?> →
        </a>
    </div>
    <?php endif; ?>
</section>
