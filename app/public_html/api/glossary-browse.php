<?php
/**
 * Glossary browse API endpoint
 * Returns paginated dictionary entries with search and filtering
 *
 * Parameters:
 *   search   - Search query (optional, searches headword, citation_form, guide_word)
 *   language - Filter by language (optional, e.g., 'akk', 'sux')
 *   pos      - Filter by part of speech (optional, e.g., 'N', 'V')
 *   offset   - Pagination offset (default: 0)
 *   limit    - Results per page (default: 50, max: 100)
 */

require_once __DIR__ . '/../includes/db.php';

header('Content-Type: application/json');

// Get parameters
$search = $_GET['search'] ?? null;
$language = $_GET['language'] ?? null;
$pos = $_GET['pos'] ?? null;
$offset = max(0, intval($_GET['offset'] ?? 0));
$limit = min(100, max(1, intval($_GET['limit'] ?? 50)));

$db = getDB();

// Build WHERE clause
$where = [];
$params = [];

if ($search && trim($search) !== '') {
    $searchTerm = '%' . $search . '%';
    $where[] = '(headword LIKE :search OR citation_form LIKE :search OR guide_word LIKE :search)';
    $params[':search'] = $searchTerm;
}

if ($language && trim($language) !== '') {
    $where[] = 'language = :language';
    $params[':language'] = $language;
}

if ($pos && trim($pos) !== '') {
    $where[] = 'pos = :pos';
    $params[':pos'] = $pos;
}

$whereClause = empty($where) ? '' : 'WHERE ' . implode(' AND ', $where);

// Get total count
$countSql = "SELECT COUNT(*) as total FROM glossary_entries $whereClause";
$stmt = $db->prepare($countSql);
foreach ($params as $key => $value) {
    $stmt->bindValue($key, $value, SQLITE3_TEXT);
}
$countResult = $stmt->execute();
$total = $countResult->fetchArray(SQLITE3_ASSOC)['total'];

// Get paginated entries
$sql = "SELECT entry_id, headword, citation_form, guide_word, language, pos, icount, project
        FROM glossary_entries
        $whereClause
        ORDER BY headword ASC
        LIMIT :limit OFFSET :offset";

$stmt = $db->prepare($sql);
foreach ($params as $key => $value) {
    $stmt->bindValue($key, $value, SQLITE3_TEXT);
}
$stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);
$stmt->bindValue(':offset', $offset, SQLITE3_INTEGER);

$result = $stmt->execute();
$entries = [];
while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    $entries[] = $row;
}

// Build response
echo json_encode([
    'entries' => $entries,
    'total' => $total,
    'offset' => $offset,
    'limit' => $limit,
    'hasMore' => ($offset + $limit) < $total,
    'filters' => [
        'search' => $search,
        'language' => $language,
        'pos' => $pos
    ]
]);
