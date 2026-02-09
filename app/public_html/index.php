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
                <?php include __DIR__ . '/includes/components/collection-card.php'; ?>
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
