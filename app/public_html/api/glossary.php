<?php
/**
 * Glossary lookup API endpoint
 * Returns dictionary entries from ORACC glossaries
 *
 * Parameters:
 *   q      - Query word (required)
 *   lang   - Filter by language (optional)
 *   limit  - Max entries to return (default: 10, max: 50)
 *   full   - If set, include variant forms and field explanations
 */

require_once __DIR__ . '/_bootstrap.php';

use Glintstone\Http\JsonResponse;
use Glintstone\Data\Labels;
use Glintstone\Repository\GlossaryRepository;
use function Glintstone\app;

// Get parameters
$params = getRequestParams();
$query = $params['q'] ?? null;
$language = $params['lang'] ?? null;
$limit = min(50, max(1, (int)($params['limit'] ?? 10)));
$fullMode = isset($params['full']);

// Validate required parameter
if (!$query) {
    JsonResponse::badRequest('Missing query parameter');
}

$repo = app()->get(GlossaryRepository::class);
$db = $repo->db();
$entries = [];

// First try exact match on headword or citation_form
$sql = "SELECT * FROM glossary_entries WHERE headword = :q OR citation_form = :q";
if ($language) {
    $sql .= " AND language = :lang";
}
$sql .= " ORDER BY icount DESC LIMIT :limit";

$stmt = $db->prepare($sql);
$stmt->bindValue(':q', $query, SQLITE3_TEXT);
if ($language) {
    $stmt->bindValue(':lang', $language, SQLITE3_TEXT);
}
$stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);

$result = $stmt->execute();
while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    $entries[] = $row;
}

// If no exact match, try partial match
if (empty($entries)) {
    $sql = "SELECT * FROM glossary_entries WHERE headword LIKE :q OR citation_form LIKE :q";
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

// If still no match, try searching variant forms
if (empty($entries)) {
    $sql = "SELECT DISTINCT ge.* FROM glossary_entries ge
            JOIN glossary_forms gf ON ge.entry_id = gf.entry_id
            WHERE gf.form LIKE :q";
    if ($language) {
        $sql .= " AND ge.language = :lang";
    }
    $sql .= " ORDER BY ge.icount DESC LIMIT :limit";

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

// Build response
$response = [
    'query' => $query,
    'language' => $language,
    'count' => count($entries),
    'entries' => $entries
];

// Add variant forms and field explanations if full mode requested
if ($fullMode && !empty($entries)) {
    // Get variant forms for all matched entries
    $entryIds = array_map(fn($e) => $e['entry_id'] ?? '', $entries);
    $entryIds = array_filter($entryIds);

    if (!empty($entryIds)) {
        $placeholders = implode(',', array_fill(0, count($entryIds), '?'));
        $sql = "SELECT entry_id, form, count FROM glossary_forms
                WHERE entry_id IN ($placeholders)
                ORDER BY count DESC";

        $stmt = $db->prepare($sql);
        foreach ($entryIds as $i => $id) {
            $stmt->bindValue($i + 1, $id, SQLITE3_TEXT);
        }

        $result = $stmt->execute();
        $forms = [];
        while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
            if (!isset($forms[$row['entry_id']])) {
                $forms[$row['entry_id']] = [];
            }
            $forms[$row['entry_id']][] = [
                'form' => $row['form'],
                'count' => $row['count']
            ];
        }

        $response['forms'] = $forms;
    }

    // Add field explanations
    $response['field_explanations'] = [
        'headword' => 'Dictionary headword - the standard form used for reference',
        'citation_form' => 'Citation form - how the word is cited in scholarly publications',
        'guide_word' => 'Guide word - primary English meaning or translation',
        'pos' => 'Part of speech - grammatical category (N=noun, V=verb, AJ=adjective, etc.)',
        'language' => 'Language code - akk (Akkadian), sux (Sumerian), etc.',
        'icount' => 'Instance count - number of occurrences in the ORACC corpus',
        'project' => 'Source project - which ORACC project this entry comes from'
    ];

    // Use consolidated labels from Labels class
    $response['pos_labels'] = Labels::getAllPosLabels();
}

JsonResponse::success($response);
