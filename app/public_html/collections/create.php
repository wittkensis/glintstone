<?php
/**
 * Create Collection Handler
 * Processes new collection form submission
 */

require_once __DIR__ . '/../includes/db.php';

// Only accept POST requests
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Location: /collections/new.php');
    exit;
}

// Validate required fields
$name = trim($_POST['name'] ?? '');
$description = trim($_POST['description'] ?? '');

if (empty($name)) {
    // TODO: Add flash message system
    header('Location: /collections/new.php?error=name_required');
    exit;
}

// Validate lengths
if (mb_strlen($name) > 255) {
    header('Location: /collections/new.php?error=name_too_long');
    exit;
}

if (mb_strlen($description) > 2000) {
    header('Location: /collections/new.php?error=description_too_long');
    exit;
}

// Create the collection
try {
    $collectionId = createCollection($name, $description);

    // Redirect to the new collection's detail page
    header("Location: /collections/detail.php?id=$collectionId");
    exit;
} catch (Exception $e) {
    // Log error and redirect back with error message
    error_log("Error creating collection: " . $e->getMessage());
    header('Location: /collections/new.php?error=creation_failed');
    exit;
}
