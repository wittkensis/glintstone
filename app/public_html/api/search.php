<?php
/**
 * Unified Search API
 * Searches across tablets, signs, dictionary, collections, and composites
 * with smart prioritization and relevance scoring
 */

header('Content-Type: application/json');
require_once __DIR__ . '/../includes/db.php';

// Get search query
$query = isset($_GET['q']) ? trim($_GET['q']) : '';
$limit = isset($_GET['limit']) ? (int)$_GET['limit'] : 20;

if (empty($query)) {
    echo json_encode([
        'query' => '',
        'total_results' => 0,
        'categories' => []
    ]);
    exit;
}

$db = getDB();

// Search results by category
$categories = [];

// 1. Search Tablets
$tablets = searchTablets($db, $query);
if (!empty($tablets)) {
    $relevanceScore = calculateCategoryRelevance('tablets', $query, $tablets);
    $categories[] = [
        'type' => 'tablets',
        'label' => 'Tablets',
        'count' => count($tablets),
        'relevance_score' => $relevanceScore,
        'results' => $tablets
    ];
}

// 2. Search Signs
$signs = searchSigns($db, $query);
if (!empty($signs)) {
    $relevanceScore = calculateCategoryRelevance('signs', $query, $signs);
    $categories[] = [
        'type' => 'signs',
        'label' => 'Signs',
        'count' => count($signs),
        'relevance_score' => $relevanceScore,
        'results' => $signs
    ];
}

// 3. Search Dictionary
$dictionary = searchDictionary($db, $query);
if (!empty($dictionary)) {
    $relevanceScore = calculateCategoryRelevance('dictionary', $query, $dictionary);
    $categories[] = [
        'type' => 'dictionary',
        'label' => 'Dictionary',
        'count' => count($dictionary),
        'relevance_score' => $relevanceScore,
        'results' => $dictionary
    ];
}

// 4. Search Collections
$collections = searchCollections($db, $query);
if (!empty($collections)) {
    $relevanceScore = calculateCategoryRelevance('collections', $query, $collections);
    $categories[] = [
        'type' => 'collections',
        'label' => 'Collections',
        'count' => count($collections),
        'relevance_score' => $relevanceScore,
        'results' => $collections
    ];
}

// 5. Search Composites
$composites = searchComposites($db, $query);
if (!empty($composites)) {
    $relevanceScore = calculateCategoryRelevance('composites', $query, $composites);
    $categories[] = [
        'type' => 'composites',
        'label' => 'Composites',
        'count' => count($composites),
        'relevance_score' => $relevanceScore,
        'results' => $composites
    ];
}

// Sort categories by relevance score (highest first)
usort($categories, function($a, $b) {
    return $b['relevance_score'] <=> $a['relevance_score'];
});

// Apply smart prioritization: allocate more results to top categories
$categories = applySmartPrioritization($categories, $limit);

// Calculate total results
$totalResults = array_sum(array_column($categories, 'count'));

// Return response
echo json_encode([
    'query' => $query,
    'total_results' => $totalResults,
    'categories' => $categories
], JSON_UNESCAPED_UNICODE);

/**
 * Search tablets
 */
function searchTablets(SQLite3 $db, string $query): array {
    $stmt = $db->prepare("
        SELECT
            a.p_number,
            a.designation,
            a.period,
            a.provenience,
            a.genre,
            a.museum_no,
            a.excavation_no,
            ps.quality_score,
            ps.has_image
        FROM artifacts a
        LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
        WHERE
            a.p_number LIKE :q
            OR a.designation LIKE :q
            OR a.museum_no LIKE :q
            OR a.excavation_no LIKE :q
            OR a.provenience LIKE :q
            OR a.genre LIKE :q
        ORDER BY
            CASE WHEN a.p_number = :exact THEN 0 ELSE 1 END,
            ps.quality_score DESC
        LIMIT 10
    ");

    $searchTerm = '%' . $query . '%';
    $stmt->bindValue(':q', $searchTerm, SQLITE3_TEXT);
    $stmt->bindValue(':exact', $query, SQLITE3_TEXT);

    $result = $stmt->execute();
    $tablets = [];

    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $tablets[] = [
            'p_number' => $row['p_number'],
            'designation' => $row['designation'],
            'period' => $row['period'],
            'provenience' => $row['provenience'],
            'genre' => $row['genre'],
            'museum_no' => $row['museum_no'],
            'excavation_no' => $row['excavation_no'],
            'quality_score' => $row['quality_score'] ? (float)$row['quality_score'] : 0.0,
            'has_image' => (bool)$row['has_image']
        ];
    }

    return $tablets;
}

/**
 * Search signs
 */
function searchSigns(SQLite3 $db, string $query): array {
    // Search by sign_id, utf8, or values
    $stmt = $db->prepare("
        SELECT
            s.sign_id,
            s.utf8,
            GROUP_CONCAT(sv.value, ', ') as sign_values
        FROM signs s
        LEFT JOIN sign_values sv ON s.sign_id = sv.sign_id
        WHERE
            s.utf8 = :exact
            OR s.sign_id LIKE :q
            OR s.sign_id IN (
                SELECT DISTINCT sign_id
                FROM sign_values
                WHERE value LIKE :q
            )
        GROUP BY s.sign_id
        LIMIT 5
    ");

    $searchTerm = '%' . $query . '%';
    $stmt->bindValue(':exact', $query, SQLITE3_TEXT);
    $stmt->bindValue(':q', $searchTerm, SQLITE3_TEXT);

    $result = $stmt->execute();
    $signs = [];

    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $signs[] = [
            'sign_id' => $row['sign_id'],
            'utf8' => $row['utf8'],
            'values' => $row['sign_values']
        ];
    }

    return $signs;
}

/**
 * Search dictionary
 */
function searchDictionary(SQLite3 $db, string $query): array {
    $stmt = $db->prepare("
        SELECT DISTINCT
            ge.entry_id,
            ge.headword,
            ge.citation_form,
            ge.guide_word,
            ge.language,
            ge.pos,
            ge.icount
        FROM glossary_entries ge
        LEFT JOIN glossary_forms gf ON ge.entry_id = gf.entry_id
        WHERE
            ge.headword LIKE :q
            OR ge.citation_form LIKE :q
            OR ge.guide_word LIKE :q
            OR gf.form LIKE :q
        GROUP BY ge.entry_id
        ORDER BY
            CASE WHEN ge.headword = :exact THEN 0 ELSE 1 END,
            ge.icount DESC
        LIMIT 10
    ");

    $searchTerm = '%' . $query . '%';
    $stmt->bindValue(':q', $searchTerm, SQLITE3_TEXT);
    $stmt->bindValue(':exact', $query, SQLITE3_TEXT);

    $result = $stmt->execute();
    $dictionary = [];

    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $dictionary[] = [
            'entry_id' => $row['entry_id'],
            'headword' => $row['headword'],
            'citation_form' => $row['citation_form'],
            'guide_word' => $row['guide_word'],
            'language' => $row['language'],
            'pos' => $row['pos'],
            'icount' => (int)$row['icount']
        ];
    }

    return $dictionary;
}

/**
 * Search collections
 */
function searchCollections(SQLite3 $db, string $query): array {
    $stmt = $db->prepare("
        SELECT
            c.collection_id,
            c.name,
            c.description,
            COUNT(cm.p_number) as tablet_count
        FROM collections c
        LEFT JOIN collection_members cm ON c.collection_id = cm.collection_id
        WHERE
            c.name LIKE :q
            OR c.description LIKE :q
        GROUP BY c.collection_id
        ORDER BY tablet_count DESC
        LIMIT 5
    ");

    $searchTerm = '%' . $query . '%';
    $stmt->bindValue(':q', $searchTerm, SQLITE3_TEXT);

    $result = $stmt->execute();
    $collections = [];

    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $collections[] = [
            'collection_id' => (int)$row['collection_id'],
            'name' => $row['name'],
            'description' => $row['description'],
            'tablet_count' => (int)$row['tablet_count']
        ];
    }

    return $collections;
}

/**
 * Search composites
 */
function searchComposites(SQLite3 $db, string $query): array {
    $stmt = $db->prepare("
        SELECT
            c.q_number,
            c.designation,
            c.artifact_comments,
            COUNT(ac.p_number) as tablet_count
        FROM composites c
        LEFT JOIN artifact_composites ac ON c.q_number = ac.q_number
        WHERE
            c.q_number LIKE :q
            OR c.designation LIKE :q
        GROUP BY c.q_number
        ORDER BY
            CASE WHEN c.q_number = :exact THEN 0 ELSE 1 END,
            tablet_count DESC
        LIMIT 5
    ");

    $searchTerm = '%' . $query . '%';
    $stmt->bindValue(':q', $searchTerm, SQLITE3_TEXT);
    $stmt->bindValue(':exact', $query, SQLITE3_TEXT);

    $result = $stmt->execute();
    $composites = [];

    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $composites[] = [
            'q_number' => $row['q_number'],
            'designation' => $row['designation'],
            'artifact_comments' => $row['artifact_comments'],
            'tablet_count' => (int)$row['tablet_count']
        ];
    }

    return $composites;
}

/**
 * Calculate category relevance score
 */
function calculateCategoryRelevance(string $entityType, string $query, array $results): float {
    $score = 0.0;

    // 1. Query pattern matching (40% weight)
    if (preg_match('/^P\d{6}/', $query) && $entityType === 'tablets') {
        $score += 0.4;
    } elseif (preg_match('/^Q\d{6}/', $query) && $entityType === 'composites') {
        $score += 0.4;
    } elseif (preg_match('/^[𒀀-𒍿]/u', $query) && $entityType === 'signs') {
        $score += 0.4;
    } else {
        // No pattern bonus, baseline
        $score += 0.1;
    }

    // 2. Match exactness (30% weight)
    $exactMatches = 0;
    $startsWithMatches = 0;

    foreach ($results as $result) {
        $searchField = getPrimarySearchField($entityType, $result);
        if (strcasecmp($searchField, $query) === 0) {
            $exactMatches++;
        } elseif (stripos($searchField, $query) === 0) {
            $startsWithMatches++;
        }
    }

    if ($exactMatches > 0) {
        $score += 0.3; // Exact match
    } elseif ($startsWithMatches > 0) {
        $score += 0.2; // Starts with query
    } else {
        $score += 0.1; // Contains query
    }

    // 3. Entity popularity (20% weight)
    $avgPopularity = calculateAveragePopularity($entityType, $results);
    $score += $avgPopularity * 0.2;

    // 4. Result count factor (10% weight)
    // More results = potentially more relevant category
    $resultCountScore = min(count($results) / 10, 1.0);
    $score += $resultCountScore * 0.1;

    return $score;
}

/**
 * Get primary search field for entity type
 */
function getPrimarySearchField(string $entityType, array $result): string {
    switch ($entityType) {
        case 'tablets':
            return $result['p_number'];
        case 'signs':
            return $result['sign_id'];
        case 'dictionary':
            return $result['headword'];
        case 'collections':
            return $result['name'];
        case 'composites':
            return $result['q_number'];
        default:
            return '';
    }
}

/**
 * Calculate average popularity score for results
 */
function calculateAveragePopularity(string $entityType, array $results): float {
    if (empty($results)) {
        return 0.0;
    }

    $total = 0.0;

    foreach ($results as $result) {
        switch ($entityType) {
            case 'tablets':
                $total += $result['quality_score'] ?? 0.0;
                break;
            case 'dictionary':
                // Normalize icount to 0-1 range (assume max ~10000)
                $total += min(($result['icount'] ?? 0) / 10000, 1.0);
                break;
            case 'collections':
            case 'composites':
                // Normalize tablet count to 0-1 range (assume max ~100)
                $total += min(($result['tablet_count'] ?? 0) / 100, 1.0);
                break;
            case 'signs':
                // Signs don't have popularity metric, use 0.5 baseline
                $total += 0.5;
                break;
        }
    }

    return $total / count($results);
}

/**
 * Apply smart prioritization to limit results per category
 * Top category gets more results, lower categories get fewer
 */
function applySmartPrioritization(array $categories, int $totalLimit): array {
    if (empty($categories)) {
        return $categories;
    }

    $numCategories = count($categories);

    // Define result limits per priority tier
    if ($numCategories === 1) {
        // Only one category, give it all results (up to 8)
        $limits = [8];
    } elseif ($numCategories === 2) {
        // Two categories: 5-8 and 3-4
        $limits = [8, 4];
    } elseif ($numCategories === 3) {
        // Three categories: 5-8, 3-4, 2-3
        $limits = [6, 4, 3];
    } else {
        // Four or more: 5-8, 3-4, 2-3, 1-2
        $limits = [6, 4, 3, 2];
    }

    // Apply limits to each category
    foreach ($categories as $i => &$category) {
        $limit = $limits[$i] ?? 1; // Default to 1 for lower tiers

        if (count($category['results']) > $limit) {
            $category['results'] = array_slice($category['results'], 0, $limit);
            $category['count'] = count($category['results']);
        }
    }

    return $categories;
}
