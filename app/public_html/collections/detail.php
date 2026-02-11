<?php
/**
 * Collection Detail Page
 * Displays a single collection with its tablets
 */

require_once __DIR__ . '/../includes/db.php';
require_once __DIR__ . '/../includes/helpers/display.php';

// Get collection ID
$collectionId = (int)($_GET['id'] ?? 0);

if ($collectionId <= 0) {
    header('Location: /collections/');
    exit;
}

// Get collection metadata
$collection = getCollection($collectionId);

if (!$collection) {
    // Collection not found
    header('Location: /collections/');
    exit;
}

// Pagination
$page = max(1, (int)($_GET['page'] ?? 1));
$tabletsPerPage = 24;
$offset = ($page - 1) * $tabletsPerPage;

// Get tablets in this collection
$tablets = getCollectionTablets($collectionId, $tabletsPerPage, $offset);
$totalTablets = $collection['tablet_count'];
$totalPages = (int)ceil($totalTablets / $tabletsPerPage);

$pageTitle = htmlspecialchars($collection['name']) . ' - Collection';

// Enqueue collections CSS
require_once __DIR__ . '/../includes/css.php';
CSSLoader::enqueue('page-collections');
require_once __DIR__ . '/../includes/header.php';
?>

<main class="collection-detail-page">
    <?php if (!empty($collection['image_path'])): ?>
        <!-- Hero Banner with Image -->
        <div class="page-hero">
            <div class="page-hero-image">
                <img src="<?= htmlspecialchars($collection['image_path']) ?>"
                     alt="<?= htmlspecialchars($collection['name']) ?>">
            </div>
            <div class="page-hero-overlay"></div>
            <div class="page-hero-content">
                <div class="page-hero-header">
                    <div class="page-hero-title">
                        <a href="/collections/" class="back-link">← Back to Collections</a>
                        <h1><?= htmlspecialchars($collection['name']) ?></h1>
                        <?php if ($collection['description']): ?>
                            <p class="subtitle">
                                <?= nl2br(htmlspecialchars($collection['description'])) ?>
                            </p>
                        <?php endif; ?>
                    </div>
                    <div class="page-hero-actions">
                        <a href="/collections/browser.php?collection_id=<?= $collectionId ?>" class="btn btn--primary">Add Tablets</a>
                        <a href="/collections/edit.php?id=<?= $collectionId ?>" class="btn btn--icon" aria-label="Edit collection" title="Edit collection">
                            <?= icon('edit') ?>
                        </a>
                        <form method="POST" action="/collections/delete.php">
                            <input type="hidden" name="collection_id" value="<?= $collectionId ?>">
                            <button type="submit" class="btn btn--icon btn--danger" aria-label="Delete collection" title="Delete collection" onclick="return confirm('Delete this collection? This will not delete the tablets themselves.');">
                                <?= icon('trash') ?>
                            </button>
                        </form>
                    </div>
                </div>
                <div class="page-hero-metadata">
                    <div class="page-hero-stats">
                        <span class="stat">
                            <?= number_format($totalTablets) ?>
                            <?= $totalTablets === 1 ? 'tablet' : 'tablets' ?>
                        </span>
                    </div>
                </div>
            </div>
        </div>
    <?php else: ?>
        <!-- Standard Page Header (no image) -->
        <div class="page-header">
            <div class="page-header-main">
                <div class="page-header-title">
                    <a href="/collections/" class="back-link">← Back to Collections</a>
                    <h1><?= htmlspecialchars($collection['name']) ?></h1>
                    <?php if ($collection['description']): ?>
                        <p class="subtitle">
                            <?= nl2br(htmlspecialchars($collection['description'])) ?>
                        </p>
                    <?php endif; ?>
                </div>
                <div class="page-header-actions">
                    <a href="/collections/browser.php?collection_id=<?= $collectionId ?>" class="btn btn--primary">Add Tablets</a>
                    <a href="/collections/edit.php?id=<?= $collectionId ?>" class="btn btn--icon" aria-label="Edit collection" title="Edit collection">
                        <?= icon('edit') ?>
                    </a>
                    <form method="POST" action="/collections/delete.php">
                        <input type="hidden" name="collection_id" value="<?= $collectionId ?>">
                        <button type="submit" class="btn btn--icon btn--danger" aria-label="Delete collection" title="Delete collection" onclick="return confirm('Delete this collection? This will not delete the tablets themselves.');">
                            <?= icon('trash') ?>
                        </button>
                    </form>
                </div>
            </div>
            <div class="page-header-metadata">
                <div class="page-stats">
                    <span class="stat">
                        <?= number_format($totalTablets) ?>
                        <?= $totalTablets === 1 ? 'tablet' : 'tablets' ?>
                    </span>
                </div>
            </div>
        </div>
    <?php endif; ?>

    <?php if (empty($tablets)): ?>
        <!-- Empty State -->
        <div class="empty-state">
            <div class="empty-icon">𒀭</div>
            <h2>This collection is empty</h2>
            <p>Add tablets to start organizing your research.</p>
            <a href="/collections/browser.php?collection_id=<?= $collectionId ?>" class="btn-primary">Add Tablets</a>
        </div>
    <?php else: ?>
        <!-- Tablet Grid -->
        <div class="tablet-grid">
            <?php
            $collection_id = $collectionId; // Set for tablet-card component
            foreach ($tablets as $tablet):
            ?>
                <?php include __DIR__ . '/../includes/components/tablet-card.php'; ?>
            <?php endforeach; ?>
        </div>

        <?php if ($totalPages > 1): ?>
        <!-- Pagination -->
        <nav class="pagination">
            <?php if ($page > 1): ?>
                <a href="?id=<?= $collectionId ?>&page=<?= $page - 1 ?>" class="pagination-link">Previous</a>
            <?php endif; ?>

            <?php for ($i = 1; $i <= $totalPages; $i++): ?>
                <?php if ($i === $page): ?>
                    <span class="pagination-link active"><?= $i ?></span>
                <?php else: ?>
                    <a href="?id=<?= $collectionId ?>&page=<?= $i ?>" class="pagination-link"><?= $i ?></a>
                <?php endif; ?>
            <?php endfor; ?>

            <?php if ($page < $totalPages): ?>
                <a href="?id=<?= $collectionId ?>&page=<?= $page + 1 ?>" class="pagination-link">Next</a>
            <?php endif; ?>
        </nav>
        <?php endif; ?>
    <?php endif; ?>
</main>

<?php require_once __DIR__ . '/../includes/footer.php'; ?>
