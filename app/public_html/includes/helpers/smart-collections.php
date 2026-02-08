<?php
/**
 * Smart Collections Query Executor
 *
 * Executes parameter-based Smart Collection queries that dynamically
 * populate collections based on criteria stored in the database.
 */

require_once __DIR__ . '/../db.php';

/**
 * Get a Smart Collection by ID
 */
function getSmartCollection(int $collectionId): ?array {
    $db = getDB();
    $stmt = $db->prepare("
        SELECT * FROM smart_collections
        WHERE smart_collection_id = :id
    ");
    $stmt->bindValue(':id', $collectionId, SQLITE3_INTEGER);
    $result = $stmt->execute();
    $row = $result->fetchArray(SQLITE3_ASSOC);
    return $row ?: null;
}

/**
 * Get all Smart Collections
 */
function getAllSmartCollections(): array {
    $db = getDB();
    $result = $db->query("
        SELECT * FROM smart_collections
        ORDER BY is_system DESC, created_at ASC
    ");

    $collections = [];
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $collections[] = $row;
    }
    return $collections;
}

/**
 * Execute a Smart Collection query and return matching tablets
 *
 * @param int $collectionId The Smart Collection ID
 * @param int $limit Maximum number of tablets to return
 * @return array Array of tablet data with noteworthy_reason metadata
 */
function executeSmartCollection(int $collectionId, int $limit = 12): array {
    $collection = getSmartCollection($collectionId);
    if (!$collection) {
        return [];
    }

    $params = json_decode($collection['query_params'], true);
    $queryType = $collection['query_type'];

    // Route to appropriate query executor based on type
    switch ($queryType) {
        case 'mixed':
            return executeMixedQuery($params, $limit);
        case 'pipeline':
            return executePipelineQuery($params, $limit);
        case 'temporal':
            return executeTemporalQuery($params, $limit);
        case 'literary':
            return executeLiteraryQuery($params, $limit);
        case 'quality':
            return executeQualityQuery($params, $limit);
        case 'connectivity':
            return executeConnectivityQuery($params, $limit);
        default:
            return [];
    }
}

/**
 * Execute mixed criteria query (combines multiple query types)
 * Used for "Noteworthy Works" collection
 */
function executeMixedQuery(array $params, int $limit): array {
    $criteria = $params['criteria'] ?? [];
    $tablets = [];
    $seenPNumbers = [];

    $limitPerCriteria = $params['limit_per_criteria'] ?? 4;

    // Part 1: Literary works
    if (in_array('literary_works', $criteria)) {
        $literaryTablets = executeLiteraryQuery($params, $limitPerCriteria);
        foreach ($literaryTablets as $tablet) {
            $tablets[] = $tablet;
            $seenPNumbers[] = $tablet['p_number'];
        }
    }

    // Part 2: High quality
    if (in_array('high_quality', $criteria)) {
        $qualityTablets = executeQualityQuery($params, $limitPerCriteria, $seenPNumbers);
        foreach ($qualityTablets as $tablet) {
            $tablets[] = $tablet;
            $seenPNumbers[] = $tablet['p_number'];
        }
    }

    // Part 3: High connectivity
    if (in_array('high_connectivity', $criteria)) {
        $connectivityTablets = executeConnectivityQuery($params, $limitPerCriteria, $seenPNumbers);
        foreach ($connectivityTablets as $tablet) {
            $tablets[] = $tablet;
            $seenPNumbers[] = $tablet['p_number'];
        }
    }

    // Shuffle for variety and limit total
    shuffle($tablets);
    return array_slice($tablets, 0, $limit);
}

/**
 * Execute literary works query
 * Finds tablets from significant literary compositions
 */
function executeLiteraryQuery(array $params, int $limit, array $excludePNumbers = []): array {
    $db = getDB();
    $patterns = $params['literary_patterns'] ?? ['Gilgamesh', 'Enuma', 'Atrahasis', 'Hammurabi'];

    // Build WHERE clause for literary patterns
    $likeConditions = [];
    foreach ($patterns as $pattern) {
        $likeConditions[] = "a.designation LIKE :pattern_" . sanitizeForBinding($pattern);
    }
    $whereClause = implode(' OR ', $likeConditions);

    // Add exclusion clause if needed
    if (!empty($excludePNumbers)) {
        $placeholders = implode(',', array_fill(0, count($excludePNumbers), '?'));
        $whereClause .= " AND a.p_number NOT IN ($placeholders)";
    }

    $sql = "
        SELECT a.*, ps.*, 'literary' as noteworthy_reason,
               CASE
                 WHEN a.designation LIKE '%Gilgamesh%' THEN 'Epic of Gilgamesh'
                 WHEN a.designation LIKE '%Enuma%' THEN 'Enuma Elish'
                 WHEN a.designation LIKE '%Atrahasis%' THEN 'Atrahasis Epic'
                 WHEN a.designation LIKE '%Hammurabi%' THEN 'Code of Hammurabi'
                 ELSE 'Literary Work'
               END as work_name
        FROM artifacts a
        JOIN pipeline_status ps ON a.p_number = ps.p_number
        WHERE ps.has_image = 1
          AND ($whereClause)
        ORDER BY RANDOM()
        LIMIT :limit
    ";

    $stmt = $db->prepare($sql);

    // Bind literary patterns
    foreach ($patterns as $pattern) {
        $bindName = ':pattern_' . sanitizeForBinding($pattern);
        $stmt->bindValue($bindName, '%' . $pattern . '%', SQLITE3_TEXT);
    }

    // Bind exclusions
    if (!empty($excludePNumbers)) {
        $i = 1;
        foreach ($excludePNumbers as $pNumber) {
            $stmt->bindValue($i++, $pNumber, SQLITE3_TEXT);
        }
    }

    $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);
    $result = $stmt->execute();

    $tablets = [];
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $tablets[] = $row;
    }
    return $tablets;
}

/**
 * Execute quality query
 * Finds tablets with high digitization quality
 */
function executeQualityQuery(array $params, int $limit, array $excludePNumbers = []): array {
    $db = getDB();
    $threshold = $params['quality_threshold'] ?? 0.8;

    $excludeClause = '';
    if (!empty($excludePNumbers)) {
        $placeholders = implode(',', array_fill(0, count($excludePNumbers), '?'));
        $excludeClause = " AND a.p_number NOT IN ($placeholders)";
    }

    $sql = "
        SELECT a.*, ps.*, 'quality' as noteworthy_reason,
               NULL as work_name
        FROM artifacts a
        JOIN pipeline_status ps ON a.p_number = ps.p_number
        WHERE ps.quality_score > :threshold
          AND ps.has_image = 1
          $excludeClause
        ORDER BY ps.quality_score DESC
        LIMIT :limit
    ";

    $stmt = $db->prepare($sql);
    $stmt->bindValue(':threshold', $threshold, SQLITE3_FLOAT);
    $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);

    if (!empty($excludePNumbers)) {
        $i = 1;
        foreach ($excludePNumbers as $pNumber) {
            $stmt->bindValue($i++, $pNumber, SQLITE3_TEXT);
        }
    }

    $result = $stmt->execute();

    $tablets = [];
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $tablets[] = $row;
    }
    return $tablets;
}

/**
 * Execute connectivity query
 * Finds tablets that belong to multiple composite texts
 */
function executeConnectivityQuery(array $params, int $limit, array $excludePNumbers = []): array {
    $db = getDB();
    $threshold = $params['composite_threshold'] ?? 2;

    $excludeClause = '';
    if (!empty($excludePNumbers)) {
        $placeholders = implode(',', array_fill(0, count($excludePNumbers), '?'));
        $excludeClause = " AND a.p_number NOT IN ($placeholders)";
    }

    $sql = "
        SELECT a.*, ps.*, 'connected' as noteworthy_reason,
               COUNT(DISTINCT ac.q_number) as composite_count
        FROM artifacts a
        JOIN pipeline_status ps ON a.p_number = ps.p_number
        JOIN artifact_composites ac ON a.p_number = ac.p_number
        WHERE ps.has_image = 1
          $excludeClause
        GROUP BY a.p_number
        HAVING composite_count > :threshold
        ORDER BY composite_count DESC
        LIMIT :limit
    ";

    $stmt = $db->prepare($sql);
    $stmt->bindValue(':threshold', $threshold, SQLITE3_INTEGER);
    $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);

    if (!empty($excludePNumbers)) {
        $i = 1;
        foreach ($excludePNumbers as $pNumber) {
            $stmt->bindValue($i++, $pNumber, SQLITE3_TEXT);
        }
    }

    $result = $stmt->execute();

    $tablets = [];
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $tablets[] = $row;
    }
    return $tablets;
}

/**
 * Execute pipeline query
 * Finds tablets at specific pipeline stages (e.g., has image but no ATF)
 */
function executePipelineQuery(array $params, int $limit): array {
    $db = getDB();

    $hasImage = $params['has_image'] ?? null;
    $hasAtf = $params['has_atf'] ?? null;
    $qualityThreshold = $params['quality_threshold'] ?? 0;

    $conditions = [];
    if ($hasImage !== null) {
        $conditions[] = "ps.has_image = " . (int)$hasImage;
    }
    if ($hasAtf !== null) {
        $conditions[] = "(ps.has_atf = " . (int)$hasAtf . " OR ps.has_atf IS NULL)";
    }
    if ($qualityThreshold > 0) {
        $conditions[] = "ps.quality_score > :threshold";
    }

    $whereClause = implode(' AND ', $conditions);

    $sql = "
        SELECT a.*, ps.*, 'pipeline' as noteworthy_reason,
               NULL as work_name
        FROM artifacts a
        JOIN pipeline_status ps ON a.p_number = ps.p_number
        WHERE $whereClause
        ORDER BY ps.quality_score DESC
        LIMIT :limit
    ";

    $stmt = $db->prepare($sql);
    if ($qualityThreshold > 0) {
        $stmt->bindValue(':threshold', $qualityThreshold, SQLITE3_FLOAT);
    }
    $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);
    $result = $stmt->execute();

    $tablets = [];
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $tablets[] = $row;
    }
    return $tablets;
}

/**
 * Execute temporal query
 * Finds tablets updated recently
 */
function executeTemporalQuery(array $params, int $limit): array {
    $db = getDB();

    $daysAgo = $params['days_ago'] ?? 30;
    $requireContent = $params['require_content'] ?? true;

    $contentClause = '';
    if ($requireContent) {
        $contentClause = " AND (ps.has_atf = 1 OR ps.has_translation = 1 OR ps.has_lemmas = 1)";
    }

    $sql = "
        SELECT a.*, ps.*, 'temporal' as noteworthy_reason,
               CAST((julianday('now') - julianday(ps.last_updated)) AS INTEGER) as days_ago
        FROM artifacts a
        JOIN pipeline_status ps ON a.p_number = ps.p_number
        WHERE ps.last_updated >= datetime('now', '-' || :days_ago || ' days')
          $contentClause
        ORDER BY ps.last_updated DESC
        LIMIT :limit
    ";

    $stmt = $db->prepare($sql);
    $stmt->bindValue(':days_ago', $daysAgo, SQLITE3_INTEGER);
    $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);
    $result = $stmt->execute();

    $tablets = [];
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $tablets[] = $row;
    }
    return $tablets;
}

/**
 * Get explanatory text for why a tablet is noteworthy
 *
 * @param array $tablet Tablet data with noteworthy_reason field
 * @return string Human-readable explanation
 */
function getTabletNoteworthyReason(array $tablet): string {
    $reason = $tablet['noteworthy_reason'] ?? '';

    switch ($reason) {
        case 'literary':
            $workName = $tablet['work_name'] ?? 'Literary Work';
            return "From $workName";

        case 'quality':
            $qualityScore = round(($tablet['quality_score'] ?? 0) * 100);
            return "Exemplary Quality ($qualityScore%)";

        case 'connected':
            $count = $tablet['composite_count'] ?? 2;
            return "Referenced in $count texts";

        case 'pipeline':
            $qualityScore = round(($tablet['quality_score'] ?? 0) * 100);
            return "Ready for Transcription ($qualityScore% quality)";

        case 'temporal':
            $daysAgo = $tablet['days_ago'] ?? 0;
            if ($daysAgo == 0) return "Updated today";
            if ($daysAgo == 1) return "Updated yesterday";
            if ($daysAgo < 7) return "Updated $daysAgo days ago";
            if ($daysAgo < 30) return "Updated " . round($daysAgo / 7) . " weeks ago";
            return "Recently updated";

        default:
            return "Noteworthy";
    }
}

/**
 * Get count of tablets in a Smart Collection
 */
function getSmartCollectionCount(int $collectionId): int {
    // For now, execute the query and count results
    // In production, might want to cache these counts
    $tablets = executeSmartCollection($collectionId, 1000); // Get up to 1000 for counting
    return count($tablets);
}

/**
 * Helper: Sanitize string for use in SQL binding parameter names
 */
function sanitizeForBinding(string $str): string {
    return preg_replace('/[^a-zA-Z0-9_]/', '', $str);
}
