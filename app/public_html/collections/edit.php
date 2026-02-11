<?php
/**
 * Edit Collection Form
 * Update an existing collection's name and description
 */

require_once __DIR__ . '/../includes/db.php';

// Get collection ID
$collectionId = (int)($_GET['id'] ?? 0);

if ($collectionId <= 0) {
    header('Location: /collections/');
    exit;
}

// Get collection data
$collection = getCollection($collectionId);

if (!$collection) {
    header('Location: /collections/');
    exit;
}

$pageTitle = 'Edit Collection';

require_once __DIR__ . '/../includes/header.php';
?>

<link rel="stylesheet" href="/assets/css/components/forms.css">

<main class="form-page">
    <div class="form-container">
        <div class="form-header">
            <a href="/collections/detail.php?id=<?= $collectionId ?>" class="back-link">← Back to Collection</a>
            <h1>Edit Collection</h1>
            <p class="subtitle">Update collection name and description</p>
        </div>

        <?php if (isset($_GET['error'])): ?>
            <div class="alert alert-error">
                Failed to update collection. Please try again.
            </div>
        <?php endif; ?>

        <form method="POST" action="/collections/update.php" class="collection-form">
            <input type="hidden" name="collection_id" value="<?= $collectionId ?>">

            <div class="form-group">
                <label for="name" class="form-label">
                    Collection Name <span class="required">*</span>
                </label>
                <input
                    type="text"
                    id="name"
                    name="name"
                    class="form-input"
                    required
                    maxlength="255"
                    value="<?= htmlspecialchars($collection['name']) ?>"
                    autofocus>
                <p class="form-help">Choose a descriptive name for your collection</p>
            </div>

            <div class="form-group">
                <label for="description" class="form-label">
                    Description
                </label>
                <textarea
                    id="description"
                    name="description"
                    class="form-textarea"
                    rows="5"
                    maxlength="2000"
                    placeholder="Add notes about what this collection contains, your research focus, or any other relevant details..."><?= htmlspecialchars($collection['description'] ?? '') ?></textarea>
                <p class="form-help">Optional: Add context or notes about this collection</p>
            </div>

            <div class="form-actions">
                <a href="/collections/detail.php?id=<?= $collectionId ?>" class="btn-secondary">Cancel</a>
                <button type="submit" class="btn-primary">Save Changes</button>
            </div>
        </form>
    </div>
</main>

<?php require_once __DIR__ . '/../includes/footer.php'; ?>
