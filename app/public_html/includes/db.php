<?php
/**
 * Database connection for Glintstone
 */

define('DB_PATH', dirname(__DIR__, 3) . '/database/glintstone.db');

function getDB(): SQLite3 {
    static $db = null;

    if ($db === null) {
        try {
            $db = new SQLite3(DB_PATH, SQLITE3_OPEN_READONLY);
            $db->enableExceptions(true);

            // Set busy timeout to handle database locking (5 seconds)
            // This prevents "database is locked" errors during concurrent access
            $db->busyTimeout(5000);

            // Enable WAL mode for better concurrent read performance
            // WAL allows readers to not block writers and vice versa
            $db->exec('PRAGMA journal_mode=WAL');
        } catch (Exception $e) {
            // If we can't open the database, throw a more helpful error
            throw new Exception("Failed to open database: " . $e->getMessage());
        }
    }

    return $db;
}

/**
 * Get artifact by P-number
 */
function getArtifact(string $pNumber): ?array {
    $db = getDB();
    $stmt = $db->prepare("
        SELECT a.*, ps.has_image, ps.has_ocr, ps.ocr_confidence, ps.has_atf,
               ps.atf_source, ps.has_lemmas, ps.lemma_coverage, ps.has_translation,
               ps.has_sign_annotations, ps.quality_score
        FROM artifacts a
        LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
        WHERE a.p_number = :p_number
    ");
    $stmt->bindValue(':p_number', $pNumber, SQLITE3_TEXT);
    $result = $stmt->execute();
    $row = $result->fetchArray(SQLITE3_ASSOC);
    return $row ?: null;
}

/**
 * Get inscription for artifact
 */
function getInscription(string $pNumber): ?array {
    $db = getDB();
    $stmt = $db->prepare("
        SELECT * FROM inscriptions
        WHERE p_number = :p_number AND is_latest = 1
    ");
    $stmt->bindValue(':p_number', $pNumber, SQLITE3_TEXT);
    $result = $stmt->execute();
    $row = $result->fetchArray(SQLITE3_ASSOC);
    return $row ?: null;
}

/**
 * Get composites for artifact
 */
function getComposites(string $pNumber): array {
    $db = getDB();
    $stmt = $db->prepare("
        SELECT c.* FROM composites c
        JOIN artifact_composites ac ON c.q_number = ac.q_number
        WHERE ac.p_number = :p_number
    ");
    $stmt->bindValue(':p_number', $pNumber, SQLITE3_TEXT);
    $result = $stmt->execute();

    $composites = [];
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $composites[] = $row;
    }
    return $composites;
}

/**
 * Get all tablets that belong to a composite
 * Returns tablets with metadata for display in composite panel
 */
function getTabletsInComposite(string $qNumber): array {
    $db = getDB();
    $stmt = $db->prepare("
        SELECT
            a.p_number,
            a.designation,
            a.period,
            ps.has_image,
            ac.line_ref
        FROM artifact_composites ac
        JOIN artifacts a ON ac.p_number = a.p_number
        LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
        WHERE ac.q_number = :q_number
        ORDER BY a.p_number ASC
    ");
    $stmt->bindValue(':q_number', $qNumber, SQLITE3_TEXT);
    $result = $stmt->execute();

    $tablets = [];
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $tablets[] = $row;
    }
    return $tablets;
}

/**
 * Get composite metadata by Q-number
 */
function getCompositeMetadata(string $qNumber): ?array {
    $db = getDB();
    $stmt = $db->prepare("
        SELECT * FROM composites WHERE q_number = :q_number
    ");
    $stmt->bindValue(':q_number', $qNumber, SQLITE3_TEXT);
    $result = $stmt->execute();
    $row = $result->fetchArray(SQLITE3_ASSOC);
    return $row ?: null;
}

/**
 * Get all composites with tablet counts
 */
function getAllComposites(): array {
    $db = getDB();
    $stmt = $db->prepare("
        SELECT
            c.q_number,
            c.designation,
            c.artifact_comments,
            COUNT(ac.p_number) as tablet_count
        FROM composites c
        LEFT JOIN artifact_composites ac ON c.q_number = ac.q_number
        GROUP BY c.q_number
        ORDER BY c.q_number ASC
    ");
    $result = $stmt->execute();

    $composites = [];
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $composites[] = $row;
    }
    return $composites;
}

/**
 * Get preview tablets for a composite (first 4 for thumbnail grid)
 */
function getCompositePreviewTablets(string $qNumber, int $limit = 4): array {
    $db = getDB();
    $stmt = $db->prepare("
        SELECT a.p_number, a.designation
        FROM artifact_composites ac
        JOIN artifacts a ON ac.p_number = a.p_number
        WHERE ac.q_number = :q_number
        ORDER BY a.p_number ASC
        LIMIT :limit
    ");
    $stmt->bindValue(':q_number', $qNumber, SQLITE3_TEXT);
    $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);
    $result = $stmt->execute();

    $tablets = [];
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $tablets[] = $row;
    }
    return $tablets;
}

/**
 * Refresh aggregated metadata cache for a single composite
 * Calculates period, provenience, genre from tablets and stores in cache columns
 */
function refreshCompositeMetadata(string $qNumber): bool {
    $db = getDB();
    $writeDb = getWritableDB();

    // Calculate fresh aggregates
    $stmt = $db->prepare("
        SELECT
            COUNT(DISTINCT ac.p_number) as exemplar_count,
            GROUP_CONCAT(DISTINCT a.period) as periods,
            GROUP_CONCAT(DISTINCT a.provenience) as proveniences,
            GROUP_CONCAT(DISTINCT a.genre) as genres
        FROM artifact_composites ac
        LEFT JOIN artifacts a ON ac.p_number = a.p_number
        WHERE ac.q_number = :q_number
    ");
    $stmt->bindValue(':q_number', $qNumber, SQLITE3_TEXT);
    $result = $stmt->execute();
    $metadata = $result->fetchArray(SQLITE3_ASSOC);

    if (!$metadata) {
        return false;
    }

    // Update cache in composites table
    $updateStmt = $writeDb->prepare("
        UPDATE composites
        SET periods_cache = :periods,
            proveniences_cache = :proveniences,
            genres_cache = :genres,
            exemplar_count_cache = :count,
            metadata_updated_at = CURRENT_TIMESTAMP
        WHERE q_number = :q_number
    ");
    $updateStmt->bindValue(':periods', $metadata['periods'], SQLITE3_TEXT);
    $updateStmt->bindValue(':proveniences', $metadata['proveniences'], SQLITE3_TEXT);
    $updateStmt->bindValue(':genres', $metadata['genres'], SQLITE3_TEXT);
    $updateStmt->bindValue(':count', (int)$metadata['exemplar_count'], SQLITE3_INTEGER);
    $updateStmt->bindValue(':q_number', $qNumber, SQLITE3_TEXT);

    return (bool)$updateStmt->execute();
}

/**
 * Get all composites with metadata (cached or fresh)
 * Uses cached metadata if available and exemplar count matches
 * Automatically refreshes cache if stale or missing
 */
function getCompositesWithMetadata(): array {
    $db = getDB();

    // Get all composites with cached metadata
    $stmt = $db->prepare("
        SELECT
            c.q_number,
            c.designation,
            c.periods_cache,
            c.proveniences_cache,
            c.genres_cache,
            c.exemplar_count_cache,
            COUNT(DISTINCT ac.p_number) as current_count
        FROM composites c
        LEFT JOIN artifact_composites ac ON c.q_number = ac.q_number
        GROUP BY c.q_number
        ORDER BY c.q_number ASC
    ");
    $result = $stmt->execute();

    $composites = [];
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $currentCount = (int)$row['current_count'];
        $cachedCount = (int)$row['exemplar_count_cache'];

        // Check if cache is valid (exists and count matches)
        $cacheValid = ($row['periods_cache'] !== null) && ($cachedCount === $currentCount);

        // If cache is stale/missing, refresh it
        if (!$cacheValid) {
            refreshCompositeMetadata($row['q_number']);

            // Re-fetch the updated cache
            $refreshStmt = $db->prepare("
                SELECT periods_cache, proveniences_cache, genres_cache, exemplar_count_cache
                FROM composites
                WHERE q_number = :q_number
            ");
            $refreshStmt->bindValue(':q_number', $row['q_number'], SQLITE3_TEXT);
            $refreshResult = $refreshStmt->execute();
            $refreshed = $refreshResult->fetchArray(SQLITE3_ASSOC);

            if ($refreshed) {
                $row['periods_cache'] = $refreshed['periods_cache'];
                $row['proveniences_cache'] = $refreshed['proveniences_cache'];
                $row['genres_cache'] = $refreshed['genres_cache'];
                $row['exemplar_count_cache'] = $refreshed['exemplar_count_cache'];
            }
        }

        // Split comma-separated values into arrays, filter empty values
        $composites[] = [
            'q_number' => $row['q_number'],
            'designation' => $row['designation'],
            'exemplar_count' => (int)$row['exemplar_count_cache'],
            'periods' => $row['periods_cache'] ? array_filter(explode(',', $row['periods_cache'])) : [],
            'proveniences' => $row['proveniences_cache'] ? array_filter(explode(',', $row['proveniences_cache'])) : [],
            'genres' => $row['genres_cache'] ? array_filter(explode(',', $row['genres_cache'])) : []
        ];
    }

    return $composites;
}

/**
 * Refresh all composite metadata caches (utility function)
 * Useful for initial population or batch maintenance
 */
function refreshAllCompositeMetadata(): int {
    $db = getDB();
    $result = $db->query("SELECT q_number FROM composites ORDER BY q_number ASC");

    $refreshed = 0;
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        if (refreshCompositeMetadata($row['q_number'])) {
            $refreshed++;
        }
    }

    return $refreshed;
}

/**
 * Search glossary
 */
function searchGlossary(string $term, ?string $language = null, int $limit = 20): array {
    $db = getDB();

    $sql = "SELECT * FROM glossary_entries WHERE headword LIKE :term";
    if ($language) {
        $sql .= " AND language = :lang";
    }
    $sql .= " ORDER BY icount DESC LIMIT :limit";

    $stmt = $db->prepare($sql);
    $stmt->bindValue(':term', "%$term%", SQLITE3_TEXT);
    if ($language) {
        $stmt->bindValue(':lang', $language, SQLITE3_TEXT);
    }
    $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);

    $result = $stmt->execute();
    $entries = [];
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $entries[] = $row;
    }
    return $entries;
}

/**
 * Get sign by ID
 */
function getSign(string $signId): ?array {
    $db = getDB();
    $stmt = $db->prepare("SELECT * FROM signs WHERE sign_id = :id");
    $stmt->bindValue(':id', $signId, SQLITE3_TEXT);
    $result = $stmt->execute();
    return $result->fetchArray(SQLITE3_ASSOC) ?: null;
}

/**
 * Get sign values
 */
function getSignValues(string $signId): array {
    $db = getDB();
    $stmt = $db->prepare("SELECT value FROM sign_values WHERE sign_id = :id");
    $stmt->bindValue(':id', $signId, SQLITE3_TEXT);
    $result = $stmt->execute();

    $values = [];
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $values[] = $row['value'];
    }
    return $values;
}

/**
 * Get translations for artifact
 */
function getTranslations(string $pNumber): array {
    $db = getDB();
    $stmt = $db->prepare("
        SELECT * FROM translations
        WHERE p_number = :p_number
        ORDER BY language ASC
    ");
    $stmt->bindValue(':p_number', $pNumber, SQLITE3_TEXT);
    $result = $stmt->execute();

    $translations = [];
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $translations[] = $row;
    }
    return $translations;
}

/**
 * Get museum name by code
 */
function getMuseumName(string $code): ?array {
    $db = getDB();
    $stmt = $db->prepare("SELECT name, city, country FROM museums WHERE code = :code");
    $stmt->bindValue(':code', $code, SQLITE3_TEXT);
    $result = $stmt->execute();
    $row = $result->fetchArray(SQLITE3_ASSOC);
    return $row ?: null;
}

/**
 * Get excavation site name by code
 */
function getExcavationSiteName(string $code): ?array {
    $db = getDB();
    $stmt = $db->prepare("SELECT name, ancient_name, modern_country FROM excavation_sites WHERE code = :code");
    $stmt->bindValue(':code', $code, SQLITE3_TEXT);
    $result = $stmt->execute();
    $row = $result->fetchArray(SQLITE3_ASSOC);
    return $row ?: null;
}

/**
 * Parse museum code from museum_no field
 * Returns array with 'code' and 'number' parts
 */
function parseMuseumNumber(string $museumNo): array {
    // Pattern: code followed by space and number (e.g., "BM 116625")
    if (preg_match('/^([A-Za-z]+)\s+(.+)$/', trim($museumNo), $matches)) {
        return ['code' => $matches[1], 'number' => $matches[2], 'full' => $museumNo];
    }
    return ['code' => null, 'number' => $museumNo, 'full' => $museumNo];
}

/**
 * Parse excavation code from excavation_no field
 * Returns array with 'code' and 'number' parts
 */
function parseExcavationNumber(string $excavationNo): array {
    // Pattern: code followed by space and number (e.g., "W 16728,2")
    if (preg_match('/^([A-Za-z][A-Za-z0-9\-\.]*)\s+(.+)$/', trim($excavationNo), $matches)) {
        return ['code' => $matches[1], 'number' => $matches[2], 'full' => $excavationNo];
    }
    return ['code' => null, 'number' => $excavationNo, 'full' => $excavationNo];
}

/**
 * Get language filter stats grouped by root language
 */
function getLanguageStats(): array {
    $db = getDB();
    $result = $db->query("
        SELECT language, root_language, tablet_count
        FROM language_stats
        ORDER BY tablet_count DESC
    ");

    $grouped = [];
    $rootTotals = [];

    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $root = $row['root_language'];
        if (!isset($grouped[$root])) {
            $grouped[$root] = [];
            $rootTotals[$root] = 0;
        }
        $grouped[$root][] = [
            'value' => $row['language'],
            'count' => (int)$row['tablet_count']
        ];
        $rootTotals[$root] += (int)$row['tablet_count'];
    }

    // Sort roots by total count
    arsort($rootTotals);

    $stats = [];
    foreach ($rootTotals as $root => $total) {
        $stats[] = [
            'group' => $root,
            'total' => $total,
            'items' => $grouped[$root]
        ];
    }

    return $stats;
}

/**
 * Get period filter stats grouped by period group
 */
function getPeriodStats(): array {
    $db = getDB();
    $result = $db->query("
        SELECT period, period_group, sort_order, tablet_count
        FROM period_stats
        ORDER BY sort_order ASC, tablet_count DESC
    ");

    $grouped = [];
    $rootTotals = [];
    $rootOrder = [];

    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $group = $row['period_group'];
        if (!isset($grouped[$group])) {
            $grouped[$group] = [];
            $rootTotals[$group] = 0;
            $rootOrder[$group] = (int)$row['sort_order'];
        }
        $grouped[$group][] = [
            'value' => $row['period'],
            'count' => (int)$row['tablet_count']
        ];
        $rootTotals[$group] += (int)$row['tablet_count'];
    }

    // Sort by chronological order
    asort($rootOrder);

    $stats = [];
    foreach ($rootOrder as $group => $order) {
        $stats[] = [
            'group' => $group,
            'total' => $rootTotals[$group],
            'items' => $grouped[$group]
        ];
    }

    return $stats;
}

/**
 * Get provenience filter stats grouped by region
 */
function getProvenienceStats(): array {
    $db = getDB();
    $result = $db->query("
        SELECT provenience, region, tablet_count
        FROM provenience_stats
        ORDER BY tablet_count DESC
    ");

    $grouped = [];
    $rootTotals = [];

    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $region = $row['region'];
        if (!isset($grouped[$region])) {
            $grouped[$region] = [];
            $rootTotals[$region] = 0;
        }
        $grouped[$region][] = [
            'value' => $row['provenience'],
            'count' => (int)$row['tablet_count']
        ];
        $rootTotals[$region] += (int)$row['tablet_count'];
    }

    // Sort regions by total count
    arsort($rootTotals);

    $stats = [];
    foreach ($rootTotals as $region => $total) {
        $stats[] = [
            'group' => $region,
            'total' => $total,
            'items' => $grouped[$region]
        ];
    }

    return $stats;
}

/**
 * Get genre filter stats grouped by category
 */
function getGenreStats(): array {
    $db = getDB();
    $result = $db->query("
        SELECT genre, category, tablet_count
        FROM genre_stats
        ORDER BY tablet_count DESC
    ");

    $grouped = [];
    $rootTotals = [];

    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $cat = $row['category'];
        if (!isset($grouped[$cat])) {
            $grouped[$cat] = [];
            $rootTotals[$cat] = 0;
        }
        $grouped[$cat][] = [
            'value' => $row['genre'],
            'count' => (int)$row['tablet_count']
        ];
        $rootTotals[$cat] += (int)$row['tablet_count'];
    }

    // Sort categories by total count
    arsort($rootTotals);

    $stats = [];
    foreach ($rootTotals as $cat => $total) {
        $stats[] = [
            'group' => $cat,
            'total' => $total,
            'items' => $grouped[$cat]
        ];
    }

    return $stats;
}

/**
 * Get filter-aware language stats
 * Counts are updated based on currently active filters
 */
function getFilteredLanguageStats(array $filters): array {
    $db = getDB();

    // Build WHERE clause from filters (exclude language filter)
    $where = [];
    $params = [];

    // Period filter
    if (!empty($filters['periods'])) {
        $periodConditions = [];
        foreach ($filters['periods'] as $i => $period) {
            $periodConditions[] = "a.period = :period{$i}";
            $params[":period{$i}"] = $period;
        }
        $where[] = '(' . implode(' OR ', $periodConditions) . ')';
    }

    // Site filter
    if (!empty($filters['sites'])) {
        $siteConditions = [];
        foreach ($filters['sites'] as $i => $site) {
            $siteConditions[] = "a.provenience LIKE :site{$i}";
            $params[":site{$i}"] = '%' . $site . '%';
        }
        $where[] = '(' . implode(' OR ', $siteConditions) . ')';
    }

    // Genre filter
    if (!empty($filters['genres'])) {
        $genreConditions = [];
        foreach ($filters['genres'] as $i => $genre) {
            $genreConditions[] = "a.genre LIKE :genre{$i}";
            $params[":genre{$i}"] = '%' . $genre . '%';
        }
        $where[] = '(' . implode(' OR ', $genreConditions) . ')';
    }

    // Pipeline filter
    if (!empty($filters['pipeline'])) {
        switch ($filters['pipeline']) {
            case 'complete':
                $where[] = "ps.has_image = 1 AND ps.has_atf = 1 AND ps.has_lemmas = 1 AND ps.has_translation = 1";
                break;
            case 'has_image':
                $where[] = "ps.has_image = 1";
                break;
            case 'has_translation':
                $where[] = "ps.has_translation = 1";
                break;
            case 'any_digitization':
                $where[] = "(ps.has_atf = 1 OR ps.has_sign_annotations = 1)";
                break;
            case 'human_transcription':
                $where[] = "ps.has_atf = 1";
                break;
            case 'machine_ocr':
                $where[] = "ps.has_sign_annotations = 1";
                break;
            case 'no_digitization':
                $where[] = "(ps.has_atf IS NULL OR ps.has_atf = 0) AND (ps.has_sign_annotations IS NULL OR ps.has_sign_annotations = 0)";
                break;
        }
    }

    // Search filter
    $inscriptionJoin = "";
    if (!empty($filters['search'])) {
        $inscriptionJoin = "LEFT JOIN inscriptions i ON a.p_number = i.p_number AND i.is_latest = 1";
        $searchTerms = array_map('trim', explode('||', $filters['search']));

        if (count($searchTerms) > 1) {
            $searchConditions = [];
            foreach ($searchTerms as $i => $term) {
                if (!empty($term)) {
                    $searchConditions[] = "(a.p_number LIKE :search{$i} OR a.designation LIKE :search{$i} OR i.transliteration_clean LIKE :search{$i})";
                    $params[":search{$i}"] = '%' . $term . '%';
                }
            }
            if (!empty($searchConditions)) {
                $where[] = "(" . implode(' OR ', $searchConditions) . ")";
            }
        } else {
            $where[] = "(a.p_number LIKE :search OR a.designation LIKE :search OR i.transliteration_clean LIKE :search)";
            $params[':search'] = '%' . $filters['search'] . '%';
        }
    }

    $whereClause = $where ? 'WHERE ' . implode(' AND ', $where) : '';

    // Efficient query: count directly from artifacts.language field
    // This avoids the expensive cross-join with language_stats
    $sql = "
        SELECT a.language, COUNT(DISTINCT a.p_number) as tablet_count
        FROM artifacts a
        LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
        $inscriptionJoin
        $whereClause
        GROUP BY a.language
        HAVING tablet_count > 0
        ORDER BY tablet_count DESC
    ";

    $stmt = $db->prepare($sql);
    foreach ($params as $key => $val) {
        $stmt->bindValue($key, $val);
    }
    $result = $stmt->execute();

    // Get language metadata for grouping
    $langMeta = [];
    $metaResult = $db->query("SELECT language, root_language FROM language_stats");
    while ($row = $metaResult->fetchArray(SQLITE3_ASSOC)) {
        $langMeta[$row['language']] = $row['root_language'];
    }

    // Group results by root language
    $grouped = [];
    $rootTotals = [];

    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $lang = $row['language'];
        // Extract individual languages from comma-separated field
        $langs = array_map('trim', explode(',', $lang));

        foreach ($langs as $singleLang) {
            if (empty($singleLang)) continue;

            $root = $langMeta[$singleLang] ?? 'Other';
            if (!isset($grouped[$root])) {
                $grouped[$root] = [];
                $rootTotals[$root] = 0;
            }

            // Find or create entry for this language
            $found = false;
            foreach ($grouped[$root] as &$item) {
                if ($item['value'] === $singleLang) {
                    $item['count'] += (int)$row['tablet_count'];
                    $found = true;
                    break;
                }
            }
            unset($item);

            if (!$found) {
                $grouped[$root][] = [
                    'value' => $singleLang,
                    'count' => (int)$row['tablet_count']
                ];
            }
            $rootTotals[$root] += (int)$row['tablet_count'];
        }
    }

    // Sort roots by total count
    arsort($rootTotals);

    // Sort items within each group
    foreach ($grouped as &$items) {
        usort($items, fn($a, $b) => $b['count'] - $a['count']);
    }
    unset($items);

    $stats = [];
    foreach ($rootTotals as $root => $total) {
        $stats[] = [
            'group' => $root,
            'total' => $total,
            'items' => $grouped[$root]
        ];
    }

    return $stats;
}

/**
 * Get filter-aware period stats
 */
function getFilteredPeriodStats(array $filters): array {
    $db = getDB();

    // Build WHERE clause (exclude period filter)
    $where = [];
    $params = [];

    // Language filter
    if (!empty($filters['languages'])) {
        $langConditions = [];
        foreach ($filters['languages'] as $i => $lang) {
            $langConditions[] = "a.language LIKE :lang{$i}";
            $params[":lang{$i}"] = '%' . $lang . '%';
        }
        $where[] = '(' . implode(' OR ', $langConditions) . ')';
    }

    // Site filter
    if (!empty($filters['sites'])) {
        $siteConditions = [];
        foreach ($filters['sites'] as $i => $site) {
            $siteConditions[] = "a.provenience LIKE :site{$i}";
            $params[":site{$i}"] = '%' . $site . '%';
        }
        $where[] = '(' . implode(' OR ', $siteConditions) . ')';
    }

    // Genre filter
    if (!empty($filters['genres'])) {
        $genreConditions = [];
        foreach ($filters['genres'] as $i => $genre) {
            $genreConditions[] = "a.genre LIKE :genre{$i}";
            $params[":genre{$i}"] = '%' . $genre . '%';
        }
        $where[] = '(' . implode(' OR ', $genreConditions) . ')';
    }

    // Pipeline filter
    if (!empty($filters['pipeline'])) {
        switch ($filters['pipeline']) {
            case 'complete':
                $where[] = "ps.has_image = 1 AND ps.has_atf = 1 AND ps.has_lemmas = 1 AND ps.has_translation = 1";
                break;
            case 'has_image':
                $where[] = "ps.has_image = 1";
                break;
            case 'has_translation':
                $where[] = "ps.has_translation = 1";
                break;
            case 'any_digitization':
                $where[] = "(ps.has_atf = 1 OR ps.has_sign_annotations = 1)";
                break;
            case 'human_transcription':
                $where[] = "ps.has_atf = 1";
                break;
            case 'machine_ocr':
                $where[] = "ps.has_sign_annotations = 1";
                break;
            case 'no_digitization':
                $where[] = "(ps.has_atf IS NULL OR ps.has_atf = 0) AND (ps.has_sign_annotations IS NULL OR ps.has_sign_annotations = 0)";
                break;
        }
    }

    // Search filter
    // Supports OR operator: "P000001 || P000025 || P010663"
    $inscriptionJoin = "";
    if (!empty($filters['search'])) {
        $inscriptionJoin = "LEFT JOIN inscriptions i ON a.p_number = i.p_number AND i.is_latest = 1";
        $searchTerms = array_map('trim', explode('||', $filters['search']));

        if (count($searchTerms) > 1) {
            // Multiple terms - build OR condition for each
            $searchConditions = [];
            foreach ($searchTerms as $i => $term) {
                if (!empty($term)) {
                    $searchConditions[] = "(a.p_number LIKE :search{$i} OR a.designation LIKE :search{$i} OR i.transliteration_clean LIKE :search{$i})";
                    $params[":search{$i}"] = '%' . $term . '%';
                }
            }
            if (!empty($searchConditions)) {
                $where[] = "(" . implode(' OR ', $searchConditions) . ")";
            }
        } else {
            // Single term - use simple search
            $where[] = "(a.p_number LIKE :search OR a.designation LIKE :search OR i.transliteration_clean LIKE :search)";
            $params[':search'] = '%' . $filters['search'] . '%';
        }
    }

    $whereClause = $where ? 'WHERE ' . implode(' AND ', $where) : '';

    // Efficient query: count directly from artifacts.period
    $sql = "
        SELECT a.period, COUNT(DISTINCT a.p_number) as tablet_count
        FROM artifacts a
        LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
        $inscriptionJoin
        $whereClause
        GROUP BY a.period
        HAVING tablet_count > 0
        ORDER BY tablet_count DESC
    ";

    $stmt = $db->prepare($sql);
    foreach ($params as $key => $val) {
        $stmt->bindValue($key, $val);
    }
    $result = $stmt->execute();

    // Get period metadata for grouping
    $periodMeta = [];
    $metaResult = $db->query("SELECT period, period_group, sort_order FROM period_stats");
    while ($row = $metaResult->fetchArray(SQLITE3_ASSOC)) {
        $periodMeta[$row['period']] = [
            'group' => $row['period_group'],
            'sort_order' => (int)$row['sort_order']
        ];
    }

    $grouped = [];
    $rootTotals = [];
    $rootOrder = [];

    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $period = $row['period'];
        if (empty($period)) continue;

        $meta = $periodMeta[$period] ?? ['group' => 'Other', 'sort_order' => 999];
        $group = $meta['group'];

        if (!isset($grouped[$group])) {
            $grouped[$group] = [];
            $rootTotals[$group] = 0;
            $rootOrder[$group] = $meta['sort_order'];
        }
        $grouped[$group][] = [
            'value' => $period,
            'count' => (int)$row['tablet_count']
        ];
        $rootTotals[$group] += (int)$row['tablet_count'];
    }

    asort($rootOrder);

    // Sort items within each group by count
    foreach ($grouped as &$items) {
        usort($items, fn($a, $b) => $b['count'] - $a['count']);
    }
    unset($items);

    $stats = [];
    foreach ($rootOrder as $group => $order) {
        $stats[] = [
            'group' => $group,
            'total' => $rootTotals[$group],
            'items' => $grouped[$group]
        ];
    }

    return $stats;
}

/**
 * Get filter-aware provenience stats
 */
function getFilteredProvenienceStats(array $filters): array {
    $db = getDB();

    // Build WHERE clause (exclude site filter)
    $where = [];
    $params = [];

    // Language filter
    if (!empty($filters['languages'])) {
        $langConditions = [];
        foreach ($filters['languages'] as $i => $lang) {
            $langConditions[] = "a.language LIKE :lang{$i}";
            $params[":lang{$i}"] = '%' . $lang . '%';
        }
        $where[] = '(' . implode(' OR ', $langConditions) . ')';
    }

    // Period filter
    if (!empty($filters['periods'])) {
        $periodConditions = [];
        foreach ($filters['periods'] as $i => $period) {
            $periodConditions[] = "a.period = :period{$i}";
            $params[":period{$i}"] = $period;
        }
        $where[] = '(' . implode(' OR ', $periodConditions) . ')';
    }

    // Genre filter
    if (!empty($filters['genres'])) {
        $genreConditions = [];
        foreach ($filters['genres'] as $i => $genre) {
            $genreConditions[] = "a.genre LIKE :genre{$i}";
            $params[":genre{$i}"] = '%' . $genre . '%';
        }
        $where[] = '(' . implode(' OR ', $genreConditions) . ')';
    }

    // Pipeline filter
    if (!empty($filters['pipeline'])) {
        switch ($filters['pipeline']) {
            case 'complete':
                $where[] = "ps.has_image = 1 AND ps.has_atf = 1 AND ps.has_lemmas = 1 AND ps.has_translation = 1";
                break;
            case 'has_image':
                $where[] = "ps.has_image = 1";
                break;
            case 'has_translation':
                $where[] = "ps.has_translation = 1";
                break;
            case 'any_digitization':
                $where[] = "(ps.has_atf = 1 OR ps.has_sign_annotations = 1)";
                break;
            case 'human_transcription':
                $where[] = "ps.has_atf = 1";
                break;
            case 'machine_ocr':
                $where[] = "ps.has_sign_annotations = 1";
                break;
            case 'no_digitization':
                $where[] = "(ps.has_atf IS NULL OR ps.has_atf = 0) AND (ps.has_sign_annotations IS NULL OR ps.has_sign_annotations = 0)";
                break;
        }
    }

    // Search filter
    // Supports OR operator: "P000001 || P000025 || P010663"
    $inscriptionJoin = "";
    if (!empty($filters['search'])) {
        $inscriptionJoin = "LEFT JOIN inscriptions i ON a.p_number = i.p_number AND i.is_latest = 1";
        $searchTerms = array_map('trim', explode('||', $filters['search']));

        if (count($searchTerms) > 1) {
            // Multiple terms - build OR condition for each
            $searchConditions = [];
            foreach ($searchTerms as $i => $term) {
                if (!empty($term)) {
                    $searchConditions[] = "(a.p_number LIKE :search{$i} OR a.designation LIKE :search{$i} OR i.transliteration_clean LIKE :search{$i})";
                    $params[":search{$i}"] = '%' . $term . '%';
                }
            }
            if (!empty($searchConditions)) {
                $where[] = "(" . implode(' OR ', $searchConditions) . ")";
            }
        } else {
            // Single term - use simple search
            $where[] = "(a.p_number LIKE :search OR a.designation LIKE :search OR i.transliteration_clean LIKE :search)";
            $params[':search'] = '%' . $filters['search'] . '%';
        }
    }

    $whereClause = $where ? 'WHERE ' . implode(' AND ', $where) : '';

    // Efficient query: count directly from artifacts.provenience
    $sql = "
        SELECT a.provenience, COUNT(DISTINCT a.p_number) as tablet_count
        FROM artifacts a
        LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
        $inscriptionJoin
        $whereClause
        GROUP BY a.provenience
        HAVING tablet_count > 0
        ORDER BY tablet_count DESC
    ";

    $stmt = $db->prepare($sql);
    foreach ($params as $key => $val) {
        $stmt->bindValue($key, $val);
    }
    $result = $stmt->execute();

    // Get provenience metadata for grouping
    $provMeta = [];
    $metaResult = $db->query("SELECT provenience, region FROM provenience_stats");
    while ($row = $metaResult->fetchArray(SQLITE3_ASSOC)) {
        $provMeta[$row['provenience']] = $row['region'];
    }

    $grouped = [];
    $rootTotals = [];

    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $prov = $row['provenience'];
        if (empty($prov)) continue;

        // Try to find region from metadata, default to 'Other'
        $region = $provMeta[$prov] ?? 'Other';

        if (!isset($grouped[$region])) {
            $grouped[$region] = [];
            $rootTotals[$region] = 0;
        }

        $grouped[$region][] = [
            'value' => $prov,
            'count' => (int)$row['tablet_count']
        ];
        $rootTotals[$region] += (int)$row['tablet_count'];
    }

    arsort($rootTotals);

    // Sort items within each group
    foreach ($grouped as &$items) {
        usort($items, fn($a, $b) => $b['count'] - $a['count']);
    }
    unset($items);

    $stats = [];
    foreach ($rootTotals as $region => $total) {
        $stats[] = [
            'group' => $region,
            'total' => $total,
            'items' => $grouped[$region]
        ];
    }

    return $stats;
}

/**
 * Get filter-aware genre stats
 */
function getFilteredGenreStats(array $filters): array {
    $db = getDB();

    // Build WHERE clause (exclude genre filter)
    $where = [];
    $params = [];

    // Language filter
    if (!empty($filters['languages'])) {
        $langConditions = [];
        foreach ($filters['languages'] as $i => $lang) {
            $langConditions[] = "a.language LIKE :lang{$i}";
            $params[":lang{$i}"] = '%' . $lang . '%';
        }
        $where[] = '(' . implode(' OR ', $langConditions) . ')';
    }

    // Period filter
    if (!empty($filters['periods'])) {
        $periodConditions = [];
        foreach ($filters['periods'] as $i => $period) {
            $periodConditions[] = "a.period = :period{$i}";
            $params[":period{$i}"] = $period;
        }
        $where[] = '(' . implode(' OR ', $periodConditions) . ')';
    }

    // Site filter
    if (!empty($filters['sites'])) {
        $siteConditions = [];
        foreach ($filters['sites'] as $i => $site) {
            $siteConditions[] = "a.provenience LIKE :site{$i}";
            $params[":site{$i}"] = '%' . $site . '%';
        }
        $where[] = '(' . implode(' OR ', $siteConditions) . ')';
    }

    // Pipeline filter
    if (!empty($filters['pipeline'])) {
        switch ($filters['pipeline']) {
            case 'complete':
                $where[] = "ps.has_image = 1 AND ps.has_atf = 1 AND ps.has_lemmas = 1 AND ps.has_translation = 1";
                break;
            case 'has_image':
                $where[] = "ps.has_image = 1";
                break;
            case 'has_translation':
                $where[] = "ps.has_translation = 1";
                break;
            case 'any_digitization':
                $where[] = "(ps.has_atf = 1 OR ps.has_sign_annotations = 1)";
                break;
            case 'human_transcription':
                $where[] = "ps.has_atf = 1";
                break;
            case 'machine_ocr':
                $where[] = "ps.has_sign_annotations = 1";
                break;
            case 'no_digitization':
                $where[] = "(ps.has_atf IS NULL OR ps.has_atf = 0) AND (ps.has_sign_annotations IS NULL OR ps.has_sign_annotations = 0)";
                break;
        }
    }

    // Search filter
    // Supports OR operator: "P000001 || P000025 || P010663"
    $inscriptionJoin = "";
    if (!empty($filters['search'])) {
        $inscriptionJoin = "LEFT JOIN inscriptions i ON a.p_number = i.p_number AND i.is_latest = 1";
        $searchTerms = array_map('trim', explode('||', $filters['search']));

        if (count($searchTerms) > 1) {
            // Multiple terms - build OR condition for each
            $searchConditions = [];
            foreach ($searchTerms as $i => $term) {
                if (!empty($term)) {
                    $searchConditions[] = "(a.p_number LIKE :search{$i} OR a.designation LIKE :search{$i} OR i.transliteration_clean LIKE :search{$i})";
                    $params[":search{$i}"] = '%' . $term . '%';
                }
            }
            if (!empty($searchConditions)) {
                $where[] = "(" . implode(' OR ', $searchConditions) . ")";
            }
        } else {
            // Single term - use simple search
            $where[] = "(a.p_number LIKE :search OR a.designation LIKE :search OR i.transliteration_clean LIKE :search)";
            $params[':search'] = '%' . $filters['search'] . '%';
        }
    }

    $whereClause = $where ? 'WHERE ' . implode(' AND ', $where) : '';

    // Efficient query: count directly from artifacts.genre
    $sql = "
        SELECT a.genre, COUNT(DISTINCT a.p_number) as tablet_count
        FROM artifacts a
        LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
        $inscriptionJoin
        $whereClause
        GROUP BY a.genre
        HAVING tablet_count > 0
        ORDER BY tablet_count DESC
    ";

    $stmt = $db->prepare($sql);
    foreach ($params as $key => $val) {
        $stmt->bindValue($key, $val);
    }
    $result = $stmt->execute();

    // Get genre metadata for grouping
    $genreMeta = [];
    $metaResult = $db->query("SELECT genre, category FROM genre_stats");
    while ($row = $metaResult->fetchArray(SQLITE3_ASSOC)) {
        $genreMeta[$row['genre']] = $row['category'];
    }

    $grouped = [];
    $rootTotals = [];

    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $genre = $row['genre'];
        if (empty($genre)) continue;

        // Try to find category from metadata, default to 'Other'
        $cat = $genreMeta[$genre] ?? 'Other';

        if (!isset($grouped[$cat])) {
            $grouped[$cat] = [];
            $rootTotals[$cat] = 0;
        }

        $grouped[$cat][] = [
            'value' => $genre,
            'count' => (int)$row['tablet_count']
        ];
        $rootTotals[$cat] += (int)$row['tablet_count'];
    }

    arsort($rootTotals);

    // Sort items within each group
    foreach ($grouped as &$items) {
        usort($items, fn($a, $b) => $b['count'] - $a['count']);
    }
    unset($items);

    $stats = [];
    foreach ($rootTotals as $cat => $total) {
        $stats[] = [
            'group' => $cat,
            'total' => $total,
            'items' => $grouped[$cat]
        ];
    }

    return $stats;
}

/**
 * Get writable database connection (for write operations)
 */
function getWritableDB(): SQLite3 {
    $db = new SQLite3(DB_PATH, SQLITE3_OPEN_READWRITE);
    $db->enableExceptions(true);
    return $db;
}

/**
 * Get all collections with tablet counts
 */
function getCollections(): array {
    $db = getDB();
    $result = $db->query("
        SELECT
            c.collection_id,
            c.name,
            c.description,
            c.image_path,
            c.created_at,
            c.updated_at,
            COUNT(cm.p_number) as tablet_count
        FROM collections c
        LEFT JOIN collection_members cm ON c.collection_id = cm.collection_id
        GROUP BY c.collection_id
        ORDER BY c.created_at DESC
    ");

    $collections = [];
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $collections[] = [
            'collection_id' => (int)$row['collection_id'],
            'name' => $row['name'],
            'description' => $row['description'],
            'image_path' => $row['image_path'],
            'created_at' => $row['created_at'],
            'updated_at' => $row['updated_at'],
            'tablet_count' => (int)$row['tablet_count']
        ];
    }
    return $collections;
}

/**
 * Get single collection by ID
 */
function getCollection(int $collectionId): ?array {
    $db = getDB();
    $stmt = $db->prepare("
        SELECT
            c.collection_id,
            c.name,
            c.description,
            c.image_path,
            c.created_at,
            c.updated_at,
            COUNT(cm.p_number) as tablet_count
        FROM collections c
        LEFT JOIN collection_members cm ON c.collection_id = cm.collection_id
        WHERE c.collection_id = :id
        GROUP BY c.collection_id
    ");
    $stmt->bindValue(':id', $collectionId, SQLITE3_INTEGER);
    $result = $stmt->execute();
    $row = $result->fetchArray(SQLITE3_ASSOC);

    if (!$row) {
        return null;
    }

    return [
        'collection_id' => (int)$row['collection_id'],
        'name' => $row['name'],
        'description' => $row['description'],
        'image_path' => $row['image_path'],
        'created_at' => $row['created_at'],
        'updated_at' => $row['updated_at'],
        'tablet_count' => (int)$row['tablet_count']
    ];
}

/**
 * Get tablets in a collection with full metadata
 */
function getCollectionTablets(int $collectionId, int $limit = 24, int $offset = 0): array {
    $db = getDB();
    $stmt = $db->prepare("
        SELECT
            a.*,
            ps.has_image,
            ps.has_ocr,
            ps.ocr_confidence,
            ps.has_atf,
            ps.atf_source,
            ps.has_lemmas,
            ps.lemma_coverage,
            ps.has_translation,
            ps.has_sign_annotations,
            ps.quality_score,
            cm.added_at
        FROM collection_members cm
        JOIN artifacts a ON cm.p_number = a.p_number
        LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
        WHERE cm.collection_id = :collection_id
        ORDER BY cm.added_at DESC
        LIMIT :limit OFFSET :offset
    ");
    $stmt->bindValue(':collection_id', $collectionId, SQLITE3_INTEGER);
    $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);
    $stmt->bindValue(':offset', $offset, SQLITE3_INTEGER);
    $result = $stmt->execute();

    $tablets = [];
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $tablets[] = $row;
    }
    return $tablets;
}

/**
 * Get count of tablets in collection
 */
function getCollectionTabletCount(int $collectionId): int {
    $db = getDB();
    $stmt = $db->prepare("
        SELECT COUNT(*) as count
        FROM collection_members
        WHERE collection_id = :collection_id
    ");
    $stmt->bindValue(':collection_id', $collectionId, SQLITE3_INTEGER);
    $result = $stmt->execute();
    $row = $result->fetchArray(SQLITE3_ASSOC);
    return (int)$row['count'];
}

/**
 * Create new collection
 * Returns the new collection ID
 */
function createCollection(string $name, string $description = ''): int {
    $db = getWritableDB();
    $stmt = $db->prepare("
        INSERT INTO collections (name, description)
        VALUES (:name, :description)
    ");
    $stmt->bindValue(':name', $name, SQLITE3_TEXT);
    $stmt->bindValue(':description', $description, SQLITE3_TEXT);
    $stmt->execute();
    return (int)$db->lastInsertRowID();
}

/**
 * Update collection metadata
 */
function updateCollection(int $collectionId, string $name, string $description): bool {
    $db = getWritableDB();
    $stmt = $db->prepare("
        UPDATE collections
        SET name = :name,
            description = :description,
            updated_at = CURRENT_TIMESTAMP
        WHERE collection_id = :id
    ");
    $stmt->bindValue(':id', $collectionId, SQLITE3_INTEGER);
    $stmt->bindValue(':name', $name, SQLITE3_TEXT);
    $stmt->bindValue(':description', $description, SQLITE3_TEXT);
    return (bool)$stmt->execute();
}

/**
 * Delete collection
 */
function deleteCollection(int $collectionId): bool {
    $db = getWritableDB();
    $stmt = $db->prepare("DELETE FROM collections WHERE collection_id = :id");
    $stmt->bindValue(':id', $collectionId, SQLITE3_INTEGER);
    return (bool)$stmt->execute();
}

/**
 * Add tablet to collection
 * Returns true on success, false if already exists
 */
function addTabletToCollection(int $collectionId, string $pNumber): bool {
    $db = getWritableDB();
    try {
        $stmt = $db->prepare("
            INSERT INTO collection_members (collection_id, p_number)
            VALUES (:collection_id, :p_number)
        ");
        $stmt->bindValue(':collection_id', $collectionId, SQLITE3_INTEGER);
        $stmt->bindValue(':p_number', $pNumber, SQLITE3_TEXT);
        return (bool)$stmt->execute();
    } catch (Exception $e) {
        // Already exists or other error
        return false;
    }
}

/**
 * Remove tablet from collection
 */
function removeTabletFromCollection(int $collectionId, string $pNumber): bool {
    $db = getWritableDB();
    $stmt = $db->prepare("
        DELETE FROM collection_members
        WHERE collection_id = :collection_id AND p_number = :p_number
    ");
    $stmt->bindValue(':collection_id', $collectionId, SQLITE3_INTEGER);
    $stmt->bindValue(':p_number', $pNumber, SQLITE3_TEXT);
    return (bool)$stmt->execute();
}

/**
 * Check if tablet is in collection
 */
function isTabletInCollection(int $collectionId, string $pNumber): bool {
    $db = getDB();
    $stmt = $db->prepare("
        SELECT COUNT(*) as count
        FROM collection_members
        WHERE collection_id = :collection_id AND p_number = :p_number
    ");
    $stmt->bindValue(':collection_id', $collectionId, SQLITE3_INTEGER);
    $stmt->bindValue(':p_number', $pNumber, SQLITE3_TEXT);
    $result = $stmt->execute();
    $row = $result->fetchArray(SQLITE3_ASSOC);
    return (int)$row['count'] > 0;
}

/**
 * Get first N tablet thumbnails for collection preview
 */
function getCollectionPreviewTablets(int $collectionId, int $limit = 4): array {
    $db = getDB();
    $stmt = $db->prepare("
        SELECT a.p_number, a.designation
        FROM collection_members cm
        JOIN artifacts a ON cm.p_number = a.p_number
        WHERE cm.collection_id = :collection_id
        ORDER BY cm.added_at DESC
        LIMIT :limit
    ");
    $stmt->bindValue(':collection_id', $collectionId, SQLITE3_INTEGER);
    $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);
    $result = $stmt->execute();

    $tablets = [];
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $tablets[] = $row;
    }
    return $tablets;
}
