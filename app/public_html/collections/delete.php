<?php
/**
 * Delete Collection
 * Handles POST request to delete a collection
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

// Delete the collection
// Note: This will cascade delete collection_members due to foreign key constraint
$success = deleteCollection($collectionId);

if ($success) {
    // Redirect to collections list with success message
    header('Location: /collections/?deleted=1');
} else {
    // Redirect back to collection detail with error
    header('Location: /collections/detail.php?id=' . $collectionId . '&error=delete_failed');
}
exit;
