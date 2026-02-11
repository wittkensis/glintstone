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
 */

require_once __DIR__ . '/../_bootstrap.php';

use Glintstone\Http\JsonResponse;
use Glintstone\Repository\GlossaryRepository;
use function Glintstone\app;

header('Cache-Control: public, max-age=60');

$params = getRequestParams();
$search = $params['search'] ?? null;
$groupType = $params['group_type'] ?? null;
$groupValue = $params['group_value'] ?? null;
$sortBy = $params['sort'] ?? 'frequency';
$offset = max(0, intval($params['offset'] ?? 0));
$limit = min(100, max(1, intval($params['limit'] ?? 50)));
$includeCounts = (bool)($params['include_counts'] ?? 0);

$validSorts = ['frequency', 'alpha'];
if (!in_array($sortBy, $validSorts)) {
    $sortBy = 'frequency';
}

$repo = app()->get(GlossaryRepository::class);
$db = $repo->db();

/**
 * Build WHERE clause and params for current filters
 */
function buildWhereClause($search, $groupType, $groupValue) {
    $where = [];
    $params = [];

    if ($search && trim($search) !== '') {
        $searchTerm = '%' . $search . '%';
        $where[] = '(headword LIKE :search OR citation_form LIKE :search OR guide_word LIKE :search OR normalized_headword LIKE :searchNorm)';
        $params[':search'] = $searchTerm;
        $params[':searchNorm'] = '%' . strtolower($search) . '%';
    }

    if ($groupType && $groupValue) {
        switch ($groupType) {
            case 'pos':
                $where[] = 'pos = :groupValue';
                $params[':groupValue'] = $groupValue;
                break;
            case 'language':
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
                    case '1': $where[] = 'icount = 1'; break;
                    case '2-10': $where[] = 'icount BETWEEN 2 AND 10'; break;
                    case '11-100': $where[] = 'icount BETWEEN 11 AND 100'; break;
                    case '101-500': $where[] = 'icount BETWEEN 101 AND 500'; break;
                    case '500+': $where[] = 'icount > 500'; break;
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
 * Get all grouping counts
 */
function getGroupingCounts($db) {
    $counts = ['all' => 0, 'pos' => [], 'language' => [], 'frequency' => []];

    $result = $db->query("SELECT COUNT(*) as total FROM glossary_entries");
    $counts['all'] = $result->fetchArray(SQLITE3_ASSOC)['total'];

    $result = $db->query("SELECT pos, COUNT(*) as count FROM glossary_entries WHERE pos IS NOT NULL AND pos != '' GROUP BY pos ORDER BY count DESC");
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $counts['pos'][$row['pos']] = (int)$row['count'];
    }

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

$whereData = buildWhereClause($search, $groupType, $groupValue);
$whereClause = $whereData['clause'];
$bindParams = $whereData['params'];

// Total count
$countSql = "SELECT COUNT(*) as total FROM glossary_entries $whereClause";
$stmt = $db->prepare($countSql);
foreach ($bindParams as $key => $value) {
    $stmt->bindValue($key, $value, SQLITE3_TEXT);
}
$countResult = $stmt->execute();
$total = (int)$countResult->fetchArray(SQLITE3_ASSOC)['total'];

$orderBy = $sortBy === 'alpha'
    ? 'ORDER BY citation_form ASC, headword ASC'
    : 'ORDER BY icount DESC, citation_form ASC';

$sql = "SELECT entry_id, headword, citation_form, guide_word, language, pos, icount
        FROM glossary_entries
        $whereClause
        $orderBy
        LIMIT :limit OFFSET :offset";

$stmt = $db->prepare($sql);
foreach ($bindParams as $key => $value) {
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

$response = [
    'entries' => $entries,
    'total' => $total,
    'offset' => $offset,
    'limit' => $limit,
    'hasMore' => ($offset + $limit) < $total
];

if ($includeCounts) {
    $response['counts'] = getGroupingCounts($db);
}

JsonResponse::success($response);
