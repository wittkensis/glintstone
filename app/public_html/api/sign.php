<?php
/**
 * Sign lookup API endpoint
 * Returns sign data from OGSL
 */

require_once __DIR__ . '/../includes/db.php';

header('Content-Type: application/json');

$query = $_GET['q'] ?? null;

if (!$query) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing query parameter']);
    exit;
}

$db = getDB();

// Search by UTF-8 character, sign ID, or value
$results = [];

// Try exact UTF-8 match first
$stmt = $db->prepare("SELECT * FROM signs WHERE utf8 = :q");
$stmt->bindValue(':q', $query, SQLITE3_TEXT);
$result = $stmt->execute();
$sign = $result->fetchArray(SQLITE3_ASSOC);

if (!$sign) {
    // Try sign ID
    $stmt = $db->prepare("SELECT * FROM signs WHERE sign_id = :q");
    $stmt->bindValue(':q', $query, SQLITE3_TEXT);
    $result = $stmt->execute();
    $sign = $result->fetchArray(SQLITE3_ASSOC);
}

if (!$sign) {
    // Try by value
    $stmt = $db->prepare("
        SELECT s.* FROM signs s
        JOIN sign_values sv ON s.sign_id = sv.sign_id
        WHERE sv.value = :q
        LIMIT 1
    ");
    $stmt->bindValue(':q', strtolower($query), SQLITE3_TEXT);
    $result = $stmt->execute();
    $sign = $result->fetchArray(SQLITE3_ASSOC);
}

if ($sign) {
    // Get all values for this sign
    $values = getSignValues($sign['sign_id']);
    $sign['values'] = $values;
    echo json_encode($sign);
} else {
    http_response_code(404);
    echo json_encode(['error' => 'Sign not found']);
}
