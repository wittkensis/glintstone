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
