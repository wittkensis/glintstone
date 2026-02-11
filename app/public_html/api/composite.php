<?php
/**
 * Composite Text API
 * Returns composite metadata and all tablets that belong to it
 */

require_once __DIR__ . '/_error-handler.php';

try {
    require_once __DIR__ . '/../includes/db.php';
} catch (Throwable $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Failed to load dependencies', 'message' => $e->getMessage()]);
    exit;
}

$qNumber = $_GET['q'] ?? null;

if (!$qNumber) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing q parameter']);
    exit;
}

$composite = getCompositeMetadata($qNumber);
if (!$composite) {
    http_response_code(404);
    echo json_encode(['error' => 'Composite not found']);
    exit;
}

$tablets = getTabletsInComposite($qNumber);

echo json_encode([
    'composite' => $composite,
    'tablets' => $tablets,
    'count' => count($tablets)
]);
