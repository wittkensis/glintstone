<?php
/**
 * Collections List Page
 * Displays all user collections with preview thumbnails
 */

require_once __DIR__ . '/../includes/db.php';
require_once __DIR__ . '/../includes/helpers/display.php';

$pageTitle = 'Collections';

// Get all collections
$collections = getCollections();

// Get preview tablets for each collection (first 4)
foreach ($collections as &$collection) {
    $collection['preview_tablets'] = getCollectionPreviewTablets($collection['collection_id'], 4);
}
unset($collection); // Break reference

require_once __DIR__ . '/../includes/header.php';
?>

<link rel="stylesheet" href="/assets/css/components/collection-cards.css">
<link rel="stylesheet" href="/assets/css/components/empty-states.css">

<main class="collections-page">
    <div class="page-header">
        <h1>Collections</h1>
        <p class="subtitle">Organize tablets into themed collections</p>
        <div class="header-actions">
            <a href="/collections/new.php" class="btn-primary">Create New Collection</a>
        </div>
    </div>

    <?php if (empty($collections)): ?>
        <!-- Empty State -->
        <div class="empty-state">
            <div class="empty-icon">📚</div>
            <h2>No collections yet</h2>
            <p>Create your first collection to organize tablets by theme, period, or research topic.</p>
            <a href="/collections/new.php" class="btn-primary">Create Collection</a>
        </div>
    <?php else: ?>
        <!-- Collections Grid -->
        <div class="collection-grid">
            <?php foreach ($collections as $collection): ?>
            <a href="/collections/detail.php?id=<?= $collection['collection_id'] ?>" class="collection-card">
                <!-- Preview Grid (first 4 tablets) -->
                <div class="collection-cover">
                    <?php if (!empty($collection['preview_tablets'])): ?>
                        <?php foreach ($collection['preview_tablets'] as $tablet): ?>
                            <div class="cover-thumb">
                                <img src="/api/thumbnail.php?p=<?= urlencode($tablet['p_number']) ?>&size=100"
                                     alt="<?= htmlspecialchars($tablet['designation'] ?? $tablet['p_number']) ?>"
                                     loading="lazy"
                                     onerror="this.parentElement.classList.add('no-image')">
                            </div>
                        <?php endforeach; ?>
                        <?php
                        // Fill empty slots if less than 4 tablets
                        $emptySlots = 4 - count($collection['preview_tablets']);
                        for ($i = 0; $i < $emptySlots; $i++):
                        ?>
                            <div class="cover-thumb empty">
                                <span class="cuneiform-icon">𒀭</span>
                            </div>
                        <?php endfor; ?>
                    <?php else: ?>
                        <!-- All empty if no tablets -->
                        <?php for ($i = 0; $i < 4; $i++): ?>
                            <div class="cover-thumb empty">
                                <span class="cuneiform-icon">𒀭</span>
                            </div>
                        <?php endfor; ?>
                    <?php endif; ?>
                </div>

                <!-- Collection Metadata -->
                <div class="collection-meta">
                    <h3 class="collection-name"><?= htmlspecialchars($collection['name']) ?></h3>
                    <?php if ($collection['description']): ?>
                        <p class="collection-description">
                            <?= htmlspecialchars(mb_substr($collection['description'], 0, 120)) ?>
                            <?= mb_strlen($collection['description']) > 120 ? '...' : '' ?>
                        </p>
                    <?php endif; ?>
                    <div class="collection-stats">
                        <span class="stat">
                            <?= $collection['tablet_count'] ?>
                            <?= $collection['tablet_count'] === 1 ? 'tablet' : 'tablets' ?>
                        </span>
                    </div>
                </div>
            </a>
            <?php endforeach; ?>
        </div>
    <?php endif; ?>
</main>

<script src="/assets/js/filters.js"></script>

<?php require_once __DIR__ . '/../includes/footer.php'; ?>
