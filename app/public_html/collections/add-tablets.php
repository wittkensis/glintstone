<?php
/**
 * Add Tablets to Collection Handler
 * Processes bulk tablet additions from the browser
 */

require_once __DIR__ . '/../includes/db.php';

// Only accept POST requests
if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    header('Location: /collections/');
    exit;
}

// Get and validate parameters
$collectionId = (int)($_POST['collection_id'] ?? 0);
$pNumbers = $_POST['p_numbers'] ?? [];

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

// Validate p_numbers is an array
if (!is_array($pNumbers)) {
    $pNumbers = [$pNumbers];
}

// Filter out empty values and sanitize
$pNumbers = array_filter(array_map('trim', $pNumbers));

if (empty($pNumbers)) {
    // No tablets selected, redirect back to browser
    header("Location: /collections/browser.php?collection_id=$collectionId&error=no_tablets_selected");
    exit;
}

// Add tablets to collection
$addedCount = 0;
$duplicateCount = 0;

foreach ($pNumbers as $pNumber) {
    try {
        $result = addTabletToCollection($collectionId, $pNumber);
        if ($result) {
            $addedCount++;
        } else {
            $duplicateCount++;
        }
    } catch (Exception $e) {
        // Log error but continue with other tablets
        error_log("Error adding tablet $pNumber to collection $collectionId: " . $e->getMessage());
    }
}

// Redirect to collection detail with success message
$message = "$addedCount tablet" . ($addedCount !== 1 ? 's' : '') . " added";
if ($duplicateCount > 0) {
    $message .= " ($duplicateCount already in collection)";
}

// For now, just redirect (later can add flash message system)
header("Location: /collections/detail.php?id=$collectionId&added=$addedCount");
exit;
