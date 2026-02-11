<?php
/**
 * Batch check which words have glossary definitions
 * Returns a map of words to boolean (has definition or not)
 */

require_once __DIR__ . '/_error-handler.php';

try {
    require_once __DIR__ . '/../includes/db.php';
} catch (Throwable $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Failed to load dependencies', 'message' => $e->getMessage()]);
    exit;
}

$input = json_decode(file_get_contents('php://input'), true);
$words = $input['words'] ?? [];

if (empty($words) || !is_array($words)) {
    echo json_encode(['error' => 'Missing or invalid words array']);
    exit;
}

// Normalize and dedupe words
$words = array_unique(array_map('strtolower', $words));
$words = array_slice($words, 0, 500); // Limit to prevent abuse

$db = getDB();
$results = [];

// Check glossary_entries headwords
$placeholders = implode(',', array_fill(0, count($words), '?'));
$sql = "SELECT LOWER(headword) as word FROM glossary_entries WHERE LOWER(headword) IN ($placeholders)";
$stmt = $db->prepare($sql);

foreach ($words as $i => $word) {
    $stmt->bindValue($i + 1, $word, SQLITE3_TEXT);
}

$result = $stmt->execute();
$foundWords = [];
while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    $foundWords[$row['word']] = true;
}

// Also check glossary_forms for variant spellings
$sql = "SELECT LOWER(form) as word FROM glossary_forms WHERE LOWER(form) IN ($placeholders)";
$stmt = $db->prepare($sql);

foreach ($words as $i => $word) {
    $stmt->bindValue($i + 1, $word, SQLITE3_TEXT);
}

$result = $stmt->execute();
while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    $foundWords[$row['word']] = true;
}

// Build response with all queried words
foreach ($words as $word) {
    $results[$word] = isset($foundWords[$word]);
}

echo json_encode([
    'definitions' => $results
]);
