<?php
/**
 * Glintstone - Collaborative Cuneiform Research Platform
 * Homepage: Progress Meter & Featured Collections
 */

require_once __DIR__ . '/includes/db.php';
require_once __DIR__ . '/includes/helpers/homepage.php';
require_once __DIR__ . '/includes/helpers/collections.php';

$pageTitle = 'Home';

// Fetch data for homepage
$kpiData = getKPIMetrics();
$featuredCollections = getRandomCollections(3);

require_once __DIR__ . '/includes/header.php';
?>

<!-- Homepage-specific CSS -->
<link rel="stylesheet" href="/assets/css/components/progress-meter.css">
<link rel="stylesheet" href="/assets/css/components/collection-cards.css">
<link rel="stylesheet" href="/assets/css/pages/homepage.css">

<main class="homepage-container">

    <!-- Progress Meter Section -->
    <section class="progress-meter-section">
        <?php require __DIR__ . '/includes/components/progress-meter.php'; ?>
    </section>

    <!-- Visual Separator -->
    <div class="section-divider"></div>

    <!-- Featured Collections Section -->
    <section class="featured-collections">
        <header class="featured-collections-header">
            <h2>Explore Collections</h2>
            <p>Discover curated sets of tablets organized by theme, period, and scholarly interest</p>
        </header>

        <?php if (!empty($featuredCollections)): ?>
        <div class="collection-grid">
            <?php foreach ($featuredCollections as $collection): ?>
            <a href="/collections/detail.php?id=<?= $collection['collection_id'] ?>" class="collection-card">
                <!-- 2x2 Preview Grid -->
                <div class="collection-cover">
                    <?php
                    $displayedThumbs = 0;
                    foreach ($collection['preview_tablets'] as $tablet):
                        $displayedThumbs++;
                    ?>
                        <div class="cover-thumb">
                            <img src="/api/thumbnail.php?p=<?= urlencode($tablet['p_number']) ?>&size=100"
                                 alt="<?= htmlspecialchars($tablet['designation'] ?? $tablet['p_number']) ?>"
                                 loading="lazy"
                                 onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                            <div class="cover-thumb__fallback" style="display:none;">
                                <span class="cuneiform-icon">𒀭</span>
                            </div>
                        </div>
                    <?php endforeach; ?>

                    <?php
                    // Fill empty slots with fallback icon
                    $emptySlots = 4 - $displayedThumbs;
                    for ($i = 0; $i < $emptySlots; $i++):
                    ?>
                        <div class="cover-thumb empty">
                            <span class="cuneiform-icon">𒀭</span>
                        </div>
                    <?php endfor; ?>
                </div>

                <!-- Collection Metadata -->
                <div class="collection-meta">
                    <h3 class="collection-name"><?= htmlspecialchars($collection['name']) ?></h3>
                    <?php if (!empty($collection['description'])): ?>
                        <p class="collection-description">
                            <?= htmlspecialchars(mb_substr($collection['description'], 0, 120)) ?>
                            <?= mb_strlen($collection['description']) > 120 ? '...' : '' ?>
                        </p>
                    <?php endif; ?>
                    <div class="collection-stats">
                        <span class="stat">
                            <?= number_format($collection['tablet_count']) ?>
                            <?= $collection['tablet_count'] === 1 ? 'tablet' : 'tablets' ?>
                        </span>
                    </div>
                </div>
            </a>
            <?php endforeach; ?>
        </div>
        <?php else: ?>
        <!-- Empty State -->
        <div class="empty-state">
            <div class="empty-icon">📚</div>
            <h3>No collections yet</h3>
            <p>Collections will appear here once created.</p>
        </div>
        <?php endif; ?>
    </section>
</main>

<?php require_once __DIR__ . '/includes/footer.php'; ?>
