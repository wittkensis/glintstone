<?php
/**
 * New Collection Form
 * Create a new collection
 */

require_once __DIR__ . '/../includes/db.php';

$pageTitle = 'Create Collection';

require_once __DIR__ . '/../includes/header.php';
?>

<link rel="stylesheet" href="/assets/css/components/forms.css">

<main class="form-page">
    <div class="form-container">
        <div class="form-header">
            <a href="/collections/" class="back-link">← Back to Collections</a>
            <h1>New Collection</h1>
            <p class="subtitle">Organize tablets by theme, period, or research topic</p>
        </div>

        <form method="POST" action="/collections/create.php" class="collection-form">
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
                    placeholder="e.g., Old Babylonian Administrative Texts"
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
                    placeholder="Add notes about what this collection contains, your research focus, or any other relevant details..."></textarea>
                <p class="form-help">Optional: Add context or notes about this collection</p>
            </div>

            <div class="form-actions">
                <a href="/collections/" class="btn-secondary">Cancel</a>
                <button type="submit" class="btn-primary">Create Collection</button>
            </div>
        </form>
    </div>
</main>

<?php require_once __DIR__ . '/../includes/footer.php'; ?>
