<?php
/**
 * Composite Text API
 * Returns composite metadata and all tablets that belong to it
 */

require_once __DIR__ . '/../includes/db.php';

header('Content-Type: application/json');

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
