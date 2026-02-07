<?php
/**
 * Database connection for Glintstone
 */

define('DB_PATH', dirname(__DIR__, 3) . '/database/glintstone.db');

function getDB(): SQLite3 {
    static $db = null;

    if ($db === null) {
        $db = new SQLite3(DB_PATH, SQLITE3_OPEN_READONLY);
        $db->enableExceptions(true);
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
