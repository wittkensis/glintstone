<?php
/**
 * Remove Tablet from Collection Handler
 * Removes a single tablet from a collection
 */

require_once __DIR__ . '/../includes/db.php';

// Only accept POST requests
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Location: /collections/');
    exit;
}

// Get and validate parameters
$collectionId = (int)($_POST['collection_id'] ?? 0);
$pNumber = trim($_POST['p_number'] ?? '');

if ($collectionId <= 0 || empty($pNumber)) {
    header('Location: /collections/');
    exit;
}

// Verify collection exists
$collection = getCollection($collectionId);
if (!$collection) {
    header('Location: /collections/');
    exit;
}

// Remove the tablet
try {
    removeTabletFromCollection($collectionId, $pNumber);

    // Redirect back to collection detail
    header("Location: /collections/detail.php?id=$collectionId");
    exit;
} catch (Exception $e) {
    error_log("Error removing tablet from collection: " . $e->getMessage());
    header("Location: /collections/detail.php?id=$collectionId&error=removal_failed");
    exit;
}
