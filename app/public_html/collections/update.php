<?php
/**
 * Update Collection
 * Handles POST request to update a collection's name and description
 */

require_once __DIR__ . '/../includes/db.php';

// Only accept POST requests
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Location: /collections/');
    exit;
}

// Get and validate collection ID
$collectionId = (int)($_POST['collection_id'] ?? 0);

if ($collectionId <= 0) {
    header('Location: /collections/');
    exit;
}

// Verify collection exists
$collection = getCollection($collectionId);
if (!$collection) {
    header('Location: /collections/');
    exit;
}

// Get form data
$name = trim($_POST['name'] ?? '');
$description = trim($_POST['description'] ?? '');

// Validate required fields
if (empty($name)) {
    header('Location: /collections/edit.php?id=' . $collectionId . '&error=missing_name');
    exit;
}

// Update the collection
$success = updateCollection($collectionId, $name, $description);

if ($success) {
    // Redirect back to collection detail page
    header('Location: /collections/detail.php?id=' . $collectionId . '&updated=1');
} else {
    // Redirect back to edit form with error
    header('Location: /collections/edit.php?id=' . $collectionId . '&error=update_failed');
}
exit;
