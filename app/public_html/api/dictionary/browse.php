<?php
/**
 * Dictionary Browse API
 * Returns paginated entries with grouping counts and filtering
 *
 * Parameters:
 *   search        - Search query (optional)
 *   group_type    - Grouping type: 'pos', 'language', 'frequency' (optional)
 *   group_value   - Filter value for the group type (optional)
 *   sort          - Sort order: 'frequency' (default), 'alpha'
 *   offset        - Pagination offset (default: 0)
 *   limit         - Results per page (default: 50, max: 100)
 *   include_counts - Include grouping counts in response (default: 0)
 *
 * Response:
 *   entries   - Array of word entries
 *   total     - Total count matching filters
 *   hasMore   - Whether more results exist
 *   counts    - Grouping counts (if include_counts=1)
 */

require_once __DIR__ . '/../_error-handler.php';

try {
    require_once __DIR__ . '/../../includes/db.php';
} catch (Throwable $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Failed to load dependencies', 'message' => $e->getMessage()]);
    exit;
}

header('Cache-Control: public, max-age=60');

// Get parameters
$search = $_GET['search'] ?? null;
$groupType = $_GET['group_type'] ?? null;
$groupValue = $_GET['group_value'] ?? null;
$sortBy = $_GET['sort'] ?? 'frequency';
$offset = max(0, intval($_GET['offset'] ?? 0));
$limit = min(100, max(1, intval($_GET['limit'] ?? 50)));
$includeCounts = (bool)($_GET['include_counts'] ?? 0);

// Validate sort parameter
$validSorts = ['frequency', 'alpha'];
if (!in_array($sortBy, $validSorts)) {
    $sortBy = 'frequency';
}

$db = getDB();

/**
 * Build WHERE clause and params for current filters
 */
function buildWhereClause($search, $groupType, $groupValue) {
    $where = [];
    $params = [];

    // Search filter
    if ($search && trim($search) !== '') {
        $searchTerm = '%' . $search . '%';
        $where[] = '(headword LIKE :search OR citation_form LIKE :search OR guide_word LIKE :search OR normalized_headword LIKE :searchNorm)';
        $params[':search'] = $searchTerm;
        $params[':searchNorm'] = '%' . strtolower($search) . '%';
    }

    // Group filters
    if ($groupType && $groupValue) {
        switch ($groupType) {
            case 'pos':
                $where[] = 'pos = :groupValue';
                $params[':groupValue'] = $groupValue;
                break;

            case 'language':
                // Handle language families (akk includes akk-x-*)
                if ($groupValue === 'akk') {
                    $where[] = "(language = 'akk' OR language LIKE 'akk-x-%')";
                } elseif ($groupValue === 'sux') {
                    $where[] = "(language = 'sux' OR language LIKE 'sux-x-%')";
                } elseif ($groupValue === 'qpn') {
                    $where[] = "(language = 'qpn' OR language LIKE 'qpn-x-%')";
                } else {
                    $where[] = 'language = :groupValue';
                    $params[':groupValue'] = $groupValue;
                }
                break;

            case 'frequency':
                switch ($groupValue) {
                    case '1':
                        $where[] = 'icount = 1';
                        break;
                    case '2-10':
                        $where[] = 'icount BETWEEN 2 AND 10';
                        break;
                    case '11-100':
                        $where[] = 'icount BETWEEN 11 AND 100';
                        break;
                    case '101-500':
                        $where[] = 'icount BETWEEN 101 AND 500';
                        break;
                    case '500+':
                        $where[] = 'icount > 500';
                        break;
                }
                break;
        }
    }

    return [
        'clause' => empty($where) ? '' : 'WHERE ' . implode(' AND ', $where),
        'params' => $params
    ];
}

/**
 * Get all grouping counts (called when include_counts=1)
 */
function getGroupingCounts($db) {
    $counts = [
        'all' => 0,
        'pos' => [],
        'language' => [],
        'frequency' => []
    ];

    // Total count
    $result = $db->query("SELECT COUNT(*) as total FROM glossary_entries");
    $counts['all'] = $result->fetchArray(SQLITE3_ASSOC)['total'];

    // POS counts
    $result = $db->query("SELECT pos, COUNT(*) as count FROM glossary_entries WHERE pos IS NOT NULL AND pos != '' GROUP BY pos ORDER BY count DESC");
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $counts['pos'][$row['pos']] = (int)$row['count'];
    }

    // Language counts (grouped by family)
    $result = $db->query("
        SELECT
            CASE
                WHEN language LIKE 'akk%' THEN 'akk'
                WHEN language LIKE 'sux%' THEN 'sux'
                WHEN language LIKE 'qpn%' THEN 'qpn'
                ELSE language
            END as lang_family,
            COUNT(*) as count
        FROM glossary_entries
        WHERE language IS NOT NULL AND language != ''
        GROUP BY lang_family
        ORDER BY count DESC
    ");
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $counts['language'][$row['lang_family']] = (int)$row['count'];
    }

    // Frequency counts
    $frequencyRanges = [
        '1' => 'icount = 1',
        '2-10' => 'icount BETWEEN 2 AND 10',
        '11-100' => 'icount BETWEEN 11 AND 100',
        '101-500' => 'icount BETWEEN 101 AND 500',
        '500+' => 'icount > 500'
    ];

    foreach ($frequencyRanges as $range => $condition) {
        $result = $db->query("SELECT COUNT(*) as count FROM glossary_entries WHERE $condition");
        $counts['frequency'][$range] = (int)$result->fetchArray(SQLITE3_ASSOC)['count'];
    }

    return $counts;
}

// Build query
$whereData = buildWhereClause($search, $groupType, $groupValue);
$whereClause = $whereData['clause'];
$params = $whereData['params'];

// Get total count for current filters
$countSql = "SELECT COUNT(*) as total FROM glossary_entries $whereClause";
$stmt = $db->prepare($countSql);
foreach ($params as $key => $value) {
    $stmt->bindValue($key, $value, SQLITE3_TEXT);
}
$countResult = $stmt->execute();
$total = (int)$countResult->fetchArray(SQLITE3_ASSOC)['total'];

// Build ORDER BY clause
$orderBy = $sortBy === 'alpha'
    ? 'ORDER BY citation_form ASC, headword ASC'
    : 'ORDER BY icount DESC, citation_form ASC';

// Get paginated entries
$sql = "SELECT entry_id, headword, citation_form, guide_word, language, pos, icount
        FROM glossary_entries
        $whereClause
        $orderBy
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
    $row['icount'] = (int)$row['icount'];
    $entries[] = $row;
}

// Build response
$response = [
    'entries' => $entries,
    'total' => $total,
    'offset' => $offset,
    'limit' => $limit,
    'hasMore' => ($offset + $limit) < $total
];

// Include counts if requested
if ($includeCounts) {
    $response['counts'] = getGroupingCounts($db);
}

echo json_encode($response);
