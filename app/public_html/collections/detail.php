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

require_once __DIR__ . '/../includes/header.php';
?>

<link rel="stylesheet" href="/assets/css/components/cards-overlay.css">
<link rel="stylesheet" href="/assets/css/components/cards-selectable.css">
<link rel="stylesheet" href="/assets/css/components/pagination.css">
<link rel="stylesheet" href="/assets/css/components/empty-states.css">
<link rel="stylesheet" href="/assets/css/pages/collection-detail.css">

<main class="collection-detail-page">
    <div class="collection-header">
        <a href="/collections/" class="back-link">← Back to Collections</a>

        <div class="collection-title-section">
            <h1><?= htmlspecialchars($collection['name']) ?></h1>
            <?php if ($collection['description']): ?>
                <p class="collection-description-full">
                    <?= nl2br(htmlspecialchars($collection['description'])) ?>
                </p>
            <?php endif; ?>
        </div>

        <div class="collection-actions">
            <a href="/collections/browser.php?collection_id=<?= $collectionId ?>" class="btn-primary">Add Tablets</a>
            <a href="/collections/edit.php?id=<?= $collectionId ?>" class="btn-secondary">Edit</a>
            <form method="POST" action="/collections/delete.php" style="display: inline;">
                <input type="hidden" name="collection_id" value="<?= $collectionId ?>">
                <button type="submit" class="btn-danger" onclick="return confirm('Delete this collection? This will not delete the tablets themselves.');">Delete</button>
            </form>
        </div>

        <div class="collection-stats">
            <span class="stat">
                <?= number_format($totalTablets) ?>
                <?= $totalTablets === 1 ? 'tablet' : 'tablets' ?>
            </span>
        </div>
    </div>

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
