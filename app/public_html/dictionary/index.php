<?php
/**
 * Dictionary Browser
 *
 * 3-column master-detail view for browsing dictionary entries:
 * - Column 1: Groupings (POS, Language, Frequency)
 * - Column 2: Filterable word list with search
 * - Column 3: Word detail view
 *
 * URL Parameters:
 *   word   - Selected word entry_id
 *   group  - Active grouping type (pos, language, frequency)
 *   value  - Active grouping value
 *   search - Search query
 */

require_once __DIR__ . '/../includes/db.php';
require_once __DIR__ . '/../includes/helpers/display.php';

// Get URL parameters
$selectedWordId = $_GET['word'] ?? null;
$activeGroup = $_GET['group'] ?? 'all';
$activeValue = $_GET['value'] ?? null;
$searchQuery = $_GET['search'] ?? '';

// Validate activeGroup
if (!in_array($activeGroup, ['all', 'pos', 'language', 'frequency'])) {
    $activeGroup = 'all';
    $activeValue = null;
}

$db = getDB();

/**
 * Fetch initial word list with current filters
 */
function fetchWordList($db, $search, $groupType, $groupValue, $limit = 50, $offset = 0) {
    $where = [];
    $params = [];

    if ($search && trim($search) !== '') {
        $searchTerm = '%' . $search . '%';
        $where[] = '(headword LIKE :search OR citation_form LIKE :search OR guide_word LIKE :search)';
        $params[':search'] = $searchTerm;
    }

    if ($groupType && $groupType !== 'all' && $groupValue) {
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

    $whereClause = empty($where) ? '' : 'WHERE ' . implode(' AND ', $where);

    // Count total
    $countSql = "SELECT COUNT(*) as total FROM glossary_entries $whereClause";
    $stmt = $db->prepare($countSql);
    foreach ($params as $key => $value) {
        $stmt->bindValue($key, $value, SQLITE3_TEXT);
    }
    $total = (int)$stmt->execute()->fetchArray(SQLITE3_ASSOC)['total'];

    // Get entries
    $sql = "SELECT entry_id, headword, citation_form, guide_word, language, pos, icount
            FROM glossary_entries $whereClause
            ORDER BY headword ASC
            LIMIT :limit OFFSET :offset";

    $stmt = $db->prepare($sql);
    foreach ($params as $key => $value) {
        $stmt->bindValue($key, $value, SQLITE3_TEXT);
    }
    $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);
    $stmt->bindValue(':offset', $offset, SQLITE3_INTEGER);

    $entries = [];
    $result = $stmt->execute();
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $row['icount'] = (int)$row['icount'];
        $entries[] = $row;
    }

    return ['entries' => $entries, 'total' => $total];
}

/**
 * Fetch grouping counts
 */
function fetchCounts($db) {
    $counts = ['all' => 0, 'pos' => [], 'language' => [], 'frequency' => []];

    // Total
    $counts['all'] = (int)$db->query("SELECT COUNT(*) as c FROM glossary_entries")->fetchArray()['c'];

    // POS
    $result = $db->query("SELECT pos, COUNT(*) as c FROM glossary_entries WHERE pos IS NOT NULL AND pos != '' GROUP BY pos ORDER BY c DESC");
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $counts['pos'][$row['pos']] = (int)$row['c'];
    }

    // Language (grouped by family)
    $result = $db->query("
        SELECT CASE
            WHEN language LIKE 'akk%' THEN 'akk'
            WHEN language LIKE 'sux%' THEN 'sux'
            WHEN language LIKE 'qpn%' THEN 'qpn'
            ELSE language END as lang,
            COUNT(*) as c
        FROM glossary_entries WHERE language IS NOT NULL GROUP BY lang ORDER BY c DESC
    ");
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $counts['language'][$row['lang']] = (int)$row['c'];
    }

    // Frequency
    $counts['frequency']['1'] = (int)$db->query("SELECT COUNT(*) as c FROM glossary_entries WHERE icount = 1")->fetchArray()['c'];
    $counts['frequency']['2-10'] = (int)$db->query("SELECT COUNT(*) as c FROM glossary_entries WHERE icount BETWEEN 2 AND 10")->fetchArray()['c'];
    $counts['frequency']['11-100'] = (int)$db->query("SELECT COUNT(*) as c FROM glossary_entries WHERE icount BETWEEN 11 AND 100")->fetchArray()['c'];
    $counts['frequency']['101-500'] = (int)$db->query("SELECT COUNT(*) as c FROM glossary_entries WHERE icount BETWEEN 101 AND 500")->fetchArray()['c'];
    $counts['frequency']['500+'] = (int)$db->query("SELECT COUNT(*) as c FROM glossary_entries WHERE icount > 500")->fetchArray()['c'];

    return $counts;
}

/**
 * Fetch word detail data
 */
function fetchWordDetail($db, $entryId) {
    if (!$entryId) return null;

    // Main entry
    $stmt = $db->prepare("SELECT * FROM glossary_entries WHERE entry_id = :id");
    $stmt->bindValue(':id', $entryId, SQLITE3_TEXT);
    $entry = $stmt->execute()->fetchArray(SQLITE3_ASSOC);

    if (!$entry) return null;

    // Variants
    // Use language family matching (e.g., 'akk' matches 'akk-x-stdbab')
    $langBase = explode('-x-', $entry['language'])[0];
    $langFamily = $langBase . '-x-%';

    $stmt = $db->prepare("
        SELECT
            gf.form,
            gf.count as stored_count,
            COALESCE(COUNT(DISTINCT l.p_number), 0) as occ,
            COALESCE(gf.count, 0) as sort_count
        FROM glossary_forms gf
        LEFT JOIN lemmas l ON (
            gf.form = l.form
            AND l.cf = :cf
            AND (l.lang = :lang OR l.lang = :lang_base OR l.lang LIKE :lang_family)
        )
        WHERE gf.entry_id = :id
        GROUP BY gf.form
        ORDER BY occ DESC, sort_count DESC
    ");
    $stmt->bindValue(':id', $entryId, SQLITE3_TEXT);
    $stmt->bindValue(':cf', $entry['citation_form'], SQLITE3_TEXT);
    $stmt->bindValue(':lang', $entry['language'], SQLITE3_TEXT);
    $stmt->bindValue(':lang_base', $langBase, SQLITE3_TEXT);
    $stmt->bindValue(':lang_family', $langFamily, SQLITE3_TEXT);
    $variants = [];
    $result = $stmt->execute();
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $variants[] = ['form' => $row['form'], 'count' => (int)$row['occ'] ?: (int)$row['stored_count']];
    }

    // Signs
    $stmt = $db->prepare("
        SELECT swu.sign_id, swu.sign_value, swu.value_type, swu.usage_count, s.utf8, s.sign_type
        FROM sign_word_usage swu
        JOIN signs s ON swu.sign_id = s.sign_id
        WHERE swu.entry_id = :id ORDER BY swu.usage_count DESC
    ");
    $stmt->bindValue(':id', $entryId, SQLITE3_TEXT);
    $signs = [];
    $result = $stmt->execute();
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $signs[] = $row;
    }

    // Senses
    $stmt = $db->prepare("SELECT * FROM glossary_senses WHERE entry_id = :id ORDER BY sense_number");
    $stmt->bindValue(':id', $entryId, SQLITE3_TEXT);
    $senses = [];
    $result = $stmt->execute();
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $senses[] = $row;
    }

    // Attestations (all distinct tablets)
    // Use language family matching (e.g., 'akk' matches 'akk-x-stdbab')
    $langBase = explode('-x-', $entry['language'])[0];
    $langFamily = $langBase . '-x-%';

    $stmt = $db->prepare("
        SELECT DISTINCT l.p_number, l.form, a.period, a.provenience, a.genre
        FROM lemmas l LEFT JOIN artifacts a ON l.p_number = a.p_number
        WHERE l.cf = :cf
          AND (l.lang = :lang OR l.lang = :lang_base OR l.lang LIKE :lang_family)
        ORDER BY l.p_number
    ");
    $stmt->bindValue(':cf', $entry['citation_form'], SQLITE3_TEXT);
    $stmt->bindValue(':lang', $entry['language'], SQLITE3_TEXT);
    $stmt->bindValue(':lang_base', $langBase, SQLITE3_TEXT);
    $stmt->bindValue(':lang_family', $langFamily, SQLITE3_TEXT);
    $attestations = [];
    $result = $stmt->execute();
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $attestations[] = $row;
    }

    // Related words
    $stmt = $db->prepare("
        SELECT gr.relationship_type, gr.notes, ge2.*
        FROM glossary_relationships gr
        JOIN glossary_entries ge2 ON gr.to_entry_id = ge2.entry_id
        WHERE gr.from_entry_id = :id ORDER BY gr.relationship_type, ge2.icount DESC
    ");
    $stmt->bindValue(':id', $entryId, SQLITE3_TEXT);
    $related = ['translations' => [], 'synonyms' => [], 'cognates' => [], 'see_also' => []];
    $result = $stmt->execute();
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $type = $row['relationship_type'];
        if (isset($related[$type])) {
            $related[$type][] = $row;
        } else {
            $related['see_also'][] = $row;
        }
    }

    // CAD (Akkadian only)
    $cad = null;
    if (strpos($entry['language'], 'akk') === 0) {
        $stmt = $db->prepare("SELECT * FROM cad_entries WHERE oracc_entry_id = :id LIMIT 1");
        $stmt->bindValue(':id', $entryId, SQLITE3_TEXT);
        $cad = $stmt->execute()->fetchArray(SQLITE3_ASSOC) ?: null;
    }

    return [
        'entry' => $entry,
        'variants' => $variants,
        'signs' => $signs,
        'senses' => $senses,
        'attestations' => $attestations,
        'related' => $related,
        'cad' => $cad
    ];
}

// Fetch data for initial render
$counts = fetchCounts($db);
$wordListData = fetchWordList($db, $searchQuery, $activeGroup, $activeValue);
$initialWords = $wordListData['entries'];
$totalWords = $wordListData['total'];

// Auto-select first word if none selected and we have results
if (!$selectedWordId && !empty($initialWords)) {
    $selectedWordId = $initialWords[0]['entry_id'];
}

$wordDetail = fetchWordDetail($db, $selectedWordId);

// Page title and CSS
$pageTitle = 'Dictionary - Words';
require_once __DIR__ . '/../includes/css.php';
CSSLoader::enqueue('page-dictionary');
require_once __DIR__ . '/../includes/header.php';

// Render the browser layout component
// Render the browser layout component
include __DIR__ . '/../includes/components/dictionary/browser-layout.php';
?>

<!-- Dictionary Browser JavaScript -->
<script src="/assets/js/dictionary-browser.js"></script>
<script>
    // Initialize dictionary browser
    document.addEventListener('DOMContentLoaded', function() {
        window.dictionaryBrowser = new DictionaryBrowser({
            initialState: {
                groupType: '<?= htmlspecialchars($activeGroup) ?>',
                groupValue: <?= $activeValue ? "'" . htmlspecialchars($activeValue) . "'" : 'null' ?>,
                searchQuery: '<?= htmlspecialchars(addslashes($searchQuery)) ?>',
                selectedWordId: <?= $selectedWordId ? "'" . htmlspecialchars($selectedWordId) . "'" : 'null' ?>,
                offset: 0,
                total: <?= $totalWords ?>
            }
        });
    });
</script>

<?php require_once __DIR__ . '/../includes/footer.php'; ?>
