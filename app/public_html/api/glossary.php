<?php
/**
 * Glossary lookup API endpoint
 * Returns dictionary entries from ORACC glossaries
 */

require_once __DIR__ . '/../includes/db.php';

header('Content-Type: application/json');

$query = $_GET['q'] ?? null;
$language = $_GET['lang'] ?? null;
$limit = min(20, max(1, intval($_GET['limit'] ?? 10)));

if (!$query) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing query parameter']);
    exit;
}

$entries = searchGlossary($query, $language, $limit);

if (empty($entries)) {
    // Try partial match
    $db = getDB();
    $sql = "SELECT * FROM glossary_entries WHERE headword LIKE :q";
    if ($language) {
        $sql .= " AND language = :lang";
    }
    $sql .= " ORDER BY icount DESC LIMIT :limit";

    $stmt = $db->prepare($sql);
    $stmt->bindValue(':q', "%$query%", SQLITE3_TEXT);
    if ($language) {
        $stmt->bindValue(':lang', $language, SQLITE3_TEXT);
    }
    $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);

    $result = $stmt->execute();
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $entries[] = $row;
    }
}

echo json_encode([
    'query' => $query,
    'language' => $language,
    'count' => count($entries),
    'entries' => $entries
]);
